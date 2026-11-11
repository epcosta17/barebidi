# Getting started

## Install

```
pip install barebidi
```

barebidi needs Python 3.12+ and Firefox from Mozilla. On Ubuntu, use Mozilla's package or tarball, not the
snap. barebidi looks for Firefox in the usual places; otherwise set the `FIREFOX_PATH` environment variable or
pass `executable_path=`.

## A first script

```python
import asyncio
import barebidi as bb

async def main():
    async with bb.Browser() as browser:
        tab = await browser.get("https://example.com")
        print(await tab.title())

asyncio.run(main())
```

`async with` starts Firefox and closes it when the block ends, even after an error. Without the block:

```python
browser = await bb.start()
tab = await browser.get("https://example.com")
...
await browser.stop()
```

Firefox starts with a fresh temporary profile that is deleted on exit. Stealth and human-like input are on.

## Starting options

All are keyword arguments of `Browser(...)` and `start(...)`:

| Option | Default | |
|---|---|---|
| `headless` | `False` | no window. On Linux, headless Firefox has no WebGL |
| `screen` | `None` | `(width, height)` in headless mode; a real window keeps the real screen |
| `stealth` | `True` | clear the automation flag pages can see (`navigator.webdriver`) |
| `humanize` | `True` | human timings and mouse trajectories |
| `profile` | `None` | a profile folder to keep cookies and storage between runs |
| `proxy` | `None` | `"http://user:pass@host:port"`, `socks5://host:port` or `socks4://host:port`; HTTP credentials are handled for you |
| `locale` | `None` | language, e.g. `"en-US"` |
| `timezone` | `None` | IANA time zone, e.g. `"America/New_York"` |
| `executable_path` | `None` | path to Firefox (or [Camoufox](guides/camoufox.md)) |
| `args` | `()` | extra Firefox command-line arguments |
| `prefs` | `None` | Firefox `about:config` preferences |
| `env` | `None` | extra environment variables for the Firefox process |
| `downloads` | `None` | folder for downloads; a temporary one if not set |
| `timeout` | `60.0` | seconds before any protocol command gives up; `None` waits forever |
| `startup_timeout` | `30.0` | seconds to wait for Firefox to start |

## Tabs

```python
tab = await browser.get("https://example.com")       # the current tab
other = await browser.get("https://example.org", new_tab=True)
background = await browser.new_tab("https://example.net", background=True)

for t in await browser.tabs():
    print(await t.url(), await t.title())

await tab.reload()
await tab.back()
await other.close()
```

`tab.get()` waits for the page to load (`wait="complete"`). Pass `wait="interactive"` to continue once the
document is parsed, or `wait="none"` not to wait at all.

## Running JavaScript

```python
title = await tab.evaluate("document.title")
total = await tab.call_function("(a, b) => a + b", 2, 3)
```

Values go back and forth as Python objects: numbers, strings, lists, dicts, dates, and elements. Pass
`isolated=True` to run in a sandbox the page's own scripts can't see or interfere with.

## Screenshots

```python
await tab.screenshot("page.png")
await tab.screenshot("full.png", full_page=True)
await (await tab.select("header")).screenshot("header.png")
```
