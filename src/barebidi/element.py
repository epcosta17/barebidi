import asyncio
import logging
from collections.abc import Awaitable, Callable, Generator
from pathlib import Path
from typing import TYPE_CHECKING, Any

from . import human

if TYPE_CHECKING:
    from .frame import Frame
    from .tab import Tab

log = logging.getLogger(__name__)

# WebDriver's codes for the keys that aren't characters.
KEYS = {
    "Enter": "",
    "Tab": "",
    "Backspace": "",
    "Escape": "",
    "ArrowLeft": "",
    "ArrowUp": "",
    "ArrowRight": "",
    "ArrowDown": "",
    "Delete": "",
}

_RECT = """function () {
  const r = this.getBoundingClientRect();
  return [r.top, r.bottom, r.left, r.right, innerWidth, innerHeight];
}"""

# A point of the element not covered by anything else, around its center but rarely right on it.
_TARGET = """function () {
  const r = this.getBoundingClientRect();
  const root = this.getRootNode(), scope = root.elementFromPoint ? root : document;
  const spread = () => (Math.random() + Math.random() + Math.random() - 1.5) / 5;
  let [x, y] = [r.left + r.width / 2, r.top + r.height / 2];
  for (let i = 0; i < 9; i++) {
    const [px, py] = [r.left + r.width * (0.5 + spread()), r.top + r.height * (0.5 + spread())];
    const hit = scope.elementFromPoint(px, py);
    if (hit && (hit === this || this.contains(hit))) { [x, y] = [px, py]; break; }
  }
  return [x, y, r.width, r.height, innerWidth, innerHeight];
}"""

# Where the browser has the pointer: over this element? over its document at all?
_HOVERED = "function () { return [this.matches(':hover'), document.documentElement.matches(':hover')] }"

# Inside an iframe: scroll the element into the frame's view, unless it is there already.
_REVEAL = """function () {
  const r = this.getBoundingClientRect();
  if (r.top < 0 || r.left < 0 || r.bottom > innerHeight || r.right > innerWidth)
    this.scrollIntoView({block: 'nearest', inline: 'nearest'});
}"""

_SELECT_CONTENTS = """function () {
  if (typeof this.select === 'function') this.select();
  else getSelection().selectAllChildren(this);
}"""


class Element:
    """An element of a page (or a shadow root), found with select(), find(), xpath() or select_all()."""

    def __init__(self, frame: "Frame", remote: dict):
        self.frame = frame
        self.shared_id: str = remote["sharedId"]
        node = remote.get("value") or {}
        self.tag: str | None = node.get("localName")
        self.attrs: dict[str, str] = node.get("attributes") or {}
        self._shadow_mode: str | None = node.get("mode")  # only shadow roots have one

    def __repr__(self) -> str:
        if self._shadow_mode:
            return f"<#shadow-root ({self._shadow_mode})>"
        attrs = "".join(f' {k}="{v}"' for k, v in self.attrs.items())
        return f"<{self.tag or 'node'}{attrs}>"

    @property
    def tab(self) -> "Tab":
        """The tab the element is in."""
        return self.frame.tab

    @property
    def reference(self) -> dict:
        """The element as a BiDi shared reference, for raw protocol commands."""
        return {"sharedId": self.shared_id}

    async def call(self, function: str, *args: Any, isolated: bool = False) -> Any:
        """Run `function` in the page with `this` bound to this element."""
        return await self.frame.call_function(function, *args, this=self, isolated=isolated)

    async def text(self) -> str:
        """The element's text content, hidden text included (`textContent`)."""
        return await self.call("function() { return this.textContent }", isolated=True)

    async def inner_text(self) -> str:
        """The element's text as rendered on screen (`innerText`)."""
        return await self.call("function() { return this.innerText }", isolated=True)

    async def html(self) -> str:
        """The element's HTML, itself included (`outerHTML`)."""
        return await self.call("function() { return this.outerHTML }", isolated=True)

    async def get_attribute(self, name: str) -> str | None:
        """The attribute's value, or None if the element doesn't have it."""
        return await self.call("function(n) { return this.getAttribute(n) }", name, isolated=True)

    async def get_property(self, name: str) -> Any:
        """A JavaScript property of the element, e.g. `value` or `checked`."""
        return await self.call("function(n) { return this[n] }", name)

    async def shadow_root(self) -> "Element | None":
        """The element's shadow root, open or closed: select() in it reaches what CSS from the document can't."""
        from .frame import _raw

        result = await self.frame.send(
            "script.callFunction",
            {
                "functionDeclaration": "function () { return this }",
                "this": self.reference,
                "target": self.frame._target(True),
                "awaitPromise": False,
                "serializationOptions": {"maxDomDepth": 0, "includeShadowTree": "all"},
            },
        )
        root = (_raw(result).get("value") or {}).get("shadowRoot")
        return Element(self.frame, root) if root else None

    async def content_frame(self) -> "Frame":
        """The document inside this <iframe> or <frame>."""
        frame = await self.call("function () { return this.contentWindow }", isolated=True)
        if frame is None:
            raise ValueError(f"{self!r} shows no document")
        frame.element = self
        return frame

    async def set_files(self, *paths: str | Path) -> None:
        """Choose files for this <input type="file">, as if picked in its file dialog."""
        files = [str(Path(path).resolve(strict=True)) for path in paths]
        await self.frame.send("input.setFiles", {"context": self.frame.id, "element": self.reference, "files": files})

    async def scroll_into_view(self) -> None:
        """Jump to the element (no wheel events); hover() and click() scroll with the wheel instead."""
        await self.call("function() { this.scrollIntoView({block: 'center', inline: 'center'}) }", isolated=True)

    async def hover(self) -> None:
        """Scroll the element into view if needed and move the mouse onto it."""
        await self._move_here()

    async def click(self) -> None:
        """Move the mouse onto the element like hover() and click it."""
        await self._move_here(then=human.click_actions(self.tab.browser.humanize))

    async def type(self, text: str) -> None:
        """Click the element, then type `text` key by key, with Shift for capitals and symbols."""
        await self.click()
        await self.frame._perform({"type": "key", "id": "keyboard", "actions": human.key_actions(text, self.tab.browser.humanize)})

    async def press(self, key: str) -> None:
        """Press and release one key: a character or a name like `Enter`, `Tab`, `Escape`, `ArrowDown`."""
        value = KEYS.get(key, key)
        hold = [{"type": "pause", "duration": human.between(50, 120)}] if self.tab.browser.humanize else []
        await self.frame._perform(
            {"type": "key", "id": "keyboard", "actions": [{"type": "keyDown", "value": value}, *hold, {"type": "keyUp", "value": value}]}
        )

    async def clear(self) -> None:
        """Select the content and press Backspace, so the page sees real input events."""
        await self.click()
        await self.call(_SELECT_CONTENTS, isolated=True)
        await self.press("Backspace")

    def select(self, css: str, timeout: float = 10.0) -> "ElementQuery":
        """The first element inside this one matching `css` (see Frame.select)."""
        return ElementQuery(lambda: self.frame._first({"type": "css", "value": css}, timeout, css, start=[self.reference]), css)

    async def select_all(self, css: str, timeout: float = 10.0) -> list["Element"]:
        """Every element inside this one matching `css` (see Frame.select_all)."""
        return await self.frame._wait_for({"type": "css", "value": css}, timeout, start=[self.reference])

    async def screenshot(self, path: str | Path | None = None) -> bytes:
        """PNG of the element; also saved to `path` if given."""
        from .tab import _save_png

        result = await self.frame.send(
            "browsingContext.captureScreenshot",
            {"context": self.frame.id, "clip": {"type": "element", "element": self.reference}},
        )
        return _save_png(result, path)

    async def _move_here(self, then: list[dict] = ()) -> None:
        await self._bring_into_view()
        tab = self.tab
        in_frame = self.frame.id != tab.id
        viewport = tuple(await tab.evaluate("[innerWidth, innerHeight]", isolated=True)) if in_frame else None
        for _ in range(3):  # the page may move the element while the mouse travels: aim again, like a person
            x, y, width, height, frame_width, frame_height = await self.call(_TARGET, isolated=True)
            x, y, scale, uncovered = await self.frame._to_tab(x, y)
            await tab._move_mouse((round(x), round(y)), min(width, height) * scale, viewport or (frame_width, frame_height))
            on_element, on_document = await self._hovered()
            if on_element:
                break
            if in_frame and uncovered and not on_document:
                # The iframe is right there, uncovered, yet the pointer never gets into its document: Firefox
                # doesn't route pointer events into iframes placed in 3D, not even a real mouse's.
                log.info("the pointer can't reach %r through the page; moving inside the frame instead", self.frame)
                await self._move_inside_frame(then)
                return
        if then:
            await tab._mouse(then)

    async def _hovered(self) -> tuple[bool, bool]:
        for _ in range(4):  # the pointer reaches out-of-process iframes a moment after the move
            on_element, on_document = await self.call(_HOVERED, isolated=True)
            if on_element:
                break
            await asyncio.sleep(0.05)
        return on_element, on_document

    async def _move_inside_frame(self, then: list[dict]) -> None:
        frame, browser = self.frame, self.tab.browser
        async with browser._input_inside_frames():
            x, y, width, height, frame_width, frame_height = await self.call(_TARGET, isolated=True)
            # The pointer is already about there: finish the approach from a few pixels off.
            start = (_clamp(x + human.between(-8, 8), frame_width), _clamp(y + human.between(-8, 8), frame_height))
            await frame._mouse([{"type": "pointerMove", "x": start[0], "y": start[1], "duration": 0, "origin": "viewport"}])
            browser._pointers[frame.id] = start
            await frame._move_mouse((round(x), round(y)), min(width, height), (frame_width, frame_height))
            if then:
                await frame._mouse(then)

    async def _bring_into_view(self) -> None:
        if self.frame.id != self.tab.id:
            # The iframe into its page's view first (and so on up), then the element into the frame's.
            await (await self.frame._container())._bring_into_view()
            await self.call(_REVEAL, isolated=True)
            return
        if self.tab.browser.humanize:
            previous = None
            for _ in range(15):
                top, bottom, left, right, width, height = await self.call(_RECT, isolated=True)
                if left < 0 or right > width:
                    break
                center = (top + bottom) / 2
                if 0.1 * height <= center <= 0.9 * height:
                    return
                if top == previous:
                    break  # the wheel moved nothing, e.g. it is over a container that can't scroll further
                previous = top
                await self.tab.scroll(round(center - height * human.between(35, 60) / 100))
                await asyncio.sleep(0.25)  # let smooth scrolling settle
        await self.scroll_into_view()


class ElementQuery:
    """An element still to be found: await it for the Element, or act on it right away, which finds it first.

        button = await tab.select("#send")    # the Element
        await tab.find("Aceptar").click()     # found, then clicked with the humanized mouse

    Each await or action looks it up anew, so it never acts on an element the page has since replaced.
    """

    def __init__(self, lookup: Callable[[], Awaitable[Element]], label: str):
        self._lookup = lookup
        self._label = label

    def __repr__(self) -> str:
        return f"<ElementQuery {self._label}>"

    def __await__(self) -> Generator[Any, None, Element]:
        return self._lookup().__await__()

    def select(self, css: str, timeout: float = 10.0) -> "ElementQuery":
        """A query for the first element matching `css` inside this one."""
        async def lookup() -> Element:
            return await (await self).select(css, timeout)

        return ElementQuery(lookup, f"{self._label} {css}")

    async def select_all(self, css: str, timeout: float = 10.0) -> list[Element]:
        """Find this element, then every element inside it matching `css`."""
        return await (await self).select_all(css, timeout)

    async def click(self) -> None:
        """Find the element, then Element.click()."""
        await (await self).click()

    async def hover(self) -> None:
        """Find the element, then Element.hover()."""
        await (await self).hover()

    async def type(self, text: str) -> None:
        """Find the element, then Element.type()."""
        await (await self).type(text)

    async def press(self, key: str) -> None:
        """Find the element, then Element.press()."""
        await (await self).press(key)

    async def clear(self) -> None:
        """Find the element, then Element.clear()."""
        await (await self).clear()

    async def set_files(self, *paths: str | Path) -> None:
        """Find the element, then Element.set_files()."""
        await (await self).set_files(*paths)

    async def scroll_into_view(self) -> None:
        """Find the element, then Element.scroll_into_view()."""
        await (await self).scroll_into_view()

    async def text(self) -> str:
        """Find the element, then Element.text()."""
        return await (await self).text()

    async def inner_text(self) -> str:
        """Find the element, then Element.inner_text()."""
        return await (await self).inner_text()

    async def html(self) -> str:
        """Find the element, then Element.html()."""
        return await (await self).html()

    async def get_attribute(self, name: str) -> str | None:
        """Find the element, then Element.get_attribute()."""
        return await (await self).get_attribute(name)

    async def get_property(self, name: str) -> Any:
        """Find the element, then Element.get_property()."""
        return await (await self).get_property(name)

    async def call(self, function: str, *args: Any, isolated: bool = False) -> Any:
        """Find the element, then Element.call()."""
        return await (await self).call(function, *args, isolated=isolated)

    async def shadow_root(self) -> Element | None:
        """Find the element, then Element.shadow_root()."""
        return await (await self).shadow_root()

    async def content_frame(self) -> "Frame":
        """Find the element, then Element.content_frame()."""
        return await (await self).content_frame()

    async def screenshot(self, path: str | Path | None = None) -> bytes:
        """Find the element, then Element.screenshot()."""
        return await (await self).screenshot(path)


def _clamp(value: float, size: float) -> int:
    return max(0, min(round(value), int(size) - 1))
