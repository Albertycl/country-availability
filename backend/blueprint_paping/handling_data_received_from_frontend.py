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
# from forms import User_enter_IP_and_show_result
from datetime import datetime
from model import db, a01_probe_list,a05_controlling_for_hiding_or_showing_the_button_and_table,a20_url_from_jenney_excel,a30_availiblity,a40_availiblity_for_each_country,a60_checking_in_which_country,a99_processing_logs,format_datetime_gmt8,get_gmt8_now
from blueprint_paping.whitelist_management import evaluate_curl_result, evaluate_curl_result_filtered
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


handling_data_received_from_frontend = Blueprint(
    "handling_data_received_from_frontend", __name__)
CORS(handling_data_received_from_frontend)


# Log streaming helper function
def emit_log(message, session_id=None):
    """Print to console and save to database for frontend polling"""
    print(message)
    if session_id:
        try:
            log_entry = a99_processing_logs(session_id=session_id, message=message)
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            print(f"[LOG ERROR] Failed to save log: {e}")
            db.session.rollback()  # Ensure session is in clean state after error


@handling_data_received_from_frontend.route('/api/logs/<session_id>', methods=["GET"])
@cross_origin()
def get_logs(session_id):
    """Fetch logs for a session, optionally after a specific log ID"""
    last_id = request.args.get('last_id', 0, type=int)
    logs = a99_processing_logs.query.filter(
        a99_processing_logs.session_id == session_id,
        a99_processing_logs.id > last_id
    ).order_by(a99_processing_logs.id.asc()).all()
    return jsonify([log.serialize for log in logs])


@handling_data_received_from_frontend.route('/api/logs/<session_id>', methods=["DELETE"])
@cross_origin()
def clear_logs(session_id):
    """Clean up logs for a session"""
    a99_processing_logs.query.filter_by(session_id=session_id).delete()
    db.session.commit()
    return jsonify({"success": True})


#######################################################################
@handling_data_received_from_frontend.route('/a10_init_get_probe_data', methods=["GET", "POST"])
@handling_data_received_from_frontend.route('/a10_init_get_probe_data/', methods=["GET", "POST"])
@cross_origin()
def a10_init_get_probe_data():

    db.session.query(a01_probe_list).delete()
    db.session.commit()
    if request.method == "POST":
        print("in route a10_init_get_probe_data")
        probe_list_send_frontend = request.data
        dict_probe_list_send_frontend = json.loads(
            probe_list_send_frontend.decode('utf-8'))
        list_probe_list = dict_probe_list_send_frontend["probe_list"]["data"]
        # if only testing a single probe, comment starting from this row
        for each_row in list_probe_list:
            # print(f"each_row={each_row}")
            probe_ip = each_row["server_private_ip"]
            country = each_row["country"]
            isp = each_row["isp"]
            link_for_open_cancan_in_browser = each_row["link_for_open_cancan_in_browser"]
            current_Time = get_gmt8_now().strftime("%Y-%m-%d-%H:%M:%S")
            if country == "CT" or country == "CU" or country == "CM":
                country = "China"
            elif country == "PH_Office":
                continue
                # skip this iteration

    #         whole_row_to_insert=a01_probe_list(probe_ip=probe_ip,country=country,isp=isp,wrote_to_db_time=current_Time,link_for_open_cancan_in_browser=link_for_open_cancan_in_browser)
    #         db.session.add(whole_row_to_insert)
    #         db.session.commit()


    return "1"


#######################################################################
@handling_data_received_from_frontend.route('/b10_when_received_from_frontend', methods=["GET", "POST"])
@handling_data_received_from_frontend.route('/b10_when_received_from_frontend/', methods=["GET", "POST"])
@cross_origin()
def b10_when_received_from_frontend():
    print(f"\n{'='*70}")
    print(f"[PROCESS] 🚀 STARTING URL AVAILABILITY CHECK")
    print(f"{'='*70}")

    # inserting result url to db a30_availiblity
    db.session.query(a30_availiblity).delete()
    db.session.commit()

    db.session.query(a20_url_from_jenney_excel).delete()
    db.session.commit()

    db.session.query(a05_controlling_for_hiding_or_showing_the_button_and_table).delete()
    db.session.commit()

    db.session.query(a60_checking_in_which_country).delete()
    db.session.commit()

    # write the urls in to db a20_url_from_jenney_excel
    if request.method == "POST":
        jenney_url_send_frontend=request.data
        dict_jenney_url_send_frontend=json.loads(jenney_url_send_frontend.decode('utf-8'))
        str_dict_jenney_url_send_frontend=dict_jenney_url_send_frontend["input_from_jenny_excel"]
        str_show_the_button_and_table=dict_jenney_url_send_frontend["show_the_button_and_table"]
        list_testing_avalibility_in_which_country=dict_jenney_url_send_frontend["list_testing_avalibility_in_which_country"]

        # Count URLs
        list_dict_jenney_url_send_frontend=str_dict_jenney_url_send_frontend.split(",")
        url_count = len([u for u in list_dict_jenney_url_send_frontend if u.strip()])

        print(f"\n[STEP 1/5] 📋 PREPARING URL COMBINATIONS FOR {url_count} DOMAINS")
        print(f"[STEP 1/5] 🌍 Countries to test: {list_testing_avalibility_in_which_country}")

        whole_row_to_insert=a05_controlling_for_hiding_or_showing_the_button_and_table(hiding_or_showing_the_button_and_table=str_show_the_button_and_table)
        db.session.add(whole_row_to_insert)
        db.session.commit()

        for each_url in list_dict_jenney_url_send_frontend:
            each_url = each_url.replace("\n", "")
            if each_url != "":
                whole_row_to_insert = a20_url_from_jenney_excel(
                    url_from_jenney_excel=each_url, has_the_url_been_checked="havent_been_checked")
                db.session.add(whole_row_to_insert)
                db.session.commit()

        print(f"[STEP 1/5] ✅ URLs prepared and stored in database")

        print(f"\n[STEP 2/5] 📡 SENDING CURL COMMANDS TO GLOBAL PROBE SERVERS")
        for each_country in list_testing_avalibility_in_which_country:
            whole_row_to_insert=a60_checking_in_which_country(which_country=each_country)
            db.session.add(whole_row_to_insert)
            db.session.commit()
            print(f"[STEP 2/5] 🔍 Checking probe connectivity for {each_country}...")
            check_if_the_probe_can_access_internet_or_not_by_country_filter(each_country)


    # read from db and check if the url can be access from each probe or not
    print(f"\n[STEP 3/5] 🌐 RUNNING AVAILABILITY TESTS FROM MULTIPLE LOCATIONS")
    whole_db_a20_url_from_jenney_excel=a20_url_from_jenney_excel.query.all()
    total_urls = len(whole_db_a20_url_from_jenney_excel)
    current_url_num = 0
    for each_row in whole_db_a20_url_from_jenney_excel:
        each_url=each_row.url_from_jenney_excel
        if each_url!="":
            current_url_num += 1
            print(f"[STEP 3/5] 🔄 Testing URL {current_url_num}/{total_urls}: {each_url}")
            b20_do_curl_to_ge_probes(each_url)

    # check from /var/www/html if the curl result contains 200 or stick cookie
    print(f"\n[STEP 4/5] 🔬 ANALYZING RESULTS - APPLYING WHITELIST CONDITIONS")
    c10_check_the_curl_result_and_update_the_result_to_db()

    # count the availability for each country
    print(f"\n[STEP 5/5] 📊 COMPUTING FINAL AVAILABILITY PERCENTAGES")
    c02_caculate_availability_for_each_country()

    print(f"\n{'='*70}")
    print(f"[PROCESS] ✅ URL AVAILABILITY CHECK COMPLETED")
    print(f"{'='*70}\n")

    return "response_from_backend"




#######################################################################
def b20_do_curl_to_ge_probes(target_ip_for_curl):


    current_Time = get_gmt8_now().strftime("%Y-%m-%d-%H:%M:%S")

    a_row_when_the_url_is_checked_update_the_checking_status = a20_url_from_jenney_excel.query.filter(
        a20_url_from_jenney_excel.url_from_jenney_excel == target_ip_for_curl).first()
    a_row_when_the_url_is_checked_update_the_checking_status.has_the_url_been_checked = "in_process_of_checking_this_url"
    a_row_when_the_url_is_checked_update_the_checking_status.start_query_time = current_Time
    db.session.commit()

    whole_db_a01_probe_list=a01_probe_list.query.all()
    probe_count = 0
    for each_row in whole_db_a01_probe_list:
        which_GE_server=each_row.probe_ip
        this_country_is_from_db=each_row.country
        is_the_probe_broken=each_row.is_the_probe_broken
        if is_the_probe_broken=="its_broken":
            continue
        all_the_coutries_that_need_to_be_checked=a60_checking_in_which_country.query.all()
        for each_country_the_i_want_to_check in all_the_coutries_that_need_to_be_checked:
            # print(f"each_country_the_i_want_to_check={each_country_the_i_want_to_check} / this_country_is_from_db={this_country_is_from_db}")
            if each_country_the_i_want_to_check.which_country==this_country_is_from_db:
                isp=each_row.isp
                link_for_open_cancan_in_browser=each_row.link_for_open_cancan_in_browser

                port = 52770
                try:
                    probe_count += 1
                    print(f"[CURL] 🔌 Probe {probe_count}: {which_GE_server} ({this_country_is_from_db}/{isp}) -> {target_ip_for_curl}")
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(which_GE_server, port, "root", os.environ.get("SSH_PASSWORD", ""))
                    current_Time = get_gmt8_now().strftime("%Y-%m-%d-%H:%M:%S")
                    time_for_filename=current_Time.replace("-","_").replace(":","_")
                    filename_for_paping_located_in_GE_apache =  "jenny_excel"+ "_" + target_ip_for_curl + "_" + "_result_" + which_GE_server + "_" + time_for_filename
                    filename_for_paping_located_in_GE_apache=filename_for_paping_located_in_GE_apache.replace("http://","").replace("https://","")
                    # curl_command = f"curl -ILk --tls-max 1.2 -m 10 --http2 {target_ip_for_curl} >> /var/www/html/{filename_for_paping_located_in_GE_apache} 2>&1"
                    # curl_command = f"curl -L -v --insecure {target_ip_for_curl} >> /var/www/html/{filename_for_paping_located_in_GE_apache} 2>&1"
                    curl_command = f"curl -s -L --insecure  {target_ip_for_curl} -A'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36' >> /var/www/html/{filename_for_paping_located_in_GE_apache} 2>&1"
                    stdin, stdout, stderr = ssh.exec_command(curl_command)
                    curl_result_link=f"http://{which_GE_server}:8787/{filename_for_paping_located_in_GE_apache}"
                    ssh.close()
                    is_the_probe_broken=a01_probe_list.query.filter(a01_probe_list.probe_ip==which_GE_server).first().is_the_probe_broken
                    whole_row_to_insert_after_running_curl = a30_availiblity(probe_ip=which_GE_server, url_that_im_testing=target_ip_for_curl, country=this_country_is_from_db,
                                                                             isp=isp, curl_result_link=curl_result_link, wrote_to_db_time=current_Time, link_for_open_cancan_in_browser=link_for_open_cancan_in_browser,can_access_internet_or_not=is_the_probe_broken)                    
                    db.session.add(whole_row_to_insert_after_running_curl)
                    db.session.commit()
                
                except Exception as error:
                    print(f"[SSH_ERROR] 🔌 Failed to connect to probe {which_GE_server} for testing {target_ip_for_curl}")
                    print(f"[SSH_ERROR] 📍 Country: {this_country_is_from_db}, ISP: {isp}")
                    print(f"[SSH_ERROR] ❌ Error details: {str(error)}")
                    if "Connection refused" in str(error):
                        print(f"[SSH_ERROR] 🚫 Probe server {which_GE_server} is refusing SSH connections on port 52770")
                    elif "timeout" in str(error).lower():
                        print(f"[SSH_ERROR] ⏱️ SSH connection to {which_GE_server} timed out - server may be down or unreachable")
                    elif "authentication failed" in str(error).lower():
                        print(f"[SSH_ERROR] 🔐 SSH authentication failed for {which_GE_server} - credentials may be incorrect")
                    whole_row_to_insert_after_running_curl = a30_availiblity(probe_ip=which_GE_server, url_that_im_testing=target_ip_for_curl, country=this_country_is_from_db,
                                                                             isp=isp, can_access_or_not=f"SSH connection failed: {error}", curl_result_link="skip", wrote_to_db_time=current_Time, link_for_open_cancan_in_browser=link_for_open_cancan_in_browser,can_access_internet_or_not=is_the_probe_broken)                    
                    db.session.add(whole_row_to_insert_after_running_curl)
                    db.session.commit()                    

    print(f"target_ip_for_curl={target_ip_for_curl} / e02_url_finished_checking")
    a_row_when_the_url_is_checked_update_the_checking_status=a20_url_from_jenney_excel.query.filter(a20_url_from_jenney_excel.url_from_jenney_excel==target_ip_for_curl).first()
    a_row_when_the_url_is_checked_update_the_checking_status.has_the_url_been_checked="finish_checking_this_url"
    a_row_when_the_url_is_checked_update_the_checking_status.end_query_time=current_Time
    db.session.commit()
    return "filename_for_paping_located_in_GE_apache"


##############################################################################################################################################
@handling_data_received_from_frontend.route('/c10_check_the_curl_result_and_update_the_result_to_db')
@handling_data_received_from_frontend.route('/c10_check_the_curl_result_and_update_the_result_to_db/')
def c10_check_the_curl_result_and_update_the_result_to_db():

    whole_db_a30_availiblity = a30_availiblity.query.all()
    total_results = len(whole_db_a30_availiblity)
    analyzed_count = 0
    success_count = 0
    failure_count = 0
    print(f"[ANALYZE] 📝 Analyzing {total_results} curl results...")
    for each_row in whole_db_a30_availiblity:
        curl_result_link=each_row.curl_result_link
        if "skip" in curl_result_link:
            continue          
        try:
            # result=requests.get(curl_result_link).text
            result=fixing_curl_cannot_get_the_contain_issue(curl_result_link)
            
            log_file = "my_log.txt"
            # if each_row.probe_ip=="192.0.2.10":
            #     with open(log_file, "w") as file:
            #         file.write(f"curl_result_link={curl_result_link}\n")
            #         file.write(f"++++++++++++++++++++++++++++++++\n")
            #         file.write(f"result={result}\n")
          
            # Use dynamic whitelist conditions instead of hardcoded logic
            status, message = evaluate_curl_result_filtered(result, each_row.country)
            each_row.can_access_or_not = message
            
            analyzed_count += 1
            if status == 'failure':
                failure_count += 1
                print(f"[ANALYZE] ❌ {analyzed_count}/{total_results} {each_row.probe_ip} ({each_row.country}): {message}")
            elif status == 'success':
                success_count += 1
                print(f"[ANALYZE] ✅ {analyzed_count}/{total_results} {each_row.probe_ip} ({each_row.country}): {message}")
            else:
                failure_count += 1
                print(f"[ANALYZE] ❓ {analyzed_count}/{total_results} {each_row.probe_ip} ({each_row.country}): Unknown result")

            db.session.commit()
        except Exception as error:
            analyzed_count += 1
            failure_count += 1
            print(f"[ANALYZE] 💥 {analyzed_count}/{total_results} Error: {each_row.probe_ip} - {error}")
            each_row.can_access_or_not = f"error analyzing result: {error}"
            db.session.commit()

    print(f"[ANALYZE] 📊 Analysis complete: {success_count} success, {failure_count} failure out of {total_results} total")
    return "1"


##############################################################################################################################################
@handling_data_received_from_frontend.route('/c02_caculate_availability_for_each_country')
@handling_data_received_from_frontend.route('/c02_caculate_availability_for_each_country/')
def c02_caculate_availability_for_each_country():

    db.session.query(a40_availiblity_for_each_country).delete()
    db.session.commit()

    set_all_the_counties = set()
    whole_db_a30_availiblity = a30_availiblity.query.all()
    for each_row in whole_db_a30_availiblity:
        country = each_row.country
        set_all_the_counties.add(country)

    print(f"[CALC] 🧮 Computing availability for {len(set_all_the_counties)} countries: {list(set_all_the_counties)}")

    whole_db_a20_url_from_jenney_excel = a20_url_from_jenney_excel.query.all()
    how_many_probes_can_access = 0
    total_how_many_probes = 0
    availiblity = 0
    for each_coutry in set_all_the_counties:
        current_Time = get_gmt8_now().strftime("%Y-%m-%d-%H:%M:%S")
        for each_row_from_url_that_we_test in whole_db_a20_url_from_jenney_excel:
            url_from_jenney_excel = each_row_from_url_that_we_test.url_from_jenney_excel
            # # mark this url as checked
            # each_row_from_url_that_we_test.has_the_url_been_checked="finish_checking_this_url"
            # db.session.commit()
            # ##########################
            a30_availiblity_whole_db_that_matches_url_and_country_that_im_testing = a30_availiblity.query.filter(a30_availiblity.url_that_im_testing == url_from_jenney_excel, a30_availiblity.country == each_coutry).all()
            how_many_probes_can_access = 0
            total_how_many_probes = 0
            for each_row_after_url_filtered in a30_availiblity_whole_db_that_matches_url_and_country_that_im_testing:
                can_access_or_not = each_row_after_url_filtered.can_access_or_not
                probe_ip = each_row_after_url_filtered.probe_ip
                is_the_probe_broken=a01_probe_list.query.filter(a01_probe_list.probe_ip==probe_ip).first().is_the_probe_broken
                # print(f"url_from_jenney_excel={url_from_jenney_excel} / each_coutry={each_coutry} / can_access_or_not={can_access_or_not}")
                if "can access" in can_access_or_not:
                    total_how_many_probes = total_how_many_probes+1
                    how_many_probes_can_access = how_many_probes_can_access+1
                elif "cannot access" in can_access_or_not and is_the_probe_broken=="can_access_internet":
                    total_how_many_probes = total_how_many_probes+1
            print(f"how_many_probes_can_access={how_many_probes_can_access} / total_how_many_probes={total_how_many_probes}")
            try:
                availiblity = round(how_many_probes_can_access/total_how_many_probes*100, 2)
            except:
                print(f"ERROR:::::each_coutry={each_coutry} / how_many_probes_can_access={how_many_probes_can_access} / total_how_many_probes={total_how_many_probes}")
            if url_from_jenney_excel == "":
                pass
            else:
                print(f'[CALC] 📈 {url_from_jenney_excel} | {each_coutry} | {availiblity}% ({how_many_probes_can_access}/{total_how_many_probes} probes)')
                whole_row_to_insert_a40 = a40_availiblity_for_each_country(testing_which_url=url_from_jenney_excel, which_country=each_coutry, availiblity=availiblity, wrote_to_db_time=current_Time)
                db.session.add(whole_row_to_insert_a40)
                db.session.commit()

    first_row_in_a05_controlling_for_hiding_or_showing_the_button_and_table = a05_controlling_for_hiding_or_showing_the_button_and_table.query.first()
    first_row_in_a05_controlling_for_hiding_or_showing_the_button_and_table.hiding_or_showing_the_button_and_table = "show_the_button_and_table"
    db.session.commit()

    return "2"


def get_current_time_formatted():
    # Get the current local date and time
    current_time = datetime.now()
    # Format the time as "YYYY-MM-DD HH:MM:SS"
    formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
    return formatted_time

#######################################################################
def check_if_the_probe_can_access_internet_or_not_by_country_filter(which_country, session_id=None):
    whole_db_a01_probe_list=a01_probe_list.query.filter(a01_probe_list.country==which_country).all()
    emit_log(f"[PROBE] Checking {len(whole_db_a01_probe_list)} probes in {which_country}...", session_id)
    for each_row in whole_db_a01_probe_list:
        each_row.is_the_probe_broken=None
        db.session.commit()
    
    for each_row in whole_db_a01_probe_list:
        
        probe_ip=each_row.probe_ip
        port=52770
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(probe_ip, port, "root", os.environ.get("SSH_PASSWORD", ""), timeout=5)
            command_for_testing_if_the_internet_is_normal_or_not = f"curl -sS --max-time 1 http://probe-check.example.com/GetMyIP"
            stdin, stdout, stderr = ssh.exec_command(command_for_testing_if_the_internet_is_normal_or_not, timeout=3)
            stdout_readlines=stdout.readlines()
            stderr_readlines=stderr.readlines()            
            str_stdout_readlines = ''.join(stdout_readlines)
            str_stderr_readlines = ''.join(stderr_readlines)
            if "failed" not in str_stderr_readlines or "not" not in str_stderr_readlines or "Resolving" not in str_stderr_readlines or "ResoConnectionlving" not in str_stderr_readlines:
                emit_log(f"[PROBE] ✓ {probe_ip} - OK (IP: {str_stdout_readlines.strip()})", session_id)
                each_row.is_the_probe_broken="can_access_internet"
                print(f"get_current_time_formatted()={get_current_time_formatted()}")
                each_row.wrote_to_db_time=get_current_time_formatted()
                db.session.commit()
                ssh.close()
        except Exception as error:
            emit_log(f"[PROBE] ✗ {probe_ip} - Error: {error}", session_id)
            each_row.is_the_probe_broken=f"no_internet: {str(error)}"
            db.session.commit()
            try:
                ssh.close()
            except:
                pass
            
            
            
            
# # ****************************************************************************************************************
@handling_data_received_from_frontend.route('/fixing_curl_cannot_get_the_contain_issue/<url>')
def fixing_curl_cannot_get_the_contain_issue(url):
# @handling_data_received_from_frontend.route('/fixing_curl_cannot_get_the_contain_issue')
# @handling_data_received_from_frontend.route('/fixing_curl_cannot_get_the_contain_issue/')
# def fixing_curl_cannot_get_the_contain_issue():
    # url="http://192.0.2.10:8787/jenny_excel_www.taptapapp.net__result_192.0.2.10_2025_08_21_11_02_39"
    session = requests.Session()

    # Add retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Set headers
    session.headers.update({
    'User-Agent': 'curl/7.68.0',  # Try curl's user agent
    'Accept': '*/*',  # Simpler accept header like curl
    })

    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        result_text = response.text
        if not result_text or result_text.strip() == "":
            print(f"[FETCH] ⚠️ Empty result from {url} (status={response.status_code}, length={len(response.content)})")
            return None
        return result_text
    except requests.exceptions.RequestException as e:
        print(f"[FETCH] ❌ Error fetching {url}: {e}")
        return None

#######################################################################
# FILTERED PAGE ROUTES - NEW FUNCTIONALITY WITH CORRECTED LOGIC
#######################################################################

@handling_data_received_from_frontend.route('/filtered/process_urls', methods=["GET", "POST"])
@handling_data_received_from_frontend.route('/filtered/process_urls/', methods=["GET", "POST"])
@cross_origin()
def filtered_process_urls():
    """Process URLs using filtered whitelist logic (SUCCESS conditions checked FIRST)"""
    session_id = None

    if request.method == "POST":
        jenney_url_send_frontend = request.data
        dict_jenney_url_send_frontend = json.loads(jenney_url_send_frontend.decode('utf-8'))
        session_id = dict_jenney_url_send_frontend.get("session_id")

    emit_log(f"\n{'='*70}", session_id)
    emit_log(f"[FILTERED] 🚀 STARTING FILTERED URL CHECK (Success conditions FIRST)", session_id)
    emit_log(f"{'='*70}", session_id)

    # Clear previous filtered results (use separate tables for original compatibility)
    db.session.query(a30_availiblity).filter(a30_availiblity.url_that_im_testing.like('FILTERED_%')).delete()
    db.session.query(a40_availiblity_for_each_country).filter(a40_availiblity_for_each_country.testing_which_url.like('FILTERED_%')).delete()
    db.session.commit()

    if request.method == "POST":
        str_dict_jenney_url_send_frontend = dict_jenney_url_send_frontend["input_from_jenny_excel"]
        list_testing_avalibility_in_which_country = dict_jenney_url_send_frontend["list_testing_avalibility_in_which_country"]

        list_dict_jenney_url_send_frontend = str_dict_jenney_url_send_frontend.split(",")
        url_count = len([u for u in list_dict_jenney_url_send_frontend if u.strip()])

        emit_log(f"[STEP 1/5] 📋 PREPARING URL COMBINATIONS FOR {url_count} DOMAINS", session_id)
        emit_log(f"[STEP 1/5] 🌍 Countries to test: {list_testing_avalibility_in_which_country}", session_id)

        emit_log(f"[STEP 2/5] 📡 CHECKING PROBE INTERNET ACCESS", session_id)
        # Check if probes can access internet for each country
        for each_country in list_testing_avalibility_in_which_country:
            emit_log(f"[STEP 2/5] 🔍 Checking probes in {each_country}...", session_id)
            check_if_the_probe_can_access_internet_or_not_by_country_filter(each_country, session_id)

        emit_log(f"[STEP 3/5] 🌐 RUNNING AVAILABILITY TESTS FROM MULTIPLE LOCATIONS", session_id)
        current_url_num = 0
        for each_url in list_dict_jenney_url_send_frontend:
            each_url = each_url.strip().replace("\n", "")
            if each_url != "":
                current_url_num += 1
                emit_log(f"[STEP 3/5] 🔄 Testing URL {current_url_num}/{url_count}: {each_url}", session_id)
                # Prefix URLs with FILTERED_ to separate from original functionality
                filtered_url = f"FILTERED_{each_url}"
                filtered_test_curl_to_probes(each_url, filtered_url, list_testing_avalibility_in_which_country, session_id)

        # Process results using filtered logic
        emit_log(f"[STEP 4/5] 🔬 ANALYZING RESULTS - APPLYING FILTERED LOGIC (SUCCESS FIRST)", session_id)
        filtered_check_curl_results(session_id)

        # Calculate availability with filtered logic
        emit_log(f"[STEP 5/5] 📊 COMPUTING FINAL AVAILABILITY PERCENTAGES", session_id)
        filtered_calculate_availability(session_id)

    emit_log(f"{'='*70}", session_id)
    emit_log(f"[FILTERED] ✅ FILTERED URL CHECK COMPLETED", session_id)
    emit_log(f"{'='*70}", session_id)

    return jsonify({"status": "success", "message": "Filtered URL processing completed"})

def filtered_test_curl_to_probes(original_url, filtered_url_key, countries_to_test, session_id=None):
    """Execute curl tests using filtered logic"""
    current_Time = get_gmt8_now().strftime("%Y-%m-%d-%H:%M:%S")

    whole_db_a01_probe_list = a01_probe_list.query.all()
    probe_count = 0

    for each_row in whole_db_a01_probe_list:
        which_GE_server = each_row.probe_ip
        this_country_is_from_db = each_row.country
        is_the_probe_broken = each_row.is_the_probe_broken

        if is_the_probe_broken == "its_broken":
            continue

        # Check if this country should be tested
        if this_country_is_from_db not in countries_to_test:
            continue

        isp = each_row.isp
        link_for_open_cancan_in_browser = each_row.link_for_open_cancan_in_browser
        port = 52770

        try:
            probe_count += 1
            emit_log(f"[CURL] 🔌 Probe {probe_count}: {which_GE_server} ({this_country_is_from_db}/{isp}) -> {original_url}", session_id)
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(which_GE_server, port, "root", os.environ.get("SSH_PASSWORD", ""))

            time_for_filename = current_Time.replace("-","_").replace(":","_")
            filename_for_paping_located_in_GE_apache = f"filtered_jenny_excel_{original_url}_{which_GE_server}_{time_for_filename}"
            filename_for_paping_located_in_GE_apache = filename_for_paping_located_in_GE_apache.replace("http://","").replace("https://","")

            curl_command = f"curl -s -L --insecure {original_url} -A'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36' >> /var/www/html/{filename_for_paping_located_in_GE_apache} 2>&1"
            stdin, stdout, stderr = ssh.exec_command(curl_command)
            curl_result_link = f"http://{which_GE_server}:8787/{filename_for_paping_located_in_GE_apache}"
            ssh.close()

            whole_row_to_insert_after_running_curl = a30_availiblity(
                probe_ip=which_GE_server,
                url_that_im_testing=filtered_url_key,
                country=this_country_is_from_db,
                isp=isp,
                curl_result_link=curl_result_link,
                wrote_to_db_time=current_Time,
                link_for_open_cancan_in_browser=link_for_open_cancan_in_browser,
                can_access_internet_or_not=is_the_probe_broken
            )
            db.session.add(whole_row_to_insert_after_running_curl)
            db.session.commit()

        except Exception as error:
            print(f"[FILTERED_SSH_ERROR] Failed to connect to probe {which_GE_server} for testing {original_url}: {error}")
            whole_row_to_insert_after_running_curl = a30_availiblity(
                probe_ip=which_GE_server,
                url_that_im_testing=filtered_url_key,
                country=this_country_is_from_db,
                isp=isp,
                can_access_or_not=f"SSH connection failed: {error}",
                curl_result_link="skip",
                wrote_to_db_time=current_Time,
                link_for_open_cancan_in_browser=link_for_open_cancan_in_browser,
                can_access_internet_or_not=is_the_probe_broken
            )
            db.session.add(whole_row_to_insert_after_running_curl)
            db.session.commit()

def filtered_check_curl_results(session_id=None):
    """Check curl results using FILTERED whitelist logic (success conditions first)"""
    # Wait for curl commands to complete on probes before fetching results
    import time
    emit_log(f"[STEP 4/5] ⏳ Waiting 5 seconds for curl commands to complete on probes...", session_id)
    time.sleep(5)

    whole_db_a30_availiblity = a30_availiblity.query.filter(a30_availiblity.url_that_im_testing.like('FILTERED_%')).all()
    total = len(whole_db_a30_availiblity)
    count = 0

    for each_row in whole_db_a30_availiblity:
        curl_result_link = each_row.curl_result_link
        if "skip" in curl_result_link:
            continue

        try:
            # Try fetching result with retry for slow probes
            result = None
            for attempt in range(3):
                result = fixing_curl_cannot_get_the_contain_issue(curl_result_link)
                if result and result.strip():
                    break
                if attempt < 2:
                    import time
                    time.sleep(2)  # Wait 2 seconds before retry

            # Use FILTERED whitelist logic (success conditions checked FIRST)
            status, message = evaluate_curl_result_filtered(result, each_row.country)
            each_row.can_access_or_not = message
            count += 1

            if status == 'failure':
                emit_log(f"[ANALYZE] ❌ {count}/{total} {each_row.probe_ip} ({each_row.country}): {message}", session_id)
            elif status == 'success':
                emit_log(f"[ANALYZE] ✅ {count}/{total} {each_row.probe_ip} ({each_row.country}): {message}", session_id)
            else:  # unknown
                emit_log(f"[ANALYZE] ❓ {count}/{total} {each_row.probe_ip} ({each_row.country}): {message}", session_id)

            db.session.commit()

        except Exception as error:
            count += 1
            emit_log(f"[ANALYZE] 💥 {count}/{total} Error: {each_row.probe_ip} - {error}", session_id)
            each_row.can_access_or_not = f"error analyzing result: {error}"
            db.session.commit()

def filtered_calculate_availability(session_id=None):
    """Calculate availability excluding unknown results from denominator"""

    # Get all countries that have filtered results
    filtered_results = a30_availiblity.query.filter(a30_availiblity.url_that_im_testing.like('FILTERED_%')).all()
    countries = set(row.country for row in filtered_results)

    for country in countries:
        # Get all URLs tested for this country
        country_results = a30_availiblity.query.filter(
            a30_availiblity.url_that_im_testing.like('FILTERED_%'),
            a30_availiblity.country == country
        ).all()

        # Group by URL
        urls = set(row.url_that_im_testing for row in country_results)

        for url in urls:
            url_country_results = a30_availiblity.query.filter(
                a30_availiblity.url_that_im_testing == url,
                a30_availiblity.country == country
            ).all()

            success_count = 0
            failure_count = 0
            unknown_count = 0

            for result in url_country_results:
                can_access_or_not = result.can_access_or_not or ""
                probe_ip = result.probe_ip

                # Skip SSH connection failures - probe was unreachable, not a website issue
                if "SSH connection failed" in can_access_or_not:
                    continue

                # Check if probe is working
                probe = a01_probe_list.query.filter_by(probe_ip=probe_ip).first()
                is_probe_working = probe and probe.is_the_probe_broken == "can_access_internet"

                if "can access" in can_access_or_not:
                    success_count += 1
                elif "cannot access" in can_access_or_not and is_probe_working:
                    failure_count += 1
                elif is_probe_working:  # No clear success/failure but probe is working
                    unknown_count += 1

            # Calculate availability excluding unknown from denominator
            total_known = success_count + failure_count
            availability = round(success_count / total_known * 100, 2) if total_known > 0 else 0

            current_Time = get_gmt8_now().strftime("%Y-%m-%d-%H:%M:%S")

            # Store results (could extend a40_availiblity_for_each_country or create new table)
            # For now, store with URL prefix to distinguish from original results
            existing_result = a40_availiblity_for_each_country.query.filter_by(
                testing_which_url=url,
                which_country=country
            ).first()

            if existing_result:
                existing_result.availiblity = availability
                existing_result.wrote_to_db_time = current_Time
            else:
                new_result = a40_availiblity_for_each_country(
                    testing_which_url=url,
                    which_country=country,
                    availiblity=availability,
                    wrote_to_db_time=current_Time
                )
                db.session.add(new_result)

            db.session.commit()

            # Clean URL for display (remove FILTERED_ prefix)
            clean_url = url.replace("FILTERED_", "")
            emit_log(f"[CALC] 📈 {clean_url} | {country} | {availability}% ({success_count}/{success_count+failure_count} probes)", session_id)

@handling_data_received_from_frontend.route('/api/filtered/results')
@handling_data_received_from_frontend.route('/api/filtered/results/')
@cross_origin()
def get_filtered_results():
    """Get filtered availability results with success/failure/unknown breakdown"""
    try:
        # Get availability results for filtered URLs
        results = a40_availiblity_for_each_country.query.filter(
            a40_availiblity_for_each_country.testing_which_url.like('FILTERED_%')
        ).all()

        detailed_results = []
        for result in results:
            # Get detailed breakdown for this URL and country
            url_results = a30_availiblity.query.filter_by(
                url_that_im_testing=result.testing_which_url,
                country=result.which_country
            ).all()

            success_count = 0
            failure_count = 0
            unknown_count = 0
            unknown_probes = []

            for url_result in url_results:
                can_access = url_result.can_access_or_not or ""
                probe_ip = url_result.probe_ip

                # Skip SSH connection failures - probe was unreachable
                if "SSH connection failed" in can_access:
                    continue

                # Check if probe is working
                probe = a01_probe_list.query.filter_by(probe_ip=probe_ip).first()
                is_probe_working = probe and probe.is_the_probe_broken == "can_access_internet"

                if "can access" in can_access:
                    success_count += 1
                elif "cannot access" in can_access and is_probe_working:
                    failure_count += 1
                elif is_probe_working:
                    unknown_count += 1
                    unknown_probes.append({
                        "probe_ip": probe_ip,
                        "curl_result_link": url_result.curl_result_link,
                        "isp": url_result.isp,
                        "result": can_access
                    })

            detailed_results.append({
                "url": result.testing_which_url.replace("FILTERED_", ""),  # Remove prefix for display
                "country": result.which_country,
                "availability": result.availiblity,
                "success_count": success_count,
                "failure_count": failure_count,
                "unknown_count": unknown_count,
                "unknown_probes": unknown_probes,
                "total_tested": success_count + failure_count + unknown_count,
                "updated_at": format_datetime_gmt8(result.wrote_to_db_time)
            })

        return jsonify(detailed_results)

    except Exception as e:
        print(f"[FILTERED_API] Error getting filtered results: {e}")
        return jsonify({"error": str(e)}), 500


