import asyncio
import base64
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from . import human
from .element import Element
from .values import deserialize, serialize

if TYPE_CHECKING:
    from .browser import Browser
    from .connection import Handler
    from .network import ExpectedResponse, Intercept, InterceptHandler, Phase, ResponseHandler, ResponseMatch

Wait = Literal["none", "interactive", "complete"]

# Realm for the library's own scripts: pages can neither see them nor tamper with the DOM APIs they use.
SANDBOX = "nodriver-bidi"

_FIND_TEXT = """(text, exact) => {
  const want = exact ? text : text.toLowerCase();
  const skip = new Set(["SCRIPT", "STYLE", "NOSCRIPT", "TEMPLATE"]);
  const walker = document.createTreeWalker(document.documentElement, NodeFilter.SHOW_TEXT);
  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    const parent = node.parentElement;
    if (!parent || skip.has(parent.tagName)) continue;
    const got = exact ? node.data.trim() : node.data.toLowerCase();
    if (exact ? got === want : got.includes(want)) return parent;
  }
  return null;
}"""


class JavaScriptError(Exception):
    def __init__(self, details: dict):
        super().__init__(details.get("text", "JavaScript exception"))
        self.details = details


class Tab:
    def __init__(self, browser: "Browser", context_id: str):
        self.browser = browser
        self.id = context_id

    def __repr__(self) -> str:
        return f"<Tab {self.id}>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Tab) and other.id == self.id

    def __hash__(self) -> int:
        return hash(self.id)

    async def send(self, method: str, params: dict | None = None) -> dict:
        return await self.browser.connection.send(method, params)

    async def get(self, url: str, wait: Wait = "complete") -> "Tab":
        await self.send("browsingContext.navigate", {"context": self.id, "url": url, "wait": wait})
        return self

    async def reload(self, wait: Wait = "complete") -> "Tab":
        await self.send("browsingContext.reload", {"context": self.id, "wait": wait})
        return self

    async def back(self) -> None:
        await self.send("browsingContext.traverseHistory", {"context": self.id, "delta": -1})

    async def forward(self) -> None:
        await self.send("browsingContext.traverseHistory", {"context": self.id, "delta": 1})

    async def url(self) -> str:
        tree = await self.send("browsingContext.getTree", {"root": self.id, "maxDepth": 0})
        return tree["contexts"][0]["url"]

    async def activate(self) -> None:
        await self.send("browsingContext.activate", {"context": self.id})

    async def close(self) -> None:
        await self.send("browsingContext.close", {"context": self.id})

    async def evaluate(self, expression: str, await_promise: bool = True, isolated: bool = False) -> Any:
        """Run `expression` in the page; with `isolated`, in a sandbox that shares only the DOM."""
        result = await self.send(
            "script.evaluate",
            {"expression": expression, "target": self._target(isolated), "awaitPromise": await_promise},
        )
        return self._unwrap(result)

    async def call_function(self, function: str, *args: Any, this: Any = None, isolated: bool = False) -> Any:
        params = {
            "functionDeclaration": function,
            "arguments": [serialize(a) for a in args],
            "target": self._target(isolated),
            "awaitPromise": True,
        }
        if this is not None:
            params["this"] = serialize(this)
        return self._unwrap(await self.send("script.callFunction", params))

    async def content(self) -> str:
        return await self.evaluate("document.documentElement.outerHTML", isolated=True)

    async def title(self) -> str:
        return await self.evaluate("document.title", isolated=True)

    async def select(self, css: str, timeout: float = 10.0) -> Element:
        return await self._first({"type": "css", "value": css}, timeout, css)

    async def select_all(self, css: str, timeout: float = 10.0) -> list[Element]:
        return await self._wait_for({"type": "css", "value": css}, timeout)

    async def xpath(self, expression: str, timeout: float = 10.0) -> list[Element]:
        return await self._wait_for({"type": "xpath", "value": expression}, timeout)

    async def find(self, text: str, exact: bool = False, timeout: float = 10.0) -> Element:
        """Element whose own text contains `text` (case-insensitive), or equals it when `exact`."""
        # BiDi's innerText locator isn't implemented in Firefox yet, so search in the page.
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        while True:
            element = await self.call_function(_FIND_TEXT, text, exact, isolated=True)
            if element is not None:
                return element
            if loop.time() >= deadline:
                raise TimeoutError(f"no element with text {text!r} after {timeout}s")
            await asyncio.sleep(0.1)

    async def scroll(self, delta_y: int) -> None:
        """Scroll with the mouse wheel where the pointer is; in notches with pauses when humanized."""
        x, y = await self._pointer()
        actions: list[dict] = []
        for delta, pause in human.wheel_steps(delta_y) if self.browser.humanize else [(delta_y, 0)]:
            actions.append({"type": "scroll", "x": x, "y": y, "deltaX": 0, "deltaY": delta, "origin": "viewport"})
            if pause:
                actions.append({"type": "pause", "duration": pause})
        await self._perform({"type": "wheel", "id": "wheel", "actions": actions})

    async def screenshot(self, path: str | Path | None = None, full_page: bool = False) -> bytes:
        params = {"context": self.id, "origin": "document" if full_page else "viewport"}
        return _save_png(await self.send("browsingContext.captureScreenshot", params), path)

    async def on(self, event: str, handler: "Handler") -> str:
        def scoped(params: dict) -> Any:
            context = params.get("context")
            if context is None or self.browser.top_level(context) == self.id:
                return handler(params)

        return await self.browser.on(event, scoped, contexts=[self.id])

    async def intercept(self, handler: "InterceptHandler", url: str | None = None, phase: "Phase" = "request") -> "Intercept":
        """Like Browser.intercept, for this tab's requests (iframes included)."""
        return await self.browser._network.intercept(handler, url, phase, contexts=[self.id])

    async def block(self, *urls: str, resource_types: tuple[str, ...] | list[str] = ()) -> "Intercept":
        return await self.browser._network.block(urls, resource_types, contexts=[self.id])

    async def set_extra_headers(self, headers: dict[str, str]) -> None:
        await self.browser._network.set_extra_headers(headers, contexts=[self.id])

    async def on_response(self, handler: "ResponseHandler", url: "ResponseMatch" = None) -> Callable[[], None]:
        """Call `handler` with every completed response that matches; returns a function that stops it.

        `url` is a substring, a glob with `*`, or a predicate on the Response.
        """
        return await self.browser._network.on_response(handler, url, tab=self.id)

    def expect_response(self, url: "ResponseMatch" = None, timeout: float = 30.0) -> AbstractAsyncContextManager["ExpectedResponse"]:
        """Wait for a response triggered inside the block:

        async with tab.expect_response("/api/items") as expected:
            await button.click()
        items = await expected.response.json()
        """
        return self.browser._network.expect_response(url, timeout, tab=self.id)

    async def _first(self, locator: dict, timeout: float, label: str, start: list | None = None) -> Element:
        found = await self._wait_for(locator, timeout, start, max_count=1)
        if not found:
            raise TimeoutError(f"no element matching {label} after {timeout}s")
        return found[0]

    async def _wait_for(
        self, locator: dict, timeout: float, start: list | None = None, max_count: int | None = None
    ) -> list[Element]:
        params: dict = {"context": self.id, "locator": locator}
        if start:
            params["startNodes"] = start
        if max_count:
            params["maxNodeCount"] = max_count
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        while True:
            nodes = (await self.send("browsingContext.locateNodes", params))["nodes"]
            if nodes or loop.time() >= deadline:
                return [Element(self, n) for n in nodes]
            await asyncio.sleep(0.1)

    async def _pointer(self, viewport: tuple[int, int] | None = None) -> tuple[int, int]:
        """Where this tab's mouse is; the first time, a random resting place."""
        if self.id not in self.browser._pointers:
            width, height = viewport or await self.evaluate("[innerWidth, innerHeight]", isolated=True)
            self.browser._pointers[self.id] = human.resting_point(width, height)
        return self.browser._pointers[self.id]

    async def _move_mouse(self, target: tuple[int, int], target_size: float, viewport: tuple[int, int]) -> None:
        start = await self._pointer(viewport)
        path = human.mouse_path(start, target, target_size, viewport) if self.browser.humanize else [(*target, 0)]
        moves = [{"type": "pointerMove", "x": x, "y": y, "duration": ms, "origin": "viewport"} for x, y, ms in path]
        await self._perform({"type": "pointer", "id": "mouse", "parameters": {"pointerType": "mouse"}, "actions": moves})
        self.browser._pointers[self.id] = target

    async def _perform(self, source: dict) -> None:
        await self.send("input.performActions", {"context": self.id, "actions": [source]})

    def _target(self, isolated: bool) -> dict:
        return {"context": self.id, "sandbox": SANDBOX} if isolated else {"context": self.id}

    def _unwrap(self, result: dict) -> Any:
        if result["type"] == "exception":
            raise JavaScriptError(result["exceptionDetails"])
        return deserialize(result["result"], self)


def _save_png(result: dict, path: str | Path | None) -> bytes:
    data = base64.b64decode(result["data"])
    if path is not None:
        Path(path).write_bytes(data)
    return data
