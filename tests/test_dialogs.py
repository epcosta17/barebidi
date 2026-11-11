import pytest

import barebidi as nb


@pytest.fixture
async def page(browser, server):
    return await browser.get(f"{server}/dialogs.html")


async def press(tab: "nb.Tab", button: str) -> None:
    await (await tab.select(f"#{button}")).click()


async def result(tab: "nb.Tab", name: str) -> str | None:
    return await tab.evaluate(f"document.body.dataset.{name}")


async def test_alert_is_closed_by_default(page):
    await press(page, "alert")
    assert await result(page, "alert") == "closed"


async def test_confirm_and_prompt_are_dismissed_by_default(page):
    await press(page, "confirm")
    await press(page, "prompt")
    assert await result(page, "confirm") == "false"
    assert await result(page, "prompt") == "null"


async def test_scripts_are_not_stuck_behind_a_dialog(page):
    assert await page.evaluate("alert('hola'), 'después'") == "después"


async def test_dialog_handler_answers_a_prompt(page):
    seen = []

    async def answer(dialog: "nb.Dialog") -> None:
        seen.append((dialog.type, dialog.message, dialog.default_value, dialog.tab))
        await dialog.accept("Beto")

    await page.on_dialog(answer)
    await press(page, "prompt")
    assert seen == [("prompt", "¿nombre?", "ana", page)]
    assert await result(page, "prompt") == "Beto"


async def test_stopped_handler_leaves_the_default(page):
    stop = await page.on_dialog(lambda dialog: dialog.accept())
    stop()
    await press(page, "confirm")
    assert await result(page, "confirm") == "false"


async def test_browser_handler_covers_every_tab(browser, server):
    await browser.on_dialog(lambda dialog: dialog.accept())
    tab = await browser.new_tab(f"{server}/dialogs.html")
    await press(tab, "confirm")
    assert await result(tab, "confirm") == "true"


async def test_dialogs_take_a_person_s_time(page):
    await press(page, "timed")
    assert float(await result(page, "waited")) >= 400


async def test_dialogs_are_instant_without_humanize(server):
    async with nb.Browser(headless=True, humanize=False) as browser:
        tab = await browser.get(f"{server}/dialogs.html")
        await press(tab, "timed")
        assert float(await result(tab, "waited")) < 400


async def test_leaving_a_guarded_page(page, server):
    await press(page, "guard")  # the click is also the user activation beforeunload prompts need
    await page.get(f"{server}/second.html")
    assert (await page.url()).endswith("/second.html")
