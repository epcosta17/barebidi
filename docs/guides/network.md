# Network

URL patterns below are a substring of the URL, or a glob when they contain `*`
(`"https://api.example.com/*/items"`).

## Waiting for a response

```python
async with tab.expect_response("/api/items") as expected:
    await tab.find("Load more").click()
response = expected.response
print(response.status, response.url)
items = await response.json()
```

It catches the first matching response that completes from the moment the block starts; when the block's
body is done, it waits for that response (30 seconds by default, `timeout=`). `url` can also be a function
taking the `Response` and returning `True` for the one you want.

## Watching responses

```python
async def log(response):
    print(response.status, response.url)

stop = await tab.on_response(log, "/api/")
...
stop()
```

`Response` has `status`, `status_text`, `url`, `headers`, `mime_type`, `from_cache` and the `request`, plus
`await response.body()`, `.text()` and `.json()`.

## Intercepting requests

```python
async def handler(request):
    if request.resource_type == "image":
        await request.abort()
    elif "/api/config" in request.url:
        await request.fulfill('{"beta": true}', headers={"content-type": "application/json"})
    else:
        await request.continue_(headers={**request.headers, "x-debug": "1"})

intercept = await tab.intercept(handler, url="*example.com*")
...
await intercept.remove()
```

Every matching request pauses until the handler settles it with `continue_()`, `abort()` or `fulfill()`. A
request the handler leaves alone continues unchanged. `continue_()` can change the `url`, `method`,
`headers` and `body`; its `headers` replaces all of them.

With `phase="response"` the handler runs when the response arrives, before the page sees it:
`request.response` holds it, and `continue_()` can change its `status` and `headers`, or `fulfill()` replace it.

## Blocking

```python
await tab.block("*.png", "https://ads.example.com/*")
await tab.block(resource_types=["image", "font", "media"])
```

## Extra headers

```python
await tab.set_extra_headers({"Accept-Language": "de-DE"})
await tab.set_extra_headers({})      # remove them
```

The same methods exist on `Browser` (every tab) and per tab (that tab only).
