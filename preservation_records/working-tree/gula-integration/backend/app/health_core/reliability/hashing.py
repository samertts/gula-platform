"""Deterministic hashing and synthetic-input validation shared by reliability designs.

All serialisation here is canonical (sorted keys, compact separators, UTF-8) so the
same logical value always produces the same bytes and therefore the same digest.
No randomness, clock, filesystem or third-party library is involved.
"""

from __future__ import annotations

import hashlib
import json
import re

from app.health_core.common.errors import InvalidSyntheticReferenceError
from app.health_core.common.ids import is_synthetic_id
from app.health_core.reliability.errors import ChecksumMismatchError, InvalidStoreValueError

_TEXT_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")


def canonical_json_bytes(value: object) -> bytes:
    """Serialise a JSON-compatible value to deterministic UTF-8 bytes."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def sha256_hex(payload: bytes) -> str:
    """Return the lowercase hex SHA-256 digest of ``payload``."""
    return hashlib.sha256(payload).hexdigest()


def decode_checked_envelope(payload: bytes, *, schema: str, label: str) -> dict[str, object]:
    """Decode a canonical JSON envelope and verify its SHA-256 checksum.

    The ``checksum`` field is computed over the envelope with that field removed.
    A missing, malformed or mismatched checksum is rejected with a structured error.
    """
    try:
        decoded: object = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ChecksumMismatchError(
            f"{label} is not valid UTF-8 JSON", details={"label": label}
        ) from exc
    if not isinstance(decoded, dict):
        raise ChecksumMismatchError(
            f"{label} envelope must be a JSON object", details={"label": label}
        )
    envelope: dict[str, object] = {str(key): value for key, value in decoded.items()}
    if envelope.get("schema") != schema:
        raise ChecksumMismatchError(
            f"{label} schema is not supported", details={"label": label, "schema": schema}
        )
    supplied = envelope.get("checksum")
    body = {key: value for key, value in envelope.items() if key != "checksum"}
    expected = sha256_hex(canonical_json_bytes(body))
    if not isinstance(supplied, str) or supplied != expected:
        raise ChecksumMismatchError(
            f"{label} checksum mismatch", details={"label": label}
        )
    return body


def sealed_envelope(body: dict[str, object]) -> dict[str, object]:
    """Return a copy of ``body`` carrying its SHA-256 checksum."""
    sealed = dict(body)
    sealed["checksum"] = sha256_hex(canonical_json_bytes(body))
    return sealed


def require_synthetic_id(value: object, *, field: str) -> str:
    """Return ``value`` only when it is a real ``SYN-`` identifier shape."""
    if not isinstance(value, str) or not is_synthetic_id(value):
        raise InvalidSyntheticReferenceError(
            f"{field} must be a synthetic SYN- reference", details={"field": field}
        )
    return value


def require_text(value: object, *, field: str) -> str:
    """Return a non-empty lowercase snake-case code used for actions and reasons."""
    if not isinstance(value, str) or not _TEXT_RE.fullmatch(value):
        raise InvalidStoreValueError(
            f"{field} must be a lowercase snake-case code", details={"field": field}
        )
    return value
