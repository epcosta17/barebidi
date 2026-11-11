import base64
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from . import human
from .frame import SANDBOX, Frame, JavaScriptError

if TYPE_CHECKING:
    from .connection import Handler
    from .dialogs import DialogHandler
    from .downloads import ExpectedDownload
    from .network import ExpectedResponse, Intercept, InterceptHandler, Phase, ResponseHandler, ResponseMatch

__all__ = ["SANDBOX", "JavaScriptError", "Tab"]

Wait = Literal["none", "interactive", "complete"]


class Tab(Frame):
    """A browser tab: its page (all of Frame), plus navigation, the mouse wheel, screenshots, events and network."""

    async def get(self, url: str, wait: Wait = "complete", timeout: float | None = None) -> "Tab":
        """Navigate and wait for the page to reach `wait`, at most `timeout` seconds (the browser's by default)."""
        await self.send("browsingContext.navigate", {"context": self.id, "url": url, "wait": wait}, timeout)
        return self

    async def reload(self, wait: Wait = "complete", timeout: float | None = None) -> "Tab":
        """Reload the page and wait for it like get() does."""
        await self.send("browsingContext.reload", {"context": self.id, "wait": wait}, timeout)
        return self

    async def back(self) -> None:
        """Go back one page in the tab's history."""
        await self.send("browsingContext.traverseHistory", {"context": self.id, "delta": -1})

    async def forward(self) -> None:
        """Go forward one page in the tab's history."""
        await self.send("browsingContext.traverseHistory", {"context": self.id, "delta": 1})

    async def activate(self) -> None:
        """Bring the tab to the front."""
        await self.send("browsingContext.activate", {"context": self.id})

    async def close(self) -> None:
        """Close the tab."""
        await self.send("browsingContext.close", {"context": self.id})

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
        """PNG of what's on screen, or of the whole page with `full_page`; also saved to `path` if given."""
        params = {"context": self.id, "origin": "document" if full_page else "viewport"}
        return _save_png(await self.send("browsingContext.captureScreenshot", params), path)

    async def on(self, event: str, handler: "Handler") -> str:
        """Like Browser.on, passing only the events of this tab and its iframes."""

        def scoped(params: dict) -> Any:
            context = params.get("context")
            if context is None or self.browser.top_level(context) == self.id:
                return handler(params)

        return await self.browser.on(event, scoped, contexts=[self.id])

    async def on_dialog(self, handler: "DialogHandler") -> Callable[[], None]:
        """Call `handler` with each dialog this tab opens (alert, confirm, prompt, "leave page?"); it answers
        with dialog.accept() or dialog.dismiss(). Returns a function that stops it.

        Unanswered dialogs get what Firefox does on its own: alerts and "leave page?" accepted, confirms and
        prompts dismissed; when humanized, after the time a person takes to read them.
        """
        return self.browser._dialogs.add(handler, self.id)

    def expect_download(self, timeout: float = 30.0) -> AbstractAsyncContextManager["ExpectedDownload"]:
        """Wait for a download started inside the block:

        async with tab.expect_download() as expected:
            await link.click()
        path = await expected.download.path()
        """
        return self.browser._downloader.expect(self.id, timeout)

    async def intercept(self, handler: "InterceptHandler", url: str | None = None, phase: "Phase" = "request") -> "Intercept":
        """Like Browser.intercept, for this tab's requests (iframes included)."""
        return await self.browser._network.intercept(handler, url, phase, contexts=[self.id])

    async def block(self, *urls: str, resource_types: tuple[str, ...] | list[str] = ()) -> "Intercept":
        """Like Browser.block, for this tab's requests."""
        return await self.browser._network.block(urls, resource_types, contexts=[self.id])

    async def set_extra_headers(self, headers: dict[str, str]) -> None:
        """Like Browser.set_extra_headers, for this tab's requests."""
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


def _save_png(result: dict, path: str | Path | None) -> bytes:
    data = base64.b64decode(result["data"])
    if path is not None:
        Path(path).write_bytes(data)
    return data
