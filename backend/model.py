from sqlalchemy.dialects.postgresql import JSON
import datetime
# from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql.sqltypes import TIMESTAMP
import pytz
db = SQLAlchemy()

# GMT+8 timezone for consistent timestamp handling
GMT_PLUS_8 = pytz.timezone('Asia/Shanghai')

def get_gmt8_now():
    """Get current timestamp in GMT+8 timezone"""
    return datetime.datetime.now(GMT_PLUS_8)

def format_datetime_gmt8(dt):
    """Format datetime object to GMT+8 timezone string"""
    if dt is None:
        return None
    
    # If datetime is naive (no timezone info), assume it's already in GMT+8
    if dt.tzinfo is None:
        # Treat as GMT+8
        dt_gmt8 = GMT_PLUS_8.localize(dt)
    else:
        # Convert to GMT+8
        dt_gmt8 = dt.astimezone(GMT_PLUS_8)
    
    return dt_gmt8.strftime('%Y-%m-%d %H:%M:%S')



        
class a01_probe_list(db.Model):
    __bind_key__="probe_list_db"
    __tablename__ = "a01_probe_list"
    id = db.Column(db.Integer, primary_key=True)
    probe_ip= db.Column(db.TEXT)
    url= db.Column(db.TEXT)
    country= db.Column(db.TEXT)
    isp= db.Column(db.TEXT)
    hostname= db.Column(db.TEXT)
    link_for_open_cancan_in_browser= db.Column(db.TEXT)
    wrote_to_db_time= db.Column(db.DateTime)
    is_the_probe_broken= db.Column(db.TEXT)

    @property
    def serialize(self):
        return {
            "probe_ip":self.probe_ip,
            "url":self.url,
            "country":self.country,
            "isp":self.isp,
            "hostname":self.hostname,
            "link_for_open_cancan_in_browser":self.link_for_open_cancan_in_browser,
            "is_the_probe_broken":self.link_for_open_cancan_in_browser,
            "wrote_to_db_time":format_datetime_gmt8(self.wrote_to_db_time),
        }


class b11_huck_ge_probes(db.Model):
    __bind_key__ = "b11_huck_ge_database"
    __tablename__ = "b11_huck_ge_probes"
    id = db.Column(db.Integer, primary_key=True)
    probe_ip = db.Column(db.TEXT)
    url = db.Column(db.TEXT)
    country = db.Column(db.TEXT)
    isp = db.Column(db.TEXT)
    hostname = db.Column(db.TEXT)
    link_for_open_cancan_in_browser = db.Column(db.TEXT)
    wrote_to_db_time = db.Column(db.DateTime)
    is_the_probe_broken = db.Column(db.TEXT)

    @property
    def serialize(self):
        return {
            "probe_ip": self.probe_ip,
            "url": self.url,
            "country": self.country,
            "isp": self.isp,
            "hostname": self.hostname,
            "link_for_open_cancan_in_browser": self.link_for_open_cancan_in_browser,
            "is_the_probe_broken": self.is_the_probe_broken,
            "wrote_to_db_time": format_datetime_gmt8(self.wrote_to_db_time),
        }


class a05_controlling_for_hiding_or_showing_the_button_and_table(db.Model):
    __tablename__ = "a05_controlling_for_hiding_or_showing_the_button_and_table"
    id = db.Column(db.Integer, primary_key=True)
    hiding_or_showing_the_button_and_table= db.Column(db.TEXT)

    @property
    def serialize(self):
        return {
            "hiding_or_showing_the_button_and_table":self.hiding_or_showing_the_button_and_table,
        }            

#********************************************

class a20_url_from_jenney_excel(db.Model):
    __tablename__ = "a20_url_from_jenney_excel"
    id = db.Column(db.Integer, primary_key=True)
    url_from_jenney_excel= db.Column(db.TEXT)
    has_the_url_been_checked= db.Column(db.TEXT)
    start_query_time= db.Column(db.DateTime)
    end_query_time= db.Column(db.DateTime)
    @property
    def serialize(self):
        return {
            "url_from_jenney_excel":self.url_from_jenney_excel,
            "has_the_url_been_checked":self.has_the_url_been_checked,
            "start_query_time":format_datetime_gmt8(self.start_query_time),
            "end_query_time":format_datetime_gmt8(self.end_query_time),
        }   

#********************************************

class a30_availiblity(db.Model):
    __tablename__ = "a30_availiblity"
    id = db.Column(db.Integer, primary_key=True)
    probe_ip= db.Column(db.TEXT)
    url_that_im_testing= db.Column(db.TEXT)
    country= db.Column(db.TEXT)
    isp= db.Column(db.TEXT)
    can_access_or_not= db.Column(db.TEXT)
    curl_result_link= db.Column(db.TEXT)
    link_for_open_cancan_in_browser= db.Column(db.TEXT)
    wrote_to_db_time= db.Column(db.DateTime)
    can_access_internet_or_not= db.Column(db.TEXT)

    @property
    def serialize(self):
        # Extract the specific condition that was matched using dynamic whitelist
        matched_condition = ""
        if self.can_access_or_not:
            try:
                # Import the dynamic condition matching function
                from blueprint_paping.whitelist_management import get_matched_condition_pattern
                matched_condition = get_matched_condition_pattern(self.can_access_or_not, self.country)
            except Exception as e:
                print(f"[MODEL] ❌ Error getting matched condition: {e}")
                matched_condition = ""

        return {
            "probe_ip":self.probe_ip,
            "url_that_im_testing":self.url_that_im_testing,
            "country":self.country,
            "isp":self.isp,
            "can_access_or_not":self.can_access_or_not,
            "matched_condition":matched_condition,
            "curl_result_link":self.curl_result_link,
            "link_for_open_cancan_in_browser":self.link_for_open_cancan_in_browser,
            "wrote_to_db_time":format_datetime_gmt8(self.wrote_to_db_time),
            "can_access_internet_or_not":f"{self.can_access_internet_or_not}",
        }





class a40_availiblity_for_each_country(db.Model):
    __tablename__ = "a40_availiblity_for_each_country"
    id = db.Column(db.Integer, primary_key=True)
    testing_which_url= db.Column(db.TEXT)
    which_country= db.Column(db.TEXT)
    availiblity= db.Column(db.TEXT)
    wrote_to_db_time= db.Column(db.DateTime)

    @property
    def serialize(self):
        return {
            "testing_which_url":self.testing_which_url,
            "which_country":self.which_country,
            "availiblity":self.availiblity,
            "wrote_to_db_time":format_datetime_gmt8(self.wrote_to_db_time),
        }   




class a60_checking_in_which_country(db.Model):
    __tablename__ = "a60_checking_in_which_country"
    id = db.Column(db.Integer, primary_key=True)
    which_country= db.Column(db.TEXT)

   

class a70_check_the_availibility_in_which_location(db.Model):
    __tablename__ = "a70_check_the_availibility_in_which_location"
    id = db.Column(db.Integer, primary_key=True)
    which_location= db.Column(db.TEXT)
    probe_ip_new= db.Column(db.TEXT)


class a80_scheduled_domains(db.Model):
    __tablename__ = "a80_scheduled_domains"
    id = db.Column(db.Integer, primary_key=True)
    domain_name = db.Column(db.TEXT)
    interval_minutes = db.Column(db.Integer)
    country = db.Column(db.TEXT)
    domain_prefix = db.Column(db.TEXT)  # root, www, aff
    starting_time = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=get_gmt8_now)
    last_checked_at = db.Column(db.DateTime)

    @property
    def serialize(self):
        return {
            "id": self.id,
            "domain_name": self.domain_name,
            "interval_minutes": self.interval_minutes,
            "country": self.country,
            "domain_prefix": self.domain_prefix,
            "starting_time": format_datetime_gmt8(self.starting_time),
            "is_active": self.is_active,
            "created_at": format_datetime_gmt8(self.created_at),
            "last_checked_at": format_datetime_gmt8(self.last_checked_at),
        }


class a90_scheduled_results(db.Model):
    __tablename__ = "a90_scheduled_results"
    id = db.Column(db.Integer, primary_key=True)
    scheduled_domain_id = db.Column(db.Integer, db.ForeignKey('a80_scheduled_domains.id'))
    domain_name = db.Column(db.TEXT)
    country = db.Column(db.TEXT)
    availability_percentage = db.Column(db.Float)
    total_probes = db.Column(db.Integer)
    successful_probes = db.Column(db.Integer)
    checked_at = db.Column(db.DateTime, default=get_gmt8_now)

    @property
    def serialize(self):
        return {
            "id": self.id,
            "scheduled_domain_id": self.scheduled_domain_id,
            "domain_name": self.domain_name,
            "country": self.country,
            "availability_percentage": self.availability_percentage,
            "total_probes": self.total_probes,
            "successful_probes": self.successful_probes,
            "checked_at": format_datetime_gmt8(self.checked_at),
        }


class a95_paping_scheduled_destinations(db.Model):
    __tablename__ = "a95_paping_scheduled_destinations"
    id = db.Column(db.Integer, primary_key=True)
    destination = db.Column(db.TEXT)  # IP address or hostname
    interval_minutes = db.Column(db.Integer)
    country = db.Column(db.TEXT)
    starting_time = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=get_gmt8_now)
    last_checked_at = db.Column(db.DateTime)
    packet_loss_threshold = db.Column(db.Float, default=10.0)  # Default 10% packet loss threshold
    latency_threshold = db.Column(db.Float, default=150.0)  # Default 150ms latency threshold

    @property
    def serialize(self):
        return {
            "id": self.id,
            "destination": self.destination,
            "interval_minutes": self.interval_minutes,
            "country": self.country,
            "starting_time": format_datetime_gmt8(self.starting_time),
            "is_active": self.is_active,
            "created_at": format_datetime_gmt8(self.created_at),
            "last_checked_at": format_datetime_gmt8(self.last_checked_at),
            "packet_loss_threshold": self.packet_loss_threshold,
            "latency_threshold": self.latency_threshold,
        }


class a96_paping_results(db.Model):
    __tablename__ = "a96_paping_results"
    id = db.Column(db.Integer, primary_key=True)
    paging_destination_id = db.Column(db.Integer, db.ForeignKey('a95_paping_scheduled_destinations.id'))
    destination = db.Column(db.TEXT)
    probe_ip = db.Column(db.TEXT)
    country = db.Column(db.TEXT)
    packet_loss_percentage = db.Column(db.Float)
    avg_latency_ms = db.Column(db.Float)
    min_latency_ms = db.Column(db.Float)
    max_latency_ms = db.Column(db.Float)
    alert_triggered = db.Column(db.Boolean, default=False)  # True if loss > 10% OR latency > 150ms
    checked_at = db.Column(db.DateTime, default=get_gmt8_now)

    @property
    def serialize(self):
        return {
            "id": self.id,
            "paging_destination_id": self.paging_destination_id,
            "destination": self.destination,
            "probe_ip": self.probe_ip,
            "country": self.country,
            "packet_loss_percentage": self.packet_loss_percentage,
            "avg_latency_ms": self.avg_latency_ms,
            "min_latency_ms": self.min_latency_ms,
            "max_latency_ms": self.max_latency_ms,
            "alert_triggered": self.alert_triggered,
            "checked_at": format_datetime_gmt8(self.checked_at),
        }


# Whitelist Management Models
class a99_processing_logs(db.Model):
    __tablename__ = 'a99_processing_logs'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(50), index=True)
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=get_gmt8_now)

    @property
    def serialize(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "message": self.message,
            "created_at": format_datetime_gmt8(self.created_at),
        }


class a97_whitelist_conditions(db.Model):
    __tablename__ = 'a97_whitelist_conditions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    condition_type = db.Column(db.String(20))  # 'success' or 'failure'
    condition_pattern = db.Column(db.String(500))  # The text pattern to match
    condition_name = db.Column(db.String(200))  # User-friendly name
    description = db.Column(db.String(500))  # Description of what this condition does
    is_enabled = db.Column(db.Boolean, default=True)  # Whether this condition is active
    is_built_in = db.Column(db.Boolean, default=False)  # Built-in conditions can't be deleted
    country_specific = db.Column(db.String(50), nullable=True)  # For conditions that only apply to specific countries
    priority = db.Column(db.Integer, default=100)  # Matching priority (lower = higher priority, checked first)
    created_at = db.Column(db.DateTime, default=get_gmt8_now)
    updated_at = db.Column(db.DateTime, default=get_gmt8_now, onupdate=get_gmt8_now)

    @property
    def serialize(self):
        return {
            "id": self.id,
            "condition_type": self.condition_type,
            "condition_pattern": self.condition_pattern,
            "condition_name": self.condition_name,
            "description": self.description,
            "is_enabled": self.is_enabled,
            "is_built_in": self.is_built_in,
            "country_specific": self.country_specific,
            "priority": self.priority if self.priority is not None else 100,
            "created_at": format_datetime_gmt8(self.created_at),
            "updated_at": format_datetime_gmt8(self.updated_at),
        }

