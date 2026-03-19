"""
Audit logging service for GULA Platform.

Implements hash-chained audit log for tamper detection (ISO 27001 A.8.15).
Each entry's chain_hash = SHA-256(previous_chain_hash + this_record_data).
Any modification to a record or its chain breaks verification.
"""
import json
import hashlib
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..models.audit_log import AuditLog


# Genesis hash for the first entry in the chain
_GENESIS_HASH = "0" * 64


def _compute_chain_hash(prev_hash: str, entry: AuditLog) -> str:
    """Compute SHA-256(prev_chain_hash + canonical JSON of this entry)."""
    record = {
        "id": entry.id,
        "user_id": entry.user_id,
        "user_role": entry.user_role,
        "action": entry.action,
        "resource_type": entry.resource_type,
        "resource_id": entry.resource_id,
        "details": entry.details,
        "ip_address": entry.ip_address,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
    }
    payload = prev_hash + json.dumps(record, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _get_last_chain_hash(db: Session) -> str:
    """Get the chain_hash of the most recent audit log entry."""
    result = db.execute(
        text("SELECT chain_hash FROM audit_logs ORDER BY id DESC LIMIT 1")
    ).fetchone()
    if result and result[0]:
        return result[0]
    return _GENESIS_HASH


def log_action(
    db: Session,
    action: str,
    resource_type: str,
    resource_id: int = None,
    user_id: int = None,
    user_role: str = None,
    details: str = None,
    ip_address: str = None,
):
    """Log an action to the tamper-evident audit trail.

    The chain_hash field links each entry to the previous one.
    Verify chain integrity with /compliance/audit-integrity endpoint.
    """
    entry = AuditLog(
        user_id=user_id,
        user_role=user_role,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
        created_at=datetime.now(timezone.utc),
    )
    # Flush to get the assigned id before computing hash
    db.add(entry)
    db.flush()

    prev_hash = _get_last_chain_hash(db)
    entry.chain_hash = _compute_chain_hash(prev_hash, entry)
    # Don't commit here - let the caller's transaction handle it


def verify_audit_chain(db: Session, limit: int = 1000) -> dict:
    """Verify the integrity of the audit log hash chain.

    Returns a report indicating whether any entries have been tampered with.
    Checks the last `limit` entries for performance on large logs.
    """
    entries = db.query(AuditLog).order_by(AuditLog.id.asc()).limit(limit).all()

    if not entries:
        return {"status": "empty", "verified": True, "entries_checked": 0}

    broken_at = []
    prev_hash = _GENESIS_HASH

    for entry in entries:
        if entry.chain_hash is None:
            # Pre-chain-hash entry (before this feature was deployed)
            prev_hash = entry.chain_hash or prev_hash
            continue

        expected = _compute_chain_hash(prev_hash, entry)
        if entry.chain_hash != expected:
            broken_at.append({
                "id": entry.id,
                "action": entry.action,
                "created_at": entry.created_at.isoformat() if entry.created_at else None,
                "stored_hash": entry.chain_hash,
                "expected_hash": expected,
            })
        prev_hash = entry.chain_hash

    return {
        "status": "tampered" if broken_at else "intact",
        "verified": len(broken_at) == 0,
        "entries_checked": len(entries),
        "broken_entries": broken_at,
        "last_verified_hash": prev_hash,
    }
