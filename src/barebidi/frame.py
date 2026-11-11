import asyncio
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from . import human
from .element import Element, ElementQuery
from .network import url_matcher
from .values import deserialize, serialize

if TYPE_CHECKING:
    from .browser import Browser
    from .tab import Tab

# Realm for the library's own scripts: pages can neither see them nor tamper with the DOM APIs they use.
SANDBOX = "barebidi"

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

# Every <iframe> and <frame> of the document, open shadow roots included, with the window it shows.
_FRAME_ELEMENTS = """() => {
  const found = [];
  const visit = root => {
    for (const element of root.querySelectorAll('*')) {
      if (element.localName === 'iframe' || element.localName === 'frame') found.push([element, element.contentWindow]);
      if (element.shadowRoot) visit(element.shadowRoot);
    }
  };
  visit(document);
  return found;
}"""

_WINDOWS = "(...frames) => frames.map(frame => frame.contentWindow)"

# A point of a frame's viewport in its parent's viewport, through the frame's <iframe> (this), and whether
# nothing covers the iframe there. Exact unless the iframe is rotated or skewed.
_INTO_PARENT = """function (x, y) {
  const box = this.getBoundingClientRect(), style = getComputedStyle(this);
  const sx = this.offsetWidth ? box.width / this.offsetWidth : 1, sy = this.offsetHeight ? box.height / this.offsetHeight : 1;
  const px = box.left + (this.clientLeft + parseFloat(style.paddingLeft) + x) * sx;
  const py = box.top + (this.clientTop + parseFloat(style.paddingTop) + y) * sy;
  const root = this.getRootNode();
  return [px, py, Math.min(sx, sy), (root.elementFromPoint ? root : document).elementFromPoint(px, py) === this];
}"""


class JavaScriptError(Exception):
    """An exception thrown by page JavaScript run through evaluate() or call_function(); `details` has BiDi's report."""

    def __init__(self, details: dict):
        super().__init__(details.get("text", "JavaScript exception"))
        self.details = details


class Frame:
    """A document in a browsing context: a tab's page, or an iframe in it (Tab.frame, Element.content_frame)."""

    def __init__(self, browser: "Browser", context_id: str, tab: "Tab | None" = None, element: Element | None = None):
        self.browser = browser
        self.id = context_id
        self.tab: Tab = tab or self  # a tab is its own top frame
        self.element = element  # the <iframe> showing this document, once known

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.id}>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Frame) and other.id == self.id

    def __hash__(self) -> int:
        return hash(self.id)

    async def send(self, method: str, params: dict | None = None, timeout: float | None = None) -> dict:
        """Send a raw WebDriver BiDi command and return its result; the context isn't added to `params` for you."""
        return await self.browser.connection.send(method, params, timeout)

    async def url(self) -> str:
        """The document's current URL."""
        tree = await self.send("browsingContext.getTree", {"root": self.id, "maxDepth": 0})
        return tree["contexts"][0]["url"]

    async def evaluate(self, expression: str, await_promise: bool = True, isolated: bool = False) -> Any:
        """Run `expression` in the page; with `isolated`, in a sandbox that shares only the DOM."""
        result = await self.send(
            "script.evaluate",
            {"expression": expression, "target": self._target(isolated), "awaitPromise": await_promise},
        )
        return self._unwrap(result)

    async def call_function(self, function: str, *args: Any, this: Any = None, isolated: bool = False) -> Any:
        """Call the JavaScript `function` with `args` (and `this`), converted both ways like evaluate()."""
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
        """The document's whole HTML, as it is now."""
        return await self.evaluate("document.documentElement.outerHTML", isolated=True)

    async def title(self) -> str:
        """The document's title."""
        return await self.evaluate("document.title", isolated=True)

    def select(self, css: str, timeout: float = 10.0) -> ElementQuery:
        """The first element matching `css`, waiting up to `timeout` seconds for it to appear. Await it for the
        Element, or chain an action: `await tab.select("#email").type("ana@example.com")`."""
        return ElementQuery(lambda: self._first({"type": "css", "value": css}, timeout, css), css)

    async def select_all(self, css: str, timeout: float = 10.0) -> list[Element]:
        """Every element matching `css`, waiting up to `timeout` seconds for at least one; empty if none appears."""
        return await self._wait_for({"type": "css", "value": css}, timeout)

    async def xpath(self, expression: str, timeout: float = 10.0) -> list[Element]:
        """Every element matching the XPath `expression`, waiting like select_all()."""
        return await self._wait_for({"type": "xpath", "value": expression}, timeout)

    def find(self, text: str, exact: bool = False, timeout: float = 10.0) -> ElementQuery:
        """The first element whose own text contains `text` (case-insensitive), or equals it when `exact`;
        waits up to `timeout` seconds. Await it, or chain an action: `await tab.find("Aceptar").click()`."""
        return ElementQuery(lambda: self._find(text, exact, timeout), repr(text))

    async def _find(self, text: str, exact: bool, timeout: float) -> Element:
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

    async def frames(self) -> list["Frame"]:
        """The iframes inside this document, nested ones included."""
        return [frame for frame, _ in await self._descendants()]

    async def frame(self, url: str, timeout: float = 10.0) -> "Frame":
        """The first iframe inside this document whose URL contains `url` (a glob if it has `*`); waits for it."""
        matches = url_matcher(url)
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        while True:
            for frame, frame_url in await self._descendants():
                if matches(frame_url):
                    return frame
            if loop.time() >= deadline:
                raise TimeoutError(f"no frame with URL matching {url!r} after {timeout}s")
            await asyncio.sleep(0.1)

    async def _descendants(self) -> list[tuple["Frame", str]]:
        tree = await self.send("browsingContext.getTree", {"root": self.id})
        found: list[tuple[Frame, str]] = []

        def walk(node: dict) -> None:
            for child in node.get("children") or ():
                found.append((Frame(self.browser, child["context"], tab=self.tab), child["url"]))
                walk(child)

        walk(tree["contexts"][0])
        return found

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

    async def _to_tab(self, x: float, y: float) -> tuple[float, float, float, bool]:
        """A point of this frame's viewport in the tab's: x, y, how much the frame is scaled there, and
        whether its iframes are uncovered at that point."""
        scale, uncovered, frame = 1.0, True, self
        while frame.id != frame.tab.id:
            container = await frame._container()
            x, y, factor, shown = await container.call(_INTO_PARENT, x, y, isolated=True)
            scale *= factor
            uncovered = uncovered and shown
            frame = container.frame
        return x, y, scale, uncovered

    async def _container(self) -> Element:
        """The <iframe> (or <frame>) showing this document, in its parent's."""
        if self.element is None:
            parent = self._parent()
            for element, window in await parent.call_function(_FRAME_ELEMENTS, isolated=True):
                if window == self:
                    self.element = element
                    break
            else:
                self.element = await parent._frame_element_in_closed_shadow_roots(self)
        return self.element

    def _parent(self) -> "Frame":
        parent = self.browser._parents.get(self.id)
        if parent is None:
            raise RuntimeError(f"{self!r} is not inside another document")
        return self.tab if parent == self.tab.id else Frame(self.browser, parent, tab=self.tab)

    async def _frame_element_in_closed_shadow_roots(self, frame: "Frame") -> Element:
        # Only BiDi's serialization reaches into closed shadow roots, where Cloudflare Turnstile puts its iframe.
        result = await self.send(
            "script.evaluate",
            {
                "expression": "document.documentElement",
                "target": self._target(True),
                "awaitPromise": False,
                "serializationOptions": {"maxDomDepth": None, "includeShadowTree": "all"},
            },
        )
        elements = [Element(self, node) for node in _frame_nodes(_raw(result))]
        windows = await self.call_function(_WINDOWS, *elements, isolated=True) if elements else []
        for element, window in zip(elements, windows):
            if window == frame:
                return element
        raise RuntimeError(f"cannot find the element that shows {frame!r}")

    def _frame_for(self, context_id: str) -> "Frame":
        """The Frame, or Tab, for a window a script handed back."""
        from .tab import Tab

        top = self.browser.top_level(context_id)
        tab = self.tab if top == self.tab.id else Tab(self.browser, top)
        return tab if context_id == top else Frame(self.browser, context_id, tab=tab)

    async def _pointer(self, viewport: tuple[int, int] | None = None) -> tuple[int, int]:
        """Where the mouse is, in this frame's viewport; the first time, a random resting place."""
        if self.id not in self.browser._pointers:
            width, height = viewport or await self.evaluate("[innerWidth, innerHeight]", isolated=True)
            self.browser._pointers[self.id] = human.resting_point(width, height)
        return self.browser._pointers[self.id]

    async def _move_mouse(self, target: tuple[int, int], target_size: float, viewport: tuple[int, int]) -> None:
        start = await self._pointer(viewport)
        path = human.mouse_path(start, target, target_size, viewport) if self.browser.humanize else [(*target, 0)]
        await self._mouse([{"type": "pointerMove", "x": x, "y": y, "duration": ms, "origin": "viewport"} for x, y, ms in path])
        self.browser._pointers[self.id] = target

    async def _mouse(self, actions: list[dict]) -> None:
        await self._perform({"type": "pointer", "id": "mouse", "parameters": {"pointerType": "mouse"}, "actions": actions})

    async def _perform(self, source: dict) -> None:
        # The command lasts as long as its actions take, so the timeout counts on top of that.
        timeout = self.browser.connection.timeout
        if timeout is not None:
            timeout += sum(action.get("duration", 0) for action in source["actions"]) / 1000
        await self.send("input.performActions", {"context": self.id, "actions": [source]}, timeout)

    def _target(self, isolated: bool) -> dict:
        return {"context": self.id, "sandbox": SANDBOX} if isolated else {"context": self.id}

    def _unwrap(self, result: dict) -> Any:
        return deserialize(_raw(result), self)


def _raw(result: dict) -> dict:
    if result["type"] == "exception":
        raise JavaScriptError(result["exceptionDetails"])
    return result["result"]


def _frame_nodes(node: dict) -> Iterator[dict]:
    value = node.get("value") or {}
    if value.get("localName") in ("iframe", "frame"):
        yield node
    if value.get("shadowRoot"):
        yield from _frame_nodes(value["shadowRoot"])
    for child in value.get("children") or ():
        yield from _frame_nodes(child)
