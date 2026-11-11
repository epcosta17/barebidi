# Iframes and shadow roots

## Iframes

Each iframe is a `Frame`, with the same lookup and JavaScript methods as a tab:

```python
# the first iframe whose URL contains this; waits for it
frame = await tab.frame("widget.example.org")
await frame.select("button").click()
print(await frame.evaluate("document.title"))

# every iframe, nested ones included
for f in await tab.frames():
    print(await f.url())
```

`frame(url)` takes a substring of the iframe's URL, or a glob with `*`, and searches nested iframes too.

From the `<iframe>` element itself:

```python
iframe = await tab.select("iframe#payment")
frame = await iframe.content_frame()
```

Cross-site iframes (a different domain from the page) work the same way. Scripts in the page can't reach
into them, but barebidi talks to each frame directly, and its clicks travel through the page into the frame
like a real mouse's.

## Shadow roots

```python
host = await tab.select("my-component")
root = await host.shadow_root()
await root.select("input").type("hello")
```

`shadow_root()` returns the shadow root as an element you can search inside, or `None` if there is none.
It works for **closed** shadow roots too, the ones `element.shadowRoot` returns `null` for in page scripts.

Combining both, e.g. a checkbox inside a closed shadow root inside a cross-site iframe:

```python
frame = await tab.frame("challenges.example.com")
root = await (await frame.select("body")).shadow_root()
await root.select("input[type=checkbox]").click()
```
