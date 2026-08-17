from __future__ import annotations

import ipaddress
import socket
from collections.abc import Callable
from urllib.parse import urlsplit, urlunsplit


class UnsafeUrlError(ValueError):
    """Raised when an outbound URL is not safe to fetch."""


Resolver = Callable[..., list[tuple]]


def _is_public_ip(address: str) -> bool:
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    return ip.is_global


def validate_public_url(url: str, resolver: Resolver = socket.getaddrinfo) -> str:
    """Validate a single public HTTP(S) URL and return its canonical form.

    This blocks obvious SSRF destinations. Production deployments should also
    block private/link-local egress at the network layer to cover DNS rebinding
    and redirects performed inside third-party extractors.
    """

    if len(url) > 2048:
        raise UnsafeUrlError("Link is too long")

    parts = urlsplit(url)
    if parts.scheme.lower() not in {"http", "https"}:
        raise UnsafeUrlError("Only http and https links are accepted")
    if not parts.hostname:
        raise UnsafeUrlError("A valid public link is required")
    if parts.username or parts.password:
        raise UnsafeUrlError("Links containing credentials are not accepted")
    try:
        port = parts.port
    except ValueError as exc:
        raise UnsafeUrlError("Invalid port") from exc
    if port not in {None, 80, 443}:
        raise UnsafeUrlError("Only standard web ports are accepted")

    host = parts.hostname.rstrip(".").lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        raise UnsafeUrlError("Private network links are not accepted")

    try:
        addresses = {item[4][0] for item in resolver(host, port or 443, type=socket.SOCK_STREAM)}
    except (socket.gaierror, OSError) as exc:
        raise UnsafeUrlError("The link host could not be verified") from exc
    if not addresses or any(not _is_public_ip(address) for address in addresses):
        raise UnsafeUrlError("Private or reserved network links are not accepted")

    clean_netloc = f"[{host}]" if ":" in host else host
    if port:
        clean_netloc = f"{clean_netloc}:{port}"
    return urlunsplit((parts.scheme.lower(), clean_netloc, parts.path or "/", parts.query, ""))
