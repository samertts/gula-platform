"""Deterministic ETag derivation and ``If-Match`` handling for T6 evidence.

An ETag is a strong, quoted SHA-256 digest of the canonical JSON of the stored
resource. The resource includes ``meta.versionId``, so the digest changes on
every stored version and two different contents at the same version cannot
collide. Comparison strips an optional weak prefix for tolerant handling of a
client that echoes ``W/``; the emitted ETag itself is always strong.

No cryptography here is used for authenticity: the digest is a change detector
for optimistic concurrency, not a signature.
"""

from __future__ import annotations

import hashlib
import json
from typing import Final

__all__ = [
    "canonical_json",
    "etag_for",
    "etag_matches",
    "normalise_etag",
    "version_from_meta",
]

_WEAK_PREFIX: Final[str] = "W/"


def canonical_json(resource: dict[str, object]) -> str:
    """Return a stable, order-independent JSON representation of a resource."""
    return json.dumps(resource, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def etag_for(resource: dict[str, object]) -> str:
    """Return a strong quoted ETag derived from content and version."""
    digest = hashlib.sha256(canonical_json(resource).encode("utf-8")).hexdigest()
    return f'"{digest}"'


def normalise_etag(value: str) -> str:
    """Normalise a client ETag for comparison (strip weak prefix and whitespace)."""
    candidate = value.strip()
    if candidate.startswith(_WEAK_PREFIX):
        candidate = candidate[len(_WEAK_PREFIX) :].strip()
    return candidate


def etag_matches(if_match: str, resource: dict[str, object]) -> bool:
    """Return whether ``If-Match`` matches the current resource ETag.

    ``If-Match: *`` matches any existing current version; the caller is still
    responsible for confirming that the resource exists.
    """
    supplied = normalise_etag(if_match)
    if supplied == "*":
        return bool(resource)
    current = normalise_etag(etag_for(resource))
    return bool(supplied) and supplied == current


def version_from_meta(resource: dict[str, object]) -> int:
    """Read a positive ``meta.versionId``; return 0 when malformed."""
    meta = resource.get("meta")
    if not isinstance(meta, dict):
        return 0
    raw = meta.get("versionId")
    if not isinstance(raw, str) or not raw.isdigit():
        return 0
    version = int(raw)
    return version if version >= 1 else 0
