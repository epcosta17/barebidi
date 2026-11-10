import base64
from collections.abc import Iterable
from typing import TYPE_CHECKING

from .tab import Tab

if TYPE_CHECKING:
    from .browser import Browser

_COOKIE_FIELDS = ("name", "domain", "path", "httpOnly", "secure", "sameSite", "expiry")


class Context:
    """An isolated identity: its own cookies and storage, optionally its own proxy, language and time zone.

    The browser's default context is the profile's; contexts from Browser.new_context() are temporary.
    """

    def __init__(self, browser: "Browser", user_context: str):
        self.browser = browser
        self.id = user_context

    def __repr__(self) -> str:
        return f"<Context {self.id}>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Context) and other.id == self.id

    def __hash__(self) -> int:
        return hash(self.id)

    async def new_tab(self, url: str | None = None, background: bool = False) -> Tab:
        result = await self.browser.connection.send(
            "browsingContext.create", {"type": "tab", "background": background, "userContext": self.id}
        )
        tab = Tab(self.browser, result["context"])
        if url:
            await tab.get(url)
        return tab

    async def tabs(self) -> list[Tab]:
        tree = await self.browser.connection.send("browsingContext.getTree", {"maxDepth": 0})
        return [Tab(self.browser, c["context"]) for c in tree["contexts"] if c.get("userContext", "default") == self.id]

    async def get(self, url: str, new_tab: bool = False) -> Tab:
        tabs = [] if new_tab else await self.tabs()
        tab = tabs[0] if tabs else await self.new_tab()
        return await tab.get(url)

    async def cookies(self, domain: str | None = None) -> list[dict]:
        params: dict = {"partition": self._partition}
        if domain:
            params["filter"] = {"domain": domain}
        result = await self.browser.connection.send("storage.getCookies", params)
        return [{**cookie, "value": _text(cookie["value"])} for cookie in result["cookies"]]

    async def set_cookies(self, cookies: Iterable[dict]) -> None:
        """Takes the dicts cookies() returns, so a saved session can be loaded back."""
        for cookie in cookies:
            fields = {key: cookie[key] for key in _COOKIE_FIELDS if cookie.get(key) is not None}
            fields["value"] = {"type": "string", "value": cookie["value"]}
            await self.browser.connection.send("storage.setCookie", {"cookie": fields, "partition": self._partition})

    async def clear_cookies(self) -> None:
        await self.browser.connection.send("storage.deleteCookies", {"partition": self._partition})

    async def close(self) -> None:
        """Close its tabs and discard its data."""
        if self.id == "default":
            raise ValueError("the default context lives as long as the browser")
        await self.browser.connection.send("browser.removeUserContext", {"userContext": self.id})
        self.browser._network.forget_proxy(self.id)

    async def _emulate(self, locale: str | None, timezone: str | None) -> None:
        # Firefox applies these to the page, its iframes and workers alike, and the locale to Accept-Language.
        if locale:
            await self.browser.connection.send("emulation.setLocaleOverride", {"locale": locale, "userContexts": [self.id]})
        if timezone:
            await self.browser.connection.send(
                "emulation.setTimezoneOverride", {"timezone": timezone, "userContexts": [self.id]}
            )

    @property
    def _partition(self) -> dict:
        # Always explicit: without a partition Firefox returns the cookies of every context.
        return {"type": "storageKey", "userContext": self.id}


def _text(value: dict) -> str:
    if value["type"] == "string":
        return value["value"]
    return base64.b64decode(value["value"]).decode("latin-1")
