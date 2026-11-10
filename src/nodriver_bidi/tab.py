import asyncio
import base64
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from .element import Element
from .values import deserialize, serialize

if TYPE_CHECKING:
    from .browser import Browser
    from .connection import Handler

Wait = Literal["none", "interactive", "complete"]

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

    async def evaluate(self, expression: str, await_promise: bool = True) -> Any:
        result = await self.send(
            "script.evaluate",
            {"expression": expression, "target": {"context": self.id}, "awaitPromise": await_promise},
        )
        return self._unwrap(result)

    async def call_function(self, function: str, *args: Any, this: Any = None) -> Any:
        params = {
            "functionDeclaration": function,
            "arguments": [serialize(a) for a in args],
            "target": {"context": self.id},
            "awaitPromise": True,
        }
        if this is not None:
            params["this"] = serialize(this)
        return self._unwrap(await self.send("script.callFunction", params))

    async def content(self) -> str:
        return await self.evaluate("document.documentElement.outerHTML")

    async def title(self) -> str:
        return await self.evaluate("document.title")

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
            element = await self.call_function(_FIND_TEXT, text, exact)
            if element is not None:
                return element
            if loop.time() >= deadline:
                raise TimeoutError(f"no element with text {text!r} after {timeout}s")
            await asyncio.sleep(0.1)

    async def screenshot(self, path: str | Path | None = None, full_page: bool = False) -> bytes:
        params = {"context": self.id, "origin": "document" if full_page else "viewport"}
        return _save_png(await self.send("browsingContext.captureScreenshot", params), path)

    async def on(self, event: str, handler: "Handler") -> str:
        def scoped(params: dict) -> Any:
            if params.get("context", self.id) == self.id:
                return handler(params)

        return await self.browser.on(event, scoped, contexts=[self.id])

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

    def _unwrap(self, result: dict) -> Any:
        if result["type"] == "exception":
            raise JavaScriptError(result["exceptionDetails"])
        return deserialize(result["result"], self)


def _save_png(result: dict, path: str | Path | None) -> bytes:
    data = base64.b64decode(result["data"])
    if path is not None:
        Path(path).write_bytes(data)
    return data
