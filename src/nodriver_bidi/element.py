from pathlib import Path
from typing import TYPE_CHECKING, Any

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

    async def call(self, function: str, *args: Any) -> Any:
        """Run `function` in the page with `this` bound to this element."""
        return await self.tab.call_function(function, *args, this=self)

    async def text(self) -> str:
        return await self.call("function() { return this.textContent }")

    async def inner_text(self) -> str:
        return await self.call("function() { return this.innerText }")

    async def html(self) -> str:
        return await self.call("function() { return this.outerHTML }")

    async def get_attribute(self, name: str) -> str | None:
        return await self.call("function(n) { return this.getAttribute(n) }", name)

    async def get_property(self, name: str) -> Any:
        return await self.call("function(n) { return this[n] }", name)

    async def scroll_into_view(self) -> None:
        await self.call("function() { this.scrollIntoView({block: 'center', inline: 'center'}) }")

    async def click(self) -> None:
        await self.scroll_into_view()
        await self._perform(
            {
                "type": "pointer",
                "id": "mouse",
                "parameters": {"pointerType": "mouse"},
                "actions": [
                    {"type": "pointerMove", "x": 0, "y": 0, "origin": {"type": "element", "element": self.reference}},
                    {"type": "pointerDown", "button": 0},
                    {"type": "pointerUp", "button": 0},
                ],
            }
        )

    async def type(self, text: str) -> None:
        await self.click()
        actions = []
        for char in text:
            key = KEYS["Enter"] if char == "\n" else char
            actions += [{"type": "keyDown", "value": key}, {"type": "keyUp", "value": key}]
        await self._perform({"type": "key", "id": "keyboard", "actions": actions})

    async def press(self, key: str) -> None:
        value = KEYS.get(key, key)
        await self._perform(
            {"type": "key", "id": "keyboard", "actions": [{"type": "keyDown", "value": value}, {"type": "keyUp", "value": value}]}
        )

    async def clear(self) -> None:
        await self.call("function() { this.value = ''; this.dispatchEvent(new Event('input', {bubbles: true})) }")

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

    async def _perform(self, source: dict) -> None:
        await self.tab.send("input.performActions", {"context": self.tab.id, "actions": [source]})
