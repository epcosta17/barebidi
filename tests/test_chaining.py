import inspect

import nodriver_bidi as nb

SWAP = """(() => {
  const button = document.createElement('button');
  button.id = 'swap';
  button.textContent = 'swap';
  button.onclick = () => button.dataset.clicks = (+button.dataset.clicks || 0) + 1;
  document.body.prepend(button);
})()"""


async def test_find_and_click_in_one_go(tab):
    await tab.find("Click me").click()
    button = await tab.select("#btn")
    assert await button.text() == "clicked"
    assert await button.get_attribute("data-trusted") == "true"  # a real, humanized click


async def test_select_and_type_in_one_go(tab):
    await tab.select("#name").type("hola")
    assert await (await tab.select("#name")).get_property("value") == "hola"


async def test_select_inside_an_element_in_one_go(tab):
    await tab.select("body").select("#btn").click()
    assert await (await tab.select("#btn")).text() == "clicked"


async def test_awaiting_still_gives_the_element(tab):
    element = await tab.select("#btn")
    assert isinstance(element, nb.Element) and element.attrs["id"] == "btn"
    assert isinstance(await tab.find("Click me"), nb.Element)


async def test_each_action_finds_the_element_again(tab):
    # The page may redraw the element between two actions; acting on the old one would hit nothing.
    await tab.evaluate(SWAP)
    swap = tab.select("#swap")
    await swap.click()
    await tab.evaluate("document.getElementById('swap').remove()")
    await tab.evaluate(SWAP)
    await swap.click()
    assert await (await tab.select("#swap")).get_attribute("data-clicks") == "1"


def test_every_element_action_can_be_chained():
    actions = {name for name, member in inspect.getmembers(nb.Element) if not name.startswith("_") and inspect.iscoroutinefunction(member)}
    missing = {name for name in actions if not inspect.iscoroutinefunction(getattr(nb.ElementQuery, name, None))}
    assert not missing
