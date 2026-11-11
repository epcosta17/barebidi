# Events and the raw protocol

barebidi wraps the common tasks; everything else in WebDriver BiDi is one call away.

## Sending commands

```python
result = await tab.send("browsingContext.captureScreenshot", {"context": tab.id, "origin": "document"})
tree = await browser.connection.send("browsingContext.getTree", {})
```

`send()` takes the method name and its parameters as in the
[WebDriver BiDi specification](https://w3c.github.io/webdriver-bidi/), and returns the result as a dict. An
error from the browser raises `BidiError`; a browser that closed or crashed raises `BrowserClosedError`.

## Events

```python
def logged(params):
    print(params["level"], params["text"])

await tab.on("log.entryAdded", logged)           # this tab's console messages
await browser.on("network.beforeRequestSent", lambda p: print(p["request"]["url"]))
```

`on()` subscribes to an event, or to a whole module (`"log"`), and calls the handler with each event's
parameters. Handlers can be plain functions or coroutines. `tab.on()` only passes events from that tab and its
iframes.

## Types

Every command, result and event of the protocol has a type in `barebidi.protocol`, generated from the
specification's CDDL. They are `TypedDict`s and literals: free at runtime, and your editor and type checker
know the shape of every message.

```python
from barebidi import protocol

def logged(params: protocol.log_Entry) -> None:
    ...

cookie: protocol.network_Cookie
```

Names follow the spec with the module as a prefix: `script.RemoteValue` is `protocol.script_RemoteValue`.
