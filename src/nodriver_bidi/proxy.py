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
