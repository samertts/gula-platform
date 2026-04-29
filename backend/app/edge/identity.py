"""Device identity & cryptographic helpers.

Section 6 (Device Identity & Trust):
  - Each device gets a unique device_id (ULID-style)
  - Devices present a public key at registration; server stores its fingerprint
  - Tasks are HMAC-signed by the server with EDGE_TASK_SIGNING_KEY
  - Heartbeats include a per-call signature over a server-issued nonce
  - Key rotation is supported via EDGE_TASK_SIGNING_KEY_PREV (verifier accepts both)
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from typing import Any

from .config import get_task_signing_key


# ── Device IDs ────────────────────────────────────────────────────────────────

_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def new_device_id() -> str:
    """Return a fresh ULID-style 26-char device identifier prefixed with 'EDG'."""
    ms = int(time.time() * 1000) & ((1 << 48) - 1)
    rand = secrets.randbits(80)
    value = (ms << 80) | rand
    out: list[str] = []
    for _ in range(26):
        out.append(_CROCKFORD[value & 0x1F])
        value >>= 5
    return "EDG" + "".join(reversed(out))


def new_task_uid() -> str:
    """36-char task UID (ULID-style with TSK prefix)."""
    ms = int(time.time() * 1000) & ((1 << 48) - 1)
    rand = secrets.randbits(80)
    value = (ms << 80) | rand
    out: list[str] = []
    for _ in range(26):
        out.append(_CROCKFORD[value & 0x1F])
        value >>= 5
    return "TSK" + "".join(reversed(out))


# ── Public-key fingerprints ───────────────────────────────────────────────────

def fingerprint_pem(public_key_pem: str) -> str:
    """Stable SHA-256 fingerprint of a PEM-encoded public key.

    Whitespace is normalized so cosmetic re-formatting does not change the
    fingerprint (which would otherwise allow a re-registration attack).
    """
    canon = "\n".join(line.strip() for line in public_key_pem.strip().splitlines())
    digest = hashlib.sha256(canon.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


# ── HMAC task signing ─────────────────────────────────────────────────────────

def _canon_payload(payload: dict[str, Any]) -> bytes:
    """Stable JSON serialization for signing — sorted keys, no whitespace."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_task(task_uid: str, kind: str, payload: dict[str, Any] | None) -> str:
    """Return an HMAC-SHA256 signature over (task_uid, kind, canon(payload))."""
    msg = (task_uid + "|" + kind + "|").encode("utf-8")
    if payload:
        msg += _canon_payload(payload)
    return hmac.new(get_task_signing_key(), msg, hashlib.sha256).hexdigest()


def verify_task_signature(
    task_uid: str, kind: str, payload: dict[str, Any] | None, sig: str,
) -> bool:
    """Constant-time verification, accepts both current and previous keys."""
    import os as _os
    expected = sign_task(task_uid, kind, payload)
    if hmac.compare_digest(expected, sig):
        return True
    prev = _os.getenv("EDGE_TASK_SIGNING_KEY_PREV", "")
    if not prev:
        return False
    msg = (task_uid + "|" + kind + "|").encode("utf-8")
    if payload:
        msg += _canon_payload(payload)
    expected_prev = hmac.new(prev.encode("utf-8"), msg, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected_prev, sig)


# ── Agent challenge / nonce ───────────────────────────────────────────────────

def make_nonce() -> str:
    """Random 32-byte hex nonce. Issued at registration; agent must echo and
    sign it on the next heartbeat to prove possession of its private key.
    """
    return secrets.token_hex(32)
