import os
from flask import Flask, render_template, redirect, url_for, jsonify, session, json, Blueprint, request
import requests
import time
import re
# from file_func_current_connection import func_prtg_current_outgoing_traffic,func_peakbw,func_prtg_current_connection
import datetime
from flask_cors import CORS, cross_origin

# starting_one_hour_ago=(datetime.datetime.now() - datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
import paramiko
from paramiko import SSHClient, SSHConfig
import subprocess
# from forms import User_enter_IP_and_show_result
from datetime import datetime
from model import db, a01_probe_list, a05_controlling_for_hiding_or_showing_the_button_and_table, a20_url_from_jenney_excel, a30_availiblity, a40_availiblity_for_each_country, a60_checking_in_which_country


check_if_can_access_internet_or_not = Blueprint("check_if_can_access_internet_or_not", __name__)
CORS(check_if_can_access_internet_or_not)

#######################################################################
@check_if_can_access_internet_or_not.route('/test')
@check_if_can_access_internet_or_not.route('/test/')
def test():
    return "1"



#######################################################################
@check_if_can_access_internet_or_not.route('/check_if_the_probe_can_access_internet_or_not')
@check_if_can_access_internet_or_not.route('/check_if_the_probe_can_access_internet_or_not/')
def check_if_the_probe_can_access_internet_or_not():
    whole_db_a01_probe_list=a01_probe_list.query.all()
    for each_row in whole_db_a01_probe_list:
        each_row.is_the_probe_broken=None
        db.session.commit()
    
    for each_row in whole_db_a01_probe_list:
        
        probe_ip=each_row.probe_ip
        port=52770
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            print(f"checking {probe_ip}")
            ssh.connect(probe_ip, port, "root", os.environ.get("SSH_PASSWORD", ""))   
            command_for_testing_if_the_internet_is_normal_or_not = f"curl -sS --max-time 3 http://probe-check.example.com/GetMyIP"     
            stdin, stdout, stderr = ssh.exec_command(command_for_testing_if_the_internet_is_normal_or_not)
            stdout_readlines=stdout.readlines()
            stderr_readlines=stderr.readlines()            
            str_stdout_readlines = ''.join(stdout_readlines)
            str_stderr_readlines = ''.join(stderr_readlines)
            print(f"str_stdout_readlines={str_stdout_readlines} / str_stderr_readlines={str_stderr_readlines} ")
            if "failed" not in str_stderr_readlines or "not" not in str_stderr_readlines:
                print(f"probe_ip={probe_ip} / ok")
                each_row.is_the_probe_broken="can_access_internet"
                db.session.commit()
        except Exception as error:
            print(f"probe_ip={probe_ip} / error={error}")
            each_row.is_the_probe_broken=error
            db.session.commit()
                
        
    
    
    return "1"

