# Contexts, proxies and cookies

## Proxies

```python
browser = await bb.start(proxy="http://user:pass@proxy.example.com:8080")
```

HTTP proxies with a user and password work without Firefox's password prompt: barebidi runs a small local
relay that adds the credentials to every request. SOCKS proxies (`socks5://`, `socks4://`) work too, but
without credentials, which Firefox doesn't support for them.

Match the browser to where the proxy exits: a US exit IP with a European time zone and language is easy
to spot.

```python
browser = await bb.start(proxy="http://user:pass@us.example.com:8080", locale="en-US", timezone="America/Chicago")
```

## Contexts: several identities in one browser

A context is like a separate browser profile inside the same Firefox: its own cookies, storage, cache,
proxy, language and time zone.

```python
us = await browser.new_context(proxy="http://user:pass@us-proxy:8080", locale="en-US", timezone="America/Chicago")
de = await browser.new_context(proxy="http://user:pass@de-proxy:8080", locale="de-DE", timezone="Europe/Berlin")

tab_us = await us.get("https://example.com")
tab_de = await de.get("https://example.com")
await us.new_tab("https://example.org")

await de.close()       # closes its tabs and forgets everything in it
```

The options given to `Browser(...)` set up the default context, the one `browser.get()` and
`browser.new_tab()` use.

## Cookies

```python
cookies = await browser.cookies()                   # all of them
cookies = await browser.cookies("example.com")      # one domain
await browser.set_cookies(cookies)
await browser.clear_cookies()
```

These work on the default context. Other contexts have the same three methods for their own cookies. Cookies are dicts in the WebDriver BiDi format,
so they can be saved as JSON and loaded back later:

```python
import json, pathlib

pathlib.Path("cookies.json").write_text(json.dumps(await browser.cookies()))
await browser.set_cookies(json.loads(pathlib.Path("cookies.json").read_text()))
```

## Keeping a profile

```python
browser = await bb.start(profile="/home/me/.cache/my-scraper-profile")
```

With `profile=`, cookies, storage and logins stay between runs. Without it, every run starts from a fresh
temporary profile.
