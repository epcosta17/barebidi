import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .connection import Connection, Handler
from .tab import Tab

log = logging.getLogger(__name__)

_WS_URL = re.compile(rb"WebDriver BiDi listening on (ws://\S+)")

DEFAULT_PREFS: dict[str, Any] = {
    "browser.shell.checkDefaultBrowser": False,
    "browser.startup.homepage_override.mstone": "ignore",
    "browser.aboutwelcome.enabled": False,
    "browser.tabs.warnOnClose": False,
    "browser.sessionstore.resume_from_crash": False,
    "datareporting.policy.dataSubmissionEnabled": False,
    "toolkit.telemetry.reportingpolicy.firstRun": False,
    "app.update.disabledForTesting": True,
}


def find_firefox() -> str:
    if path := os.environ.get("FIREFOX_PATH"):
        return path
    candidates = {
        "darwin": ["/Applications/Firefox.app/Contents/MacOS/firefox", "/Applications/Firefox Nightly.app/Contents/MacOS/firefox"],
        "win32": [
            rf"{os.environ.get('PROGRAMFILES', 'C:/Program Files')}\Mozilla Firefox\firefox.exe",
            rf"{os.environ.get('PROGRAMFILES(X86)', 'C:/Program Files (x86)')}\Mozilla Firefox\firefox.exe",
        ],
    }.get(sys.platform, [])
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    for name in ("firefox", "firefox-esr", "firefox-nightly"):
        if found := shutil.which(name):
            return found
    raise FileNotFoundError("Firefox not found; install it or set FIREFOX_PATH")


class Browser:
    def __init__(
        self,
        *,
        headless: bool = False,
        executable_path: str | None = None,
        args: Iterable[str] = (),
        prefs: dict[str, Any] | None = None,
        startup_timeout: float = 30.0,
    ):
        self.headless = headless
        self.executable_path = executable_path
        self.args = list(args)
        self.prefs = {**DEFAULT_PREFS, **(prefs or {})}
        self.startup_timeout = startup_timeout
        self.connection: Connection
        self.session_id: str | None = None
        self.capabilities: dict = {}
        self._process: asyncio.subprocess.Process | None = None
        self._profile: str | None = None
        self._stderr_task: asyncio.Task | None = None

    async def __aenter__(self) -> "Browser":
        return await self.start()

    async def __aexit__(self, *exc: object) -> None:
        await self.stop()

    async def start(self) -> "Browser":
        self._profile = tempfile.mkdtemp(prefix="nodriver-bidi-")
        prefs = "".join(f"user_pref({json.dumps(k)}, {json.dumps(v)});\n" for k, v in self.prefs.items())
        Path(self._profile, "user.js").write_text(prefs)

        cmd = [self.executable_path or find_firefox(), "--remote-debugging-port=0", "--profile", self._profile, "--no-remote"]
        if self.headless:
            cmd.append("--headless")
        cmd += [*self.args, "about:blank"]
        log.debug("launching %s", cmd)
        self._process = await asyncio.create_subprocess_exec(
            *cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
        )
        try:
            url = await asyncio.wait_for(self._read_ws_url(), self.startup_timeout)
            self._stderr_task = asyncio.create_task(self._drain_stderr())
            self.connection = await Connection.connect(f"{url}/session")
            session = await self.connection.send("session.new", {"capabilities": {}})
        except BaseException:
            await self._cleanup(grace=0)
            raise
        self.session_id = session["sessionId"]
        self.capabilities = session["capabilities"]
        return self

    async def stop(self) -> None:
        if self._process is None:
            return
        if hasattr(self, "connection") and not self.connection.closed:
            try:
                await asyncio.wait_for(self.connection.send("browser.close"), 5)
            except Exception:
                pass
            await self.connection.close()
        await self._cleanup()

    async def tabs(self) -> list[Tab]:
        tree = await self.connection.send("browsingContext.getTree", {"maxDepth": 0})
        return [Tab(self, c["context"]) for c in tree["contexts"]]

    async def new_tab(self, url: str | None = None, background: bool = False) -> Tab:
        result = await self.connection.send("browsingContext.create", {"type": "tab", "background": background})
        tab = Tab(self, result["context"])
        if url:
            await tab.get(url)
        return tab

    async def get(self, url: str, new_tab: bool = False) -> Tab:
        tab = await self.new_tab() if new_tab else (await self.tabs())[0]
        return await tab.get(url)

    async def on(self, event: str, handler: Handler, contexts: list[str] | None = None) -> str:
        """Subscribe to a BiDi event or module ("network.responseCompleted", "log")."""
        self.connection.on(event, handler)
        params: dict = {"events": [event]}
        if contexts:
            params["contexts"] = contexts
        result = await self.connection.send("session.subscribe", params)
        return result.get("subscription", "")

    async def _read_ws_url(self) -> str:
        assert self._process and self._process.stderr
        output = []
        while line := await self._process.stderr.readline():
            output.append(line)
            if match := _WS_URL.search(line):
                return match.group(1).decode()
        raise RuntimeError("Firefox exited during startup:\n" + b"".join(output).decode(errors="replace"))

    async def _drain_stderr(self) -> None:
        assert self._process and self._process.stderr
        while line := await self._process.stderr.readline():
            log.debug("firefox: %s", line.decode(errors="replace").rstrip())

    async def _cleanup(self, grace: float = 10) -> None:
        if self._process and self._process.returncode is None:
            try:
                await asyncio.wait_for(self._process.wait(), grace)
            except TimeoutError:
                self._process.kill()
                await self._process.wait()
        if self._stderr_task:
            self._stderr_task.cancel()
        if self._profile:
            shutil.rmtree(self._profile, ignore_errors=True)
        self._process = None


async def start(**kwargs: Any) -> Browser:
    return await Browser(**kwargs).start()
