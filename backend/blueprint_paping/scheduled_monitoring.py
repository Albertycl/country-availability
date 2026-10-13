import os
from flask import Flask, render_template, redirect, url_for, jsonify, session, json, Blueprint, request, current_app
import requests
import time
import re
import datetime
from datetime import datetime, timedelta
import socket
from flask_cors import CORS, cross_origin
import paramiko
from paramiko import SSHClient, SSHConfig
import pytz
from model import db, a01_probe_list, a80_scheduled_domains, a90_scheduled_results, a40_availiblity_for_each_country
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED, EVENT_JOB_MAX_INSTANCES
import atexit
import threading

scheduled_monitoring = Blueprint("scheduled_monitoring", __name__)
CORS(scheduled_monitoring)

# GMT+8 timezone for consistent timestamp handling
GMT_PLUS_8 = pytz.timezone('Asia/Shanghai')

def get_gmt8_now():
    """Get current timestamp in GMT+8 timezone"""
    return datetime.now(GMT_PLUS_8)

def get_availability_from_main_system(domain_name, country):
    """Get availability from the same data source as the main system (a40_availiblity_for_each_country)"""
    try:
        print(f"[SCHEDULER] 🔍 get_availability_from_main_system() called for {domain_name} in {country}")
        # Look up availability in the same table that the main system uses
        availability_record = a40_availiblity_for_each_country.query.filter_by(
            testing_which_url=domain_name,
            which_country=country
        ).order_by(a40_availiblity_for_each_country.wrote_to_db_time.desc()).first()
        
        if availability_record:
            availability_percentage = float(availability_record.availiblity)
            print(f"[SCHEDULER] 📈 Using main system availability data: {availability_percentage}% for {domain_name} in {country}")
            print(f"[SCHEDULER] 📊 Found existing availability record from main system")
            
            # Return in the same format as perform_domain_check for consistency
            return {
                'availability': availability_percentage,
                'successful_probes': int(availability_percentage * 52 / 100),  # Estimate based on typical probe count
                'total_probes': 52  # Typical number of probes per country
            }
        else:
            print(f"[SCHEDULER] 🚫 No main system data found for {domain_name} in {country}, falling back to real-time check")
            print(f"[SCHEDULER] 🔄 Initiating fallback to real-time probe checking")
            # Fallback to real-time checking if no main system data exists
            return perform_domain_check(domain_name, country)
            
    except Exception as e:
        print(f"[SCHEDULER] 💥 Error getting main system availability data: {e}, falling back to real-time check")
        print(f"[SCHEDULER] 🔥 Exception in get_availability_from_main_system(): {str(e)}")
        # Fallback to real-time checking on error
        return perform_domain_check(domain_name, country)

# Background scheduler for periodic domain checking with misfire handling
scheduler = BackgroundScheduler()

# Configure scheduler to handle job misfires gracefully
scheduler.configure(
    job_defaults={
        'misfire_grace_time': 300,  # Allow jobs to run up to 5 minutes late
        'coalesce': True,  # Coalesce missed jobs to prevent queue buildup
        'max_instances': 1  # Prevent multiple instances of same job
    }
)

# Add event listeners for job monitoring
def job_listener(event):
    """Listen for scheduler events to track job performance"""
    if event.code == EVENT_JOB_MISSED:
        print(f"[SCHEDULER] ⚠️  JOB MISSED: {event.job_id} - was supposed to run at {event.scheduled_run_time}")
    elif event.code == EVENT_JOB_ERROR:
        print(f"[SCHEDULER] ❌ JOB ERROR: {event.job_id} - {event.exception}")
    elif event.code == EVENT_JOB_EXECUTED:
        print(f"[SCHEDULER] ✅ JOB EXECUTED: {event.job_id} - completed successfully")
    elif event.code == EVENT_JOB_MAX_INSTANCES:
        print(f"[SCHEDULER] 🚫 JOB MAX INSTANCES: {event.job_id} - maximum instances reached")

# Add the listener before starting
scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED | EVENT_JOB_MAX_INSTANCES)

scheduler.start()

# Configuration for automatic retry mechanism
AUTO_RETRY_CONFIG = {
    'enabled': True,  # Enable/disable automatic retries
    'late_retry_threshold_multiplier': 1.5,  # Retry when > 1.5x interval since last check
    'overdue_retry_threshold_multiplier': 2.0,  # Aggressive retry when > 2x interval
    'max_retry_attempts': 3,  # Maximum retry attempts per domain
    'retry_interval_minutes': 5,  # Base interval between retry attempts
    'concurrent_retries': 5,  # Maximum concurrent retry operations
    'check_interval_minutes': 2  # How often to scan for late/overdue domains
}

# Track retry attempts per domain to avoid infinite loops
retry_attempts = {}
currently_retrying = set()  # Set of domain IDs currently being retried

# Function to restore existing scheduled jobs on startup
def restore_scheduled_jobs():
    """Restore existing scheduled domains from database as scheduler jobs"""
    try:
        # Get all active scheduled domains from database
        active_domains = a80_scheduled_domains.query.filter_by(is_active=True).all()
        
        print(f"[SCHEDULER] 📊 Restoring {len(active_domains)} scheduled domain jobs to scheduler queue")
        
        for domain in active_domains:
            # Calculate the next run time based on starting_time and interval
            now = get_gmt8_now()
            
            if domain.starting_time:
                # Get the time components from the starting_time
                start_hour = domain.starting_time.hour
                start_minute = domain.starting_time.minute
                
                # Create next run time for today at the starting time
                today_start = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
                
                # If last check exists, calculate next run based on intervals from last check
                if domain.last_checked_at:
                    # Ensure last_checked_at is timezone-aware
                    if domain.last_checked_at.tzinfo is None:
                        last_checked_gmt8 = GMT_PLUS_8.localize(domain.last_checked_at)
                    else:
                        last_checked_gmt8 = domain.last_checked_at.astimezone(GMT_PLUS_8)
                    
                    # Calculate next run based on interval from last check
                    next_run = last_checked_gmt8 + timedelta(minutes=domain.interval_minutes)
                    
                    # If next run is in the past, schedule for the next interval cycle
                    while next_run <= now:
                        next_run += timedelta(minutes=domain.interval_minutes)
                else:
                    # No previous check - use today's starting time or next occurrence
                    next_run = today_start
                    if next_run <= now:
                        next_run += timedelta(minutes=domain.interval_minutes)
                
                print(f"[SCHEDULER] Scheduling domain {domain.domain_name} next run: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                # No specific starting time - use interval from now
                next_run = now + timedelta(minutes=domain.interval_minutes)
                print(f"[SCHEDULER] Scheduling domain {domain.domain_name} next run (no start time): {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Use IntervalTrigger with calculated start_date and misfire handling
            scheduler.add_job(
                func=check_scheduled_domain_with_context,
                trigger=IntervalTrigger(minutes=domain.interval_minutes, start_date=next_run.astimezone()),
                id=f'domain_{domain.id}',
                args=[domain.id, current_app._get_current_object()],
                replace_existing=True,
                misfire_grace_time=300,  # Allow up to 5 minutes late execution
                coalesce=True,  # Coalesce missed executions
                max_instances=1  # Prevent overlapping executions
            )
            print(f"[SCHEDULER] Restored job for domain {domain.domain_name} (every {domain.interval_minutes} min)")
        
        print(f"[SCHEDULER] Restored {len(active_domains)} scheduled domain jobs")
        
        # Start automatic retry service after restoring jobs
        start_automatic_retry_service()
        
    except Exception as e:
        print(f"[SCHEDULER] Error restoring scheduled jobs: {e}")

# Add startup route to restore jobs - call this endpoint after server starts
@scheduled_monitoring.route('/api/restore-jobs', methods=['POST'])
@cross_origin()
def restore_jobs_endpoint():
    """Manual endpoint to restore scheduled jobs"""
    restore_scheduled_jobs()
    return jsonify({"success": True, "message": "Scheduled jobs restored"})

@scheduled_monitoring.route('/api/scheduler-health', methods=['GET'])
@cross_origin()
def get_scheduler_health():
    """Get scheduler health information for monitoring"""
    try:
        jobs = scheduler.get_jobs()
        job_count = len(jobs)
        
        # Get next execution times for the next few jobs
        next_runs = []
        for job in jobs[:5]:  # Show next 5 jobs
            if job.next_run_time:
                # Convert to GMT+8 timezone for consistency
                next_run_gmt8 = job.next_run_time.astimezone(GMT_PLUS_8)
                next_runs.append({
                    'job_id': job.id,
                    'next_run': next_run_gmt8.strftime('%Y-%m-%d %H:%M:%S'),
                    'function': job.func.__name__
                })
        
        # Analyze job performance and timing
        now = get_gmt8_now()
        overdue_jobs = []
        upcoming_jobs = []
        job_interval_stats = {}
        
        for job in jobs:
            if job.next_run_time:
                next_run_gmt8 = job.next_run_time.astimezone(GMT_PLUS_8)
                time_diff = (next_run_gmt8 - now).total_seconds() / 60  # minutes
                
                # Check for overdue jobs (negative time means past due)
                if time_diff < 0:
                    overdue_jobs.append({
                        'job_id': job.id,
                        'overdue_minutes': abs(time_diff),
                        'scheduled_time': next_run_gmt8.strftime('%Y-%m-%d %H:%M:%S')
                    })
                elif time_diff <= 10:  # Jobs due within 10 minutes
                    upcoming_jobs.append({
                        'job_id': job.id,
                        'minutes_until_run': time_diff,
                        'scheduled_time': next_run_gmt8.strftime('%Y-%m-%d %H:%M:%S')
                    })
                
                # Track job interval statistics
                if 'domain_' in job.id:
                    trigger = job.trigger
                    if hasattr(trigger, 'interval'):
                        interval_minutes = trigger.interval.total_seconds() / 60
                        if interval_minutes not in job_interval_stats:
                            job_interval_stats[interval_minutes] = 0
                        job_interval_stats[interval_minutes] += 1
        
        # Get scheduler state information
        try:
            job_defaults = getattr(scheduler, '_job_defaults', {})
            state_info = {
                'scheduler_state': scheduler.state,
                'scheduler_started': scheduler.running,
                'misfire_grace_time': job_defaults.get('misfire_grace_time', 'configured via scheduler.configure()'),
                'coalesce': job_defaults.get('coalesce', 'configured via scheduler.configure()'),
                'max_instances': job_defaults.get('max_instances', 'configured via scheduler.configure()')
            }
        except Exception as config_error:
            state_info = {
                'scheduler_state': scheduler.state,
                'scheduler_started': scheduler.running,
                'config_note': 'Misfire settings applied via scheduler.configure()',
                'config_error': str(config_error)
            }

        health_info = {
            'scheduler_running': scheduler.running,
            'total_jobs': job_count,
            'next_jobs': next_runs,
            'current_time': now.strftime('%Y-%m-%d %H:%M:%S'),
            'performance_metrics': {
                'overdue_jobs': len(overdue_jobs),
                'overdue_details': overdue_jobs[:3],  # Show first 3 overdue jobs
                'upcoming_jobs': len(upcoming_jobs),
                'upcoming_details': upcoming_jobs[:3],  # Show first 3 upcoming jobs
                'job_intervals': job_interval_stats,
                'auto_retry_active': len(currently_retrying),
                'domains_being_retried': list(currently_retrying)
            },
            'scheduler_config': state_info
        }
        
        return jsonify(health_info)
        
    except Exception as e:
        return jsonify({"error": f"Scheduler health check failed: {e}"}), 500

@scheduled_monitoring.route('/api/auto-retry-status', methods=['GET'])
@cross_origin()
def get_auto_retry_status():
    """Get automatic retry service status and statistics"""
    try:
        # Get domains currently being retried
        retrying_domains = []
        if currently_retrying:
            retrying_domain_ids = list(currently_retrying)
            domains = a80_scheduled_domains.query.filter(a80_scheduled_domains.id.in_(retrying_domain_ids)).all()
            retrying_domains = [{'id': d.id, 'domain_name': d.domain_name, 'country': d.country} for d in domains]
        
        # Get retry attempt counts
        retry_stats = {}
        for domain_id, attempts in retry_attempts.items():
            domain = a80_scheduled_domains.query.get(domain_id)
            if domain:
                retry_stats[domain_id] = {
                    'domain_name': domain.domain_name,
                    'attempts': attempts,
                    'max_attempts': AUTO_RETRY_CONFIG['max_retry_attempts']
                }
        
        # Scan for delayed domains (without executing retries) - use comprehensive logic
        delayed_domains_info = []
        active_domains = a80_scheduled_domains.query.filter_by(is_active=True).all()
        for domain in active_domains:
            should_retry, reason = should_domain_be_retried(domain)
            if should_retry:
                delayed_domains_info.append({
                    'id': domain.id,
                    'domain_name': domain.domain_name,
                    'country': domain.country,
                    'reason': reason,
                    'retry_attempts': get_retry_attempts(domain.id)
                })
        
        status_info = {
            'auto_retry_enabled': AUTO_RETRY_CONFIG['enabled'],
            'config': AUTO_RETRY_CONFIG,
            'currently_retrying': retrying_domains,
            'retry_statistics': retry_stats,
            'delayed_domains': delayed_domains_info,
            'current_time': get_gmt8_now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return jsonify(status_info)
        
    except Exception as e:
        return jsonify({"error": f"Auto-retry status check failed: {e}"}), 500



#######################################################################
@scheduled_monitoring.route('/api/scheduled-domains', methods=['GET'])
@cross_origin()
def get_scheduled_domains():
    domains = a80_scheduled_domains.query.filter_by(is_active=True).all()
    
    # Enhance each domain with next_check_time calculation
    enhanced_domains = []
    for domain in domains:
        domain_data = domain.serialize
        domain_data['next_check_time'] = calculate_next_check_time(domain)
        enhanced_domains.append(domain_data)
    
    return jsonify(enhanced_domains)

def calculate_next_check_time(domain):
    """Calculate the next check time for a domain based on scheduler logic"""
    try:
        now = get_gmt8_now()
        
        if domain.starting_time:
            # Get the time components from the starting_time
            start_hour = domain.starting_time.hour
            start_minute = domain.starting_time.minute
            
            # Create next run time for today at the starting time
            today_start = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
            
            # If last check exists, calculate next run based on intervals from last check
            if domain.last_checked_at:
                # Ensure last_checked_at is timezone-aware
                if domain.last_checked_at.tzinfo is None:
                    last_checked_gmt8 = GMT_PLUS_8.localize(domain.last_checked_at)
                else:
                    last_checked_gmt8 = domain.last_checked_at.astimezone(GMT_PLUS_8)
                
                # Calculate next run based on interval from last check
                next_run = last_checked_gmt8 + timedelta(minutes=domain.interval_minutes)
                
                # If next run is in the past, schedule for the next interval cycle
                while next_run <= now:
                    next_run += timedelta(minutes=domain.interval_minutes)
            else:
                # No previous check - use today's starting time or next occurrence
                next_run = today_start
                if next_run <= now:
                    next_run += timedelta(minutes=domain.interval_minutes)
        else:
            # No specific starting time - use interval from last check or now
            if domain.last_checked_at:
                # Ensure last_checked_at is timezone-aware
                if domain.last_checked_at.tzinfo is None:
                    last_checked_gmt8 = GMT_PLUS_8.localize(domain.last_checked_at)
                else:
                    last_checked_gmt8 = domain.last_checked_at.astimezone(GMT_PLUS_8)
                
                next_run = last_checked_gmt8 + timedelta(minutes=domain.interval_minutes)
                
                # If next run is in the past, schedule for the next interval cycle
                while next_run <= now:
                    next_run += timedelta(minutes=domain.interval_minutes)
            else:
                # No starting time and no last check - use interval from now
                next_run = now + timedelta(minutes=domain.interval_minutes)
        
        # Format the datetime for frontend display
        from model import format_datetime_gmt8
        return format_datetime_gmt8(next_run)
        
    except Exception as e:
        print(f"[SCHEDULER] Error calculating next check time for domain {domain.id}: {e}")
        return None

#######################################################################
@scheduled_monitoring.route('/api/scheduled-domains', methods=['POST'])
@cross_origin()
def add_scheduled_domain():
    data = request.get_json()
    
    domain_name = data.get('domain_name')
    interval_minutes = int(data.get('interval_minutes', 5))
    country = data.get('country')
    domain_prefix = data.get('domain_prefix', 'www')
    starting_time_str = data.get('starting_time')  # Format: "HH:MM"
    
    # Parse starting time and convert to GMT+8 datetime
    starting_time = None
    if starting_time_str:
        try:
            # Parse time string (HH:MM format)
            time_parts = starting_time_str.split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            
            # Create datetime for today at the specified time in GMT+8
            today = get_gmt8_now().date()
            from datetime import time
            starting_time = GMT_PLUS_8.localize(datetime.combine(today, time(hour, minute)))
        except (ValueError, IndexError):
            print(f"[SCHEDULER] Invalid starting_time format: {starting_time_str}")
    
    # Construct full URL with prefix
    if domain_prefix == 'root':
        full_url = f"https://{domain_name}"
    else:
        full_url = f"https://{domain_prefix}.{domain_name}"
    
    # Create scheduled domain record
    scheduled_domain = a80_scheduled_domains(
        domain_name=full_url,
        interval_minutes=interval_minutes,
        country=country,
        domain_prefix=domain_prefix,
        starting_time=starting_time,
        is_active=True
    )
    
    db.session.add(scheduled_domain)
    db.session.commit()
    
    # Schedule the monitoring job with app context and misfire handling
    scheduler.add_job(
        func=check_scheduled_domain_with_context,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id=f'domain_{scheduled_domain.id}',
        args=[scheduled_domain.id, current_app._get_current_object()],
        replace_existing=True,
        misfire_grace_time=300,  # Allow up to 5 minutes late execution
        coalesce=True,  # Coalesce missed executions
        max_instances=1  # Prevent overlapping executions
    )
    print(f"[SCHEDULER] Scheduled domain {full_url} with {interval_minutes}min intervals")
    
    # Get domain ID and app context for background test
    domain_id = scheduled_domain.id
    app_context = current_app._get_current_object()
    
    # Run immediate first test in background thread (don't block API response)
    def run_immediate_test():
        try:
            print(f"[SCHEDULER] Starting immediate first test for domain: {full_url}")
            check_scheduled_domain_with_context(domain_id, app_context)
            print(f"[SCHEDULER] Immediate first test completed for domain: {full_url}")
        except Exception as e:
            print(f"[SCHEDULER] Error in immediate first test for domain {full_url}: {e}")
    
    # Start background thread for immediate test
    test_thread = threading.Thread(target=run_immediate_test)
    test_thread.daemon = True
    test_thread.start()
    
    return jsonify({"success": True, "domain": scheduled_domain.serialize})

#######################################################################
@scheduled_monitoring.route('/api/scheduled-domains/<int:domain_id>', methods=['DELETE'])
@cross_origin()
def delete_scheduled_domain(domain_id):
    domain = a80_scheduled_domains.query.get(domain_id)
    if domain:
        domain.is_active = False
        db.session.commit()
        
        # Remove the scheduled job
        try:
            scheduler.remove_job(f'domain_{domain_id}')
        except:
            pass
        
        return jsonify({"success": True})
    
    return jsonify({"success": False, "error": "Domain not found"}), 404

#######################################################################
@scheduled_monitoring.route('/api/scheduled-results', methods=['GET'])
@cross_origin()
def get_scheduled_results():
    results = a90_scheduled_results.query.order_by(a90_scheduled_results.checked_at.desc()).all()
    return jsonify([result.serialize for result in results])

#######################################################################
@scheduled_monitoring.route('/api/manual-check/<int:domain_id>', methods=['POST'])
@cross_origin()
def manual_check_domain(domain_id):
    """Manually trigger a check for a specific scheduled domain"""
    try:
        print(f"[MANUAL CHECK] 🚀 Manual check API called for domain ID: {domain_id}")
        
        domain = a80_scheduled_domains.query.get(domain_id)
        if not domain or not domain.is_active:
            print(f"[MANUAL CHECK] ❌ Domain not found or inactive - ID: {domain_id}")
            return jsonify({"success": False, "error": "Domain not found or inactive"}), 404
        
        print(f"[MANUAL CHECK] 📋 Found domain: {domain.domain_name} (Country: {domain.country})")
        print(f"[MANUAL CHECK] 🎯 Starting manual check for domain ID: {domain_id}")
        
        # Update last checked time immediately to show it's being checked
        domain.last_checked_at = get_gmt8_now()
        db.session.commit()
        print(f"[MANUAL CHECK] 💾 Updated last_checked_at timestamp")
        
        print(f"[MANUAL CHECK] 🌐 Starting manual check for domain: {domain.domain_name}")
        
        # Run manual check directly (synchronous) to avoid threading context issues
        try:
            domain_name = domain.domain_name  # Store domain name before check
            print(f"[MANUAL CHECK] 🔄 Executing REAL-TIME domain check (bypassing cache) for: {domain_name}")
            manual_check_scheduled_domain(domain_id)
            print(f"[MANUAL CHECK] ✅ Manual real-time test completed for domain: {domain_name}")
            
            # Re-query domain object from database since check_scheduled_domain detaches it
            domain = a80_scheduled_domains.query.get(domain_id)
            
            return jsonify({
                "success": True, 
                "message": f"Manual check completed for {domain_name}",
                "domain": domain.serialize if domain else None
            })
            
        except Exception as check_error:
            print(f"[MANUAL CHECK] 💥 Error in manual test for domain {domain.domain_name}: {check_error}")
            print(f"[MANUAL CHECK] 🔥 Manual check failed - Domain ID: {domain_id}, Error: {str(check_error)}")
            
            # Re-query domain object from database to avoid session issues
            domain = a80_scheduled_domains.query.get(domain_id)
            
            return jsonify({
                "success": False, 
                "message": f"Manual check failed for domain {domain.domain_name if domain else 'unknown'}: {str(check_error)}",
                "domain": domain.serialize if domain else None
            }), 500
        
    except Exception as e:
        import traceback
        print(f"[MANUAL CHECK] Error in manual check endpoint: {e}")
        print(f"[MANUAL CHECK] Full traceback: {traceback.format_exc()}")
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500



#######################################################################
def check_scheduled_domain_with_context(domain_id, app):
    """Wrapper function that runs domain check with Flask application context"""
    with app.app_context():
        check_scheduled_domain(domain_id)

def manual_check_scheduled_domain(domain_id):
    """Check a scheduled domain availability using REAL-TIME testing (bypasses cached data)"""
    session = None
    start_time = get_gmt8_now()
    
    try:
        print(f"[MANUAL CHECK] 🚀 Starting REAL-TIME check for domain ID: {domain_id} at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[MANUAL CHECK] 📊 Manual domain check initiated - bypassing cached data - ID: {domain_id}")
        
        # Create new session for this manual job
        session = db.session
        
        domain = a80_scheduled_domains.query.get(domain_id)
        if not domain or not domain.is_active:
            print(f"[MANUAL CHECK] Domain {domain_id} not found or inactive")
            return
        
        print(f"[MANUAL CHECK] 🌐 Executing REAL-TIME test for domain: {domain.domain_name} in {domain.country}")
        print(f"[MANUAL CHECK] 🔥 FORCING real-time probe execution - NO CACHED DATA")
        
        # Update last checked time
        domain.last_checked_at = start_time
        session.commit()
        print(f"[MANUAL CHECK] 💾 Updated last_checked_at timestamp for domain ID: {domain_id}")
        
        # FORCE real-time testing - bypass cached data completely
        print(f"[MANUAL CHECK] 🔍 BYPASSING cache - executing fresh curl commands on all probes")
        availability_result = perform_domain_check(domain.domain_name, domain.country)
        
        if availability_result:
            print(f"[MANUAL CHECK] 📈 REAL-TIME availability result: {availability_result['availability']}% ({availability_result['successful_probes']}/{availability_result['total_probes']} probes)")
            # Store result
            result = a90_scheduled_results(
                scheduled_domain_id=domain.id,
                domain_name=domain.domain_name,
                country=domain.country,
                availability_percentage=availability_result['availability'],
                total_probes=availability_result['total_probes'],
                successful_probes=availability_result['successful_probes']
            )
            
            session.add(result)
            session.commit()
            print(f"[MANUAL CHECK] 💾 Saved REAL-TIME result to database for domain: {domain.domain_name}")
            
            # Calculate and log execution time
            end_time = get_gmt8_now()
            execution_seconds = (end_time - start_time).total_seconds()
            print(f"[MANUAL CHECK] ✅ REAL-TIME domain check completed in {execution_seconds:.1f}s - Availability: {availability_result['availability']}% ({availability_result['successful_probes']}/{availability_result['total_probes']} probes) - {domain.domain_name}")
            print(f"[MANUAL CHECK] 🎯 Manual check cycle complete for domain ID: {domain_id}")
            
            # Reset retry attempts on successful check
            reset_retry_attempts(domain.id)
        else:
            end_time = get_gmt8_now()
            execution_seconds = (end_time - start_time).total_seconds()
            print(f"[MANUAL CHECK] ❌ No REAL-TIME availability result returned for domain: {domain.domain_name} (took {execution_seconds:.1f}s)")
            print(f"[MANUAL CHECK] 🚫 Failed to get REAL-TIME availability data for domain ID: {domain_id}")
            
    except Exception as e:
        end_time = get_gmt8_now()
        execution_seconds = (end_time - start_time).total_seconds()
        print(f"[MANUAL CHECK] 💥 Error in REAL-TIME manual check for domain {domain_id} after {execution_seconds:.1f}s: {e}")
        print(f"[MANUAL CHECK] 🔥 Exception occurred during manual domain check - ID: {domain_id}, Error: {str(e)}")
        if session:
            try:
                session.rollback()
            except:
                pass
    finally:
        # Ensure database connection is properly closed after job completes
        try:
            if session:
                session.close()
        except:
            pass

def check_scheduled_domain(domain_id):
    """Check a scheduled domain availability"""
    session = None
    start_time = get_gmt8_now()
    
    try:
        print(f"[SCHEDULER] 🚀 Starting check for domain ID: {domain_id} at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[SCHEDULER] 📊 Domain check initiated - ID: {domain_id}")
        
        # Create new session for this scheduled job to avoid connection pool exhaustion
        session = db.session
        
        domain = a80_scheduled_domains.query.get(domain_id)
        if not domain or not domain.is_active:
            print(f"[SCHEDULER] Domain {domain_id} not found or inactive")
            return
        
        # Calculate timing accuracy if there was a previous check
        timing_info = ""
        if domain.last_checked_at:
            # Ensure last_checked_at is timezone-aware (GMT+8)
            if domain.last_checked_at.tzinfo is None:
                last_checked_gmt8 = GMT_PLUS_8.localize(domain.last_checked_at)
            else:
                last_checked_gmt8 = domain.last_checked_at.astimezone(GMT_PLUS_8)
            
            expected_next_check = last_checked_gmt8 + timedelta(minutes=domain.interval_minutes)
            timing_drift_minutes = (start_time - expected_next_check).total_seconds() / 60
            timing_info = f" [Timing: {timing_drift_minutes:+.1f}min vs expected]"
        
        print(f"[SCHEDULER] 🌐 Checking domain: {domain.domain_name} in {domain.country}{timing_info}")
        print(f"[SCHEDULER] ⏰ Interval: {domain.interval_minutes} minutes")
        
        # Update last checked time
        domain.last_checked_at = start_time
        session.commit()
        print(f"[SCHEDULER] 💾 Updated last_checked_at timestamp for domain ID: {domain_id}")
        
        # Use the same availability data as the main system (a40_availiblity_for_each_country)
        print(f"[SCHEDULER] 🔍 Fetching availability data for {domain.domain_name} in {domain.country}")
        availability_result = get_availability_from_main_system(domain.domain_name, domain.country)
        
        if availability_result:
            print(f"[SCHEDULER] 📈 Availability data retrieved: {availability_result['availability']}% ({availability_result['successful_probes']}/{availability_result['total_probes']} probes)")
            # Store result
            result = a90_scheduled_results(
                scheduled_domain_id=domain.id,
                domain_name=domain.domain_name,
                country=domain.country,
                availability_percentage=availability_result['availability'],
                total_probes=availability_result['total_probes'],
                successful_probes=availability_result['successful_probes']
            )
            
            session.add(result)
            session.commit()
            print(f"[SCHEDULER] 💾 Saved result to database for domain: {domain.domain_name}")
            
            # Calculate and log execution time
            end_time = get_gmt8_now()
            execution_seconds = (end_time - start_time).total_seconds()
            print(f"[SCHEDULER] ✅ Domain check completed in {execution_seconds:.1f}s - Availability: {availability_result['availability']}% ({availability_result['successful_probes']}/{availability_result['total_probes']} probes) - {domain.domain_name}")
            print(f"[SCHEDULER] 🎯 Check cycle complete for domain ID: {domain_id}")
            
            # Reset retry attempts on successful check
            reset_retry_attempts(domain.id)
        else:
            end_time = get_gmt8_now()
            execution_seconds = (end_time - start_time).total_seconds()
            print(f"[SCHEDULER] ❌ No availability result returned for domain: {domain.domain_name} (took {execution_seconds:.1f}s)")
            print(f"[SCHEDULER] 🚫 Failed to get availability data for domain ID: {domain_id}")
            
    except Exception as e:
        end_time = get_gmt8_now()
        execution_seconds = (end_time - start_time).total_seconds()
        print(f"[SCHEDULER] 💥 Error checking scheduled domain {domain_id} after {execution_seconds:.1f}s: {e}")
        print(f"[SCHEDULER] 🔥 Exception occurred during domain check - ID: {domain_id}, Error: {str(e)}")
        if session:
            try:
                session.rollback()
            except:
                pass
    finally:
        # Ensure database connection is properly closed after job completes
        try:
            if session:
                session.close()
        except:
            pass

#######################################################################
def perform_domain_check(domain_url, country):
    """Perform domain availability check using existing curl logic"""
    try:
        print(f"[SCHEDULER] 🚀 perform_domain_check() starting for {domain_url} in {country}")
        print(f"[SCHEDULER] 🌐 Real-time probe checking initiated")
        
        # Clear previous results for this specific check
        current_time = get_gmt8_now().strftime("%Y-%m-%d-%H:%M:%S")
        
        # Get probes for the specified country
        probes = a01_probe_list.query.filter_by(country=country).all()
        
        if not probes:
            print(f"[SCHEDULER] 🚫 No probes found for country: {country}")
            return None
        
        print(f"[SCHEDULER] 📋 Found {len(probes)} probes for {country}")
        print(f"[SCHEDULER] 📊 Starting probe loop for availability testing")
        
        successful_probes = 0
        total_probes = 0
        
        for probe in probes:
            if probe.is_the_probe_broken == "its_broken":
                print(f"[SCHEDULER] ⚠️ Skipping broken probe: {probe.probe_ip}")
                continue
                
            total_probes += 1
            print(f"[SCHEDULER] 🔍 Testing probe {probe.probe_ip} ({total_probes}/{len([p for p in probes if p.is_the_probe_broken != 'its_broken'])})")
            print(f"[SCHEDULER] 🎯 Executing REAL-TIME curl check on probe {probe.probe_ip}")
            print(f"[SCHEDULER] 📡 SSH connecting to {probe.probe_ip}:52770 for curl execution...")
            
            # Use existing curl logic from handling_data_received_from_frontend.py
            result = perform_curl_check_with_country(probe.probe_ip, domain_url, country)
            
            if result and "can access" in result:
                successful_probes += 1
                print(f"[SCHEDULER] ✓ Probe {probe.probe_ip} can access {domain_url}")
                print(f"[SCHEDULER] ✅ Successful probe result: {result}")
            else:
                print(f"[SCHEDULER] ✗ Probe {probe.probe_ip} cannot access {domain_url} - {result}")
                print(f"[SCHEDULER] ❌ Failed probe result: {result}")
            
            print(f"[SCHEDULER] 🔄 Completed probe {total_probes} of {len([p for p in probes if p.is_the_probe_broken != 'its_broken'])}")
        
        if total_probes == 0:
            print(f"[SCHEDULER] No working probes available for {country}")
            return None
        
        availability = round((successful_probes / total_probes) * 100, 2)
        print(f"[SCHEDULER] 📈 Final result: {availability}% availability ({successful_probes}/{total_probes} probes successful)")
        print(f"[SCHEDULER] 🎯 Real-time check completed - returning availability data")
        
        return {
            'availability': availability,
            'successful_probes': successful_probes,
            'total_probes': total_probes
        }
    
    except Exception as e:
        print(f"[SCHEDULER] 💥 Error performing domain check: {e}")
        print(f"[SCHEDULER] 🔥 Exception in perform_domain_check(): {str(e)}")
        return None

#######################################################################
def perform_curl_check_with_country(probe_ip, target_url, country):
    """Perform curl check on a single probe with country context"""
    try:
        port = 52770
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # SSH connection with detailed error logging
        try:
            print(f"[REAL-TIME CURL] 🔌 Connecting to SSH {probe_ip}:52770...")
            ssh.connect(probe_ip, port, "root", os.environ.get("SSH_PASSWORD", ""), timeout=10)
            print(f"[REAL-TIME CURL] ✅ SSH connection established to {probe_ip}")
        except paramiko.AuthenticationException as e:
            print(f"[REAL-TIME CURL] 🔐 SSH authentication failed for {probe_ip}")
            return "cannot access - SSH authentication failed"
        except paramiko.SSHException as e:
            print(f"[REAL-TIME CURL] 🚫 SSH connection error to {probe_ip}")
            return "cannot access - SSH connection error"
        except socket.timeout as e:
            print(f"[REAL-TIME CURL] ⏱️ SSH timeout connecting to {probe_ip}")
            return "cannot access - SSH timeout"
        except socket.error as e:
            print(f"[REAL-TIME CURL] 🌐 Network error connecting to {probe_ip}")
            return "cannot access - Network error"
        
        current_time = get_gmt8_now().strftime("%Y-%m-%d-%H:%M:%S")
        time_for_filename = current_time.replace("-", "_").replace(":", "_")
        filename = f"scheduled_check_{target_url}_{probe_ip}_{time_for_filename}".replace("http://", "").replace("https://", "").replace(".", "_")
        
        curl_command = f"curl -s -L --insecure --connect-timeout 5 --max-time 10 {target_url} -A 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36' >> /var/www/html/{filename} 2>&1"
        
        # Execute curl command with detailed error logging
        try:
            print(f"[REAL-TIME CURL] 🚀 Executing curl command on {probe_ip}: {target_url}")
            start_curl = time.time()
            stdin, stdout, stderr = ssh.exec_command(curl_command)
            
            # Wait a bit for command to complete
            print(f"[REAL-TIME CURL] ⏳ Waiting for curl command to complete on {probe_ip}...")
            time.sleep(2)
            end_curl = time.time()
            
            curl_duration = end_curl - start_curl
            print(f"[REAL-TIME CURL] ⚡ Curl execution completed in {curl_duration:.1f}s on {probe_ip}")
            
            # Check if there were any command execution errors
            stderr_output = stderr.read().decode('utf-8').strip()
            if stderr_output:
                print(f"[REAL-TIME CURL] ⚠️ Curl stderr from {probe_ip}: {stderr_output}")
                
        except Exception as e:
            print(f"[REAL-TIME CURL] 💥 Curl command execution failed on {probe_ip}: {e}")
            ssh.close()
            return "cannot access - curl command execution failed"
        
        # Check result with detailed error logging
        curl_result_link = f"http://{probe_ip}:8787/{filename}"
        
        try:
            print(f"[REAL-TIME CURL] 📥 Retrieving curl result from {curl_result_link}")
            result = get_curl_result_content(curl_result_link)
            print(f"[REAL-TIME CURL] 📊 Retrieved {len(result)} characters from curl result on {probe_ip}")
        except Exception as e:
            print(f"[REAL-TIME CURL] 💥 Failed to retrieve curl result from {probe_ip}: {e}")
            ssh.close()
            return "cannot access - result retrieval failed"
        
        ssh.close()
        
        analysis_result = analyze_curl_result(result, country)
        print(f"[REAL-TIME CURL] 🎯 Analysis result for {probe_ip}: {analysis_result}")
        return analysis_result
        
    except Exception as e:
        return "cannot access - unexpected error"

def perform_curl_check(probe_ip, target_url):
    """Perform curl check on a single probe (legacy method without country)"""
    try:
        port = 52770
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # SSH connection with detailed error logging
        try:
            ssh.connect(probe_ip, port, "root", os.environ.get("SSH_PASSWORD", ""), timeout=10)
        except paramiko.AuthenticationException as e:
            return "cannot access - SSH authentication failed"
        except paramiko.SSHException as e:
            return "cannot access - SSH connection error"
        except socket.timeout as e:
            return "cannot access - SSH timeout"
        except socket.error as e:
            return "cannot access - Network error"
        
        current_time = get_gmt8_now().strftime("%Y-%m-%d-%H:%M:%S")
        time_for_filename = current_time.replace("-", "_").replace(":", "_")
        filename = f"scheduled_check_{target_url}_{probe_ip}_{time_for_filename}".replace("http://", "").replace("https://", "").replace(".", "_")
        
        curl_command = f"curl -s -L --insecure --connect-timeout 5 --max-time 10 {target_url} -A 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36' >> /var/www/html/{filename} 2>&1"
        
        # Execute curl command with detailed error logging
        try:
            stdin, stdout, stderr = ssh.exec_command(curl_command)
            
            # Wait a bit for command to complete
            time.sleep(2)
            
            # Check if there were any command execution errors
            stderr_output = stderr.read().decode('utf-8').strip()
                
        except Exception as e:
            ssh.close()
            return "cannot access - curl command execution failed"
        
        # Check result with detailed error logging
        curl_result_link = f"http://{probe_ip}:8787/{filename}"
        
        try:
            result = get_curl_result_content(curl_result_link)
        except Exception as e:
            ssh.close()
            return "cannot access - result retrieval failed"
        
        ssh.close()
        
        # Get country from domain check context - we need to pass it from the calling function
        analysis_result = analyze_curl_result(result, None)
        return analysis_result
        
    except Exception as e:
        return "cannot access - unexpected error"

#######################################################################
def get_curl_result_content(url):
    """Get curl result content from probe server"""
    try:
        response = requests.get(url, timeout=30)
        return response.text
    except:
        return ""

#######################################################################
def analyze_curl_result(result, country=None):
    """Judge a curl result with the whitelist rules stored in the database"""
    from blueprint_paping.whitelist_management import evaluate_curl_result_filtered
    return evaluate_curl_result_filtered(result, country)[1]

# Automatic retry functions
def is_domain_late_or_overdue(domain):
    """Check if a domain is late or overdue for its scheduled check"""
    if not domain.last_checked_at:
        return False, "never_checked"
    
    now = get_gmt8_now()
    
    # Ensure last_checked_at is timezone-aware
    if domain.last_checked_at.tzinfo is None:
        last_checked_gmt8 = GMT_PLUS_8.localize(domain.last_checked_at)
    else:
        last_checked_gmt8 = domain.last_checked_at.astimezone(GMT_PLUS_8)
    
    minutes_since_check = (now - last_checked_gmt8).total_seconds() / 60
    late_threshold = domain.interval_minutes * AUTO_RETRY_CONFIG['late_retry_threshold_multiplier']
    overdue_threshold = domain.interval_minutes * AUTO_RETRY_CONFIG['overdue_retry_threshold_multiplier']
    
    if minutes_since_check > overdue_threshold:
        return True, "overdue"
    elif minutes_since_check > late_threshold:
        return True, "late"
    else:
        return False, "on_time"

def get_retry_attempts(domain_id):
    """Get current retry attempt count for a domain"""
    return retry_attempts.get(domain_id, 0)

def increment_retry_attempts(domain_id):
    """Increment retry attempt count for a domain"""
    retry_attempts[domain_id] = retry_attempts.get(domain_id, 0) + 1
    return retry_attempts[domain_id]

def reset_retry_attempts(domain_id):
    """Reset retry attempt count for a domain (called after successful check)"""
    if domain_id in retry_attempts:
        del retry_attempts[domain_id]

def should_domain_be_retried(domain):
    """Check if domain should be retried using same logic as frontend shouldShowCheckButton"""
    # Check condition 1: Late/Overdue domains
    is_delayed, status = is_domain_late_or_overdue(domain)
    if is_delayed:
        return True, f"late_overdue_{status}"
    
    # Check condition 2: Domains missing from recent results (same as frontend logic)
    if domain.last_checked_at:
        now = get_gmt8_now()
        
        # Ensure last_checked_at is timezone-aware
        if domain.last_checked_at.tzinfo is None:
            last_checked_gmt8 = GMT_PLUS_8.localize(domain.last_checked_at)
        else:
            last_checked_gmt8 = domain.last_checked_at.astimezone(GMT_PLUS_8)
        
        diff_minutes = (now - last_checked_gmt8).total_seconds() / 60
        
        # If it's been at least the interval time, check if domain exists in recent results
        if diff_minutes >= domain.interval_minutes:
            # Check if domain exists in recent results for this specific domain+country+prefix combination
            recent_results = a90_scheduled_results.query.filter_by(
                domain_name=domain.domain_name,
                country=domain.country
            ).order_by(a90_scheduled_results.checked_at.desc()).first()
            
            # If no recent result found or result is too old, retry needed
            if not recent_results:
                return True, "missing_results"
            
            # Check if the most recent result is older than expected
            if recent_results.checked_at.tzinfo is None:
                result_time_gmt8 = GMT_PLUS_8.localize(recent_results.checked_at)
            else:
                result_time_gmt8 = recent_results.checked_at.astimezone(GMT_PLUS_8)
            
            result_age_minutes = (now - result_time_gmt8).total_seconds() / 60
            
            # If result is older than 1.2x interval, consider it stale
            if result_age_minutes > (domain.interval_minutes * 1.2):
                return True, "stale_results"
    
    return False, "on_time"

def scan_for_delayed_domains():
    """Scan for domains that are late or overdue and need automatic retries"""
    if not AUTO_RETRY_CONFIG['enabled']:
        return
    
    try:
        print(f"[AUTO-RETRY] 🔍 Scanning for delayed domains...")
        
        # Get all active scheduled domains
        active_domains = a80_scheduled_domains.query.filter_by(is_active=True).all()
        delayed_domains = []
        
        for domain in active_domains:
            # Skip if already being retried
            if domain.id in currently_retrying:
                continue
            
            # Check if domain should be retried (using comprehensive logic)
            should_retry, reason = should_domain_be_retried(domain)
            
            if should_retry:
                current_attempts = get_retry_attempts(domain.id)
                
                # Skip if max retry attempts reached
                if current_attempts >= AUTO_RETRY_CONFIG['max_retry_attempts']:
                    print(f"[AUTO-RETRY] ⏭️  Skipping domain {domain.id} ({domain.domain_name}) - max retries ({current_attempts}) reached")
                    continue
                
                # Check if we should retry based on concurrent limit
                if len(currently_retrying) >= AUTO_RETRY_CONFIG['concurrent_retries']:
                    print(f"[AUTO-RETRY] ⏸️  Concurrent retry limit ({AUTO_RETRY_CONFIG['concurrent_retries']}) reached, will retry next scan")
                    break
                
                delayed_domains.append((domain, reason, current_attempts))
        
        # Execute retries for delayed domains
        for domain, reason, current_attempts in delayed_domains:
            if len(currently_retrying) >= AUTO_RETRY_CONFIG['concurrent_retries']:
                break
                
            execute_automatic_retry(domain, reason, current_attempts)
        
        initiated_retries = len([d for d, _, _ in delayed_domains if d.id in currently_retrying])
        if delayed_domains:
            print(f"[AUTO-RETRY] 📊 Initiated {initiated_retries} automatic retries out of {len(delayed_domains)} delayed domains")
            print(f"[AUTO-RETRY] 🎯 Auto-retry scan completed - {initiated_retries} retries started")
        else:
            print(f"[AUTO-RETRY] ✅ No delayed domains found - all {len(active_domains)} domains are on schedule")
            print(f"[AUTO-RETRY] 😎 All domains running smoothly - no retries needed")
        
    except Exception as e:
        print(f"[AUTO-RETRY] ❌ Error scanning for delayed domains: {e}")
        print(f"[AUTO-RETRY] 💥 Exception in scan_for_delayed_domains(): {str(e)}")

def execute_automatic_retry(domain, status, attempt_number):
    """Execute automatic retry for a delayed domain"""
    try:
        # Mark domain as being retried
        currently_retrying.add(domain.id)
        
        # Increment retry attempts
        new_attempt_count = increment_retry_attempts(domain.id)
        
        print(f"[AUTO-RETRY] 🔄 Initiating retry #{new_attempt_count} for {status} domain: {domain.domain_name} (ID: {domain.id})")
        
        # Get app context for background execution
        app_context = current_app._get_current_object()
        
        # Execute retry in background thread to avoid blocking the scanner
        def run_retry():
            try:
                # Execute the domain check with app context
                check_scheduled_domain_with_context(domain.id, app_context)
                
                # On successful completion, reset retry attempts
                reset_retry_attempts(domain.id)
                print(f"[AUTO-RETRY] ✅ Retry successful for domain: {domain.domain_name} (ID: {domain.id})")
                
            except Exception as retry_error:
                print(f"[AUTO-RETRY] ❌ Retry failed for domain {domain.domain_name} (ID: {domain.id}): {retry_error}")
            finally:
                # Remove from currently retrying set
                currently_retrying.discard(domain.id)
        
        # Start retry thread
        retry_thread = threading.Thread(target=run_retry)
        retry_thread.daemon = True
        retry_thread.start()
        
    except Exception as e:
        print(f"[AUTO-RETRY] ❌ Error executing retry for domain {domain.id}: {e}")
        currently_retrying.discard(domain.id)

def scan_for_delayed_domains_with_context(app):
    """Wrapper function that runs delayed domain scanning with Flask application context"""
    with app.app_context():
        scan_for_delayed_domains()

def start_automatic_retry_service():
    """Start the automatic retry service as a scheduled job"""
    if AUTO_RETRY_CONFIG['enabled']:
        print(f"[AUTO-RETRY] 🚀 Starting automatic retry service (scan every {AUTO_RETRY_CONFIG['check_interval_minutes']} minutes)")
        
        # Schedule the retry scanner to run periodically with app context and misfire handling
        scheduler.add_job(
            func=scan_for_delayed_domains_with_context,
            trigger=IntervalTrigger(minutes=AUTO_RETRY_CONFIG['check_interval_minutes']),
            id='auto_retry_scanner',
            args=[current_app._get_current_object()],
            replace_existing=True,
            misfire_grace_time=120,  # Allow up to 2 minutes late for retry scanner
            coalesce=True,  # Coalesce missed scans
            max_instances=1  # Prevent overlapping scans
        )
        
        print(f"[AUTO-RETRY] ✅ Automatic retry service started successfully")
    else:
        print(f"[AUTO-RETRY] ⏸️  Automatic retry service is disabled")

# Shutdown scheduler when app stops
atexit.register(lambda: scheduler.shutdown())