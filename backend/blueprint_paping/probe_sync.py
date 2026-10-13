from flask import Blueprint, jsonify
from model import db, a01_probe_list, b11_huck_ge_probes, get_gmt8_now
import logging

probe_sync = Blueprint('probe_sync', __name__)

@probe_sync.route('/api/sync-probes', methods=['POST'])
def sync_probes_from_b11_huck_ge():
    """
    Sync probe data from b11_huck_ge.b11_huck_ge_probes to local a01_probe_list table
    """
    try:
        print("[PROBE SYNC] 🔄 Starting probe synchronization from b11_huck_ge database...")

        # Query b11_huck_ge_probes table for server list
        print("[PROBE SYNC] 📡 Querying b11_huck_ge_probes table...")
        b11_probes = b11_huck_ge_probes.query.all()

        if not b11_probes:
            print("[PROBE SYNC] ⚠️ No probes found in b11_huck_ge_probes table")
            return jsonify({
                'success': False,
                'message': 'No probes found in b11_huck_ge_probes table',
                'synced_count': 0
            }), 404

        print(f"[PROBE SYNC] 📊 Found {len(b11_probes)} probes in b11_huck_ge_probes")

        synced_count = 0
        current_time = get_gmt8_now()

        for probe in b11_probes:
            try:
                # Check if probe already exists in local a01_probe_list
                existing_probe = a01_probe_list.query.filter_by(probe_ip=probe.probe_ip).first()

                if existing_probe:
                    # Update existing probe
                    existing_probe.url = probe.url
                    existing_probe.country = probe.country
                    existing_probe.isp = probe.isp
                    existing_probe.hostname = probe.hostname
                    existing_probe.link_for_open_cancan_in_browser = probe.link_for_open_cancan_in_browser
                    existing_probe.wrote_to_db_time = current_time
                    existing_probe.is_the_probe_broken = probe.is_the_probe_broken
                    print(f"[PROBE SYNC] 🔄 Updated existing probe: {probe.probe_ip}")
                else:
                    # Create new probe entry
                    new_probe = a01_probe_list(
                        probe_ip=probe.probe_ip,
                        url=probe.url,
                        country=probe.country,
                        isp=probe.isp,
                        hostname=probe.hostname,
                        link_for_open_cancan_in_browser=probe.link_for_open_cancan_in_browser,
                        wrote_to_db_time=current_time,
                        is_the_probe_broken=probe.is_the_probe_broken
                    )
                    db.session.add(new_probe)
                    print(f"[PROBE SYNC] ➕ Added new probe: {probe.probe_ip}")

                synced_count += 1

            except Exception as e:
                print(f"[PROBE SYNC] ❌ Error syncing probe {probe.probe_ip}: {e}")
                continue

        # Commit all changes
        db.session.commit()

        print(f"[PROBE SYNC] ✅ Successfully synced {synced_count} probes from b11_huck_ge to local database")

        return jsonify({
            'success': True,
            'message': f'Successfully synced {synced_count} probes from b11_huck_ge',
            'synced_count': synced_count,
            'total_found': len(b11_probes)
        })

    except Exception as e:
        db.session.rollback()
        error_msg = f"Error syncing probes from b11_huck_ge: {str(e)}"
        print(f"[PROBE SYNC] ❌ {error_msg}")
        logging.error(error_msg)

        return jsonify({
            'success': False,
            'message': error_msg,
            'synced_count': 0
        }), 500


@probe_sync.route('/api/probe-stats', methods=['GET'])
def get_probe_statistics():
    """
    Get statistics about probe counts in both databases
    """
    try:
        # Count probes in b11_huck_ge_probes
        b11_count = b11_huck_ge_probes.query.count()

        # Count probes in local a01_probe_list
        local_count = a01_probe_list.query.count()

        return jsonify({
            'success': True,
            'b11_huck_ge_probes_count': b11_count,
            'local_a01_probe_list_count': local_count,
            'message': f'B11 Huck GE: {b11_count} probes, Local: {local_count} probes'
        })

    except Exception as e:
        error_msg = f"Error getting probe statistics: {str(e)}"
        print(f"[PROBE SYNC] ❌ {error_msg}")

        return jsonify({
            'success': False,
            'message': error_msg
        }), 500


@probe_sync.route('/api/test-b11-connection', methods=['GET'])
def test_b11_connection():
    """
    Test connection to b11_huck_ge database
    """
    try:
        # Try to query the b11_huck_ge_probes table
        probe_count = b11_huck_ge_probes.query.count()

        print(f"[PROBE SYNC] ✅ B11 Huck GE database connection successful. Found {probe_count} probes.")

        return jsonify({
            'success': True,
            'message': f'B11 Huck GE database connection successful. Found {probe_count} probes.',
            'probe_count': probe_count
        })

    except Exception as e:
        error_msg = f"B11 Huck GE database connection failed: {str(e)}"
        print(f"[PROBE SYNC] ❌ {error_msg}")

        return jsonify({
            'success': False,
            'message': error_msg
        }), 500