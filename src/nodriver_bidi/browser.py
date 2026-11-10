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

from .connection import BidiError, Connection, Handler
from .network import Intercept, InterceptHandler, Network, Phase
from .stealth import CLEAR_AUTOMATION_FLAG, HIDE_WEBDRIVER
from .stealth import PREFS as STEALTH_PREFS
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
        stealth: bool = True,
        executable_path: str | None = None,
        args: Iterable[str] = (),
        prefs: dict[str, Any] | None = None,
        startup_timeout: float = 30.0,
    ):
        self.headless = headless
        self.stealth = stealth
        self.executable_path = executable_path
        self.args = list(args)
        self.prefs = {**DEFAULT_PREFS, **(STEALTH_PREFS if stealth else {}), **(prefs or {})}
        self.startup_timeout = startup_timeout
        self.connection: Connection
        self.session_id: str | None = None
        self.capabilities: dict = {}
        self._process: asyncio.subprocess.Process | None = None
        self._profile: str | None = None
        self._stderr_task: asyncio.Task | None = None
        self._parents: dict[str, str] = {}
        self._network = Network(self)

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
        if self.stealth:
            cmd.append("--remote-allow-system-access")
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
            await self._track_frames()
            if self.stealth:
                await self._clear_automation_flag()
            tab = await self._replace_initial_tab()
            if self.stealth and not await self._webdriver_hidden(tab):
                log.info("this Firefox keeps navigator.webdriver on; hiding it with a preload script instead")
                await self.connection.send("script.addPreloadScript", {"functionDeclaration": HIDE_WEBDRIVER})
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

    async def intercept(self, handler: InterceptHandler, url: str | None = None, phase: Phase = "request") -> Intercept:
        """Pause matching requests in every tab and pass them to `handler`.

        The handler settles each one with continue_(), abort() or fulfill(); if it doesn't,
        the next matching intercept gets it, and if none does the request continues untouched.
        """
        return await self._network.intercept(handler, url, phase)

    async def block(self, *urls: str, resource_types: Iterable[str] = ()) -> Intercept:
        """Abort requests matching any URL pattern or resource type ("image", "font", "media", ...)."""
        return await self._network.block(urls, resource_types)

    async def set_extra_headers(self, headers: dict[str, str]) -> None:
        """Add headers to every request; an empty dict removes them."""
        await self._network.set_extra_headers(headers)

    def top_level(self, context: str) -> str:
        """The tab a browsing context (e.g. an iframe) belongs to."""
        while context in self._parents:
            context = self._parents[context]
        return context

    async def _clear_automation_flag(self) -> None:
        try:
            tree = await self.connection.send("browsingContext.getTree", {"moz:scope": "chrome", "maxDepth": 0})
            target = {"context": tree["contexts"][0]["context"]}
            await self.connection.send(
                "script.evaluate", {"expression": CLEAR_AUTOMATION_FLAG, "target": target, "awaitPromise": False}
            )
        except (BidiError, IndexError) as error:
            log.debug("could not clear the automation flag: %s", error)

    async def _webdriver_hidden(self, tab: Tab) -> bool:
        for _ in range(10):  # the flag reaches content processes asynchronously
            if not await tab.evaluate("navigator.webdriver", isolated=True):
                return True
            await asyncio.sleep(0.05)
        return False

    async def _replace_initial_tab(self) -> Tab:
        # Firefox focuses the address bar of the startup about:blank tab, so documents loaded there never
        # get focus (document.hasFocus() stays false). Tabs opened over BiDi get content focus.
        initial = await self.tabs()
        tab = await self.new_tab()
        for old in initial:
            await old.close()
        return tab

    async def _track_frames(self) -> None:
        def created(params: dict) -> None:
            if params.get("parent"):
                self._parents[params["context"]] = params["parent"]

        def destroyed(params: dict) -> None:
            self._parents.pop(params["context"], None)
            for child in params.get("children") or ():
                destroyed(child)

        self.connection.on("browsingContext.contextCreated", created)
        self.connection.on("browsingContext.contextDestroyed", destroyed)
        await self.connection.send(
            "session.subscribe", {"events": ["browsingContext.contextCreated", "browsingContext.contextDestroyed"]}
        )

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
