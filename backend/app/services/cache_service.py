"""Safe, bounded caching for non-PII platform aggregates.

This module deliberately rejects raw national identifiers, health numbers, patient
identifiers, contact data, and clinical payloads. It is suitable for policy metadata,
public catalogues, aggregate dashboards, and operational counters only.
"""
from __future__ import annotations

import hashlib
import json
import threading
from collections.abc import Callable
from typing import Any, TypeVar

from ..security.redis_client import CacheUnavailable, cache

T = TypeVar("T")

_PREFIX = "gula:v1"
_ALLOWED_KINDS = frozenset({"immunization_policy", "vaccine_catalog", "outbox_metrics", "immunization_report"})
_FORBIDDEN_TOKENS = ("national", "nid", "health_number", "patient", "phone", "address", "name", "aefi", "clinical")
_MAX_VALUE_BYTES = 256 * 1024
_MAX_TTL_SECONDS = 900

_locks_guard = threading.Lock()
_single_flight: dict[str, threading.Lock] = {}


def _lock_for(key: str) -> threading.Lock:
    with _locks_guard:
        return _single_flight.setdefault(key, threading.Lock())


def cache_key(kind: str, tenant_id: int | str, *, version: str = "current", **dimensions: Any) -> str:
    """Build a tenant-scoped key without accepting identifiers that could contain PII."""
    if kind not in _ALLOWED_KINDS:
        raise ValueError("Unsupported cache kind")
    tenant = str(tenant_id).strip()
    if not tenant or not tenant.isdigit():
        raise ValueError("tenant_id must be numeric")
    values = {"version": str(version), **dimensions}
    raw = json.dumps(values, sort_keys=True, separators=(",", ":"), default=str)
    if any(token in raw.lower() for token in _FORBIDDEN_TOKENS):
        raise ValueError("Cache dimensions must not contain personal or clinical identifiers")
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    return f"{_PREFIX}:{kind}:tenant:{tenant}:{digest}"


def get_json(key: str) -> Any | None:
    try:
        raw = cache.get(key)
        return json.loads(raw) if raw else None
    except (CacheUnavailable, ValueError, TypeError, json.JSONDecodeError):
        return None
    except Exception:
        return None


def set_json(key: str, value: Any, *, ttl_seconds: int) -> bool:
    if not 1 <= ttl_seconds <= _MAX_TTL_SECONDS:
        raise ValueError("ttl_seconds is outside the safe range")
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)
    if len(encoded.encode("utf-8")) > _MAX_VALUE_BYTES:
        raise ValueError("Cache value exceeds the safe size limit")
    try:
        cache.set(key, encoded, ex=ttl_seconds)
        return True
    except Exception:
        return False


def delete(key: str) -> bool:
    try:
        cache.delete(key)
        return True
    except Exception:
        return False


def get_or_set(key: str, loader: Callable[[], T], *, ttl_seconds: int) -> T:
    """Use one loader per process and tolerate cache outages for non-critical reads."""
    cached = get_json(key)
    if cached is not None:
        return cached  # type: ignore[return-value]
    lock = _lock_for(key)
    with lock:
        cached = get_json(key)
        if cached is not None:
            return cached  # type: ignore[return-value]
        value = loader()
        set_json(key, value, ttl_seconds=ttl_seconds)
        return value
