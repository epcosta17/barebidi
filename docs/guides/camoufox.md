# Driving Camoufox

[Camoufox](https://github.com/daijro/camoufox) is a patched Firefox build. Since it is still Firefox and still
speaks WebDriver BiDi, barebidi drives it like any other Firefox: point `executable_path` at its binary.

**Why drive Camoufox with barebidi**

- no Playwright and no Node.js driver process: Python talks to Camoufox directly
- standard WebDriver BiDi instead of Juggler, Playwright's own patched-in protocol
- nothing injected into the page: barebidi's scripts run in isolated BiDi sandboxes
- the same API drives stock Firefox and Camoufox; switch with `executable_path=`

## 1. Download Camoufox

```
pip install camoufox
python -m camoufox fetch
```

## 2. Find the binary

- macOS: `~/Library/Caches/camoufox/browsers/official/<version>/Camoufox.app/Contents/MacOS/camoufox`
- Linux: `~/.cache/camoufox/browsers/official/<version>/camoufox`

## 3. Start barebidi with it

Turn barebidi's own stealth off: Camoufox handles that part itself.

```python
browser = await bb.start(executable_path="/path/to/camoufox", stealth=False)
```

## 4. Optional: a coherent fingerprint

The `camoufox` package can build a coherent fingerprint (screen, fonts, hardware, OS). `launch_options()`
doesn't start Playwright; it only returns how to launch Camoufox:

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

## Compared with Camoufox + Playwright

**You gain**: no Playwright or Node.js, a standard protocol that ships with Firefox, the same code for stock
Firefox and Camoufox, and barebidi's own features (closed shadow roots, input routed into cross-site iframes,
human input).

**You give up**: Playwright's mature API (actionability checks, sync API, tracing), and the path Camoufox is
built and tested on. Some Camoufox options may be implemented on the Playwright side and not apply over
BiDi, such as its own humanized cursor.
