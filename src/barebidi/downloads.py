import asyncio
import shutil
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .browser import Browser
    from .tab import Tab


class Download:
    """A file the browser is downloading; path() waits for it to finish."""

    def __init__(self, tab: "Tab", params: dict):
        self.tab = tab
        self.url: str = params["url"]
        self.suggested_filename: str = params.get("suggestedFilename", "")
        self._finished: asyncio.Future[Path | None] = asyncio.get_running_loop().create_future()

    def __repr__(self) -> str:
        return f"<Download {self.suggested_filename or self.url}>"

    async def path(self, timeout: float = 120.0) -> Path:
        """Where the finished file is."""
        try:
            path = await asyncio.wait_for(asyncio.shield(self._finished), timeout)
        except TimeoutError:
            raise TimeoutError(f"{self!r} didn't finish within {timeout}s") from None
        if path is None:
            raise RuntimeError(f"{self!r} was canceled")
        return path

    async def save_as(self, destination: str | Path) -> Path:
        """Copy the finished file to `destination`."""
        destination = Path(destination)
        shutil.copyfile(await self.path(), destination)
        return destination


class ExpectedDownload:
    def __init__(self) -> None:
        self.download: Download | None = None


class Downloads:
    def __init__(self, browser: "Browser"):
        self.browser = browser
        self._active: dict[str, Download] = {}
        self._waiters: list[tuple[str, asyncio.Future[Download]]] = []

    def begun(self, params: dict) -> None:
        from .tab import Tab

        download = Download(Tab(self.browser, self.browser.top_level(params["context"])), params)
        self._active[_key(params)] = download
        for tab, future in self._waiters:
            if tab == download.tab.id and not future.done():
                future.set_result(download)

    def ended(self, params: dict) -> None:
        download = self._active.pop(_key(params), None)
        if download is not None and not download._finished.done():
            download._finished.set_result(Path(params["filepath"]) if params.get("status") == "complete" else None)

    @asynccontextmanager
    async def expect(self, tab: str, timeout: float) -> AsyncIterator[ExpectedDownload]:
        expected = ExpectedDownload()
        entry = (tab, asyncio.get_running_loop().create_future())
        self._waiters.append(entry)
        try:
            yield expected
            try:
                expected.download = await asyncio.wait_for(entry[1], timeout)
            except TimeoutError:
                raise TimeoutError(f"no download began within {timeout}s") from None
        finally:
            self._waiters.remove(entry)


def _key(params: dict) -> str:
    return params.get("download") or params["navigation"]
