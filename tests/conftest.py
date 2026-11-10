import functools
import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

import nodriver_bidi as nb

PAGES = Path(__file__).parent / "pages"


class Handler(SimpleHTTPRequestHandler):
    """Static files from tests/pages plus /echo, which returns what the server received."""

    def do_GET(self):
        if self.path.startswith("/echo"):
            return self._echo(b"")
        super().do_GET()

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
