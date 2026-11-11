BAREBIDI
========

### Async Firefox automation for Python, speaking WebDriver BiDi straight to the browser

**[Documentation](https://barebidi.readthedocs.io)** · **[GitHub](https://github.com/epcosta17/barebidi)** · **[PyPI](https://pypi.org/project/barebidi/)**

https://github.com/user-attachments/assets/3df66962-4ffc-43e8-b46e-d9f661dd7d90

*The demo: regular Firefox from Mozilla, driven by barebidi through public bot-detection test pages.*

- **built for Firefox**: the regular Firefox you download from Mozilla, nothing patched
- no driver binaries: no geckodriver, no Selenium
- no Playwright-style browser builds: it drives the Firefox you already have
- one dependency: `websockets`

WebDriver BiDi is the W3C standard for browser automation, the successor of both classic WebDriver and the
Chrome DevTools Protocol. Firefox speaks it natively: barebidi opens a websocket to Firefox and talks to it
directly, so there is nothing in between to install, keep in sync or get detected.

Most automation tools are Chrome-first and treat Firefox as an afterthought. barebidi is the other way
around: every feature is built and tested against Firefox, including its quirks with cross-site iframes,
closed shadow roots and input routing. Chrome support may come later; Firefox is the point.

### Some features

- `tab.select(css)`, `tab.find(text)`, `tab.xpath(expr)`, all waiting until the element appears
- chainable queries: `await tab.select("form").select("button").click()`
- mouse and keyboard input with human timings and trajectories, on by default; with
  `pip install "barebidi[cursory]"`, mouse movements replayed from recordings of real people
- elements inside cross-site iframes and closed shadow roots, the ones scripts can't reach
- proxies with credentials (no password prompt), plus per-context locale and time zone
- isolated browser contexts: separate cookies, storage and proxy in one browser
- network: intercept, block or modify requests, wait for responses, extra headers
- dialogs (alert, confirm, prompt), file uploads and downloads
- cookies: read, set, clear
- every protocol type generated from the spec's CDDL, so your editor knows the shape of every message

# Installation

barebidi needs Firefox installed, from Mozilla (on Ubuntu, not the snap). It finds it in the usual places;
otherwise set `FIREFOX_PATH` or pass `executable_path=`. On a headless server, run Firefox under Xvfb (or use
`headless=True`).

```
pip install barebidi
```

To update:

```
pip install -U barebidi
```

Optionally, for mouse movements replayed from recordings of real people instead of generated curves:

```
pip install "barebidi[cursory]"
```

This adds [Cursory](https://github.com/Vinyzu/cursory) (LGPL-3.0) and numpy. barebidi uses it whenever it is
installed; without it, it stays MIT with a single dependency. See
[Mouse and keyboard](https://barebidi.readthedocs.io/en/latest/guides/input/#recorded-movements).

# Usage examples

The browser starts with sensible defaults: a temporary profile, stealth and human input on. Everything is
async, and the browser closes itself when the `async with` block ends.

## Simple

```python
import asyncio
import barebidi as bb

async def main():
    async with bb.Browser() as browser:
        tab = await browser.get("https://example.com")
        print(await tab.title())

        ... further code ...

if __name__ == "__main__":
    asyncio.run(main())
```

Or without the block, nodriver style:

```python
browser = await bb.start()
tab = await browser.get("https://example.com")
...
await browser.stop()
```

## Custom starting options

```python
browser = await bb.start(
    headless=True,
    screen=(1920, 1080),                    # headless only; a real window keeps the real screen
    profile="/path/to/profile",             # keep cookies and storage between runs
    proxy="http://user:pass@host:8080",     # credentials are handled for you
    locale="en-US",
    timezone="America/New_York",
    executable_path="/path/to/firefox",     # or set FIREFOX_PATH
    args=["--some-firefox-arg"],
    prefs={"some.pref": True},              # Firefox about:config prefs
    downloads="/path/to/downloads",
    humanize=True,                          # human-like mouse and keyboard
)
```

## Finding and using elements

```python
tab = await browser.get("https://example.com/login")

await tab.select("input[name=user]").type("me@example.com")
await tab.select("input[name=password]").type("secret")
await tab.find("Sign in").click()

items = await tab.select_all(".item")
for item in items:
    print(await item.text(), await item.get_attribute("href"))
```

Inside an iframe or a shadow root:

```python
frame = await tab.frame("widget.example.org")         # by URL
button = await frame.select("button")

root = await (await tab.select("my-component")).shadow_root()
await root.select("input").type("hello")
```

## Network

```python
async with tab.expect_response("/api/items") as expected:
    await tab.find("Load more").click()
items = await expected.response.json()

await tab.block(resource_types=["image", "font"])
await tab.set_extra_headers({"X-Debug": "1"})
```

## Dialogs, uploads and downloads

```python
async def answer(dialog):
    await dialog.accept("Barebidi")

await tab.on_dialog(answer)

await tab.select("input[type=file]").set_files("report.pdf")

async with tab.expect_download() as expected:
    await tab.find("Export CSV").click()
path = await expected.download.path()
```

## Separate identities in one browser

```python
us = await browser.new_context(proxy="http://user:pass@us-proxy:8080", locale="en-US", timezone="America/Chicago")
de = await browser.new_context(proxy="http://user:pass@de-proxy:8080", locale="de-DE", timezone="Europe/Berlin")

await us.get("https://example.com")
await de.get("https://example.com")   # different cookies, storage, IP, language and clock
```

## Raw protocol

Anything barebidi doesn't wrap is one call away:

```python
result = await tab.send("browsingContext.captureScreenshot", {"context": tab.id, "origin": "document"})
```

# Note: driving Camoufox

[Camoufox](https://github.com/daijro/camoufox) is a patched Firefox build. Since it is still Firefox and
still speaks WebDriver BiDi, barebidi drives it like any other Firefox: point `executable_path` at its binary.

**Why drive Camoufox with barebidi**

- no Playwright and no Node.js driver process: Python talks to Camoufox directly
- standard WebDriver BiDi instead of Juggler, Playwright's own patched-in protocol
- nothing injected into the page: barebidi's scripts run in isolated BiDi sandboxes
- the same API drives stock Firefox and Camoufox; switch with `executable_path=`

1. Download Camoufox with its own tool:

   ```
   pip install camoufox
   python -m camoufox fetch
   ```

2. Find the binary it downloaded:

   - macOS: `~/Library/Caches/camoufox/browsers/official/<version>/Camoufox.app/Contents/MacOS/camoufox`
   - Linux: `~/.cache/camoufox/browsers/official/<version>/camoufox`

3. Start barebidi with that path. Turn barebidi's own stealth off: Camoufox handles that part itself.

   ```python
   browser = await bb.start(executable_path="/path/to/camoufox", stealth=False)
   ```

4. Optionally, let the `camoufox` package build a coherent fingerprint (screen, fonts, hardware, OS) and
   hand it to barebidi. `launch_options()` doesn't start Playwright; it only returns how to launch Camoufox:

   ```python
   from camoufox.utils import launch_options

   opts = launch_options(os="windows")
   browser = await bb.start(
       executable_path=opts["executable_path"],
       args=opts["args"],
       prefs=opts["firefox_user_prefs"],
       env={k: v for k, v in opts["env"].items() if k.startswith("CAMOU_")},
       stealth=False,
   )
   ```

   `launch_options()` returns a copy of your whole environment; keep only the `CAMOU_*` variables, barebidi
   passes the rest on by itself. When the fingerprint claims another OS or GPU than your machine's, Camoufox
   adds canvas and WebGL noise and warns about it; `canvas_noise=False` turns that off.

The `camoufox` package is only needed to download the browser and, optionally, to build fingerprints;
barebidi doesn't depend on it.
