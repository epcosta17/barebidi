import base64
import functools
import http.client
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

import nodriver_bidi as nb

PAGES = Path(__file__).parent / "pages"
HOP_BY_HOP = {"connection", "proxy-connection", "proxy-authorization", "keep-alive", "transfer-encoding", "te", "upgrade"}
# Firefox never proxies requests to localhost unless told to.
LOCAL_PROXY_PREFS = {"network.proxy.allow_hijacking_localhost": True}


class Handler(SimpleHTTPRequestHandler):
    """Static files from tests/pages, plus /echo (what the server received), /hang?seconds=N (a page
    that takes that long) and /download?name=F (a small CSV served as an attachment)."""

    def do_GET(self):
        if self.path.startswith("/echo"):
            return self._echo(b"")
        if self.path.startswith("/hang"):
            time.sleep(float(parse_qs(urlsplit(self.path).query).get("seconds", ["5"])[0]))
            return self._send(b"<!doctype html><title>late</title>", "text/html")
        if self.path.startswith("/download"):
            name = parse_qs(urlsplit(self.path).query).get("name", ["report.csv"])[0]
            return self._send(b"a,b\n1,2\n", "text/csv", {"Content-Disposition": f'attachment; filename="{name}"'})
        super().do_GET()

    def _send(self, body: bytes, content_type: str, headers: dict[str, str] | None = None):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        return self._echo(self.rfile.read(int(self.headers.get("Content-Length", 0))))

    def _echo(self, body: bytes):
        payload = json.dumps(
            {"method": self.command, "path": self.path, "headers": {k.lower(): v for k, v in self.headers.items()}, "body": body.decode()}
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass


class ProxyHandler(BaseHTTPRequestHandler):
    """Plain-HTTP forward proxy that adds X-Via-Proxy upstream and can demand Basic credentials."""

    def do_GET(self):
        self._forward()

    def do_POST(self):
        self._forward()

    def _forward(self):
        if self.server.credentials:
            expected = "Basic " + base64.b64encode(self.server.credentials.encode()).decode()
            if self.headers.get("Proxy-Authorization") != expected:
                self.send_response(407)
                self.send_header("Proxy-Authenticate", 'Basic realm="test proxy"')
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
        self.server.requests.append(self.path)
        url = urlsplit(self.path)
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        headers = {k: v for k, v in self.headers.items() if k.lower() not in HOP_BY_HOP}
        headers["X-Via-Proxy"] = self.server.name
        upstream = http.client.HTTPConnection(url.hostname, url.port or 80, timeout=10)
        upstream.request(self.command, url.path + (f"?{url.query}" if url.query else ""), body or None, headers)
        response = upstream.getresponse()
        payload = response.read()
        upstream.close()
        self.send_response(response.status, response.reason)
        for name, value in response.getheaders():
            if name.lower() not in HOP_BY_HOP | {"content-length"}:
                self.send_header(name, value)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass


def start_proxy(name: str, credentials: str | None = None) -> ThreadingHTTPServer:
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), ProxyHandler)
    httpd.name = name
    httpd.credentials = credentials
    httpd.requests = []
    httpd.url = f"http://127.0.0.1:{httpd.server_address[1]}"
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


@pytest.fixture
def proxy():
    httpd = start_proxy("open")
    yield httpd
    httpd.shutdown()


@pytest.fixture
def auth_proxy():
    httpd = start_proxy("auth", "user:secret")
    yield httpd
    httpd.shutdown()


def serve():
    return ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=str(PAGES)))


@pytest.fixture(scope="session")
def server():
    httpd = serve()
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


@pytest.fixture
async def browser():
    async with nb.Browser(headless=True) as b:
        yield b


@pytest.fixture
async def tab(browser, server):
    return await browser.get(f"{server}/index.html")
