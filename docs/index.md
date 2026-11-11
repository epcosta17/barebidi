# barebidi

**Async Firefox automation for Python, speaking WebDriver BiDi straight to the browser.**

- **built for Firefox**: the regular Firefox you download from Mozilla, nothing patched
- no driver binaries: no geckodriver, no Selenium
- no Playwright-style browser builds: it drives the Firefox you already have
- one dependency: `websockets`

```python
import asyncio
import barebidi as bb

async def main():
    async with bb.Browser() as browser:
        tab = await browser.get("https://example.com")
        print(await tab.title())
        await tab.find("Learn more").click()

asyncio.run(main())
```

## Why WebDriver BiDi

WebDriver BiDi is the W3C standard for browser automation, the successor of both classic WebDriver and the
Chrome DevTools Protocol. Firefox speaks it natively. barebidi opens a websocket to Firefox and talks to it
directly, so there is nothing in between to install, keep in sync or get detected.

## Why Firefox first

Most automation tools are Chrome-first and treat Firefox as an afterthought. barebidi is the other way around:
every feature is built and tested against Firefox, including its quirks with cross-site iframes, closed shadow
roots and input routing.

## What you get

- `select(css)`, `find(text)`, `xpath(expr)`, all waiting until the element appears, and chainable
- mouse and keyboard input with human timings and trajectories, on by default
- elements inside cross-site iframes and closed shadow roots
- proxies with credentials, plus per-context locale and time zone
- isolated browser contexts: separate cookies, storage and proxy in one browser
- network interception, blocking, response waiting and extra headers
- dialogs, file uploads and downloads
- every protocol type generated from the spec, for your editor and type checker

Start with [Getting started](getting-started.md).
