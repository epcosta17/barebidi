import asyncio
import contextlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import AsyncIterator, Iterable
from pathlib import Path
from typing import Any

from .connection import BidiError, Connection, Handler
from .context import Context
from .network import Intercept, InterceptHandler, Network, Phase
from .proxy import NO_PROXY_PREFS, Proxy
from .stealth import CLEAR_AUTOMATION_FLAG, HIDE_WEBDRIVER
from .stealth import PREFS as STEALTH_PREFS
from .tab import Tab

log = logging.getLogger(__name__)

_WS_URL = re.compile(rb"WebDriver BiDi listening on (ws://\S+)")

DEFAULT_HEADLESS_SCREEN = (1920, 1080)

ROUTED_MOUSE = "remote.events.async.mouse.enabled"

DEFAULT_PREFS: dict[str, Any] = {
    "browser.shell.checkDefaultBrowser": False,
    "browser.startup.homepage_override.mstone": "ignore",
    "browser.aboutwelcome.enabled": False,
    "browser.tabs.warnOnClose": False,
    "browser.sessionstore.resume_from_crash": False,
    "datareporting.policy.dataSubmissionEnabled": False,
    "toolkit.telemetry.reportingpolicy.firstRun": False,
    "app.update.disabledForTesting": True,
    # Behind a proxy, WebRTC must not reveal the real IP by reaching STUN servers directly.
    "media.peerconnection.ice.proxy_only_if_behind_proxy": True,
    # Mouse and wheel input enters through the browser window and its hit testing, like real input, instead
    # of being synthesized inside the page's process: it reaches cross-site iframes, with coherent coordinates.
    ROUTED_MOUSE: True,
    "remote.events.async.wheel.enabled": True,
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
    """Firefox driven over WebDriver BiDi.

    `proxy`, `locale` and `timezone` set up the default context (see Context); `profile` keeps its
    cookies and storage between runs instead of starting from a temporary profile. `screen` is the
    size of the virtual screen in headless mode; otherwise the real screen is used. With `humanize`,
    the mouse travels in curves, keys are typed at a human rhythm and scrolling uses the wheel;
    turn it off (here or later through the attribute) for speed.
    """

    def __init__(
        self,
        *,
        headless: bool = False,
        screen: tuple[int, int] | None = None,
        stealth: bool = True,
        humanize: bool = True,
        profile: str | Path | None = None,
        proxy: str | None = None,
        locale: str | None = None,
        timezone: str | None = None,
        executable_path: str | None = None,
        args: Iterable[str] = (),
        prefs: dict[str, Any] | None = None,
        startup_timeout: float = 30.0,
    ):
        if screen and not headless:
            raise ValueError("the screen size can only be chosen in headless mode; otherwise it is the real one")
        self.headless = headless
        self.screen = screen or DEFAULT_HEADLESS_SCREEN
        self.stealth = stealth
        self.humanize = humanize
        self.profile = Path(profile) if profile else None
        self.proxy = Proxy.parse(proxy) if proxy else None
        self.locale = locale
        self.timezone = timezone
        self.executable_path = executable_path
        self.args = list(args)
        self.prefs = {
            **DEFAULT_PREFS,
            **(STEALTH_PREFS if stealth else {}),
            **(self.proxy.prefs() if self.proxy else NO_PROXY_PREFS),
            **(prefs or {}),
        }
        self.startup_timeout = startup_timeout
        self.connection: Connection
        self.session_id: str | None = None
        self.capabilities: dict = {}
        self._process: asyncio.subprocess.Process | None = None
        self._profile: str | None = None
        self._stderr_task: asyncio.Task | None = None
        self._parents: dict[str, str] = {}
        self._user_contexts: dict[str, str] = {}
        self._pointers: dict[str, tuple[int, int]] = {}
        self._network = Network(self)
        self.context = Context(self, "default")

    async def __aenter__(self) -> "Browser":
        return await self.start()

    async def __aexit__(self, *exc: object) -> None:
        await self.stop()

    async def start(self) -> "Browser":
        if self.profile:
            self.profile.mkdir(parents=True, exist_ok=True)
            self._profile = str(self.profile)
        else:
            self._profile = tempfile.mkdtemp(prefix="nodriver-bidi-")
        prefs = "".join(f"user_pref({json.dumps(k)}, {json.dumps(v)});\n" for k, v in self.prefs.items())
        Path(self._profile, "user.js").write_text(prefs)

        cmd = [self.executable_path or find_firefox(), "--remote-debugging-port=0", "--profile", self._profile, "--no-remote"]
        if self.headless:
            cmd.append("--headless")
        if self.stealth:
            cmd.append("--remote-allow-system-access")
        cmd += [*self.args, "about:blank"]
        env = None
        if self.headless:
            width, height = self.screen
            env = {**os.environ, "MOZ_HEADLESS_WIDTH": str(width), "MOZ_HEADLESS_HEIGHT": str(height)}
        log.debug("launching %s", cmd)
        self._process = await asyncio.create_subprocess_exec(
            *cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, env=env
        )
        try:
            url = await asyncio.wait_for(self._read_ws_url(), self.startup_timeout)
            self._stderr_task = asyncio.create_task(self._drain_stderr())
            self.connection = await Connection.connect(f"{url}/session")
            session = await self.connection.send("session.new", {"capabilities": {}})
            await self._track_frames()
            if self.proxy:
                await self._network.register_proxy(None, self.proxy.credentials)
            await self.context._emulate(self.locale, self.timezone)
            if self.stealth:
                await self._clear_automation_flag()
            tab = await self._replace_initial_tab()
            if self.headless:
                await self._fit_window(tab)
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
        return await self.context.new_tab(url, background)

    async def get(self, url: str, new_tab: bool = False) -> Tab:
        return await self.context.get(url, new_tab)

    async def new_context(self, *, proxy: str | None = None, locale: str | None = None, timezone: str | None = None) -> Context:
        """A new isolated identity, gone when closed or when the browser stops."""
        parsed = Proxy.parse(proxy) if proxy else None
        result = await self.connection.send("browser.createUserContext", {"proxy": parsed.bidi()} if parsed else {})
        context = Context(self, result["userContext"])
        if parsed:
            await self._network.register_proxy(context.id, parsed.credentials)
        await context._emulate(locale, timezone)
        return context

    async def cookies(self, domain: str | None = None) -> list[dict]:
        return await self.context.cookies(domain)

    async def set_cookies(self, cookies: Iterable[dict]) -> None:
        await self.context.set_cookies(cookies)

    async def clear_cookies(self) -> None:
        await self.context.clear_cookies()

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

    def user_context_of(self, context: str) -> str:
        return self._user_contexts.get(context, "default")

    async def _clear_automation_flag(self) -> None:
        await self._chrome_eval(CLEAR_AUTOMATION_FLAG)

    @contextlib.asynccontextmanager
    async def _input_inside_frames(self) -> AsyncIterator[None]:
        """Mouse input sent to a frame goes straight into its document instead of through the window."""
        switch = f"Services.prefs.setBoolPref({json.dumps(ROUTED_MOUSE)}, %s)"
        switched = bool(self.prefs.get(ROUTED_MOUSE)) and await self._chrome_eval(switch % "false")
        try:
            yield
        finally:
            if switched:
                await self._chrome_eval(switch % "true")

    async def _chrome_eval(self, expression: str) -> bool:
        """Run `expression` in the browser's own scope, which needs the system access stealth mode asks for."""
        try:
            tree = await self.connection.send("browsingContext.getTree", {"moz:scope": "chrome", "maxDepth": 0})
            target = {"context": tree["contexts"][0]["context"]}
            result = await self.connection.send("script.evaluate", {"expression": expression, "target": target, "awaitPromise": False})
        except (BidiError, IndexError) as error:
            log.debug("cannot run in the browser's scope: %s", error)
            return False
        return result.get("type") != "exception"

    async def _webdriver_hidden(self, tab: Tab) -> bool:
        for _ in range(10):  # the flag reaches content processes asynchronously
            if not await tab.evaluate("navigator.webdriver", isolated=True):
                return True
            await asyncio.sleep(0.05)
        return False

    async def _fit_window(self, tab: Tab) -> None:
        # Headless Firefox spreads its window over the whole screen, menu bar and dock included, which no
        # real window does. Place it over the available area instead, like a maximized window.
        x, y, width, height = await tab.evaluate(
            "[screen.availLeft, screen.availTop, screen.availWidth, screen.availHeight]", isolated=True
        )
        window = (await self.connection.send("browser.getClientWindows"))["clientWindows"][0]["clientWindow"]
        await self.connection.send(
            "browser.setClientWindowState",
            {"clientWindow": window, "state": "normal", "x": x, "y": y, "width": width, "height": height},
        )

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
            self._user_contexts[params["context"]] = params.get("userContext", "default")
            if params.get("parent"):
                self._parents[params["context"]] = params["parent"]

        def destroyed(params: dict) -> None:
            self._parents.pop(params["context"], None)
            self._user_contexts.pop(params["context"], None)
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
        if self._profile and self.profile is None:
            shutil.rmtree(self._profile, ignore_errors=True)
        self._process = None


async def start(**kwargs: Any) -> Browser:
    return await Browser(**kwargs).start()
