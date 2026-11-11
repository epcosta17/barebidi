import logging

import pytest

import barebidi as nb

FALLBACK = "inside the frame"


@pytest.fixture
async def page(browser, server, caplog):
    caplog.set_level(logging.INFO, logger="barebidi")
    return await browser.get(f"{server}/frames.html")


async def checkbox_in(frame: "nb.Frame") -> "nb.Element":
    root = await (await frame.select("#widget")).shadow_root()
    return await root.select("input[type=checkbox]")


async def test_frames_lists_every_iframe(page):
    urls = sorted([await frame.url() for frame in await page.frames()])
    assert [url.rsplit("#", 1)[1] for url in urls] == ["cube", "plain", "shadow"]
    assert all(url.startswith("http://localhost:") for url in urls)


async def test_frame_by_url_runs_scripts_in_its_document(page):
    frame = await page.frame("#shadow")
    assert isinstance(frame, nb.Frame)
    assert await frame.evaluate("location.hash") == "#shadow"


async def test_frame_by_url_times_out(page):
    with pytest.raises(TimeoutError):
        await page.frame("missing.html", timeout=0.3)


async def test_select_in_frame(page):
    frame = await page.frame("#plain")
    field = await frame.select("#name")
    assert field.frame == frame and field.tab == page
    assert await field.call("function() { return location.hash }", isolated=True) == "#plain"


async def test_closed_shadow_root(page):
    frame = await page.frame("#plain")
    checkbox = await checkbox_in(frame)
    assert await checkbox.get_property("type") == "checkbox"
    assert await (await frame.select("#name")).shadow_root() is None


async def test_content_frame_of_iframe_in_closed_shadow_root(page):
    root = await (await page.select("#host")).shadow_root()
    frame = await (await root.select("iframe")).content_frame()
    assert (await frame.url()).endswith("#shadow")


async def test_windows_from_scripts_become_frames(page):
    frame = await page.evaluate("document.getElementById('plain').contentWindow")
    assert isinstance(frame, nb.Frame) and (await frame.url()).endswith("#plain")
    assert await page.evaluate("window") == page


async def test_click_in_cross_site_frame_below_the_fold(page, caplog):
    frame = await page.frame("#plain")
    await (await checkbox_in(frame)).click()
    assert await frame.evaluate("checked()") is True
    events = await frame.evaluate("events")
    kinds = [kind for kind, _ in events]
    assert kinds.count("mousemove") >= 3 and kinds.index("mousemove") < kinds.index("mousedown")
    assert all(trusted for _, trusted in events)
    assert FALLBACK not in caplog.text  # the pointer got there through the page, like a real mouse


async def test_click_in_frame_inside_closed_shadow_root(page):
    frame = await page.frame("#shadow")
    await (await checkbox_in(frame)).click()
    assert await frame.evaluate("checked()") is True
    # Over the iframe the pointer's events belong to its document: the page only sees it enter.
    page_events = await page.evaluate("events")
    assert ["mouseover", "host"] in page_events and ["mousemove", "host"] not in page_events


async def test_type_in_frame(page):
    frame = await page.frame("#shadow")
    field = await frame.select("#name")
    await field.type("hola")
    assert await field.get_property("value") == "hola"


async def test_click_in_frame_on_animated_3d_cube(page, caplog):
    # Firefox doesn't route pointer events into an iframe on a 3D transform under a CSS animation (as on
    # nowsecure.nl), so the click is dispatched inside the frame's document.
    frame = await page.frame("#cube")
    await (await checkbox_in(frame)).click()
    assert await frame.evaluate("checked()") is True
    assert FALLBACK in caplog.text


async def test_pointer_is_routed_again_after_an_animated_3d_frame(page):
    await (await checkbox_in(await page.frame("#cube"))).click()
    await page.evaluate("events.length = 0")
    await (await checkbox_in(await page.frame("#shadow"))).click()
    assert ["mousemove", "host"] not in await page.evaluate("events")
