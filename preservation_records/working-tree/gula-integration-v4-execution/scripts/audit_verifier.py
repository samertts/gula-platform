#!/usr/bin/env python3
"""GULA Platform - Audit Integrity Verifier.

Verifies the SHA-256 hash chain of ``audit_logs`` using the single canonical
implementation in ``app.services.audit_service.verify_audit_chain``. No local
hash computation is performed (AUD-F04).

Exit codes (consumed by ``scripts/gula_guardian.py::verify_audit_chain``):
    0 - chain intact or empty
    1 - tampering detected
    2 - verification error (guardian still alerts because the code is non-zero)

Only reads are performed. No audit row is written, no daemon is restarted and
no deployment is triggered by this script.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Callable
from typing import Any

# Add backend to path to import models and the canonical verifier.
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

try:
    from app.database import SessionLocal
    from app.models.audit_log import AuditLog
    from app.services import audit_service as canonical
    from sqlalchemy import func
except ImportError:
    sys.stderr.write("Error: Could not import backend modules. Run from the scripts directory.\n")
    sys.exit(1)

EXIT_OK = 0
EXIT_TAMPERED = 1
EXIT_ERROR = 2

# The canonical helper caps its query with ``limit`` (default 1000). Use the
# actual row count plus a small buffer so concurrent inserts are not skipped.
_VERIFY_BUFFER = 1000


def verify_chain(db: Any | None = None, output: Callable[[str], None] = print) -> int:
    """Verify the full chain through the canonical algorithm; return an exit code."""
    owns_session = db is None
    if owns_session:
        db = SessionLocal()
    try:
        output("Starting Audit Log Integrity Verification...")
        total = int(db.query(func.count(AuditLog.id)).scalar() or 0)
        result = canonical.verify_audit_chain(db, limit=max(total + _VERIFY_BUFFER, 1))

        if result["status"] == "empty":
            output("[✓] Audit log is empty. Nothing to verify.")
            return EXIT_OK

        broken = result.get("broken_entries") or []
        for row in broken:
            output(f"[✗] TAMPER DETECTED at Record ID: {row['id']}")
            output(f"    Expected: {row['expected_hash']}")
            output(f"    Stored:   {row['stored_hash']}")

        if not broken:
            output(f"[✓] Integrity Verified. All {result['entries_checked']} records are valid.")
            return EXIT_OK

        output(f"[!] Critical: Found {len(broken)} corrupted or tampered records.")
        return EXIT_TAMPERED
    except Exception as exc:  # guardian must alert on verification failure too
        output(f"[!] Audit verification error: {type(exc).__name__}")
        return EXIT_ERROR
    finally:
        if owns_session:
            db.close()


def main() -> int:
    return verify_chain()


if __name__ == "__main__":
    sys.exit(main())
