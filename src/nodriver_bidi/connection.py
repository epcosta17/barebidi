import asyncio
import itertools
import json
import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any

from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import ConnectionClosed

log = logging.getLogger(__name__)

Handler = Callable[[dict], Any]


class BidiError(Exception):
    def __init__(self, error: str, message: str, stacktrace: str | None = None):
        super().__init__(f"{error}: {message}")
        self.error = error
        self.message = message
        self.stacktrace = stacktrace


class Connection:
    def __init__(self, ws: ClientConnection):
        self._ws = ws
        self._ids = itertools.count(1)
        self._pending: dict[int, asyncio.Future] = {}
        self._handlers: dict[str, list[Handler]] = defaultdict(list)
        self._tasks: set[asyncio.Task] = set()
        self._reader = asyncio.create_task(self._read_loop())

    @classmethod
    async def connect(cls, url: str) -> "Connection":
        return cls(await connect(url, max_size=None))

    @property
    def closed(self) -> bool:
        return self._reader.done()

    async def send(self, method: str, params: dict | None = None) -> dict:
        if self.closed:
            raise ConnectionError("connection is closed")
        msg_id = next(self._ids)
        future = asyncio.get_running_loop().create_future()
        self._pending[msg_id] = future
        payload = json.dumps({"id": msg_id, "method": method, "params": params or {}})
        log.debug("-> %s", payload)
        try:
            await self._ws.send(payload)
            return await future
        finally:
            self._pending.pop(msg_id, None)

    def on(self, event: str, handler: Handler) -> None:
        """Register a local handler. `event` may be a full name or a module ("network")."""
        self._handlers[event].append(handler)

    def off(self, event: str, handler: Handler) -> None:
        if handler in self._handlers.get(event, []):
            self._handlers[event].remove(handler)

    async def close(self) -> None:
        await self._ws.close()
        await asyncio.gather(self._reader, return_exceptions=True)

    async def _read_loop(self) -> None:
        try:
            async for raw in self._ws:
                log.debug("<- %s", raw)
                msg = json.loads(raw)
                if msg.get("type") == "event":
                    self._dispatch(msg["method"], msg.get("params", {}))
                else:
                    self._resolve(msg)
        except ConnectionClosed:
            pass
        finally:
            for future in self._pending.values():
                if not future.done():
                    future.set_exception(ConnectionError("connection closed"))

    def _resolve(self, msg: dict) -> None:
        future = self._pending.get(msg.get("id"))
        if future is None:
            if msg.get("type") == "error":
                log.warning("unmatched error: %s", msg)
            return
        if future.done():
            return
        if msg.get("type") == "error":
            future.set_exception(BidiError(msg["error"], msg.get("message", ""), msg.get("stacktrace")))
        else:
            future.set_result(msg.get("result", {}))

    def _dispatch(self, method: str, params: dict) -> None:
        module = method.split(".", 1)[0]
        for handler in [*self._handlers.get(method, ()), *self._handlers.get(module, ())]:
            try:
                result = handler(params)
            except Exception:
                log.exception("event handler for %s failed", method)
                continue
            if asyncio.iscoroutine(result):
                task = asyncio.create_task(result)
                self._tasks.add(task)
                task.add_done_callback(self._tasks.discard)
