"""Canonical hashing, chain verification and tamper detection.

Verification is deterministic and structured: it never logs record contents,
signatures or key material. Reason codes are stable identifiers.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from app.health_core.audit_anchor.keys import KeyProvider
from app.health_core.audit_anchor.store import AuditAnchorStore

GENESIS_HASH = "0" * 64

_REQUIRED_FIELDS = (
    "seq",
    "prev_hash",
    "payload_hash",
    "timestamp",
    "tenant_id",
    "actor",
    "action",
    "key_id",
    "payload",
    "signature",
)
_HEX_DIGITS = frozenset("0123456789abcdef")


@dataclass(frozen=True, slots=True)
class VerificationReport:
    """Structured result of a chain verification pass."""

    ok: bool
    total: int
    first_bad_seq: int | None
    reason: str | None
    # Extra convenience field for append(): the verified tail record hash.
    tail_hash: str | None = None


def canonical_json(value: Any) -> bytes:
    """Deterministic UTF-8 JSON bytes (sorted keys, compact separators)."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_hash(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in _HEX_DIGITS for character in value)
    )


def record_body(entry: Mapping[str, Any]) -> dict[str, Any]:
    """Everything in the record except its signature (the signed/hashed body)."""
    return {key: value for key, value in entry.items() if key != "signature"}


def record_hash(entry: Mapping[str, Any]) -> str:
    """SHA-256 over the canonical JSON of the whole record body."""
    return sha256_hex(canonical_json(record_body(entry)))


def payload_hash(payload: Mapping[str, Any]) -> str:
    """SHA-256 over the canonical JSON of the (already redacted) payload."""
    return sha256_hex(canonical_json(payload))


def verify_chain(
    store: AuditAnchorStore,
    key_provider: KeyProvider,
    *,
    tenant_id: str | None = None,
) -> VerificationReport:
    """Verify a complete chain, optionally requiring a single tenant.

    A chain is scoped to exactly one tenant. Any mixed-tenant chain is rejected,
    whether or not ``tenant_id`` is supplied.
    """
    try:
        entries = store.read_all()
    except Exception:
        return VerificationReport(
            ok=False, total=0, first_bad_seq=None, reason="store_unreadable"
        )

    total = len(entries)
    if total == 0:
        return VerificationReport(ok=True, total=0, first_bad_seq=None, reason=None)

    def bad(seq: int | None, reason: str) -> VerificationReport:
        return VerificationReport(
            ok=False, total=total, first_bad_seq=seq, reason=reason
        )

    expected_seq = 1
    expected_prev = GENESIS_HASH
    seen_seqs: set[int] = set()
    bound_tenant: str | None = None
    tail_hash = GENESIS_HASH

    for position, entry in enumerate(entries, start=1):
        missing = [field for field in _REQUIRED_FIELDS if field not in entry]
        if missing:
            return bad(position, "malformed_entry")
        seq = entry["seq"]
        if not isinstance(seq, int) or isinstance(seq, bool) or seq < 1:
            return bad(position, "malformed_entry")
        if not is_hash(entry["prev_hash"]) or not is_hash(entry["payload_hash"]):
            return bad(seq, "malformed_entry")
        if (
            not isinstance(entry["timestamp"], str)
            or not isinstance(entry["tenant_id"], str)
            or not entry["tenant_id"]
            or not isinstance(entry["actor"], str)
            or not isinstance(entry["action"], str)
            or not isinstance(entry["key_id"], str)
            or not entry["key_id"]
            or not isinstance(entry["signature"], str)
            or not isinstance(entry["payload"], dict)
        ):
            return bad(seq, "malformed_entry")

        if seq in seen_seqs:
            return bad(seq, "duplicate_seq")
        seen_seqs.add(seq)

        if seq != expected_seq:
            return bad(seq, "sequence_gap")

        entry_tenant = entry["tenant_id"]
        if tenant_id is not None and entry_tenant != tenant_id:
            return bad(seq, "cross_tenant_contamination")
        if bound_tenant is None:
            bound_tenant = entry_tenant
        elif entry_tenant != bound_tenant:
            return bad(seq, "cross_tenant_contamination")

        if entry["prev_hash"] != expected_prev:
            return bad(seq, "prev_hash_mismatch")
        if entry["payload_hash"] != payload_hash(entry["payload"]):
            return bad(seq, "payload_tampered")

        body = canonical_json(record_body(entry))
        if not key_provider.has_key(entry["key_id"]):
            return bad(seq, "unknown_key_id")
        if not key_provider.verify(entry["key_id"], body, entry["signature"]):
            return bad(seq, "invalid_signature")

        expected_seq = seq + 1
        tail_hash = record_hash(entry)
        expected_prev = tail_hash

    return VerificationReport(
        ok=True,
        total=total,
        first_bad_seq=None,
        reason=None,
        tail_hash=tail_hash,
    )


__all__ = [
    "GENESIS_HASH",
    "VerificationReport",
    "canonical_json",
    "is_hash",
    "payload_hash",
    "record_body",
    "record_hash",
    "sha256_hex",
    "verify_chain",
]
