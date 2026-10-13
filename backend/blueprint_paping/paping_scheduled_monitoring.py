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
from model import db, a01_probe_list, a95_paping_scheduled_destinations, a96_paping_results
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED, EVENT_JOB_MAX_INSTANCES
import atexit
import threading

paping_scheduled_monitoring = Blueprint("paping_scheduled_monitoring", __name__)
CORS(paping_scheduled_monitoring)

# GMT+8 timezone for consistent timestamp handling
GMT_PLUS_8 = pytz.timezone('Asia/Shanghai')

def get_gmt8_now():
    """Get current timestamp in GMT+8 timezone"""
    return datetime.now(GMT_PLUS_8)

# Use lazy import to avoid circular dependency
scheduler = None

def get_scheduler():
    global scheduler
    if scheduler is None:
        from blueprint_paping.scheduled_monitoring import scheduler as imported_scheduler
        scheduler = imported_scheduler
    return scheduler

#######################################################################
@paping_scheduled_monitoring.route('/api/paping-destinations', methods=['GET', 'OPTIONS'])
@cross_origin()
def get_paging_destinations():
    destinations = a95_paping_scheduled_destinations.query.filter_by(is_active=True).all()
    
    # Enhance each destination with next_check_time calculation
    enhanced_destinations = []
    for destination in destinations:
        destination_data = destination.serialize
        destination_data['next_check_time'] = calculate_next_paging_check_time(destination)
        enhanced_destinations.append(destination_data)
    
    return jsonify(enhanced_destinations)

def calculate_next_paging_check_time(destination):
    """Calculate the next check time for a paging destination"""
    try:
        now = get_gmt8_now()
        
        if destination.starting_time:
            # Get the time components from the starting_time
            start_hour = destination.starting_time.hour
            start_minute = destination.starting_time.minute
            
            # Create next run time for today at the starting time
            today_start = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
            
            # If last check exists, calculate next run based on intervals from last check
            if destination.last_checked_at:
                # Ensure last_checked_at is timezone-aware
                if destination.last_checked_at.tzinfo is None:
                    last_checked_gmt8 = GMT_PLUS_8.localize(destination.last_checked_at)
                else:
                    last_checked_gmt8 = destination.last_checked_at.astimezone(GMT_PLUS_8)
                
                # Calculate next run based on interval from last check
                next_run = last_checked_gmt8 + timedelta(minutes=destination.interval_minutes)
                
                # If next run is in the past, schedule for the next interval cycle
                while next_run <= now:
                    next_run += timedelta(minutes=destination.interval_minutes)
            else:
                # No previous check - use today's starting time or next occurrence
                next_run = today_start
                if next_run <= now:
                    next_run += timedelta(minutes=destination.interval_minutes)
        else:
            # No specific starting time - use interval from last check or now
            if destination.last_checked_at:
                # Ensure last_checked_at is timezone-aware
                if destination.last_checked_at.tzinfo is None:
                    last_checked_gmt8 = GMT_PLUS_8.localize(destination.last_checked_at)
                else:
                    last_checked_gmt8 = destination.last_checked_at.astimezone(GMT_PLUS_8)
                
                next_run = last_checked_gmt8 + timedelta(minutes=destination.interval_minutes)
                
                # If next run is in the past, schedule for the next interval cycle
                while next_run <= now:
                    next_run += timedelta(minutes=destination.interval_minutes)
            else:
                # No starting time and no last check - use interval from now
                next_run = now + timedelta(minutes=destination.interval_minutes)
        
        # Format the datetime for frontend display
        from model import format_datetime_gmt8
        return format_datetime_gmt8(next_run)
        
    except Exception as e:
        print(f"[PAPING SCHEDULER] Error calculating next check time for destination {destination.id}: {e}")
        return None

#######################################################################
@paping_scheduled_monitoring.route('/api/paping-destinations', methods=['POST', 'OPTIONS'])
@cross_origin()
def add_paging_destination():
    if request.method == 'OPTIONS':
        # Handle CORS preflight request
        response = jsonify({'status': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        return response
        
    data = request.get_json()
    
    destination = data.get('destination')
    interval_minutes = int(data.get('interval_minutes', 5))
    country = data.get('country')
    starting_time_str = data.get('starting_time')  # Format: "HH:MM"
    packet_loss_threshold = float(data.get('packet_loss_threshold', 10.0))
    latency_threshold = float(data.get('latency_threshold', 150.0))
    
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
            print(f"[PAGING SCHEDULER] Invalid starting_time format: {starting_time_str}")
    
    # Create scheduled paging destination record
    scheduled_destination = a95_paping_scheduled_destinations(
        destination=destination,
        interval_minutes=interval_minutes,
        country=country,
        starting_time=starting_time,
        is_active=True,
        packet_loss_threshold=packet_loss_threshold,
        latency_threshold=latency_threshold
    )
    
    db.session.add(scheduled_destination)
    db.session.commit()
    
    # Schedule the monitoring job with unique paging ID
    get_scheduler().add_job(
        func=check_paging_destination_with_context,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id=f'paging_{scheduled_destination.id}',  # Unique ID for paping jobs
        args=[scheduled_destination.id, current_app._get_current_object()],
        replace_existing=True,
        misfire_grace_time=300,  # Allow up to 5 minutes late execution
        coalesce=True,  # Coalesce missed executions
        max_instances=1  # Prevent overlapping executions
    )
    print(f"[PAPING SCHEDULER] Scheduled paging destination {destination} with {interval_minutes}min intervals")
    
    # Get destination ID and app context for background test
    destination_id = scheduled_destination.id
    app_context = current_app._get_current_object()
    
    # Run immediate first test in background thread
    def run_immediate_paging_test():
        try:
            print(f"[PAPING SCHEDULER] Starting immediate first test for destination: {destination}")
            check_paging_destination_with_context(destination_id, app_context)
            print(f"[PAGING SCHEDULER] Immediate first test completed for destination: {destination}")
        except Exception as e:
            print(f"[PAGING SCHEDULER] Error in immediate first test for destination {destination}: {e}")
    
    # Start background thread for immediate test
    test_thread = threading.Thread(target=run_immediate_paging_test)
    test_thread.daemon = True
    test_thread.start()
    
    return jsonify({"success": True, "destination": scheduled_destination.serialize, "destination_id": scheduled_destination.id})

#######################################################################
@paping_scheduled_monitoring.route('/api/paping-destinations/<int:destination_id>', methods=['DELETE', 'OPTIONS'])
@cross_origin()
def delete_paging_destination(destination_id):
    destination = a95_paping_scheduled_destinations.query.get(destination_id)
    if destination:
        destination.is_active = False
        db.session.commit()
        
        # Remove the scheduled job
        try:
            get_scheduler().remove_job(f'paging_{destination_id}')
        except:
            pass
        
        return jsonify({"success": True})
    
    return jsonify({"success": False, "error": "Destination not found"}), 404

#######################################################################
@paping_scheduled_monitoring.route('/api/paping-results', methods=['GET', 'OPTIONS'])
@cross_origin()
def get_paging_results():
    results = a96_paping_results.query.order_by(a96_paping_results.checked_at.desc()).all()
    return jsonify([result.serialize for result in results])

#######################################################################
@paping_scheduled_monitoring.route('/api/paping-alerts', methods=['GET', 'OPTIONS'])
@cross_origin()
def get_paging_alerts():
    """Get paging results that triggered alerts (packet loss > 10% OR latency > 150ms)"""
    alerts = a96_paping_results.query.filter_by(alert_triggered=True).order_by(a96_paping_results.checked_at.desc()).all()
    
    # Enrich alerts with hostname data from probe list
    enriched_alerts = []
    for alert in alerts:
        alert_data = alert.serialize
        # Look up hostname from probe list
        probe = a01_probe_list.query.filter_by(probe_ip=alert.probe_ip).first()
        alert_data['hostname'] = probe.hostname if probe and probe.hostname else 'Unknown'
        enriched_alerts.append(alert_data)
    
    return jsonify(enriched_alerts)

#######################################################################
@paping_scheduled_monitoring.route('/api/paping-test-summary', methods=['GET', 'OPTIONS'])
@cross_origin()
def get_paping_test_summary():
    """Get all paging results with test summary statistics (Attempted, Connected, Failed, etc.)"""
    results = a96_paping_results.query.order_by(a96_paping_results.checked_at.desc()).limit(50).all()
    
    # Enhanced logging for debugging probe display issues
    print(f"[PAGING TEST SUMMARY] 📊 Retrieved {len(results)} total results from database")
    
    # Group by destination for logging
    destination_groups = {}
    for result in results:
        dest_key = result.destination
        if dest_key not in destination_groups:
            destination_groups[dest_key] = []
        destination_groups[dest_key].append(result.probe_ip)
    
    for dest, probes in destination_groups.items():
        print(f"[PAGING TEST SUMMARY] 🌍 Destination {dest}: {len(probes)} probes - {', '.join(probes)}")
    
    # Calculate summary statistics for each result
    summary_results = []
    for result in results:
        # Calculate attempted, connected, failed based on packet loss
        attempted = 20  # Default paging attempts
        failed = int(attempted * (result.packet_loss_percentage / 100))
        connected = attempted - failed
        
        # Add calculated fields to the serialized result
        result_data = result.serialize
        result_data.update({
            'attempted': attempted,
            'connected': connected,
            'failed': failed
        })
        
        # Look up hostname from probe list
        probe = a01_probe_list.query.filter_by(probe_ip=result.probe_ip).first()
        result_data['hostname'] = probe.hostname if probe and probe.hostname else 'Unknown'
        
        summary_results.append(result_data)
    
    print(f"[PAGING TEST SUMMARY] 📤 Returning {len(summary_results)} summary results to frontend")
    return jsonify(summary_results)

#######################################################################
@paping_scheduled_monitoring.route('/api/test-endpoint', methods=['GET'])
@cross_origin()
def test_endpoint():
    """Test endpoint to verify paging routes work"""
    return jsonify({"status": "paging routes working", "timestamp": get_gmt8_now().strftime('%Y-%m-%d %H:%M:%S')})

@paping_scheduled_monitoring.route('/api/manual-test/<int:destination_id>', methods=['POST', 'OPTIONS'])
@cross_origin()
def manual_test(destination_id):
    """Simplified manual test endpoint"""
    try:
        print(f"[MANUAL TEST] Testing destination ID: {destination_id}")
        destination = a95_paping_scheduled_destinations.query.get(destination_id)
        if not destination:
            return jsonify({"success": False, "error": "Destination not found"}), 404
        
        # Test probe connectivity first
        probes = a01_probe_list.query.filter_by(country='KR').all()
        print(f"[MANUAL TEST] Found {len(probes)} probes for KR")
        
        probe_status = []
        for probe in probes:
            if probe.is_the_probe_broken == "its_broken":
                status = "broken"
            else:
                # Test SSH connectivity
                try:
                    import paramiko
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(probe.probe_ip, 52770, "root", os.environ.get("SSH_PASSWORD", ""), timeout=5)
                    ssh.close()
                    status = "ssh_ok"
                except:
                    status = "ssh_failed"
            
            probe_status.append({
                "ip": probe.probe_ip,
                "status": status
            })
            
        # Call the paging function directly
        print(f"[MANUAL TEST] Calling perform_paging_check for {destination.destination} in {destination.country}")
        results = perform_paging_check(destination.destination, destination.country)
        print(f"[MANUAL TEST] Results: {results}")
        
        return jsonify({
            "success": True, 
            "message": f"Test completed for {destination.destination}",
            "results_count": len(results) if results else 0,
            "results": results,
            "probe_status": probe_status
        })
    except Exception as e:
        print(f"[MANUAL TEST] Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@paping_scheduled_monitoring.route('/api/manual-paping-check/<int:destination_id>', methods=['POST', 'OPTIONS'])
@cross_origin()
def manual_paging_check(destination_id):
    """Manually trigger a paging check for a specific scheduled destination"""
    try:
        destination = a95_paping_scheduled_destinations.query.get(destination_id)
        if not destination or not destination.is_active:
            return jsonify({"success": False, "error": "Destination not found or inactive"}), 404
        
        print(f"[MANUAL PAGING CHECK] Starting manual check for destination ID: {destination_id}")
        
        # Update last checked time immediately to show it's being checked
        destination.last_checked_at = get_gmt8_now()
        db.session.commit()
        
        print(f"[MANUAL PAGING CHECK] Starting manual check for destination: {destination.destination}")
        
        # Run manual check directly (synchronous)
        try:
            destination_name = destination.destination  # Store destination name before check
            print(f"[MANUAL PAGING CHECK] Calling check_paging_destination for ID: {destination_id}")
            check_paging_destination(destination_id)
            print(f"[MANUAL PAGING CHECK] Manual paging test completed for destination: {destination_name}")
            
            # Re-query destination object from database
            destination = a95_paping_scheduled_destinations.query.get(destination_id)
            
            return jsonify({
                "success": True, 
                "message": f"Manual check completed for {destination_name}",
                "destination": destination.serialize if destination else None
            })
            
        except Exception as check_error:
            print(f"[MANUAL PAGING CHECK] Error in manual test for destination {destination.destination}: {check_error}")
            
            # Re-query destination object from database to avoid session issues
            destination = a95_paping_scheduled_destinations.query.get(destination_id)
            
            return jsonify({
                "success": False, 
                "message": f"Manual check failed for destination {destination.destination if destination else 'unknown'}: {str(check_error)}",
                "destination": destination.serialize if destination else None
            }), 500
        
    except Exception as e:
        import traceback
        print(f"[MANUAL PAGING CHECK] Error in manual check endpoint: {e}")
        print(f"[MANUAL PAGING CHECK] Full traceback: {traceback.format_exc()}")
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500

#######################################################################
def check_paging_destination_with_context(destination_id, app):
    """Wrapper function that runs paging destination check with Flask application context"""
    with app.app_context():
        check_paging_destination(destination_id)

def check_paging_destination(destination_id):
    """Check a scheduled paging destination"""
    session = None
    start_time = get_gmt8_now()
    
    try:
        print(f"[PAGING SCHEDULER] Starting paging check for destination ID: {destination_id} at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Create new session for this scheduled job
        session = db.session
        
        destination = a95_paping_scheduled_destinations.query.get(destination_id)
        if not destination or not destination.is_active:
            print(f"[PAGING SCHEDULER] Destination {destination_id} not found or inactive")
            return
        
        # Calculate timing accuracy if there was a previous check
        timing_info = ""
        if destination.last_checked_at:
            # Ensure last_checked_at is timezone-aware (GMT+8)
            if destination.last_checked_at.tzinfo is None:
                last_checked_gmt8 = GMT_PLUS_8.localize(destination.last_checked_at)
            else:
                last_checked_gmt8 = destination.last_checked_at.astimezone(GMT_PLUS_8)
            
            expected_next_check = last_checked_gmt8 + timedelta(minutes=destination.interval_minutes)
            timing_drift_minutes = (start_time - expected_next_check).total_seconds() / 60
            timing_info = f" [Timing: {timing_drift_minutes:+.1f}min vs expected]"
        
        print(f"[PAGING SCHEDULER] Checking destination: {destination.destination} in {destination.country}{timing_info}")
        
        # Update last checked time
        destination.last_checked_at = start_time
        session.commit()
        
        # Perform paging check
        print(f"[PAGING SCHEDULER] ⚡ About to call perform_paging_check for {destination.destination} in {destination.country}")
        paging_results = perform_paging_check(destination.destination, destination.country)
        print(f"[PAGING SCHEDULER] ⚡ perform_paging_check returned: {paging_results}")
        print(f"[PAGING SCHEDULER] ⚡ Results type: {type(paging_results)}, Length: {len(paging_results) if paging_results else 'None'}")
        
        if paging_results:
            # Store results for all probes that responded
            for probe_result in paging_results:
                # Determine if this result should trigger an alert using custom thresholds
                alert_triggered = (
                    probe_result['packet_loss_percentage'] > destination.packet_loss_threshold or 
                    probe_result['avg_latency_ms'] > destination.latency_threshold
                )
                
                result = a96_paping_results(
                    paging_destination_id=destination.id,
                    destination=destination.destination,
                    probe_ip=probe_result['probe_ip'],
                    country=destination.country,
                    packet_loss_percentage=probe_result['packet_loss_percentage'],
                    avg_latency_ms=probe_result['avg_latency_ms'],
                    min_latency_ms=probe_result['min_latency_ms'],
                    max_latency_ms=probe_result['max_latency_ms'],
                    alert_triggered=alert_triggered
                )
                
                session.add(result)
            
            session.commit()
            
            # Calculate and log execution time
            end_time = get_gmt8_now()
            execution_seconds = (end_time - start_time).total_seconds()
            
            # Count alerts using custom thresholds
            alert_count = len([r for r in paging_results if r['packet_loss_percentage'] > destination.packet_loss_threshold or r['avg_latency_ms'] > destination.latency_threshold])
            
            print(f"[PAGING SCHEDULER] ✅ Paping check completed in {execution_seconds:.1f}s - {len(paging_results)} probes tested, {alert_count} alerts - {destination.destination}")
            
        else:
            end_time = get_gmt8_now()
            execution_seconds = (end_time - start_time).total_seconds()
            print(f"[PAGING SCHEDULER] ❌ No paping results returned for destination: {destination.destination} (took {execution_seconds:.1f}s)")
            
    except Exception as e:
        end_time = get_gmt8_now()
        execution_seconds = (end_time - start_time).total_seconds()
        print(f"[PAGING SCHEDULER] 💥 Error checking scheduled destination {destination_id} after {execution_seconds:.1f}s: {e}")
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
def perform_paging_check(destination, country):
    """Perform paging check using existing probe infrastructure"""
    try:
        print(f"[PAGING SCHEDULER] Starting paging check for {destination} in {country}")
        
        # Map display country names to database country codes
        country_code_map = {
            'Korea': 'KR',
            'China': 'China',
            'Vietnam': 'Vietnam',
            'Indonesia': 'Indonesia', 
            'Thailand': 'Thailand',
            'Malaysia': 'Malaysia',
            'Cambodia': 'Cambodia'
        }
        
        # Use mapped country code or original value if no mapping exists
        db_country = country_code_map.get(country, country)
        print(f"[PAGING SCHEDULER] Mapped country '{country}' to database value '{db_country}'")
        
        # Get probes for the specified country
        probes = a01_probe_list.query.filter_by(country=db_country).all()
        
        if not probes:
            print(f"[PAGING SCHEDULER] No probes found for country: {country} (mapped to: {db_country})")
            return None
        
        print(f"[PAGING SCHEDULER] Found {len(probes)} probes for {country} (mapped to: {db_country})")
        
        paging_results = []
        
        for probe in probes:
            if probe.is_the_probe_broken == "its_broken":
                print(f"[PAGING SCHEDULER] Skipping broken probe: {probe.probe_ip}")
                continue
                
            print(f"[PAGING SCHEDULER] Testing probe {probe.probe_ip}")
            
            # Perform paging test on this probe
            print(f"[PAGING SCHEDULER] 🧪 About to test probe {probe.probe_ip} for destination {destination}")
            try:
                probe_result = perform_paging_test_on_probe(probe.probe_ip, destination)
                print(f"[PAGING SCHEDULER] 🧪 Probe {probe.probe_ip} returned: {probe_result}")
            except Exception as probe_error:
                print(f"[PAGING SCHEDULER] 💥 Exception testing probe {probe.probe_ip}: {probe_error}")
                probe_result = None
            
            if probe_result:
                probe_result['probe_ip'] = probe.probe_ip  # Add probe IP to result
                paging_results.append(probe_result)
                
                # Log result
                loss_str = f"{probe_result['packet_loss_percentage']:.1f}%"
                latency_str = f"{probe_result['avg_latency_ms']:.1f}ms"
                    
                print(f"[PAGING SCHEDULER] ✓ Probe {probe.probe_ip}: {loss_str} loss, {latency_str} avg")
            else:
                print(f"[PAGING SCHEDULER] ✗ Probe {probe.probe_ip} paging test failed")
        
        print(f"[PAGING SCHEDULER] Final results: {len(paging_results)} probes responded successfully")
        print(f"[PAGING SCHEDULER] 🎯 Returning paging_results: {paging_results}")
        return paging_results
    
    except Exception as e:
        print(f"[PAGING SCHEDULER] Error performing paging check: {e}")
        return None

#######################################################################
def perform_paging_test_on_probe(probe_ip, destination):
    """Perform paging test on a single probe using SSH"""
    try:
        print(f"[PAGING TEST] 🚀 Starting real paging test for probe {probe_ip} → {destination}")
        
        # ORIGINAL CODE (now enabled):
        port = 52770
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # SSH connection
        try:
            ssh.connect(probe_ip, port, "root", os.environ.get("SSH_PASSWORD", ""), timeout=15)
        except Exception as e:
            return None
        
        # Generate unique filename
        current_time = get_gmt8_now().strftime("%Y-%m-%d-%H:%M:%S")
        time_for_filename = current_time.replace("-", "_").replace(":", "_")
        filename = f"paging_check_{destination}_{probe_ip}_{time_for_filename}".replace(".", "_").replace(":", "_")
        
        # Execute paging command
        paging_command = f"paging -c 20 {destination} -p 443 --nocolor > /var/www/html/{filename} 2>&1"
        
        # Print the paging command being executed for verification
        print(f"[PAGING RESULT] 🚀 Executing paging command on probe {probe_ip}:")
        print(f"[PAGING RESULT] 💻 Command: {paging_command}")
        
        try:
            stdin, stdout, stderr = ssh.exec_command(paging_command)
            
            # Wait for command to complete
            time.sleep(3)
            
            print(f"[PAGING RESULT] ✅ Paging command completed on probe {probe_ip}")
            print(f"[PAGING RESULT] 🌐 Result will be retrieved from: http://{probe_ip}:8787/{filename}")
            
        except Exception as e:
            print(f"[PAGING RESULT] ❌ Paging command failed on probe {probe_ip}: {e}")
            ssh.close()
            return None
        
        # Retrieve result
        result_url = f"http://{probe_ip}:8787/{filename}"
        
        try:
            result_content = get_paging_result_content(result_url)
            ssh.close()
            
            # Parse paging result
            parsed_result = parse_paging_output(result_content)
            return parsed_result
            
        except Exception as e:
            ssh.close()
            return None
        
    except Exception as e:
        return None

#######################################################################
def get_paging_result_content(url):
    """Get paging result content from probe server"""
    try:
        print(f"[PAGING RESULT] 🌐 Attempting to retrieve results from: {url}")
        response = requests.get(url, timeout=30)
        print(f"[PAGING RESULT] 📡 HTTP Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result_content = response.text
            print(f"[PAGING RESULT] 📥 Successfully retrieved paging results from {url}")
            print(f"[PAGING RESULT] 📊 Content length: {len(result_content)} characters")
            if result_content.strip():
                print(f"[PAGING RESULT] 📝 First 200 chars: {result_content[:200]}...")
                return result_content
            else:
                print(f"[PAGING RESULT] ⚠️ Retrieved empty content from {url}")
                return ""
        else:
            print(f"[PAGING RESULT] ❌ HTTP Error {response.status_code} from {url}")
            return ""
    except Exception as e:
        print(f"[PAGING RESULT] ❌ Failed to retrieve paging results from {url}: {e}")
        print(f"[PAGING RESULT] 🔍 Exception type: {type(e).__name__}")
        return ""

#######################################################################
def parse_paging_output(output):
    """Parse paging command output to extract packet loss and latency statistics"""
    try:
        print(f"[PAGING PARSER] 🔍 Starting to parse paging output...")
        print(f"[PAGING PARSER] 📏 Output length: {len(output) if output else 0} characters")
        
        if not output or len(output.strip()) == 0:
            print(f"[PAGING PARSER] ❌ No output content to parse - returning None")
            return None
            
        print(f"[PAGING PARSER] 📝 Output content preview (first 300 chars):")
        print(f"[PAGING PARSER] {'='*60}")
        print(output[:300] + ("..." if len(output) > 300 else ""))
        print(f"[PAGING PARSER] {'='*60}")
        
        # Initialize default values
        packet_loss_percentage = 100.0
        avg_latency_ms = 0.0
        min_latency_ms = 0.0
        max_latency_ms = 0.0
        attempted = 20  # Default paging attempts
        connected = 0
        failed = 0
        
        lines = output.strip().split('\n')
        
        # Look for paging connection statistics
        for line in lines:
            # Look for patterns like "Attempted = 20, Connected = 20, Failed = 0 (0.00%)"
            if "attempted" in line.lower() and "connected" in line.lower() and "failed" in line.lower():
                import re
                # Extract attempted, connected, failed counts and percentage
                attempted_match = re.search(r'attempted\s*=\s*(\d+)', line.lower())
                connected_match = re.search(r'connected\s*=\s*(\d+)', line.lower())
                failed_match = re.search(r'failed\s*=\s*(\d+)', line.lower())
                percentage_match = re.search(r'(\d+(?:\.\d+)?)%', line)
                
                if attempted_match and connected_match and failed_match and percentage_match:
                    attempted = int(attempted_match.group(1))
                    connected = int(connected_match.group(1))
                    failed = int(failed_match.group(1))
                    packet_loss_percentage = float(percentage_match.group(1))
                    break
        
        # NEW APPROACH: Collect all individual latency values and calculate statistics
        latency_values = []
        successful_connections = 0
        total_attempts = 0
        
        print(f"[PAGING PARSER] 🔍 Analyzing individual latency lines...")
        
        for line in lines:
            # Look for individual latency lines like "192.0.2.1  latency=112.10ms  443"
            if "latency=" in line.lower():
                import re
                latency_match = re.search(r'latency=(\d+(?:\.\d+)?)ms', line.lower())
                if latency_match:
                    latency_value = float(latency_match.group(1))
                    latency_values.append(latency_value)
                    successful_connections += 1
                    total_attempts += 1
                    print(f"[PAGING PARSER] 📊 Found latency: {latency_value:.2f}ms")
                    
        # Calculate statistics from collected latency values
        if latency_values:
            min_latency_ms = min(latency_values)
            max_latency_ms = max(latency_values)
            avg_latency_ms = sum(latency_values) / len(latency_values)
            
            # Update connection statistics based on successful latency measurements
            attempted = total_attempts if total_attempts > 0 else 20
            connected = successful_connections
            failed = attempted - connected
            packet_loss_percentage = (failed / attempted) * 100.0 if attempted > 0 else 0.0
            
            print(f"[PAGING PARSER] 📈 Calculated from {len(latency_values)} individual measurements:")
            print(f"[PAGING PARSER] 📊 Min={min_latency_ms:.2f}ms, Max={max_latency_ms:.2f}ms, Avg={avg_latency_ms:.2f}ms")
            print(f"[PAGING PARSER] 📊 Attempted={attempted}, Connected={connected}, Failed={failed} ({packet_loss_percentage:.2f}%)")
        
        else:
            # FALLBACK: Look for pre-calculated summary statistics
            print(f"[PAGING PARSER] 🔄 No individual latency lines found, looking for summary statistics...")
            
            for line in lines:
                # Look for patterns like "Minimum = 110.04ms, Maximum = 117.82ms, Average = 113.98ms"
                if "minimum" in line.lower() and "maximum" in line.lower() and "average" in line.lower():
                    import re
                    # Extract minimum, maximum, average latency values
                    min_match = re.search(r'minimum\s*=\s*(\d+(?:\.\d+)?)ms', line.lower())
                    max_match = re.search(r'maximum\s*=\s*(\d+(?:\.\d+)?)ms', line.lower())
                    avg_match = re.search(r'average\s*=\s*(\d+(?:\.\d+)?)ms', line.lower())
                    
                    if min_match and max_match and avg_match:
                        min_latency_ms = float(min_match.group(1))
                        max_latency_ms = float(max_match.group(1))
                        avg_latency_ms = float(avg_match.group(1))
                        break
                # Look for patterns like "min/avg/max = 45.2/52.1/61.3 ms"
                elif "min/avg/max" in line.lower():
                    import re
                    latency_match = re.search(r'(\d+(?:\.\d+)?)/(\d+(?:\.\d+)?)/(\d+(?:\.\d+)?)', line)
                    if latency_match:
                        min_latency_ms = float(latency_match.group(1))
                        avg_latency_ms = float(latency_match.group(2))
                        max_latency_ms = float(latency_match.group(3))
                        break
        
        # Return parsed results
        result = {
            'packet_loss_percentage': packet_loss_percentage,
            'avg_latency_ms': avg_latency_ms,
            'min_latency_ms': min_latency_ms,
            'max_latency_ms': max_latency_ms,
            'attempted': attempted,
            'connected': connected,
            'failed': failed
        }
        
        # Print parsed paging results in concise format
        print(f"[PAGING RESULT] 📊 Attempted={attempted}, Connected={connected}, Failed={failed} ({packet_loss_percentage:.2f}%)")
        print(f"[PAGING RESULT] ⏱️ Min={min_latency_ms:.2f}ms, Max={max_latency_ms:.2f}ms, Avg={avg_latency_ms:.2f}ms")
        
        return result
        
    except Exception as e:
        print(f"[PAGING SCHEDULER] Error parsing paging output: {e}")
        return None