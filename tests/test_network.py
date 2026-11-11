import asyncio

import pytest

import barebidi as nb

IMAGE_WIDTH = """new Promise(resolve => {
  const img = document.getElementById('pixel');
  if (img.complete) resolve(img.naturalWidth);
  else img.onload = img.onerror = () => resolve(img.naturalWidth);
})"""

FETCH_JSON = "(url, init) => fetch(url, init).then(r => r.json())"
DATA = {"message": "hola desde la API", "items": [1, 2, 3]}


async def until(condition, timeout=5.0):
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while not condition():
        if loop.time() > deadline:
            raise TimeoutError
        await asyncio.sleep(0.05)


async def test_images_load_normally(browser, server):
    tab = await browser.get(f"{server}/images.html")
    assert await tab.evaluate(IMAGE_WIDTH) == 1


async def test_block_by_resource_type(browser, server):
    await browser.block(resource_types=["image"])
    tab = await browser.get(f"{server}/images.html")
    assert await tab.evaluate(IMAGE_WIDTH) == 0


async def test_block_by_url_glob(tab, server):
    await tab.block("*/pixel.png")
    await tab.get(f"{server}/images.html")
    assert await tab.evaluate(IMAGE_WIDTH) == 0
    assert await tab.call_function(FETCH_JSON, "/data.json") == DATA


async def test_block_needs_a_target(tab):
    with pytest.raises(ValueError):
        await tab.block()


async def test_resource_types(tab, server):
    seen = {}
    await tab.intercept(lambda request: seen.setdefault(request.url.removeprefix(server), request.resource_type))
    await tab.get(f"{server}/images.html")
    await tab.call_function(FETCH_JSON, "/data.json")
    assert seen["/images.html"] == "document"
    assert seen["/pixel.png"] == "image"
    assert seen["/data.json"] == "fetch"


async def test_modify_request_headers(tab):
    async def add_header(request):
        await request.continue_(headers={**request.headers, "x-injected": "yes"})

    await tab.intercept(add_header, "/echo")
    echoed = await tab.call_function(FETCH_JSON, "/echo")
    assert echoed["headers"]["x-injected"] == "yes"
    assert echoed["headers"]["user-agent"].startswith("Mozilla/5.0")


async def test_rewrite_method_and_body(tab):
    async def to_post(request):
        await request.continue_(method="POST", body="hola", headers={**request.headers, "content-type": "text/plain"})

    await tab.intercept(to_post, "/echo")
    echoed = await tab.call_function(FETCH_JSON, "/echo")
    assert (echoed["method"], echoed["body"]) == ("POST", "hola")


async def test_fulfill_without_server(tab):
    async def mock(request):
        await request.fulfill('{"mocked": true}', headers={"content-type": "application/json"})

    await tab.intercept(mock, "/does-not-exist")
    assert await tab.call_function(FETCH_JSON, "/does-not-exist") == {"mocked": True}


async def test_abort(tab):
    async def fail(request):
        await request.abort()

    await tab.intercept(fail, "/data.json")
    assert await tab.evaluate("fetch('/data.json').then(() => 'loaded', error => error.name)") == "TypeError"


async def test_undecided_requests_continue(tab, server):
    seen = []
    await tab.intercept(lambda request: seen.append(request.url))
    await tab.get(f"{server}/second.html")
    assert await tab.title() == "Second page"
    assert f"{server}/second.html" in seen


async def test_failing_handler_does_not_hang_the_page(tab, server):
    def broken(request):
        raise RuntimeError("boom")

    await tab.intercept(broken)
    await tab.get(f"{server}/second.html")
    assert await tab.title() == "Second page"


async def test_handlers_chain_until_one_decides(tab):
    seen = []

    async def mock(request):
        seen.append("second")
        await request.fulfill("{}")

    await tab.intercept(lambda request: "/data.json" in request.url and seen.append("first"))
    await tab.intercept(mock, "/data.json")
    assert await tab.call_function(FETCH_JSON, "/data.json") == {}
    assert seen == ["first", "second"]


async def test_remove_intercept(tab):
    async def fail(request):
        await request.abort()

    intercept = await tab.intercept(fail, "/data.json")
    await intercept.remove()
    assert await tab.call_function(FETCH_JSON, "/data.json") == DATA


async def test_response_phase_modify_headers(tab):
    statuses = []

    async def add_header(request):
        statuses.append(request.response.status)
        await request.continue_(headers={**request.response.headers, "x-added": "1"})

    await tab.intercept(add_header, "/data.json", phase="response")
    assert await tab.evaluate("fetch('/data.json').then(r => r.headers.get('x-added'))") == "1"
    assert statuses == [200]


async def test_set_extra_headers(tab):
    await tab.set_extra_headers({"X-Extra": "1"})
    echoed = await tab.call_function(FETCH_JSON, "/echo")
    assert echoed["headers"]["x-extra"] == "1"


async def test_expect_response(tab):
    async with tab.expect_response("/data.json") as expected:
        await tab.evaluate("fetch('/data.json')")
    response = expected.response
    assert response.status == 200
    assert response.request.method == "GET"
    assert response.headers["content-type"] == "application/json"
    assert await response.json() == DATA
    assert "hola" in await response.text()


async def test_expect_response_during_navigation(tab, server):
    async with tab.expect_response("*/pixel.png") as expected:
        await tab.get(f"{server}/images.html")
    assert (await expected.response.body()).startswith(b"\x89PNG")


async def test_expect_response_with_predicate(tab):
    async with tab.expect_response(lambda response: response.status == 404) as expected:
        await tab.evaluate("fetch('/missing')")
    assert expected.response.url.endswith("/missing")


async def test_expect_response_timeout(tab):
    with pytest.raises(TimeoutError):
        async with tab.expect_response("/never", timeout=0.3):
            pass


async def test_iframe_responses_belong_to_their_tab(tab):
    async with tab.expect_response("/second.html") as expected:
        await tab.evaluate("document.body.append(Object.assign(document.createElement('iframe'), {src: '/second.html'}))")
    assert expected.response.request.tab == tab
    assert expected.response.request.context != tab.id


async def test_on_response_collects_bodies(tab):
    bodies = []

    async def collect(response):
        bodies.append(await response.json())

    stop = await tab.on_response(collect, "/data.json")
    await tab.evaluate("fetch('/data.json', {cache: 'no-store'})")
    await tab.evaluate("fetch('/data.json?again', {cache: 'no-store'})")
    await until(lambda: len(bodies) == 2)
    stop()
    await tab.evaluate("fetch('/data.json?ignored', {cache: 'no-store'})")
    await asyncio.sleep(0.2)
    assert bodies == [DATA, DATA]
