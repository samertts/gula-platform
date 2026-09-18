"""Audit logging service — canonical shared.audit with backend-specific extensions.

Hash-chained audit log for tamper detection (ISO 27001 A.8.15).
Each entry's chain_hash = SHA-256(previous_chain_hash + this_record_data).

Delegates core chain computation and entry creation to shared.audit,
while maintaining backend-specific anchor file HMAC checkpoints.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

from app._compat import UTC

from ..config import AUDIT_ANCHOR_KEY
from ..models.audit_log import AuditLog

logger = logging.getLogger("gula.audit")

_GENESIS_HASH = "0" * 64

_ANCHOR_DIR = Path(os.getenv("AUDIT_ANCHOR_DIR", "/app/data/anchors"))
_ANCHOR_INTERVAL = 100

_ANCHOR_KEY_VERSION = int(os.getenv("ANCHOR_KEY_VERSION", "1"))

_raw_anchor_key = os.getenv("AUDIT_ANCHOR_KEY", "")
if not _raw_anchor_key:
    if not AUDIT_ANCHOR_KEY:
        sys.exit(1)
    _raw_anchor_key = AUDIT_ANCHOR_KEY
_ANCHOR_HMAC_KEY = _raw_anchor_key.encode("utf-8")
_ANCHOR_HMAC_KEY_PREV = os.getenv("AUDIT_ANCHOR_KEY_PREV", "").encode("utf-8")
_KEY_TAG = f"v{_ANCHOR_KEY_VERSION}"


def _canonical_audit_timestamp(value: datetime | None) -> str | None:
    """Return a dialect-independent UTC timestamp for chain hashing.

    PostgreSQL preserves timezone information while SQLite may return a naive
    datetime for DateTime(timezone=True). Treating a naive persisted value as
    UTC makes write-time and verification-time hashes identical across both
    supported dialects without changing the stored schema.
    """
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    else:
        value = value.astimezone(UTC)
    return value.isoformat(timespec="microseconds")


def _current_anchor_file() -> Path:
    month_tag = datetime.now(UTC).strftime("%Y-%m")
    return _ANCHOR_DIR / f"audit_anchors_{month_tag}.log"


def _all_anchor_files() -> list[Path]:
    if not _ANCHOR_DIR.exists():
        return []
    files = sorted(_ANCHOR_DIR.glob("audit_anchors_*.log"), reverse=True)
    return list(files)


def _anchor_hmac(data: str, key: bytes | None = None) -> str:
    k = key if key is not None else _ANCHOR_HMAC_KEY
    return hmac.new(k, data.encode("utf-8"), hashlib.sha256).hexdigest()


def _verify_anchor_hmac(data: str, expected_hmac: str) -> bool:
    if hmac.compare_digest(_anchor_hmac(data, _ANCHOR_HMAC_KEY), expected_hmac):
        return True
    if _ANCHOR_HMAC_KEY_PREV:
        return hmac.compare_digest(_anchor_hmac(data, _ANCHOR_HMAC_KEY_PREV), expected_hmac)
    return False


def _compute_chain_hash(prev_hash: str, entry: AuditLog) -> str:
    record = {
        "id": entry.id,
        "user_id": entry.user_id,
        "user_role": entry.user_role,
        "action": entry.action,
        "resource_type": entry.resource_type,
        "resource_id": entry.resource_id,
        "details": entry.details,
        "ip_address": entry.ip_address,
        "created_at": _canonical_audit_timestamp(entry.created_at),
    }
    payload = prev_hash + json.dumps(record, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _get_last_chain_hash(db: Session) -> str:
    result = db.execute(
        text("SELECT chain_hash FROM audit_logs ORDER BY id DESC LIMIT 1"),
    ).fetchone()
    if result and result[0]:
        return result[0]
    return _GENESIS_HASH


def _write_anchor(entry_id: int, chain_hash: str) -> None:
    try:
        anchor_file = _current_anchor_file()
        anchor_file.parent.mkdir(parents=True, exist_ok=True)
        data = f"{_KEY_TAG}|{datetime.now(UTC).isoformat()}|{entry_id}|{chain_hash}"
        sig = _anchor_hmac(data)
        with open(anchor_file, "a", encoding="utf-8") as f:
            f.write(f"{data}|{sig}\n")
    except Exception as e:
        logger.error("AUDIT ANCHOR WRITE FAILED (id=%s): %s", entry_id, e)


def get_latest_anchor() -> dict | None:
    try:
        files = _all_anchor_files()
        if not files:
            return None

        all_lines: list[str] = []
        for f_path in files:
            with open(f_path, encoding="utf-8") as f:
                chunk = [line.strip() for line in f if line.strip()]
            all_lines = chunk + all_lines

        if not all_lines:
            return None

        hmac_failures = 0
        for raw_line in all_lines:
            parts = raw_line.split("|")
            if len(parts) == 5:
                if not _verify_anchor_hmac("|".join(parts[:4]), parts[4]):
                    hmac_failures += 1
            elif len(parts) == 4 and not _verify_anchor_hmac("|".join(parts[:3]), parts[3]):
                hmac_failures += 1

        last = all_lines[-1].split("|")
        if len(last) == 5:
            hmac_ok = _verify_anchor_hmac("|".join(last[:4]), last[4])
            key_version = last[0]
            timestamp, entry_id_str, chain_hash = last[1], last[2], last[3]
        elif len(last) == 4:
            hmac_ok = _verify_anchor_hmac("|".join(last[:3]), last[3])
            key_version = "v0-legacy"
            timestamp, entry_id_str, chain_hash = last[0], last[1], last[2]
        elif len(last) == 3:
            hmac_ok = None
            key_version = "v0-legacy"
            timestamp, entry_id_str, chain_hash = last[0], last[1], last[2]
        else:
            return None

        return {
            "timestamp": timestamp,
            "entry_id": int(entry_id_str),
            "chain_hash": chain_hash,
            "total_anchors": len(all_lines),
            "total_monthly_files": len(files),
            "hmac_verified": hmac_ok,
            "hmac_failures": hmac_failures,
            "key_version": key_version,
            "anchor_dir": str(_ANCHOR_DIR),
            "current_file": str(_current_anchor_file().name),
        }
    except Exception as e:
        logger.warning("Could not read anchor file: %s", e)
        return None


def normalize_resource_id(resource_id: str | int | None) -> int | None:
    """Fit a resource identifier to audit_logs.resource_id, which is INTEGER.

    Most domains outside the legacy core key their rows with a varchar
    identifier -- a UUID, a ULID, a 26-character blood bank key. Passing one
    through raises DataError from inside this module and takes the caller's
    whole transaction with it, so an audit attempt breaks the operation it was
    meant to record (NR-027).

    Returns None for anything that is not integer-like. The caller is expected
    to keep the unabridged identifier in `details`, so identity is preserved
    even though the typed column cannot hold it.

    This is the CANONICAL implementation. It existed independently in
    ClinicalCommandGuard and in the blood bank service, which is exactly the
    drift that let the blood bank update path and create path disagree about
    tenant ownership under NR-105. One copy, three callers.
    """
    if resource_id is None:
        return None
    try:
        return int(resource_id)
    except (TypeError, ValueError):
        return None


def log_action(
    db: Session,
    action: str,
    resource_type: str,
    resource_id: int | None = None,
    user_id: int | None = None,
    user_role: str | None = None,
    lab_id: int | None = None,
    details: str | dict[str, object] | None = None,
    ip_address: str | None = None,
):
    """Log an action to the tamper-evident audit trail. Delegates chain hash
    computation to shared.audit while maintaining backend anchor files.
    """
    serialized_details = (
        # `default=str` renders values json has no encoding for — a datetime,
        # a Decimal, a UUID. Without it a clinical mutation carrying a
        # timestamp in its details raised TypeError from inside the audit
        # writer and took the whole transaction down with it. No audit row can
        # already hold such a value, so no existing chain hash changes.
        json.dumps(details, sort_keys=True, ensure_ascii=False,
                   separators=(",", ":"), default=str)
        if isinstance(details, dict)
        else details
    )
    entry = AuditLog(
        user_id=user_id,
        user_role=user_role,
        lab_id=lab_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=serialized_details,
        ip_address=ip_address,
        created_at=datetime.now(UTC),
    )
    bind = db.get_bind()
    if bind is not None and bind.dialect.name == "postgresql":
        # The append-only trigger correctly rejects UPDATE, so reserve the
        # serial ID before INSERT and compute the hash on the final row image.
        next_id = db.execute(
            text("SELECT nextval(pg_get_serial_sequence('audit_logs', 'id'))"),
        ).scalar_one()
        entry.id = int(next_id)
        prev_hash = _get_last_chain_hash(db)
        entry.chain_hash = _compute_chain_hash(prev_hash, entry)
        db.add(entry)
        db.flush()
    else:
        db.add(entry)
        db.flush()
        prev_hash = _get_last_chain_hash(db)
        entry.chain_hash = _compute_chain_hash(prev_hash, entry)
        db.flush()
    # Write anchor checkpoint every N entries
    if entry.id % _ANCHOR_INTERVAL == 0:
        _write_anchor(entry.id, entry.chain_hash)



def verify_audit_chain(db: Session, limit: int = 1000) -> dict:
    entries = db.query(AuditLog).order_by(AuditLog.id.asc()).limit(limit).all()

    if not entries:
        return {"status": "empty", "verified": True, "entries_checked": 0}

    broken_at = []
    prev_hash = _GENESIS_HASH

    for entry in entries:
        if entry.chain_hash is None:
            prev_hash = entry.chain_hash or prev_hash
            continue
        expected = _compute_chain_hash(prev_hash, entry)
        if entry.chain_hash != expected:
            broken_at.append(
                {
                    "id": entry.id,
                    "action": entry.action,
                    "created_at": entry.created_at.isoformat() if entry.created_at else None,
                    "stored_hash": entry.chain_hash,
                    "expected_hash": expected,
                },
            )
        prev_hash = entry.chain_hash

    return {
        "status": "tampered" if broken_at else "intact",
        "verified": len(broken_at) == 0,
        "entries_checked": len(entries),
        "broken_entries": broken_at,
        "last_verified_hash": prev_hash,
    }
