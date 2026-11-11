import math

import pytest

import barebidi as nb


async def test_session_started(browser):
    assert browser.session_id
    assert browser.capabilities["browserName"] == "firefox"


async def test_navigate(tab, server):
    assert await tab.title() == "Test page"
    assert await tab.url() == f"{server}/index.html"


async def test_evaluate_types(tab):
    value = await tab.evaluate("({a: 1, b: [1, 'x', null], c: true, d: NaN, e: 10n, f: undefined})")
    assert value["a"] == 1
    assert value["b"] == [1, "x", None]
    assert value["c"] is True
    assert math.isnan(value["d"])
    assert value["e"] == 10
    assert value["f"] is None


async def test_evaluate_awaits_promises(tab):
    assert await tab.evaluate("new Promise(r => setTimeout(() => r(42), 50))") == 42


async def test_call_function_with_args(tab):
    assert await tab.call_function("(a, b) => a.x + b", {"x": 2}, 3) == 5


async def test_javascript_error(tab):
    with pytest.raises(nb.JavaScriptError):
        await tab.evaluate("undefinedThing.foo")


async def test_evaluate_returns_element(tab):
    element = await tab.evaluate("document.querySelector('h1')")
    assert isinstance(element, nb.Element)
    assert await element.text() == "Hello BiDi"


async def test_select(tab):
    title = await tab.select("#title")
    assert title.tag == "h1"
    assert title.attrs["id"] == "title"
    assert await title.text() == "Hello BiDi"


async def test_select_all_and_nested(tab):
    items = await tab.select_all("li.item")
    assert [await i.text() for i in items] == ["one", "two", "three"]
    ul = await tab.select("#list")
    assert len(await ul.select_all("li")) == 3


async def test_select_waits_for_late_element(tab):
    late = await tab.select(".late", timeout=5)
    assert await late.text() == "late"


async def test_select_timeout(tab):
    with pytest.raises(TimeoutError):
        await tab.select(".missing", timeout=0.3)


async def test_xpath(tab):
    items = await tab.xpath("//li[@class='item']")
    assert len(items) == 3


async def test_find_by_text(tab):
    button = await tab.find("click me")
    assert button.tag == "button"


async def test_click_is_trusted(tab):
    button = await tab.select("#btn")
    await button.click()
    assert await button.get_attribute("data-trusted") == "true"
    assert await button.text() == "clicked"


async def test_type(tab):
    field = await tab.select("#name")
    await field.type("hola mundo")
    assert await field.get_property("value") == "hola mundo"


async def test_click_link_navigates(tab):
    await (await tab.select("#link")).click()
    await tab.select("p")
    assert await tab.title() == "Second page"


async def test_screenshot(tab, tmp_path):
    png = await tab.screenshot(tmp_path / "page.png")
    assert png.startswith(b"\x89PNG")
    assert (tmp_path / "page.png").read_bytes() == png
    assert (await (await tab.select("#title")).screenshot()).startswith(b"\x89PNG")


async def test_tabs(browser, server):
    first = (await browser.tabs())[0]
    second = await browser.new_tab(f"{server}/second.html")
    assert await browser.tabs() == [first, second]
    assert await second.title() == "Second page"
    await second.close()
    assert await browser.tabs() == [first]


async def test_network_events(browser, server):
    requests = []
    await browser.on("network.beforeRequestSent", lambda p: requests.append(p["request"]["url"]))
    await browser.get(f"{server}/index.html")
    assert f"{server}/index.html" in requests


async def test_console_events(tab):
    messages = []
    await tab.on("log.entryAdded", lambda p: messages.append(p["text"]))
    await tab.evaluate("console.log('desde la página')")
    await tab.evaluate("new Promise(r => setTimeout(r, 50))")
    assert "desde la página" in messages
