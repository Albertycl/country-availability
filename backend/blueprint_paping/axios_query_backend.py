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
from model import db, a01_probe_list, a20_url_from_jenney_excel, a30_availiblity, a40_availiblity_for_each_country, a05_controlling_for_hiding_or_showing_the_button_and_table
# import logging

# # Set the logging level to WARNING to suppress request logs
# logging.basicConfig(level=logging.ERROR)


axios_query_backend = Blueprint("axios_query_backend", __name__)
CORS(axios_query_backend)

# Only fetch curl result files from known probes (http://<probe_ip>:8787/<file>).
# Any other URL is refused, so these routes cannot be used to reach other hosts.
_PROBE_RESULT_URL = re.compile(r"http://(\d{1,3}(?:\.\d{1,3}){3}):8787/[^\s#\\]+")


def _is_probe_result_url(url):
    match = _PROBE_RESULT_URL.fullmatch(url or "")
    if not match:
        return False
    return a01_probe_list.query.filter_by(probe_ip=match.group(1)).first() is not None


##############################################################################################################################################
@axios_query_backend.route('/a05_pass_root_wwww_m_aff_and_update_the_urls_to_test')
@axios_query_backend.route('/a05_pass_root_wwww_m_aff_and_update_the_urls_to_test/<something>')
def a05_pass_root_wwww_m_aff_and_update_the_urls_to_test(something):
    print(f'something={something}')
    return "jsonify(list_whole_db_a40_availiblity_for_each_country)"


##############################################################################################################################################
@axios_query_backend.route('/d01_show_availibility_table')
@axios_query_backend.route('/d01_show_availibility_table/')
@cross_origin()
def d01_show_availibility_table():
    list_whole_db_a40_availiblity_for_each_country = a40_availiblity_for_each_country.query.order_by(
        a40_availiblity_for_each_country.testing_which_url.asc()).all()
    # list_whole_db_a40_availiblity_for_each_country = a40_availiblity_for_each_country.query.filter(a40_availiblity_for_each_country.testing_which_url=="https://www.demobrand.com").order_by(a40_availiblity_for_each_country.testing_which_url.asc()).all()
    list_whole_db_a40_availiblity_for_each_country = [
        data.serialize for data in list_whole_db_a40_availiblity_for_each_country]
    return jsonify(list_whole_db_a40_availiblity_for_each_country)


##############################################################################################################################################
@axios_query_backend.route('/d02_show_raw_data')
@axios_query_backend.route('/d02_show_raw_data/')
@axios_query_backend.route('/d02_show_raw_data/<check_which_country>/<check_which_url>')
def d02_show_raw_data(check_which_country, check_which_url):
    check_which_url = f"https://{check_which_url}"
    list_whole_db_a30_availiblity = a30_availiblity.query.filter(
        a30_availiblity.country == check_which_country, a30_availiblity.url_that_im_testing == check_which_url).order_by(a30_availiblity.can_access_or_not.desc()).all()
    list_whole_db_a30_availiblity = [
        data.serialize for data in list_whole_db_a30_availiblity]
    return jsonify(list_whole_db_a30_availiblity)


##############################################################################################################################################
@axios_query_backend.route('/d02_show_raw_data_filtered')
@axios_query_backend.route('/d02_show_raw_data_filtered/')
@axios_query_backend.route('/d02_show_raw_data_filtered/<check_which_country>/<path:check_which_url>')
@cross_origin()
def d02_show_raw_data_filtered(check_which_country, check_which_url):
    # For filtered data, URLs are stored in database as "FILTERED_https://example.com"
    # The frontend passes "FILTERED_www.example.com", so we need to construct the full URL
    # Remove FILTERED_ prefix if present, then add protocol and FILTERED_ back
    original_url_param = check_which_url
    if check_which_url.startswith("FILTERED_"):
        url_without_prefix = check_which_url.replace("FILTERED_", "")
        check_which_url = f"FILTERED_https://{url_without_prefix}"
    else:
        check_which_url = f"https://{check_which_url}"

    print(f"[DEBUG_RAW_DATA] Country: {check_which_country}, Query URL: {check_which_url.replace('FILTERED_', '')}")

    list_whole_db_a30_availiblity = a30_availiblity.query.filter(
        a30_availiblity.country == check_which_country, a30_availiblity.url_that_im_testing == check_which_url).order_by(a30_availiblity.can_access_or_not.desc()).all()

    print(f"[DEBUG_RAW_DATA] Found {len(list_whole_db_a30_availiblity)} records")

    # Debug: Show what URLs exist in DB for this country
    if len(list_whole_db_a30_availiblity) == 0:
        all_urls_in_db = a30_availiblity.query.filter(a30_availiblity.country == check_which_country).with_entities(a30_availiblity.url_that_im_testing).distinct().all()
        print(f"[DEBUG_RAW_DATA] Available URLs in DB for {check_which_country}: {[u[0].replace('FILTERED_', '') for u in all_urls_in_db]}")

    list_whole_db_a30_availiblity = [
        data.serialize for data in list_whole_db_a30_availiblity]
    return jsonify(list_whole_db_a30_availiblity)


##############################################################################################################################################
@axios_query_backend.route('/proxy_curl_result')
@axios_query_backend.route('/proxy_curl_result/')
@cross_origin()
def proxy_curl_result():
    """Proxy endpoint to fetch curl results from probe servers (avoids CORS issues)"""
    curl_url = request.args.get('url')
    if not curl_url:
        return jsonify({"error": "Missing url parameter"}), 400
    if not _is_probe_result_url(curl_url):
        return jsonify({"error": "Only probe result URLs are allowed"}), 400

    try:
        import requests
        response = requests.get(curl_url, timeout=10, allow_redirects=False)
        if response.status_code == 200:
            return response.text, 200, {'Content-Type': 'text/plain; charset=utf-8'}
        else:
            return f"Error: HTTP {response.status_code}", response.status_code
    except requests.exceptions.RequestException as e:
        return f"Error fetching curl result: {str(e)}", 500


##############################################################################################################################################
@axios_query_backend.route('/a10_lock_the_button_or_table')
@axios_query_backend.route('/a10_lock_the_button_or_table/')
@cross_origin()
def a10_lock_the_button_or_table():
    controlling_for_hiding_or_showing_the_button_and_table = a05_controlling_for_hiding_or_showing_the_button_and_table.query.first(
    ).hiding_or_showing_the_button_and_table
    return controlling_for_hiding_or_showing_the_button_and_table


##############################################################################################################################################
@axios_query_backend.route('/a20_which_url_is_being_handled')
@axios_query_backend.route('/a20_which_url_is_being_handled/')
@cross_origin()
def a20_which_url_is_being_handled():
    list_whole_db_a20_url_from_jenney_excel = a20_url_from_jenney_excel.query.all()
    list_whole_db_a20_url_from_jenney_excel = [
        data.serialize for data in list_whole_db_a20_url_from_jenney_excel]
    return jsonify(list_whole_db_a20_url_from_jenney_excel)


#######################################################################
@axios_query_backend.route('/open_link')
@axios_query_backend.route('/open_link/')
@axios_query_backend.route('/open_link/<url_to_open>')
@axios_query_backend.route('/open_link/<url_to_open>/')
def open_link(url_to_open="192.0.2.10:8787_jenny_excel_www.baidu.com__result_192.0.2.10_2022_12_05_04_24_40"):
    # url="http://192.0.2.10:8787/jenny_excel_www.baidu.com__result_192.0.2.10_2022_12_05_04_24_40"
    url_after_replace = url_to_open.replace("8787_", "8787/")
    url_to_open_finally = f"http://{url_after_replace}"
    if not _is_probe_result_url(url_to_open_finally):
        return jsonify({"error": "Only probe result URLs are allowed"}), 400
    resopnse_from_each_ge_server = requests.get(url_to_open_finally, timeout=10, allow_redirects=False).text
    print(f"resopnse_from_each_ge_server={resopnse_from_each_ge_server}")
    resopnse_from_each_ge_server = resopnse_from_each_ge_server.replace("0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0", "").replace("% Total", "").replace("% Received", "").replace("% Xferd", "").replace("Average Speed   Time    Time     Time  Current", "").replace("Dload  Upload   Total   Spent    Left  Speed", "").replace("0  ", "").replace("277", "").replace("\n\n", "\n").replace("0 --:--:--  0:00:01 --:--:--     0", "").replace("0 --:--:--  0:00:02 --:--:--     0", "").replace("146", "").replace("0 21326", "").replace("0 21233", "").replace("249", "").replace("curl: (28)", "").replace("0 --:--:--  0:00:03 --:--:--", "").replace("curl: (6)", "").replace("curl: (7)", "").replace(
        "0 --:--:--  0:00:04 --:--:--     0", "").replace("0 --:--:--  0:00:04 --:--:--     0 266", "").replace("0 --:--:--  0:00:05 --:--:--     0", "").replace("0 --:--:--  0:00:06 --:--:--     0", "").replace("0 --:--:--  0:00:07 --:--:--     0", "").replace("0 --:--:--  0:00:08 --:--:--", "").replace("0 --:--:--  0:00:09 --:--:--     0", "").replace("0 --:--:--  0:00:06 --:--:--     0", "").replace("0 --:--:--  0:00:10 --:--:--     0", "").replace("0 --:--:--  0:00:06 --:--:--     0", "").replace("  ", " ").replace("   ", " ").replace("  ", " ").replace("  ", " ").replace("  ", " ").replace("  ", " ").replace("  ", " ").replace("curl: (35)", "").replace("0 266", "").replace("--:--:--", "").replace("0:00:", "")
    return resopnse_from_each_ge_server


##############################################################################################################################################
@axios_query_backend.route('/b10_which_url_has_been_queried_from_last_request')
@axios_query_backend.route('/b10_which_url_has_been_queried_from_last_request/')
def b10_which_url_has_been_queried_from_last_request():
    list_whole_db_a20_url_from_jenney_excel = a20_url_from_jenney_excel.query.all()
    # https://www.demobrand.com,\nhttps://www.example-games.net,
    all_the_url_which_was_queried_from_last_request = ""
    for each_row in list_whole_db_a20_url_from_jenney_excel:
        url_from_jenney_excel = each_row.url_from_jenney_excel
        # print(f"url_from_jenney_excel={url_from_jenney_excel}")
        url_from_jenney_excel = url_from_jenney_excel.replace("www.", "").replace(
            "aff.", "").replace("m.", "").replace("https://", "")
        if url_from_jenney_excel not in all_the_url_which_was_queried_from_last_request:
            all_the_url_which_was_queried_from_last_request = all_the_url_which_was_queried_from_last_request + \
                url_from_jenney_excel+","
            # print(f"all_the_url_which_was_queried_from_last_request={all_the_url_which_was_queried_from_last_request}")

    return all_the_url_which_was_queried_from_last_request


#######################################################################
@axios_query_backend.route('/check_alive')
@axios_query_backend.route('/check_alive/')
def check_alive():

    return "im alive"


#######################################################################
@axios_query_backend.route('/unlock_itself')
@axios_query_backend.route('/unlock_itself/')
def unlock_itself():
    hiding_or_showing_the_button_and_table = a05_controlling_for_hiding_or_showing_the_button_and_table.query.first().hiding_or_showing_the_button_and_table
    this = a05_controlling_for_hiding_or_showing_the_button_and_table.query.first()
    this.hiding_or_showing_the_button_and_table = "show_the_button_and_table"
    db.session.commit()
    return "1"
