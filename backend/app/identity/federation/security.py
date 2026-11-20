from __future__ import annotations

import ipaddress
import os
from collections.abc import Iterable
from urllib.parse import SplitResult, urlsplit

_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
_BLOCKED_HOSTS = {"metadata.google.internal", "metadata", "169.254.169.254"}


def _is_production() -> bool:
    return os.getenv("ENV", "production").lower() in {"production", "staging"}


def _allowed_hosts() -> set[str]:
    return {
        item.strip().lower().rstrip(".")
        for item in os.getenv("FEDERATION_ALLOWED_HOSTS", "").split(",")
        if item.strip()
    }


def _parse_url(value: str, field: str) -> tuple[SplitResult, str]:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{field} must be a non-empty URL without surrounding whitespace")
    if "\\" in value or "*" in value:
        raise ValueError(f"{field} must not contain wildcard or backslash characters")

    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"{field} must be an absolute HTTP(S) URL")
    if parsed.username or parsed.password:
        raise ValueError(f"{field} must not contain embedded credentials")
    if parsed.fragment:
        raise ValueError(f"{field} must not contain a URL fragment")

    try:
        host = parsed.hostname.lower().rstrip(".")
        port = parsed.port
        if port is not None and not 0 < port < 65536:
            raise ValueError("port outside valid range")
    except ValueError as exc:
        raise ValueError(f"{field} contains an invalid host or port") from exc
    return parsed, host


def _validate_host(host: str, field: str) -> None:
    if host in _BLOCKED_HOSTS:
        raise ValueError(f"{field} host is not allowed")

    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None:
        if address.is_loopback and host in _LOCAL_HOSTS and not _is_production():
            return
        if (
            address.is_private
            or address.is_link_local
            or address.is_reserved
            or address.is_loopback
        ):
            raise ValueError(f"{field} cannot target a private, local, or link-local address")

    allowed = _allowed_hosts()
    if allowed:
        if host not in allowed:
            raise ValueError(f"{field} host is not in FEDERATION_ALLOWED_HOSTS")
    elif _is_production():
        raise ValueError("FEDERATION_ALLOWED_HOSTS must be configured in production")


def validate_endpoint_url(value: str | None, field: str) -> str | None:
    if value is None:
        return None
    parsed, host = _parse_url(value, field)
    if parsed.scheme != "https" and not (not _is_production() and host in _LOCAL_HOSTS):
        raise ValueError(f"{field} must use HTTPS outside local development")
    _validate_host(host, field)
    return parsed.geturl().rstrip("/")


def validate_redirect_uris(values: Iterable[str] | None) -> list[str] | None:
    if values is None:
        return None
    uris = list(values)
    if len(uris) > 20:
        raise ValueError("redirect_uris cannot contain more than 20 entries")

    validated: list[str] = []
    for index, value in enumerate(uris):
        field = f"redirect_uris[{index}]"
        parsed, host = _parse_url(value, field)
        if parsed.scheme != "https" and not (not _is_production() and host in _LOCAL_HOSTS):
            raise ValueError(f"{field} must use HTTPS outside local development")
        _validate_host(host, field)
        validated.append(parsed.geturl())
    return validated


__all__ = ["validate_endpoint_url", "validate_redirect_uris"]
