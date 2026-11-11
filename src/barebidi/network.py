import asyncio
import base64
import http
import inspect
import json
import logging
import re
from collections.abc import AsyncIterator, Awaitable, Callable, Iterable
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, Literal

from .connection import BidiError

if TYPE_CHECKING:
    from .browser import Browser
    from .tab import Tab

log = logging.getLogger(__name__)

Phase = Literal["request", "response"]
_EVENTS = {"request": "network.beforeRequestSent", "response": "network.responseStarted"}
_PHASES = {"request": "beforeRequestSent", "response": "responseStarted"}
MAX_BODY_SIZE = 50 * 1024 * 1024


def url_matcher(pattern: str | None) -> Callable[[str], bool]:
    """`None` matches every URL, a pattern containing `*` is a glob, anything else a substring."""
    if pattern is None:
        return lambda url: True
    if "*" not in pattern:
        return lambda url: pattern in url
    regex = re.compile(".*".join(re.escape(part) for part in pattern.split("*")))
    return lambda url: regex.fullmatch(url) is not None


class Request:
    """A request the page made: `url`, `method`, `headers`, `resource_type` and the `context` it came from."""

    def __init__(self, browser: "Browser", params: dict):
        data = params["request"]
        self._browser = browser
        self.id: str = data["request"]
        self.url: str = data["url"]
        self.method: str = data["method"]
        self.headers = _parse_headers(data.get("headers", []))
        self.resource_type: str = data.get("destination") or data.get("initiatorType") or "other"
        self.context: str | None = params.get("context")

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.method} {self.url}>"

    @property
    def tab(self) -> "Tab | None":
        """The tab that made the request, or None if it didn't come from a page."""
        from .tab import Tab

        return Tab(self._browser, self._browser.top_level(self.context)) if self.context else None


class Response:
    """A response: `status`, `status_text`, `url`, `headers`, `mime_type`, `from_cache` and its `request`."""

    def __init__(self, request: Request, data: dict, collector: str | None):
        self.request = request
        self.url: str = data["url"]
        self.status: int = data["status"]
        self.status_text: str = data.get("statusText", "")
        self.headers = _parse_headers(data.get("headers", []))
        self.mime_type: str = data.get("mimeType", "")
        self.from_cache: bool = data.get("fromCache", False)
        self._collector = collector
        self._body: bytes | None = None

    def __repr__(self) -> str:
        return f"<Response {self.status} {self.url}>"

    async def body(self) -> bytes:
        """The body as bytes; only once the response has completed (on_response, expect_response)."""
        if self._body is None:
            if self._collector is None:
                raise RuntimeError("the body is only available once the response has completed")
            result = await self.request._browser.connection.send(
                "network.getData", {"dataType": "response", "request": self.request.id, "collector": self._collector}
            )
            self._body = _decode(result["bytes"])
        return self._body

    async def text(self) -> str:
        """The body decoded with the charset in Content-Type, UTF-8 otherwise."""
        charset = re.search(r"charset=([\w-]+)", self.headers.get("content-type", ""))
        try:
            return (await self.body()).decode(charset.group(1) if charset else "utf-8", errors="replace")
        except LookupError:
            return (await self.body()).decode("utf-8", errors="replace")

    async def json(self) -> Any:
        """The body parsed as JSON."""
        return json.loads(await self.body())


class InterceptedRequest(Request):
    """A paused request. Settle it with one of continue_(), abort() or fulfill()."""

    def __init__(self, browser: "Browser", params: dict, phase: Phase):
        super().__init__(browser, params)
        self.phase = phase
        self.response = Response(self, params["response"], None) if phase == "response" else None
        self.handled = False

    async def continue_(
        self,
        *,
        url: str | None = None,
        method: str | None = None,
        headers: dict[str, str] | None = None,
        body: str | bytes | None = None,
        status: int | None = None,
    ) -> None:
        """Let it through. `headers` replaces all headers: of the request, or of the response in that phase."""
        params: dict = {"request": self.id}
        if headers is not None:
            params["headers"] = _serialize_headers(headers)
        if self.phase == "request":
            if status is not None:
                raise ValueError("status can only be changed in the response phase")
            for key, value in (("url", url), ("method", method)):
                if value is not None:
                    params[key] = value
            if body is not None:
                params["body"] = _encode(body)
            await self._settle("network.continueRequest", params)
        else:
            if url is not None or method is not None or body is not None:
                raise ValueError("url, method and body belong to the request phase; use fulfill() to replace a response")
            if status is not None:
                params["statusCode"] = status
            await self._settle("network.continueResponse", params)

    async def abort(self) -> None:
        """Fail the request, as if the network had dropped it."""
        await self._settle("network.failRequest", {"request": self.id})

    async def fulfill(self, body: str | bytes = b"", *, status: int = 200, headers: dict[str, str] | None = None) -> None:
        """Answer with this response; the server is never contacted (or its response is discarded)."""
        params: dict = {"request": self.id, "statusCode": status, "reasonPhrase": _reason(status), "body": _encode(body)}
        if headers is not None:
            params["headers"] = _serialize_headers(headers)
        await self._settle("network.provideResponse", params)

    async def _settle(self, method: str, params: dict) -> None:
        if self.handled:
            raise RuntimeError(f"{self!r} was already handled")
        self.handled = True
        await self._browser.connection.send(method, params)


InterceptHandler = Callable[[InterceptedRequest], Awaitable[None] | None]
ResponseHandler = Callable[[Response], Awaitable[None] | None]
ResponseMatch = str | Callable[[Response], bool] | None


class Intercept:
    """A request interception set up with intercept() or block()."""

    def __init__(self, network: "Network", intercept_id: str, handler: InterceptHandler, matches: Callable[[str], bool]):
        self._network = network
        self.id = intercept_id
        self.handler = handler
        self.matches = matches

    async def remove(self) -> None:
        """Stop intercepting."""
        if self._network._intercepts.pop(self.id, None) is not None:
            await self._network.browser.connection.send("network.removeIntercept", {"intercept": self.id})


class ExpectedResponse:
    """Holder for the response expect_response() waits for, set when the block ends."""

    def __init__(self) -> None:
        self.response: Response | None = None


class Network:
    def __init__(self, browser: "Browser"):
        self.browser = browser
        self._lock = asyncio.Lock()
        self._subscribed: set[str] = set()
        self._intercepts: dict[str, Intercept] = {}
        self._listeners: list[ResponseHandler] = []
        self._collector: str | None = None
        self._tasks: set[asyncio.Task] = set()

    async def intercept(
        self, handler: InterceptHandler, url: str | None = None, phase: Phase = "request", contexts: list[str] | None = None
    ) -> Intercept:
        await self._subscribe(_EVENTS[phase], lambda params: self._on_blocked(phase, params))
        params: dict = {"phases": [_PHASES[phase]]}
        if contexts:
            params["contexts"] = contexts
        async with self._lock:
            result = await self.browser.connection.send("network.addIntercept", params)
            intercept = Intercept(self, result["intercept"], handler, url_matcher(url))
            self._intercepts[intercept.id] = intercept
        return intercept

    async def block(self, urls: Iterable[str], resource_types: Iterable[str], contexts: list[str] | None = None) -> Intercept:
        matchers = [url_matcher(url) for url in urls]
        types = set(resource_types)
        if not matchers and not types:
            raise ValueError("give at least one URL pattern or resource type to block")

        async def handler(request: InterceptedRequest) -> None:
            if request.resource_type in types or any(match(request.url) for match in matchers):
                await request.abort()

        return await self.intercept(handler, contexts=contexts)

    async def set_extra_headers(self, headers: dict[str, str], contexts: list[str] | None = None) -> None:
        params: dict = {"headers": _serialize_headers(headers)}
        if contexts:
            params["contexts"] = contexts
        await self.browser.connection.send("network.setExtraHeaders", params)

    async def on_response(self, handler: ResponseHandler, url: ResponseMatch = None, tab: str | None = None) -> Callable[[], None]:
        matches = _response_matcher(url)

        def listener(response: Response) -> Awaitable[None] | None:
            if tab is not None and (response.request.context is None or self.browser.top_level(response.request.context) != tab):
                return None
            return handler(response) if matches(response) else None

        def remove() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        await self._capture_responses()
        self._listeners.append(listener)
        return remove

    @asynccontextmanager
    async def expect_response(
        self, url: ResponseMatch = None, timeout: float = 30.0, tab: str | None = None
    ) -> AsyncIterator[ExpectedResponse]:
        expected = ExpectedResponse()
        future: asyncio.Future[Response] = asyncio.get_running_loop().create_future()

        def resolve(response: Response) -> None:
            if not future.done():
                future.set_result(response)

        remove = await self.on_response(resolve, url, tab)
        try:
            yield expected
            try:
                expected.response = await asyncio.wait_for(future, timeout)
            except TimeoutError:
                raise TimeoutError(f"no response matching {url!r} within {timeout}s") from None
        finally:
            remove()

    async def _capture_responses(self) -> None:
        async with self._lock:
            if self._collector is None:
                result = await self.browser.connection.send(
                    "network.addDataCollector", {"dataTypes": ["response"], "maxEncodedDataSize": MAX_BODY_SIZE}
                )
                self._collector = result["collector"]
        await self._subscribe("network.responseCompleted", self._on_response)

    async def _subscribe(self, event: str, handler: Callable[[dict], Any]) -> None:
        async with self._lock:
            if event in self._subscribed:
                return
            # Register before subscribing so no event slips through in between.
            self.browser.connection.on(event, handler)
            try:
                await self.browser.connection.send("session.subscribe", {"events": [event]})
            except BaseException:
                self.browser.connection.off(event, handler)
                raise
            self._subscribed.add(event)

    async def _on_blocked(self, phase: Phase, params: dict) -> None:
        if not params.get("isBlocked"):
            return
        ids = params.get("intercepts", [])
        if any(intercept_id not in self._intercepts for intercept_id in ids):
            async with self._lock:  # wait for an intercept() that is still registering
                pass
        request = InterceptedRequest(self.browser, params, phase)
        try:
            for intercept_id in ids:
                intercept = self._intercepts.get(intercept_id)
                if intercept is None or not intercept.matches(request.url):
                    continue
                result = intercept.handler(request)
                if inspect.isawaitable(result):
                    await result
                if request.handled:
                    return
        except Exception:
            log.exception("intercept handler failed for %s", request.url)
        if not request.handled:
            try:
                await request.continue_()
            except (BidiError, ConnectionError) as error:
                log.debug("could not continue %s: %s", request.url, error)

    def _on_response(self, params: dict) -> None:
        if not self._listeners:
            return
        response = Response(Request(self.browser, params), params["response"], self._collector)
        for listener in list(self._listeners):
            try:
                result = listener(response)
            except Exception:
                log.exception("response handler failed for %s", response.url)
                continue
            if inspect.isawaitable(result):
                task = asyncio.ensure_future(result)
                self._tasks.add(task)
                task.add_done_callback(self._task_done)

    def _task_done(self, task: asyncio.Task) -> None:
        self._tasks.discard(task)
        if not task.cancelled() and task.exception() is not None:
            log.error("response handler failed", exc_info=task.exception())


def _response_matcher(url: ResponseMatch) -> Callable[[Response], bool]:
    if callable(url):
        return url
    match = url_matcher(url)
    return lambda response: match(response.url)


def _parse_headers(headers: list[dict]) -> dict[str, str]:
    result: dict[str, str] = {}
    for header in headers:
        name = header["name"].lower()
        value = header["value"]
        text = value["value"] if value["type"] == "string" else base64.b64decode(value["value"]).decode("latin-1")
        result[name] = f"{result[name]}, {text}" if name in result else text
    return result


def _serialize_headers(headers: dict[str, str]) -> list[dict]:
    return [{"name": name, "value": {"type": "string", "value": str(value)}} for name, value in headers.items()]


def _encode(data: str | bytes) -> dict:
    if isinstance(data, str):
        return {"type": "string", "value": data}
    return {"type": "base64", "value": base64.b64encode(data).decode()}


def _decode(value: dict) -> bytes:
    if value["type"] == "base64":
        return base64.b64decode(value["value"])
    return value["value"].encode()


def _reason(status: int) -> str:
    try:
        return http.HTTPStatus(status).phrase
    except ValueError:
        return ""
