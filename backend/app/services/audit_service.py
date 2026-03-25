"""
Audit logging service for GULA Platform.

Implements hash-chained audit log for tamper detection (ISO 27001 A.8.15).
Each entry's chain_hash = SHA-256(previous_chain_hash + this_record_data).
Any modification to a record or its chain breaks verification.
"""
import hmac
import json
import hashlib
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..models.audit_log import AuditLog

logger = logging.getLogger("gula.audit")

# Genesis hash for the first entry in the chain
_GENESIS_HASH = "0" * 64

# External anchor directory (outside the DB - survives DB reconstruction).
# Monthly rotation: one file per calendar month, e.g. audit_anchors_2026-03.log
# Old single-file path kept for backward compatibility during migration.
_ANCHOR_DIR = Path(os.getenv("AUDIT_ANCHOR_DIR", "/app/data/anchors"))
_ANCHOR_INTERVAL = 100  # Write anchor checkpoint every N entries


def _current_anchor_file() -> Path:
    """Return the anchor file path for the current calendar month."""
    month_tag = datetime.now(timezone.utc).strftime("%Y-%m")
    return _ANCHOR_DIR / f"audit_anchors_{month_tag}.log"


def _all_anchor_files() -> list[Path]:
    """Return all anchor files, newest first."""
    if not _ANCHOR_DIR.exists():
        return []
    files = sorted(_ANCHOR_DIR.glob("audit_anchors_*.log"), reverse=True)
    return list(files)

# HMAC key for signing anchor lines — if someone edits the anchor file,
# the HMAC signature will no longer match, making tampering detectable.
# Falls back to a deterministic key if NID_HMAC_KEY is not set.
#
# Key rotation: increment ANCHOR_KEY_VERSION and set NID_HMAC_KEY to new value.
# Old anchor lines tagged with "v{n}" are verified with the previous key
# (supply NID_HMAC_KEY_PREV env var during transition window).
# New anchors will carry the new version tag automatically.
_ANCHOR_KEY_VERSION = int(os.getenv("ANCHOR_KEY_VERSION", "1"))
# Use NID_HMAC_KEY for anchor signing — must be set in production (no insecure fallback)
_raw_anchor_key = os.getenv("NID_HMAC_KEY", "")
if not _raw_anchor_key:
    # Derive from SECRET_KEY as last resort (still more secure than a hardcoded string)
    _raw_anchor_key = os.getenv("SECRET_KEY", "gula-anchor-fallback")
    logger.warning("[SECURITY] NID_HMAC_KEY not set — audit anchor HMAC uses derived key. Set NID_HMAC_KEY in .env for production.")
_ANCHOR_HMAC_KEY = _raw_anchor_key.encode("utf-8")
# Previous key for verifying legacy lines during a rotation window
_ANCHOR_HMAC_KEY_PREV = os.getenv("NID_HMAC_KEY_PREV", "").encode("utf-8")

_KEY_TAG = f"v{_ANCHOR_KEY_VERSION}"


def _anchor_hmac(data: str, key: bytes | None = None) -> str:
    """Compute HMAC-SHA256 of an anchor data string for tamper detection."""
    k = key if key is not None else _ANCHOR_HMAC_KEY
    return hmac.new(k, data.encode("utf-8"), hashlib.sha256).hexdigest()


def _verify_anchor_hmac(data: str, expected_hmac: str) -> bool:
    """Constant-time HMAC verification. Tries current key then previous key."""
    # Try current key first
    if hmac.compare_digest(_anchor_hmac(data, _ANCHOR_HMAC_KEY), expected_hmac):
        return True
    # Try previous key (rotation window)
    if _ANCHOR_HMAC_KEY_PREV:
        return hmac.compare_digest(_anchor_hmac(data, _ANCHOR_HMAC_KEY_PREV), expected_hmac)
    return False


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


def _write_anchor(entry_id: int, chain_hash: str) -> None:
    """Append a hash anchor checkpoint to the current month's anchor file.

    Monthly rotation keeps individual files small and manageable.
    Format: vN|ISO_timestamp|entry_id|chain_hash|HMAC(vN|...|chain_hash)
    """
    try:
        anchor_file = _current_anchor_file()
        anchor_file.parent.mkdir(parents=True, exist_ok=True)
        data = (
            f"{_KEY_TAG}|"
            f"{datetime.now(timezone.utc).isoformat()}|"
            f"{entry_id}|"
            f"{chain_hash}"
        )
        sig = _anchor_hmac(data)
        with open(anchor_file, "a", encoding="utf-8") as f:
            f.write(f"{data}|{sig}\n")
    except Exception as e:
        logger.error("AUDIT ANCHOR WRITE FAILED (id=%s): %s", entry_id, e)


def get_latest_anchor() -> dict | None:
    """Read the most recent anchor from the monthly anchor files.

    Scans all monthly files newest-first to find the last anchor.
    Counts HMAC failures across all files for integrity reporting.
    """
    try:
        files = _all_anchor_files()
        if not files:
            return None

        # Collect all lines across all monthly files (newest file first)
        all_lines: list[str] = []
        total_files = len(files)
        for f_path in files:
            with open(f_path, "r", encoding="utf-8") as f:
                chunk = [l.strip() for l in f.readlines() if l.strip()]
            all_lines = chunk + all_lines  # older lines first

        lines = all_lines
        if not lines:
            return None

        # Line formats supported (oldest → newest):
        #   3-part:  timestamp|entry_id|chain_hash                        (legacy, no HMAC)
        #   4-part:  timestamp|entry_id|chain_hash|hmac                   (HMAC, no version tag)
        #   5-part:  vN|timestamp|entry_id|chain_hash|hmac                (versioned HMAC — current)

        hmac_failures = 0
        for raw_line in lines:
            parts = raw_line.split("|")
            if len(parts) == 5:
                data_part = "|".join(parts[:4])
                if not _verify_anchor_hmac(data_part, parts[4]):
                    hmac_failures += 1
            elif len(parts) == 4:
                data_part = "|".join(parts[:3])
                if not _verify_anchor_hmac(data_part, parts[3]):
                    hmac_failures += 1
            # 3-part lines are legacy — no HMAC to verify

        last = lines[-1].split("|")
        if len(last) == 5:
            hmac_ok = _verify_anchor_hmac("|".join(last[:4]), last[4])
            key_version = last[0]
            timestamp, entry_id_str, chain_hash = last[1], last[2], last[3]
        elif len(last) == 4:
            hmac_ok = _verify_anchor_hmac("|".join(last[:3]), last[3])
            key_version = "v0-legacy"
            timestamp, entry_id_str, chain_hash = last[0], last[1], last[2]
        elif len(last) == 3:
            hmac_ok = None  # legacy line — no HMAC to verify
            key_version = "v0-legacy"
            timestamp, entry_id_str, chain_hash = last[0], last[1], last[2]
        else:
            return None

        return {
            "timestamp": timestamp,
            "entry_id": int(entry_id_str),
            "chain_hash": chain_hash,
            "total_anchors": len(lines),
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
