import asyncio
import math
import statistics

import pytest

import barebidi as nb
from barebidi import human

RECT = "function () { const r = this.getBoundingClientRect(); return [r.left, r.top, r.width, r.height] }"


@pytest.fixture
async def page(browser, server):
    return await browser.get(f"{server}/behavior.html")


def straightness_gap(path, start, end):
    (x0, y0), (x1, y1) = start, end
    return max(abs((x1 - x0) * (y0 - y) - (x0 - x) * (y1 - y0)) / math.dist(start, end) for x, y, _ in path)


def test_mouse_paths_curve_and_ease_in_and_out():
    start, end = (100, 600), (900, 200)
    curved, edge_speeds, middle_speeds = 0, [], []
    for _ in range(200):
        path = human.mouse_path(start, end, 40, (1920, 1080))
        assert path[-1][:2] == end
        assert 150 < sum(ms for *_, ms in path) < 2500
        curved += straightness_gap(path, start, end) > 0.02 * math.dist(start, end)
        points = [start, *(p[:2] for p in path)]
        speeds = [math.dist(a, b) / max(ms, 1) for a, b, (*_, ms) in zip(points, points[1:], path)]
        third = len(speeds) // 3
        edge_speeds.append(statistics.mean(speeds[:third]))
        middle_speeds.append(statistics.mean(speeds[third : 2 * third]))
    assert curved > 180
    assert statistics.mean(middle_speeds) > 1.5 * statistics.mean(edge_speeds)


def test_mouse_paths_stay_in_the_viewport():
    for _ in range(100):
        for x, y, _ in human.mouse_path((5, 5), (60, 700), 20, (800, 720)):
            assert 0 <= x < 800 and 0 <= y < 720


def test_typing_rhythm_varies():
    strokes = human.keystrokes("el veloz murcielago hindu comia feliz cardillo y kiwi " * 2)
    pauses = [pause for _, _, pause in strokes]
    assert 70 < statistics.mean(pauses) < 300 and statistics.stdev(pauses) > 20
    assert all(45 <= hold <= 115 for _, hold, _ in strokes)


async def test_click_travels_to_the_element(page):
    field = await page.select("#field")
    await field.click()
    events = await page.evaluate("window.events")
    assert all(event["trusted"] for event in events)
    kinds = [event["type"] for event in events]
    down, up = events[kinds.index("mousedown")], events[kinds.index("mouseup")]
    assert kinds[: kinds.index("mousedown")].count("mousemove") >= 8
    assert up["t"] - down["t"] >= 30
    left, top, width, height = await field.call(RECT)
    assert left <= down["x"] <= left + width and top <= down["y"] <= top + height


async def test_typing_like_a_person(page):
    field = await page.select("#field")
    await field.type("Hola Mundo!")
    assert await field.get_property("value") == "Hola Mundo!"
    keys = [e for e in await page.evaluate("window.events") if e["type"] in ("keydown", "keyup")]
    downs = [e for e in keys if e["type"] == "keydown" and e["key"] != "Shift"]
    gaps = [b["t"] - a["t"] for a, b in zip(downs, downs[1:])]
    assert statistics.mean(gaps) > 80 and statistics.stdev(gaps) > 10
    assert all(next(e for e in downs if e["key"] == char)["shift"] for char in "HM!")
    assert not next(e for e in downs if e["key"] == "o")["shift"]
    assert any(e["key"] == "Shift" for e in keys)
    for down in downs:
        up = next(e for e in keys if e["type"] == "keyup" and e["key"] == down["key"] and e["t"] >= down["t"])
        assert up["t"] - down["t"] >= 30


async def test_click_scrolls_with_the_wheel(page):
    far = await page.select("#far")
    await far.click()
    assert await far.get_attribute("data-clicked") == "yes"
    events = await page.evaluate("window.events")
    assert sum(event["type"] == "wheel" for event in events) >= 10
    assert await page.evaluate("scrollY") > 2000


async def test_scroll_in_wheel_notches(page):
    await page.scroll(600)
    await asyncio.sleep(0.5)
    assert sum(event["type"] == "wheel" for event in await page.evaluate("window.events")) >= 4
    assert await page.evaluate("scrollY") > 400


async def test_hover_moves_without_clicking(page):
    await (await page.select("#field")).hover()
    kinds = {event["type"] for event in await page.evaluate("window.events")}
    assert {"mousemove", "mouseover"} <= kinds and "mousedown" not in kinds


async def test_humanize_off_is_direct(server):
    async with nb.Browser(headless=True, humanize=False) as browser:
        page = await browser.get(f"{server}/behavior.html")
        field = await page.select("#field")
        await field.type("Fast")
        assert await field.get_property("value") == "Fast"
        events = await page.evaluate("window.events")
    assert sum(event["type"] == "mousemove" for event in events) <= 2
    downs = [event["t"] for event in events if event["type"] == "keydown" and event["key"] != "Shift"]
    assert downs[-1] - downs[0] < 100
