-- Demo data for Country Availability: made-up probes (documentation-range IPs) and neutral whitelist rules.
-- Probes are simulated by backend/simulation.py, so nothing here needs a real server.
-- Re-runnable: clears the demo rows and refreshes timestamps (GMT+8 wall time).
-- Loaded automatically by init_db.py when SEED_DEMO=1 and the probe table is empty.
SET @now = DATE_ADD(UTC_TIMESTAMP(), INTERVAL 8 HOUR);

DELETE FROM a99_processing_logs;
DELETE FROM a97_whitelist_conditions;
DELETE FROM a90_scheduled_results;
DELETE FROM a80_scheduled_domains;
DELETE FROM a30_availiblity;
DELETE FROM a40_availiblity_for_each_country;
DELETE FROM a20_url_from_jenney_excel;
DELETE FROM a05_controlling_for_hiding_or_showing_the_button_and_table;
DELETE FROM a01_probe_list;

INSERT INTO a05_controlling_for_hiding_or_showing_the_button_and_table (hiding_or_showing_the_button_and_table) VALUES ('show');

INSERT INTO a01_probe_list (probe_ip, url, country, isp, hostname, link_for_open_cancan_in_browser, wrote_to_db_time, is_the_probe_broken) VALUES
 ('203.0.113.11', 'http://203.0.113.11:8787', 'China', 'CT', 'CH_Guangzhou', 'http://203.0.113.11:8787/', @now, 'can_access_internet'),
 ('203.0.113.12', 'http://203.0.113.12:8787', 'China', 'CT', 'CH_Shanghai', 'http://203.0.113.12:8787/', @now, 'can_access_internet'),
 ('203.0.113.13', 'http://203.0.113.13:8787', 'China', 'CT', 'CH_Beijing', 'http://203.0.113.13:8787/', @now, 'can_access_internet'),
 ('203.0.113.14', 'http://203.0.113.14:8787', 'China', 'CU', 'CH_Shenzhen', 'http://203.0.113.14:8787/', @now, 'can_access_internet'),
 ('203.0.113.15', 'http://203.0.113.15:8787', 'China', 'CU', 'CH_Hangzhou', 'http://203.0.113.15:8787/', @now, 'can_access_internet'),
 ('203.0.113.16', 'http://203.0.113.16:8787', 'China', 'CU', 'CH_Tianjin', 'http://203.0.113.16:8787/', @now, 'can_access_internet'),
 ('203.0.113.17', 'http://203.0.113.17:8787', 'China', 'CM', 'CH_Chengdu', 'http://203.0.113.17:8787/', @now, 'can_access_internet'),
 ('203.0.113.18', 'http://203.0.113.18:8787', 'China', 'CM', 'CH_Wuhan', 'http://203.0.113.18:8787/', @now, 'can_access_internet'),
 ('203.0.113.19', 'http://203.0.113.19:8787', 'China', 'CM', 'CH_Nanjing', 'http://203.0.113.19:8787/', @now, 'can_access_internet'),
 ('198.51.100.11', 'http://198.51.100.11:8787', 'Thailand', 'AIS', 'TH_Bangkok', 'http://198.51.100.11:8787/', @now, 'can_access_internet'),
 ('198.51.100.12', 'http://198.51.100.12:8787', 'Thailand', 'TrueMove', 'TH_Chiang Mai', 'http://198.51.100.12:8787/', @now, 'can_access_internet'),
 ('198.51.100.13', 'http://198.51.100.13:8787', 'Thailand', '3BB', 'TH_Phuket', 'http://198.51.100.13:8787/', @now, 'can_access_internet'),
 ('198.51.100.21', 'http://198.51.100.21:8787', 'Vietnam', 'VNPT', 'VI_Hanoi', 'http://198.51.100.21:8787/', @now, 'can_access_internet'),
 ('198.51.100.22', 'http://198.51.100.22:8787', 'Vietnam', 'Viettel', 'VI_Ho Chi Minh', 'http://198.51.100.22:8787/', @now, 'can_access_internet'),
 ('198.51.100.23', 'http://198.51.100.23:8787', 'Vietnam', 'FPT', 'VI_Da Nang', 'http://198.51.100.23:8787/', @now, 'can_access_internet'),
 ('192.0.2.31', 'http://192.0.2.31:8787', 'Indonesia', 'Telkomsel', 'IN_Jakarta', 'http://192.0.2.31:8787/', @now, 'can_access_internet'),
 ('192.0.2.32', 'http://192.0.2.32:8787', 'Indonesia', 'Indosat', 'IN_Surabaya', 'http://192.0.2.32:8787/', @now, 'can_access_internet'),
 ('192.0.2.41', 'http://192.0.2.41:8787', 'Malaysia', 'Maxis', 'MA_Kuala Lumpur', 'http://192.0.2.41:8787/', @now, 'can_access_internet'),
 ('192.0.2.42', 'http://192.0.2.42:8787', 'Malaysia', 'Celcom', 'MA_Penang', 'http://192.0.2.42:8787/', @now, 'can_access_internet'),
 ('192.0.2.51', 'http://192.0.2.51:8787', 'Cambodia', 'Cellcard', 'CA_Phnom Penh', 'http://192.0.2.51:8787/', @now, 'can_access_internet'),
 ('192.0.2.52', 'http://192.0.2.52:8787', 'Cambodia', 'Smart', 'CA_Siem Reap', 'http://192.0.2.52:8787/', @now, 'can_access_internet'),
 ('192.0.2.61', 'http://192.0.2.61:8787', 'Brazil', 'Vivo', 'BR_Sao Paulo', 'http://192.0.2.61:8787/', @now, 'can_access_internet'),
 ('192.0.2.62', 'http://192.0.2.62:8787', 'Brazil', 'Claro', 'BR_Rio', 'http://192.0.2.62:8787/', @now, 'can_access_internet'),
 ('192.0.2.71', 'http://192.0.2.71:8787', 'KR', 'KT', 'KR_Seoul', 'http://192.0.2.71:8787/', @now, 'can_access_internet'),
 ('192.0.2.72', 'http://192.0.2.72:8787', 'KR', 'SKB', 'KR_Busan', 'http://192.0.2.72:8787/', @now, 'can_access_internet');

-- Whitelist rules: how a curl result is judged. Failure rules are curl error texts; success rules are page markers.
INSERT INTO a97_whitelist_conditions (condition_type, condition_pattern, condition_name, description, is_enabled, is_built_in, country_specific, priority, created_at, updated_at) VALUES
 ('failure', 'Could not resolve',    'DNS Resolution Failed',  'Domain cannot be resolved to an IP address', 1, 1, NULL, 100, @now, @now),
 ('failure', 'timeout',              'Connection Timeout',     'Server not responding within the time limit', 1, 1, NULL, 100, @now, @now),
 ('failure', 'Failed to connect to', 'Connection Failed',      'Server refused the connection or is unreachable', 1, 1, NULL, 100, @now, @now),
 ('failure', 'SSL_ERROR_SYSCALL',    'SSL/TLS Error',          'TLS handshake broke, often a block in the middle', 1, 1, NULL, 100, @now, @now),
 ('success', 'demo-ok',              'Demo page marker',       'The page carries the expected marker, so the site is reachable', 1, 1, NULL, 100, @now, @now);

-- Scheduled monitoring: inactive entries with a little history, so the page is not empty.
INSERT INTO a80_scheduled_domains (id, domain_name, interval_minutes, country, domain_prefix, starting_time, is_active, created_at, last_checked_at) VALUES
 (1, 'demo-site-one.example', 60, 'China', 'www', @now, 0, @now, @now),
 (2, 'blocked-demo.example', 60, 'China', 'www', @now, 0, @now, @now);

INSERT INTO a90_scheduled_results (scheduled_domain_id, domain_name, country, availability_percentage, total_probes, successful_probes, checked_at)
SELECT 1, 'demo-site-one.example', 'China', 100, 9, 9, DATE_SUB(@now, INTERVAL n HOUR) FROM (SELECT 0 n UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5) h
UNION ALL
SELECT 2, 'blocked-demo.example', 'China', IF(n=0,0,IF(n<3,33.33,100)), 9, IF(n=0,0,IF(n<3,3,9)), DATE_SUB(@now, INTERVAL n HOUR) FROM (SELECT 0 n UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5) h;
