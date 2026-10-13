from flask import Flask, render_template, redirect, url_for, jsonify, session, json
import os
import requests
import time
import re
# from file_func_current_connection import func_prtg_current_outgoing_traffic,func_peakbw,func_prtg_current_connection
import datetime
import logging
import threading

current_Time = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S")

# Heartbeat configuration
heartbeat_start_time = None
request_counter = 0
# starting_one_hour_ago=(datetime.datetime.now() - datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
import paramiko
from paramiko import SSHClient, SSHConfig
# from forms import User_enter_IP_and_show_result
from datetime import datetime

# from blueprint_paping.paping_blueprint import paping_blueprint
# from blueprint_paping.mtr_blueprint import mtr_blueprint
# from blueprint_paping.axios_blueprint import axios_blueprint
# from blueprint_paping.show_papaing_or_mtr_result_by_querying_apache_blueprint import show_papaing_or_mtr_result_by_querying_apache_blueprint
# from blueprint_paping.dig_blueprint import dig_blueprint
# from blueprint_paping.curl_blueprint import curl_blueprint
from blueprint_paping.axios_query_backend import axios_query_backend
from blueprint_paping.handling_data_received_from_frontend import handling_data_received_from_frontend
from blueprint_paping.check_if_can_access_internet_or_not import check_if_can_access_internet_or_not
from blueprint_paping.scheduled_monitoring import scheduled_monitoring
# from blueprint_paping.paping_scheduled_monitoring import paping_scheduled_monitoring
from blueprint_paping.whitelist_management import whitelist_management
from blueprint_paping.probe_sync import probe_sync

if os.environ.get('SIMULATION_MODE', '1') == '1':
    import simulation
    simulation.enable()

#########Migrations#############
app = Flask(__name__)

# Configure logging to suppress GET request messages
logging.getLogger('werkzeug').setLevel(logging.WARNING)

# app.register_blueprint(paping_blueprint)
# app.register_blueprint(mtr_blueprint)
# app.register_blueprint(axios_blueprint)
# app.register_blueprint(show_papaing_or_mtr_result_by_querying_apache_blueprint)
# app.register_blueprint(dig_blueprint)
# app.register_blueprint(curl_blueprint)
app.register_blueprint(axios_query_backend)
app.register_blueprint(handling_data_received_from_frontend)
app.register_blueprint(check_if_can_access_internet_or_not,url_prefix="/check")
app.register_blueprint(scheduled_monitoring,url_prefix="/scheduled")
# app.register_blueprint(paping_scheduled_monitoring,url_prefix="/paping")
app.register_blueprint(whitelist_management,url_prefix="/whitelist")
app.register_blueprint(probe_sync,url_prefix="/probe-sync")

from model import db, a01_probe_list, b11_huck_ge_probes, a80_scheduled_domains, a90_scheduled_results, a95_paping_scheduled_destinations, a96_paping_results, a97_whitelist_conditions

from flask_migrate import Migrate
from flask_cors import CORS, cross_origin

migrate = Migrate(app, db)
from config import DevConfig
app.config.from_object(DevConfig)
CORS(app, origins=['http://localhost:8082', 'http://localhost:8082'], 
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization'])

db.init_app(app)

# Restore scheduled monitoring jobs after database initialization
with app.app_context():
    from blueprint_paping.scheduled_monitoring import restore_scheduled_jobs
    restore_scheduled_jobs()

# Heartbeat logging to show backend is running
def heartbeat_logger():
    global heartbeat_start_time
    heartbeat_start_time = datetime.now()
    interval = 60  # seconds
    while True:
        time.sleep(interval)
        uptime = datetime.now() - heartbeat_start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        print(f"[HEARTBEAT] 💓 Backend running - Uptime: {hours}h {minutes}m {seconds}s | Requests: {request_counter}")

# Start heartbeat thread
heartbeat_thread = threading.Thread(target=heartbeat_logger, daemon=True)
heartbeat_thread.start()
print("[HEARTBEAT] 💚 Heartbeat logging started (status every 60 seconds)")

# Count incoming requests
@app.before_request
def count_requests():
    global request_counter
    request_counter += 1

######################session control#########################################
from flask import session

app.secret_key = os.urandom(24)

#to insert time into the session
from datetime import datetime


# Add this function at the bottom of your Flask application code
def create_app(host='0.0.0.0', port=5030):
    return app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5030, debug=True)