from flask import Blueprint, request, jsonify
from model import db, a97_whitelist_conditions
from datetime import datetime
from flask_cors import CORS, cross_origin

def get_matched_condition_pattern(result, country=None):
    """
    Find the condition pattern that determined the final result status
    Returns: string - the condition pattern that actually determined the result, or empty string if none
    """
    try:
        # Handle empty response case - no actual pattern match
        if result and "empty response" in result.lower():
            return ""

        # Get all enabled conditions ordered by priority (lower = higher priority)
        enabled_conditions = a97_whitelist_conditions.query.filter_by(is_enabled=True).order_by(
            a97_whitelist_conditions.priority.asc()
        ).all()

        # Check SUCCESS conditions FIRST (same logic as evaluate_curl_result_filtered)
        for condition in enabled_conditions:
            if condition.condition_type == 'success':
                # Check if country-specific condition applies
                if condition.country_specific:
                    # If country is not provided, or if it doesn't match, skip this condition
                    if not country or condition.country_specific.lower() != country.lower():
                        continue

                if condition.condition_pattern in result:
                    return condition.condition_pattern

        # Check FAILURE conditions SECOND (same logic as evaluate_curl_result_filtered)
        for condition in enabled_conditions:
            if condition.condition_type == 'failure':
                # Check if country-specific condition applies
                if condition.country_specific:
                    # If country is not provided, or if it doesn't match, skip this condition
                    if not country or condition.country_specific.lower() != country.lower():
                        continue

                if condition.condition_pattern in result:
                    return condition.condition_pattern

        # No matching conditions found
        return ""

    except Exception as e:
        print(f"[WHITELIST] ❌ Error finding matched condition: {e}")
        return ""

def evaluate_curl_result(result, country=None):
    """
    Evaluate curl result against enabled whitelist conditions (ORIGINAL VERSION)
    Returns: tuple (status, message)
    - status: 'success', 'failure', or 'unknown'
    - message: description of what was found
    - CONDITIONS ORDERED BY: priority field (lower = higher priority, checked first)
    """
    try:
        # Get all enabled conditions ordered by priority (lower = higher priority)
        enabled_conditions = a97_whitelist_conditions.query.filter_by(is_enabled=True).order_by(
            a97_whitelist_conditions.priority.asc()
        ).all()

        # Check failure conditions first
        for condition in enabled_conditions:
            if condition.condition_type == 'failure':
                if condition.condition_pattern in result:
                    return 'failure', f"cannot access, {condition.condition_name.lower()}"

        # Check success conditions
        for condition in enabled_conditions:
            if condition.condition_type == 'success':
                # Check if country-specific condition applies
                if condition.country_specific:
                    # If country is not provided, or if it doesn't match, skip this condition
                    if not country or condition.country_specific.lower() != country.lower():
                        continue

                if condition.condition_pattern in result:
                    return 'success', f"can access, {condition.condition_name.lower()}"

        # No matching conditions found
        return 'unknown', "in else cannot access"

    except Exception as e:
        print(f"[WHITELIST] ❌ Error evaluating conditions: {e}")
        return 'failure', f"error analyzing result: {e}"

def evaluate_curl_result_filtered(result, country=None):
    """
    Evaluate curl result with CORRECTED priority order for filtered page
    Returns: tuple (status, message)
    - status: 'success', 'failure', or 'unknown'
    - message: description of what was found
    - PRIORITY: Success conditions checked FIRST, then failure conditions
    - CONDITIONS ORDERED BY: priority field (lower = higher priority, checked first)
    """
    try:
        # Handle empty or None results as failure (connection failed/no response)
        if result is None or (isinstance(result, str) and result.strip() == ""):
            return 'failure', "cannot access, empty response (connection failed or no response)"

        # Get all enabled conditions ordered by priority (lower = higher priority)
        enabled_conditions = a97_whitelist_conditions.query.filter_by(is_enabled=True).order_by(
            a97_whitelist_conditions.priority.asc()
        ).all()

        # Check SUCCESS conditions FIRST (corrected priority)
        for condition in enabled_conditions:
            if condition.condition_type == 'success':
                # Check if country-specific condition applies
                if condition.country_specific:
                    # If country is not provided, or if it doesn't match, skip this condition
                    if not country or condition.country_specific.lower() != country.lower():
                        continue

                if condition.condition_pattern in result:
                    return 'success', f"can access, {condition.condition_name.lower()}"

        # Check FAILURE conditions ONLY if no success conditions matched
        for condition in enabled_conditions:
            if condition.condition_type == 'failure':
                if condition.condition_pattern in result:
                    return 'failure', f"cannot access, {condition.condition_name.lower()}"

        # No matching conditions found
        return 'unknown', "no matching success or failure conditions found"

    except Exception as e:
        print(f"[WHITELIST_FILTERED] ❌ Error evaluating conditions: {e}")
        return 'failure', f"error analyzing result: {e}"

whitelist_management = Blueprint('whitelist_management', __name__)
CORS(whitelist_management)

@whitelist_management.route('/api/whitelist/conditions')
@whitelist_management.route('/api/whitelist/conditions/')
def get_whitelist_conditions():
    """Get all whitelist conditions ordered by type then priority"""
    try:
        conditions = a97_whitelist_conditions.query.order_by(
            a97_whitelist_conditions.condition_type,
            a97_whitelist_conditions.priority.asc(),
            a97_whitelist_conditions.condition_name
        ).all()

        return jsonify([condition.serialize for condition in conditions])
    except Exception as e:
        print(f"[WHITELIST API] ❌ Error getting conditions: {e}")
        return jsonify({"error": str(e)}), 500

@whitelist_management.route('/api/whitelist/conditions', methods=['POST'])
@whitelist_management.route('/api/whitelist/conditions/', methods=['POST'])
def create_or_update_whitelist_condition():
    """Create or update a whitelist condition"""
    try:
        data = request.get_json()
        condition_id = data.get('id')

        if condition_id:
            # Update existing condition
            condition = a97_whitelist_conditions.query.get(condition_id)
            if not condition:
                return jsonify({"error": "Condition not found"}), 404

            condition.condition_name = data.get('condition_name', condition.condition_name)
            condition.condition_pattern = data.get('condition_pattern', condition.condition_pattern)
            condition.description = data.get('description', condition.description)
            condition.is_enabled = data.get('is_enabled', condition.is_enabled)
            condition.country_specific = data.get('country_specific', condition.country_specific)
            # Update priority if provided
            if 'priority' in data:
                condition.priority = data.get('priority')
            condition.updated_at = datetime.now()

            print(f"[WHITELIST API] ✏️ Updated condition: {condition.condition_name} (priority: {condition.priority})")
        else:
            # Create new condition
            condition = a97_whitelist_conditions(
                condition_type=data.get('condition_type', 'success'),
                condition_pattern=data.get('condition_pattern'),
                condition_name=data.get('condition_name'),
                description=data.get('description'),
                is_enabled=data.get('is_enabled', True),
                is_built_in=data.get('is_built_in', False),
                country_specific=data.get('country_specific'),
                priority=data.get('priority', 100)  # Default priority 100
            )
            db.session.add(condition)
            print(f"[WHITELIST API] ➕ Created new condition: {condition.condition_name} (priority: {condition.priority})")

        db.session.commit()
        return jsonify(condition.serialize)

    except Exception as e:
        db.session.rollback()
        print(f"[WHITELIST API] ❌ Error creating/updating condition: {e}")
        return jsonify({"error": str(e)}), 500

@whitelist_management.route('/api/whitelist/conditions/<int:condition_id>', methods=['DELETE'])
def delete_whitelist_condition(condition_id):
    """Delete a whitelist condition (only custom ones)"""
    try:
        condition = a97_whitelist_conditions.query.get(condition_id)
        if not condition:
            return jsonify({"error": "Condition not found"}), 404
            
        if condition.is_built_in:
            return jsonify({"error": "Cannot delete built-in conditions"}), 400
            
        db.session.delete(condition)
        db.session.commit()
        
        print(f"[WHITELIST API] 🗑️ Deleted condition: {condition.condition_name}")
        return jsonify({"message": "Condition deleted successfully"})
        
    except Exception as e:
        db.session.rollback()
        print(f"[WHITELIST API] ❌ Error deleting condition: {e}")
        return jsonify({"error": str(e)}), 500

@whitelist_management.route('/api/whitelist/conditions/toggle/<int:condition_id>', methods=['POST'])
def toggle_whitelist_condition(condition_id):
    """Toggle a whitelist condition on/off"""
    try:
        condition = a97_whitelist_conditions.query.get(condition_id)
        if not condition:
            return jsonify({"error": "Condition not found"}), 404
            
        condition.is_enabled = not condition.is_enabled
        condition.updated_at = datetime.now()
        db.session.commit()
        
        status = "enabled" if condition.is_enabled else "disabled"
        print(f"[WHITELIST API] 🔄 {status.title()} condition: {condition.condition_name}")
        return jsonify(condition.serialize)
        
    except Exception as e:
        db.session.rollback()
        print(f"[WHITELIST API] ❌ Error toggling condition: {e}")
        return jsonify({"error": str(e)}), 500

@whitelist_management.route('/api/whitelist/conditions/enabled')
@whitelist_management.route('/api/whitelist/conditions/enabled/')
def get_enabled_conditions():
    """Get only enabled conditions for display, ordered by priority"""
    try:
        conditions = a97_whitelist_conditions.query.filter_by(is_enabled=True).order_by(
            a97_whitelist_conditions.condition_type,
            a97_whitelist_conditions.priority.asc(),
            a97_whitelist_conditions.condition_name
        ).all()

        return jsonify([condition.serialize for condition in conditions])
    except Exception as e:
        print(f"[WHITELIST API] ❌ Error getting enabled conditions: {e}")
        return jsonify({"error": str(e)}), 500

@whitelist_management.route('/api/whitelist/initialize', methods=['POST'])
@whitelist_management.route('/api/whitelist/initialize/', methods=['POST'])
def initialize_default_conditions():
    """Initialize the database with default built-in conditions"""
    try:
        # Check if already initialized
        existing_count = a97_whitelist_conditions.query.filter_by(is_built_in=True).count()
        if existing_count > 0:
            return jsonify({"message": "Default conditions already initialized", "count": existing_count})
        
        # Default failure conditions
        failure_conditions = [
            {
                "condition_pattern": "Could not resolve",
                "condition_name": "DNS Resolution Failed", 
                "description": "Domain cannot be resolved to IP address"
            },
            {
                "condition_pattern": "timeout",
                "condition_name": "Connection Timeout",
                "description": "Server not responding within time limit"
            },
            {
                "condition_pattern": "Failed to connect to",
                "condition_name": "Connection Failed",
                "description": "Server refused connection or unreachable"
            },
            {
                "condition_pattern": "SSL_ERROR_SYSCALL",
                "condition_name": "SSL/TLS Error",
                "description": "SSL/TLS connection error - certificate or encryption issues"
            },
            {
                "condition_pattern": "52770",
                "condition_name": "SSH Port 52770 Access Failed",
                "description": "SSH probe connection error - port 52770 access failed"
            }
        ]
        
        # Default success conditions
        success_conditions = [
            {
                "condition_pattern": "a-demo-cookie",
                "condition_name": "DemoCookie Cookie",
                "description": "Cookie name a-demo-cookie found in response"
            },
            {
                "condition_pattern": "demo-marker-a",
                "condition_name": "DemoMarkerA Content",
                "description": "DemoMarkerA content identifier found"
            },
            {
                "condition_pattern": "demobrand",
                "condition_name": "DemoBrand Content (lowercase)",
                "description": "demobrand identifier found in response"
            },
            {
                "condition_pattern": "DEMOBRAND",
                "condition_name": "DemoBrand Content (uppercase)",
                "description": "DEMOBRAND identifier found in response"
            },
            {
                "condition_pattern": "demo-redirect-1",
                "condition_name": "DemoRedirect1 Redirect (China)",
                "description": "demo-redirect-1 redirect found - China specific",
                "country_specific": "China"
            },
            {
                "condition_pattern": "demo-redirect-2",
                "condition_name": "DemoRedirect2 Redirect (China)",
                "description": "demo-redirect-2 redirect found - China specific", 
                "country_specific": "China"
            },
            {
                "condition_pattern": "demo-redirect-3",
                "condition_name": "DemoRedirect3 Redirect (China)",
                "description": "demo-redirect-3 redirect found - China specific",
                "country_specific": "China"
            },
            {
                "condition_pattern": "demo-redirect-4",
                "condition_name": "DemoRedirect4 Redirect (China)",
                "description": "demo-redirect-4 redirect found - China specific",
                "country_specific": "China"
            },
            {
                "condition_pattern": "demo-ok",
                "condition_name": "Demo OK marker",
                "description": "demo-ok marker found in response"
            }
        ]
        
        # Add failure conditions
        for condition_data in failure_conditions:
            condition = a97_whitelist_conditions(
                condition_type='failure',
                condition_pattern=condition_data['condition_pattern'],
                condition_name=condition_data['condition_name'],
                description=condition_data['description'],
                is_enabled=True,
                is_built_in=True,
                country_specific=condition_data.get('country_specific')
            )
            db.session.add(condition)
            
        # Add success conditions  
        for condition_data in success_conditions:
            condition = a97_whitelist_conditions(
                condition_type='success',
                condition_pattern=condition_data['condition_pattern'],
                condition_name=condition_data['condition_name'],
                description=condition_data['description'],
                is_enabled=True,
                is_built_in=True,
                country_specific=condition_data.get('country_specific')
            )
            db.session.add(condition)
        
        db.session.commit()
        total_created = len(failure_conditions) + len(success_conditions)
        
        print(f"[WHITELIST API] 🎯 Initialized {total_created} default conditions")
        return jsonify({
            "message": "Default conditions initialized successfully",
            "failure_conditions": len(failure_conditions),
            "success_conditions": len(success_conditions),
            "total_created": total_created
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"[WHITELIST API] ❌ Error initializing default conditions: {e}")
        return jsonify({"error": str(e)}), 500