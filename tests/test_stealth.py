import pytest

import barebidi as nb
import barebidi.browser as browser_module

NATIVE_GETTER = "function webdriver() {\n    [native code]\n}"
NATIVE_TO_STRING = "function toString() {\n    [native code]\n}"


@pytest.fixture(params=["native", "preload-fallback"])
async def page(request, server, monkeypatch):
    if request.param == "preload-fallback":
        monkeypatch.setattr(browser_module, "CLEAR_AUTOMATION_FLAG", "undefined")
    async with nb.Browser(headless=True) as browser:
        yield await browser.get(f"{server}/stealth.html")


async def test_native_mode_leaves_no_trace(browser, server):
    tab = await browser.get(f"{server}/stealth.html")
    same_depth = await tab.evaluate(
        """(() => {
          const get = Object.getOwnPropertyDescriptor(Navigator.prototype, 'webdriver').get;
          let thrown;
          try { get.call({}); } catch (e) { thrown = e.stack; }
          return thrown.split('\\n').length === new Error().stack.split('\\n').length;
        })()"""
    )
    assert same_depth is True


async def test_webdriver_is_false(page):
    assert await page.evaluate("navigator.webdriver") is False


async def test_patched_before_page_scripts(page):
    assert await page.evaluate("window.seenAtLoad") is False


async def test_getter_looks_native(page):
    info = await page.evaluate(
        """(() => {
          const d = Object.getOwnPropertyDescriptor(Navigator.prototype, 'webdriver');
          return {
            source: Function.prototype.toString.call(d.get),
            name: d.get.name,
            length: d.get.length,
            enumerable: d.enumerable,
            configurable: d.configurable,
            noSetter: d.set === undefined,
            hasPrototype: 'prototype' in d.get,
            ownNavigatorProps: Object.getOwnPropertyNames(navigator),
            toStringSource: Function.prototype.toString.toString(),
            toStringOnItself: Function.prototype.toString.call(Function.prototype.toString),
            toStringName: Function.prototype.toString.name,
          };
        })()"""
    )
    assert info == {
        "source": NATIVE_GETTER,
        "name": "get webdriver",
        "length": 0,
        "enumerable": True,
        "configurable": True,
        "noSetter": True,
        "hasPrototype": False,
        "ownNavigatorProps": [],
        "toStringSource": NATIVE_TO_STRING,
        "toStringOnItself": NATIVE_TO_STRING,
        "toStringName": "toString",
    }


async def test_wrong_receiver_still_throws(page):
    result = await page.evaluate(
        """(() => {
          const get = Object.getOwnPropertyDescriptor(Navigator.prototype, 'webdriver').get;
          try { get.call({}); return 'no error'; } catch (e) { return e instanceof TypeError; }
        })()"""
    )
    assert result is True


async def test_iframes_are_patched_and_consistent(page):
    result = await page.evaluate(
        """(() => {
          const frame = document.createElement('iframe');
          document.body.appendChild(frame);
          const win = frame.contentWindow;
          const parentGetter = Object.getOwnPropertyDescriptor(Navigator.prototype, 'webdriver').get;
          const childGetter = Object.getOwnPropertyDescriptor(win.Navigator.prototype, 'webdriver').get;
          return {
            webdriver: win.navigator.webdriver,
            childToStringOnParentGetter: win.Function.prototype.toString.call(parentGetter),
            parentToStringOnChildGetter: Function.prototype.toString.call(childGetter),
            childToStringOnParentToString: win.Function.prototype.toString.call(Function.prototype.toString),
          };
        })()"""
    )
    assert result == {
        "webdriver": False,
        "childToStringOnParentGetter": NATIVE_GETTER,
        "parentToStringOnChildGetter": NATIVE_GETTER,
        "childToStringOnParentToString": NATIVE_TO_STRING,
    }


async def test_popups_are_patched(page):
    await (await page.select("#popup")).click()
    assert await page.evaluate("window.popup.navigator.webdriver") is False


async def test_popup_blocker_is_on(page):
    assert await page.evaluate("window.open('about:blank') === null") is True


async def test_document_has_focus(page):
    assert await page.evaluate("document.hasFocus()") is True


async def test_stealth_can_be_disabled(server):
    async with nb.Browser(headless=True, stealth=False) as browser:
        tab = await browser.get(f"{server}/stealth.html")
        assert await tab.evaluate("navigator.webdriver") is True


async def test_library_scripts_ignore_page_tampering(tab):
    await tab.evaluate("void Object.defineProperty(Node.prototype, 'textContent', {get() { return 'tampered' }})")
    assert await (await tab.select("#title")).text() == "Hello BiDi"
    assert await tab.evaluate("document.getElementById('title').textContent") == "tampered"


async def test_clear_fires_input_event(tab):
    field = await tab.select("#name")
    await field.type("abc")
    await field.clear()
    assert await field.get_property("value") == ""
    assert await field.get_attribute("data-inputs") == "4"
