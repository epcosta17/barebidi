import asyncio
import inspect
import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from . import human

if TYPE_CHECKING:
    from .browser import Browser
    from .tab import Tab

log = logging.getLogger(__name__)

DialogHandler = Callable[["Dialog"], Awaitable[None] | None]


class Dialog:
    """A JavaScript dialog waiting for an answer: an alert, confirm, prompt or "leave this page?" (beforeunload)."""

    def __init__(self, tab: "Tab", params: dict):
        self.tab = tab
        self.type: str = params["type"]
        self.message: str = params.get("message", "")
        self.default_value: str | None = params.get("defaultValue")
        self.answered = False

    def __repr__(self) -> str:
        return f"<Dialog {self.type} {self.message!r}>"

    async def accept(self, text: str | None = None) -> None:
        """OK, or "Leave page"; for a prompt, with `text` typed in."""
        await self._answer(True, text)

    async def dismiss(self) -> None:
        """Cancel, or "Stay on page"."""
        await self._answer(False)

    async def _answer(self, accept: bool, text: str | None = None) -> None:
        if self.answered:
            return
        self.answered = True
        if self.tab.browser.humanize:
            await asyncio.sleep(human.dialog_time(self.message, text) / 1000)  # read it, type the answer, click
        params: dict[str, Any] = {"context": self.tab.id, "accept": accept}
        if text is not None:
            params["userText"] = text
        await self.tab.send("browsingContext.handleUserPrompt", params)


class Dialogs:
    """Hands each dialog to the handlers of its tab, then the browser's; answers what nobody did."""

    def __init__(self, browser: "Browser"):
        self.browser = browser
        self._handlers: list[tuple[str | None, DialogHandler]] = []

    def add(self, handler: DialogHandler, tab: str | None = None) -> Callable[[], None]:
        entry = (tab, handler)
        self._handlers.append(entry)

        def remove() -> None:
            if entry in self._handlers:
                self._handlers.remove(entry)

        return remove

    async def opened(self, params: dict) -> None:
        from .tab import Tab

        tab = Tab(self.browser, self.browser.top_level(params["context"]))
        dialog = Dialog(tab, params)
        handlers = [h for owner, h in self._handlers if owner == tab.id] + [h for owner, h in self._handlers if owner is None]
        for handler in handlers:
            try:
                result = handler(dialog)
                if inspect.isawaitable(result):
                    await result
            except Exception:
                log.exception("dialog handler failed on %r", dialog)
            if dialog.answered:
                return
        # What Firefox does when nobody answers: alerts and "leave page?" accepted, the rest dismissed.
        if dialog.type in ("alert", "beforeunload"):
            await dialog.accept()
        else:
            await dialog.dismiss()
