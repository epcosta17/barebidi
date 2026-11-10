import asyncio
import contextlib
import time

import pytest

import nodriver_bidi as nb
from conftest import LOCAL_PROXY_PREFS

ECHO = "() => fetch('/echo').then(r => r.json())"

REGION = """async () => {
  const read = () => ({language: navigator.language, timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone});
  const worker = new Worker(URL.createObjectURL(new Blob([`postMessage((${read})())`])));
  const inWorker = await new Promise(resolve => { worker.onmessage = event => resolve(event.data); });
  const echo = await fetch('/echo').then(r => r.json());
  return {page: read(), worker: inWorker, acceptLanguage: echo.headers['accept-language']};
}"""


def with_credentials(proxy, credentials="user:secret"):
    return proxy.url.replace("http://", f"http://{credentials}@")


async def proxy_name(tab):
    return (await tab.call_function(ECHO))["headers"].get("x-via-proxy")


async def test_browser_proxy(server, proxy):
    async with nb.Browser(headless=True, proxy=proxy.url, prefs=LOCAL_PROXY_PREFS) as browser:
        tab = await browser.get(f"{server}/index.html")
        assert await proxy_name(tab) == "open"
    assert f"{server}/index.html" in proxy.requests


async def test_proxy_credentials(server, auth_proxy):
    async with nb.Browser(headless=True, proxy=with_credentials(auth_proxy), prefs=LOCAL_PROXY_PREFS) as browser:
        tab = await browser.get(f"{server}/index.html")
        assert await tab.title() == "Test page"
        assert await proxy_name(tab) == "auth"


async def test_wrong_credentials_give_up(server, auth_proxy):
    async with nb.Browser(headless=True, proxy=with_credentials(auth_proxy, "user:wrong"), prefs=LOCAL_PROXY_PREFS) as browser:
        tab = (await browser.tabs())[0]
        with contextlib.suppress(nb.BidiError):
            await asyncio.wait_for(tab.get(f"{server}/index.html"), 10)
    assert auth_proxy.requests == []


async def test_contexts_have_their_own_proxy(server, proxy, auth_proxy):
    async with nb.Browser(headless=True, prefs=LOCAL_PROXY_PREFS) as browser:
        open_context = await browser.new_context(proxy=proxy.url)
        auth_context = await browser.new_context(proxy=with_credentials(auth_proxy))
        assert await proxy_name(await open_context.new_tab(f"{server}/index.html")) == "open"
        assert await proxy_name(await auth_context.new_tab(f"{server}/index.html")) == "auth"
        assert await proxy_name(await browser.get(f"{server}/index.html")) is None


async def test_locale_and_timezone(server):
    async with nb.Browser(headless=True, locale="de-DE", timezone="Europe/Berlin") as browser:
        region = await (await browser.get(f"{server}/index.html")).call_function(REGION)
    expected = {"language": "de-DE", "timeZone": "Europe/Berlin"}
    assert region == {"page": expected, "worker": expected, "acceptLanguage": "de-DE"}


async def test_context_region_is_isolated(browser, server):
    context = await browser.new_context(locale="ja-JP", timezone="Asia/Tokyo")
    region = await (await context.new_tab(f"{server}/index.html")).call_function(REGION)
    assert region["page"] == region["worker"] == {"language": "ja-JP", "timeZone": "Asia/Tokyo"}
    assert region["acceptLanguage"] == "ja-JP"
    default = await (await browser.get(f"{server}/index.html")).call_function(REGION)
    assert default["page"]["language"] != "ja-JP"


async def test_cookies_roundtrip(browser, tab):
    await tab.evaluate("document.cookie = 'from_page=1; path=/'")
    assert [(c["name"], c["value"]) for c in await browser.cookies()] == [("from_page", "1")]
    await browser.set_cookies([{"name": "from_python", "value": "2", "domain": "127.0.0.1", "path": "/"}])
    assert "from_python=2" in await tab.evaluate("document.cookie")
    await browser.clear_cookies()
    assert await browser.cookies() == []


async def test_saved_cookies_load_back(browser, tab):
    await tab.evaluate("document.cookie = 'session=abc; path=/; max-age=3600'")
    saved = await browser.cookies()
    await browser.clear_cookies()
    await browser.set_cookies(saved)
    assert await browser.cookies() == saved


async def test_cookies_are_per_context(browser, tab, server):
    context = await browser.new_context()
    await context.set_cookies([{"name": "secret", "value": "x", "domain": "127.0.0.1", "path": "/"}])
    assert [c["name"] for c in await context.cookies()] == ["secret"]
    assert await browser.cookies() == []
    assert await tab.evaluate("document.cookie") == ""
    assert await (await context.new_tab(f"{server}/index.html")).evaluate("document.cookie") == "secret=x"


async def test_persistent_profile(tmp_path):
    profile = tmp_path / "profile"
    cookie = {"name": "login", "value": "ok", "domain": "127.0.0.1", "path": "/", "expiry": int(time.time()) + 3600}
    async with nb.Browser(headless=True, profile=profile) as browser:
        await browser.set_cookies([cookie])
    assert profile.is_dir()
    async with nb.Browser(headless=True, profile=profile) as browser:
        assert [(c["name"], c["value"]) for c in await browser.cookies()] == [("login", "ok")]


async def test_close_context(browser, server):
    context = await browser.new_context()
    tab = await context.new_tab(f"{server}/index.html")
    assert tab in await context.tabs()
    await context.close()
    assert tab not in await browser.tabs()
    with pytest.raises(ValueError):
        await browser.context.close()


def test_proxy_validation():
    for bad in ("ftp://host:21", "http://host", "socks5://user:pass@host:1080"):
        with pytest.raises(ValueError):
            nb.Browser(proxy=bad)
    socks = nb.Browser(proxy="socks5://127.0.0.1:1080")
    assert socks.prefs["network.proxy.socks_version"] == 5
    assert socks.prefs["network.proxy.socks5_remote_dns"] is True
    assert nb.Browser().prefs["network.proxy.type"] == 5


GEOMETRY = """() => ({screen: [screen.width, screen.height],
  avail: [screen.availLeft, screen.availTop, screen.availWidth, screen.availHeight],
  outer: [screenX, screenY, outerWidth, outerHeight], inner: [innerWidth, innerHeight]})"""


def assert_window_fits(geometry):
    left, top, avail_width, avail_height = geometry["avail"]
    x, y, width, height = geometry["outer"]
    assert left <= x and top <= y and x + width <= left + avail_width and y + height <= top + avail_height
    assert geometry["inner"][0] == width and 0 < geometry["inner"][1] < height


async def test_headless_window_fits_the_screen(browser):
    tab = await browser.get("data:text/html,<body>x</body>")
    geometry = await tab.call_function(GEOMETRY)
    assert geometry["screen"] == [1920, 1080]
    assert_window_fits(geometry)
    assert geometry["outer"][2:] == geometry["avail"][2:]


async def test_custom_screen():
    async with nb.Browser(headless=True, screen=(1366, 768)) as browser:
        geometry = await (await browser.get("data:text/html,<body>x</body>")).call_function(GEOMETRY)
    assert geometry["screen"] == [1366, 768]
    assert_window_fits(geometry)


def test_screen_needs_headless():
    with pytest.raises(ValueError):
        nb.Browser(screen=(1920, 1080))
