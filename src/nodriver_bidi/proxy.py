import asyncio
import base64
import contextlib
from dataclasses import dataclass
from urllib.parse import unquote, urlsplit

_SOCKS_VERSIONS = {"socks": 5, "socks5": 5, "socks5h": 5, "socks4": 4, "socks4a": 4}


@dataclass(frozen=True)
class Proxy:
    host: str
    port: int
    socks_version: int | None = None
    credentials: tuple[str, str] | None = None

    @classmethod
    def parse(cls, url: str) -> "Proxy":
        """`http://[user:password@]host:port`, `socks5://host:port` or `socks4://host:port`."""
        parts = urlsplit(url if "://" in url else f"http://{url}")
        scheme = parts.scheme.lower()
        if scheme != "http" and scheme not in _SOCKS_VERSIONS:
            raise ValueError(f"unsupported proxy scheme {scheme!r}; use http://, socks5:// or socks4://")
        if not parts.hostname or not parts.port:
            raise ValueError(f"proxy {url!r} needs a host and a port")
        credentials = (unquote(parts.username), unquote(parts.password or "")) if parts.username else None
        if credentials and scheme != "http":
            raise ValueError("Firefox can only authenticate HTTP proxies, not SOCKS ones")
        return cls(parts.hostname, parts.port, _SOCKS_VERSIONS.get(scheme), credentials)

    @property
    def address(self) -> str:
        return f"[{self.host}]:{self.port}" if ":" in self.host else f"{self.host}:{self.port}"

    def bidi(self) -> dict:
        """WebDriver BiDi proxy configuration, for a single context."""
        if self.socks_version:
            return {"proxyType": "manual", "socksProxy": self.address, "socksVersion": self.socks_version}
        return {"proxyType": "manual", "httpProxy": self.address, "sslProxy": self.address}

    def prefs(self) -> dict:
        """Firefox prefs, for the whole browser. Every field is set so a reused profile keeps no stale proxy."""
        if self.socks_version:
            return {
                "network.proxy.type": 1,
                "network.proxy.http": "",
                "network.proxy.ssl": "",
                "network.proxy.socks": self.host,
                "network.proxy.socks_port": self.port,
                "network.proxy.socks_version": self.socks_version,
                "network.proxy.socks_remote_dns": True,
                "network.proxy.socks5_remote_dns": True,
            }
        return {
            "network.proxy.type": 1,
            "network.proxy.http": self.host,
            "network.proxy.http_port": self.port,
            "network.proxy.ssl": self.host,
            "network.proxy.ssl_port": self.port,
            "network.proxy.socks": "",
        }


# Firefox's default: the system proxy settings.
NO_PROXY_PREFS = {"network.proxy.type": 5}


class Relay:
    """A proxy on 127.0.0.1 without credentials, in front of one that needs them.

    A 407 that BiDi can't answer, such as one for Firefox's own background requests, opens a dialog asking the
    person for the proxy's password, and the browser waits on it. Through the relay Firefox never meets a 407:
    the relay adds the credentials to every request it forwards.
    """

    def __init__(self, upstream: Proxy):
        assert upstream.credentials and not upstream.socks_version
        self.upstream = upstream
        self._authorization = b"Proxy-Authorization: Basic " + base64.b64encode(":".join(upstream.credentials).encode())
        self._server: asyncio.Server | None = None

    async def start(self) -> "Relay":
        self._server = await asyncio.start_server(self._serve, "127.0.0.1", 0)
        self.local = Proxy("127.0.0.1", self._server.sockets[0].getsockname()[1])  # what Firefox should use
        return self

    def close(self) -> None:
        if self._server:
            self._server.close()

    async def _serve(self, client_reader: asyncio.StreamReader, client_writer: asyncio.StreamWriter) -> None:
        upstream_writer = None
        try:
            head = await client_reader.readuntil(b"\r\n\r\n")
            upstream_reader, upstream_writer = await asyncio.open_connection(self.upstream.host, self.upstream.port)
            upstream_writer.write(self._with_credentials(head))
            # Send a request body (or tunnelled bytes) as it comes, while the answer is awaited.
            upload = asyncio.create_task(_pipe(client_reader, upstream_writer))
            answer = await upstream_reader.readuntil(b"\r\n\r\n")
            if answer.split(b" ", 2)[1:2] == [b"407"]:
                # Rejected credentials: an error page, not a 407 that would make Firefox ask the person.
                upload.cancel()
                client_writer.write(_REJECTED)
                await client_writer.drain()
                return
            client_writer.write(answer)
            await asyncio.gather(upload, _pipe(upstream_reader, client_writer))
        except (OSError, asyncio.IncompleteReadError, asyncio.LimitOverrunError):
            pass
        finally:
            for writer in (client_writer, upstream_writer):
                if writer is not None:
                    writer.close()

    def _with_credentials(self, head: bytes) -> bytes:
        request_line, *headers = head[:-4].split(b"\r\n")
        tunnel = request_line[:8].upper() == b"CONNECT "
        dropped = (b"proxy-authorization:",) if tunnel else (b"proxy-authorization:", b"connection:", b"proxy-connection:")
        kept = [header for header in headers if not header.lower().startswith(dropped)]
        if not tunnel:
            kept.append(b"Connection: close")  # one request per connection, so each one carries the credentials
        return b"\r\n".join([request_line, self._authorization, *kept]) + b"\r\n\r\n"


_REJECTED = (
    b"HTTP/1.1 502 Bad Gateway\r\nContent-Type: text/plain\r\nContent-Length: 36\r\nConnection: close\r\n\r\n"
    b"The proxy rejected the credentials.\n"
)


async def _pipe(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    with contextlib.suppress(OSError):
        while data := await reader.read(65536):
            writer.write(data)
            await writer.drain()
    with contextlib.suppress(OSError):
        writer.close()
