"""Simulated probes for the demo.

The real system SSHes into probe servers abroad, runs curl there, and reads the result
file back over HTTP (port 8787). Neither is reachable from a laptop, so this module swaps
those two transport calls for in-process fakes. Everything above them (whitelist rules,
availability maths, scheduler, UI) runs unchanged.

Host name keywords decide what the simulated probes see:
  down      -> unreachable from every country
  blocked   -> unreachable from China only
  partial   -> about half of the probes in every country fail
  unknown   -> Malaysia and Thailand get an unrecognised page (neither pass nor fail)
  (other)   -> picked from a hash of the host name: mostly healthy, sometimes blocked
               in one country, sometimes partial
"""
import hashlib
import os
import re
import socket
import time

import paramiko
import requests
from requests.adapters import HTTPAdapter

COUNTRIES = ["Brazil", "Cambodia", "China", "Indonesia", "KR", "Malaysia", "Thailand", "Vietnam"]
OFFLINE_PROBES = set(filter(None, os.environ.get("SIM_OFFLINE_PROBES", "198.51.100.23").split(",")))
SSH_DELAY = float(os.environ.get("SIM_SSH_DELAY", "0.15"))

_results = {}


def _h(*parts):
    return int(hashlib.md5("|".join(str(p) for p in parts).encode()).hexdigest(), 16)


def _host(url):
    return re.sub(r"^https?://", "", url).split("/")[0].lower()


def _probe_info(probe_ip):
    from model import a01_probe_list
    row = a01_probe_list.query.filter_by(probe_ip=probe_ip).first()
    if row:
        return row.country, row.hostname or probe_ip
    return None, probe_ip


def decide(url, country, probe_ip):
    """Return 'ok', 'dns', 'timeout', 'refused', 'ssl' or 'unknown' for one probe."""
    host = _host(url)
    fail_kind = ["dns", "timeout", "refused", "ssl"][_h("kind", host, probe_ip) % 4]
    if "down" in host:
        return fail_kind
    if "blocked" in host:
        return fail_kind if country == "China" else "ok"
    if "partial" in host:
        return fail_kind if _h("partial", host, probe_ip) % 2 == 0 else "ok"
    if "unknown" in host:
        return "unknown" if country in ("Malaysia", "Thailand") else "ok"
    bucket = _h("site", host) % 10
    if bucket <= 6:
        return "ok"
    if bucket <= 8:
        blocked = COUNTRIES[_h("country", host) % len(COUNTRIES)]
        return fail_kind if country == blocked else "ok"
    return fail_kind if _h("partial", host, probe_ip) % 2 == 0 else "ok"


def render_curl_output(kind, url, probe_ip, city):
    host = _host(url)
    if kind == "ok":
        return (
            f"<!DOCTYPE html>\n<html><head><title>{host}</title>"
            f'<meta name="demo-ok" content="simulated"></head>\n'
            f"<body><h1>{host}</h1><p>Simulated response seen by probe {probe_ip} ({city}).</p></body></html>\n"
        )
    if kind == "dns":
        return f"curl: (6) Could not resolve host: {host}\n"
    if kind == "timeout":
        return f"curl: (28) Connection timeout after 5001 ms\n"
    if kind == "refused":
        return f"curl: (7) Failed to connect to {host} port 443 after 12 ms: Connection refused\n"
    if kind == "ssl":
        return f"curl: (35) OpenSSL SSL_connect: SSL_ERROR_SYSCALL in connection to {host}:443\n"
    return (
        f"<!DOCTYPE html>\n<html><head><title>Access Denied</title></head>"
        f"<body><h1>Access Denied</h1><p>Reference #{_h('ref', host, probe_ip) % 100000}</p></body></html>\n"
    )


class _Stream:
    def __init__(self, text=""):
        self._text = text

    def readlines(self):
        return self._text.splitlines(keepends=True)

    def read(self):
        return self._text.encode()


class FakeSSHClient:
    def __init__(self):
        self.probe_ip = None

    def set_missing_host_key_policy(self, policy):
        pass

    def connect(self, hostname, port=22, username=None, password=None, timeout=None, **kwargs):
        time.sleep(SSH_DELAY)
        if hostname in OFFLINE_PROBES:
            raise socket.timeout("timed out (simulated offline probe)")
        self.probe_ip = hostname

    def exec_command(self, command, timeout=None):
        country, city = _probe_info(self.probe_ip)
        target = re.search(r"https?://\S+", command)
        written = re.search(r">>\s*/var/www/html/(\S+)", command)
        if "GetMyIP" in command:
            egress = f"203.0.113.{_h('egress', self.probe_ip) % 200 + 20}"
            return _Stream(), _Stream(egress + "\n"), _Stream()
        if target and written:
            kind = decide(target.group(0), country, self.probe_ip)
            body = render_curl_output(kind, target.group(0), self.probe_ip, city)
            _results[f"http://{self.probe_ip}:8787/{written.group(1)}"] = body
        return _Stream(), _Stream(), _Stream()

    def close(self):
        pass


_real_send = HTTPAdapter.send


def _fake_send(self, request, *args, **kwargs):
    url = request.url
    if ":8787/" in url:
        response = requests.Response()
        response.url = url
        response.request = request
        response.encoding = "utf-8"
        response._content_consumed = True
        if url in _results:
            response.status_code = 200
            response._content = _results[url].encode()
        else:
            response.status_code = 404
            response._content = b"not found"
        return response
    return _real_send(self, request, *args, **kwargs)


def enable():
    paramiko.SSHClient = FakeSSHClient
    HTTPAdapter.send = _fake_send
    print("[SIMULATION] Probes are simulated: no SSH, no remote servers.")
