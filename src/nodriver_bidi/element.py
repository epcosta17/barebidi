import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Any

from . import human

if TYPE_CHECKING:
    from .tab import Tab

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
  const spread = () => (Math.random() + Math.random() + Math.random() - 1.5) / 5;
  let [x, y] = [r.left + r.width / 2, r.top + r.height / 2];
  for (let i = 0; i < 9; i++) {
    const [px, py] = [r.left + r.width * (0.5 + spread()), r.top + r.height * (0.5 + spread())];
    const hit = document.elementFromPoint(px, py);
    if (hit && (hit === this || this.contains(hit))) { [x, y] = [px, py]; break; }
  }
  return [Math.round(x), Math.round(y), r.width, r.height, innerWidth, innerHeight];
}"""

_UNDER = """function (x, y) {
  const hit = document.elementFromPoint(x, y);
  return !!hit && (hit === this || this.contains(hit));
}"""

_SELECT_CONTENTS = """function () {
  if (typeof this.select === 'function') this.select();
  else getSelection().selectAllChildren(this);
}"""


class Element:
    def __init__(self, tab: "Tab", remote: dict):
        self.tab = tab
        self.shared_id: str = remote["sharedId"]
        node = remote.get("value") or {}
        self.tag: str | None = node.get("localName")
        self.attrs: dict[str, str] = node.get("attributes") or {}

    def __repr__(self) -> str:
        attrs = "".join(f' {k}="{v}"' for k, v in self.attrs.items())
        return f"<{self.tag or 'node'}{attrs}>"

    @property
    def reference(self) -> dict:
        return {"sharedId": self.shared_id}

    async def call(self, function: str, *args: Any, isolated: bool = False) -> Any:
        """Run `function` in the page with `this` bound to this element."""
        return await self.tab.call_function(function, *args, this=self, isolated=isolated)

    async def text(self) -> str:
        return await self.call("function() { return this.textContent }", isolated=True)

    async def inner_text(self) -> str:
        return await self.call("function() { return this.innerText }", isolated=True)

    async def html(self) -> str:
        return await self.call("function() { return this.outerHTML }", isolated=True)

    async def get_attribute(self, name: str) -> str | None:
        return await self.call("function(n) { return this.getAttribute(n) }", name, isolated=True)

    async def get_property(self, name: str) -> Any:
        return await self.call("function(n) { return this[n] }", name)

    async def scroll_into_view(self) -> None:
        """Jump to the element (no wheel events); hover() and click() scroll with the wheel instead."""
        await self.call("function() { this.scrollIntoView({block: 'center', inline: 'center'}) }", isolated=True)

    async def hover(self) -> None:
        await self._move_here()

    async def click(self) -> None:
        await self._move_here(then=human.click_actions(self.tab.browser.humanize))

    async def type(self, text: str) -> None:
        await self.click()
        await self.tab._perform({"type": "key", "id": "keyboard", "actions": human.key_actions(text, self.tab.browser.humanize)})

    async def press(self, key: str) -> None:
        value = KEYS.get(key, key)
        hold = [{"type": "pause", "duration": human.between(50, 120)}] if self.tab.browser.humanize else []
        await self.tab._perform(
            {"type": "key", "id": "keyboard", "actions": [{"type": "keyDown", "value": value}, *hold, {"type": "keyUp", "value": value}]}
        )

    async def clear(self) -> None:
        """Select the content and press Backspace, so the page sees real input events."""
        await self.click()
        await self.call(_SELECT_CONTENTS, isolated=True)
        await self.press("Backspace")

    async def select(self, css: str, timeout: float = 10.0) -> "Element":
        return await self.tab._first({"type": "css", "value": css}, timeout, css, start=[self.reference])

    async def select_all(self, css: str, timeout: float = 10.0) -> list["Element"]:
        return await self.tab._wait_for({"type": "css", "value": css}, timeout, start=[self.reference])

    async def screenshot(self, path: str | Path | None = None) -> bytes:
        from .tab import _save_png

        result = await self.tab.send(
            "browsingContext.captureScreenshot",
            {"context": self.tab.id, "clip": {"type": "element", "element": self.reference}},
        )
        return _save_png(result, path)

    async def _move_here(self, then: list[dict] = ()) -> None:
        await self._bring_into_view()
        for _ in range(3):  # the page may move the element while the mouse travels: aim again, like a person
            x, y, width, height, viewport_width, viewport_height = await self.call(_TARGET, isolated=True)
            await self.tab._move_mouse((x, y), min(width, height), (viewport_width, viewport_height))
            if await self.call(_UNDER, x, y, isolated=True):
                break
        if then:
            await self.tab._perform({"type": "pointer", "id": "mouse", "parameters": {"pointerType": "mouse"}, "actions": then})

    async def _bring_into_view(self) -> None:
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
