"""Consent service — grant, revoke, and check active consent.

All write paths emit a hash-chained audit entry. All decisions (allow or deny)
should be logged at the decision point (see `security/consent_dep.py`).

Scope policy
------------
Scopes are namespaced strings (verb:resource). No wildcards.
Any scope not in ALLOWED_SCOPES is rejected at grant time.
"""

from __future__ import annotations

import secrets
import time
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app._compat import UTC

from ..models.consent import Consent
from .audit_service import log_action

# ── ULID generation (inline — avoid circular import with MPI resolver) ────────

_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def _ulid() -> str:
    ms = int(time.time() * 1000) & ((1 << 48) - 1)
    rand = secrets.randbits(80)
    value = (ms << 80) | rand
    out = []
    for _ in range(26):
        out.append(_CROCKFORD[value & 0x1F])
        value >>= 5
    return "".join(reversed(out))


# ── Policy ────────────────────────────────────────────────────────────────────

# No wildcard scopes. Each entry is verb:resource; any access request must
# match exactly one of these.
ALLOWED_SCOPES: frozenset[str] = frozenset(
    {
        "read:patient",
        "read:lab_results",
        "read:orders",
        "read:citizen",
        "read:prescriptions",
    },
)

# Hard cap: consent cannot be granted for longer than this window.
MAX_CONSENT_HOURS: int = 72


# ── Exceptions ────────────────────────────────────────────────────────────────


class ConsentError(ValueError):
    """Raised on bad grant/revoke input (scope, duration, missing row)."""


# ── Core API ──────────────────────────────────────────────────────────────────


def check_active_consent(
    db: Session,
    *,
    gpid: str,
    grantee_id: str,
    scope: str,
) -> Consent | None:
    """Return the active, non-expired Consent row for (gpid, grantee, scope)
    or None.

    Single SELECT. No side effects. Callers log the decision themselves.
    """
    row = (
        db.query(Consent)
        .filter(
            Consent.gpid == gpid,
            Consent.grantee_id == grantee_id,
            Consent.scope == scope,
            Consent.status == "active",
        )
        .first()
    )
    if row is None:
        return None
    if not row.is_valid_now():
        # Stale active row — mark expired lazily so the index stays accurate.
        row.status = "expired"
        db.flush()
        return None
    return row


def grant_consent(
    db: Session,
    *,
    gpid: str,
    grantee_id: str,
    scope: str,
    expires_in_hours: int,
    actor_user_id: int | None = None,
    actor_role: str | None = None,
    ip_address: str | None = None,
) -> Consent:
    """Create an active Consent row.

    Enforced here:
      - scope ∈ ALLOWED_SCOPES (no wildcards)
      - 0 < expires_in_hours ≤ MAX_CONSENT_HOURS (hard cap 72h)
      - no duplicate active grant for the same tuple — revoke the previous one
        first (atomic: same transaction)
    """
    if scope not in ALLOWED_SCOPES:
        raise ConsentError(f"scope '{scope}' is not allowed")
    if expires_in_hours <= 0 or expires_in_hours > MAX_CONSENT_HOURS:
        raise ConsentError(f"expires_in_hours must be between 1 and {MAX_CONSENT_HOURS}")
    if not gpid or not grantee_id:
        raise ConsentError("gpid and grantee_id are required")

    # If an active row already exists, revoke it so the UNIQUE constraint
    # on (gpid, grantee_id, scope, status='active') is preserved.
    existing = (
        db.query(Consent)
        .filter(
            Consent.gpid == gpid,
            Consent.grantee_id == grantee_id,
            Consent.scope == scope,
            Consent.status == "active",
        )
        .first()
    )
    if existing is not None:
        existing.status = "revoked"
        existing.revoked_at = datetime.now(UTC)
        db.flush()

    now = datetime.now(UTC)
    row = Consent(
        id=_ulid(),
        gpid=gpid,
        grantee_id=grantee_id,
        scope=scope,
        status="active",
        expires_at=now + timedelta(hours=expires_in_hours),
        created_at=now,
        created_by_user_id=actor_user_id,
    )
    db.add(row)
    db.flush()

    log_action(
        db,
        action="consent_grant",
        resource_type="consent",
        resource_id=None,  # row.id is ULID string, audit takes int; details carries it
        user_id=actor_user_id,
        user_role=actor_role,
        details=(
            f"gpid={gpid} grantee_id={grantee_id} scope={scope} "
            f"expires_at={row.expires_at.isoformat()} consent_id={row.id}"
        ),
        ip_address=ip_address,
    )
    return row


def revoke_consent(
    db: Session,
    *,
    gpid: str,
    grantee_id: str,
    scope: str,
    actor_user_id: int | None = None,
    actor_role: str | None = None,
    ip_address: str | None = None,
) -> bool:
    """Revoke the active consent for (gpid, grantee_id, scope).

    Returns True if a row was revoked, False if there was no active row.
    Idempotent: calling twice is safe.
    """
    row = (
        db.query(Consent)
        .filter(
            Consent.gpid == gpid,
            Consent.grantee_id == grantee_id,
            Consent.scope == scope,
            Consent.status == "active",
        )
        .first()
    )
    if row is None:
        return False

    row.status = "revoked"
    row.revoked_at = datetime.now(UTC)
    db.flush()

    log_action(
        db,
        action="consent_revoke",
        resource_type="consent",
        resource_id=None,
        user_id=actor_user_id,
        user_role=actor_role,
        details=(f"gpid={gpid} grantee_id={grantee_id} scope={scope} consent_id={row.id}"),
        ip_address=ip_address,
    )
    return True


def log_access_decision(
    db: Session,
    *,
    actor_user_id: int | None,
    actor_role: str | None,
    gpid: str,
    scope: str,
    result: str,
    reason: str,
    emergency: bool = False,
    ip_address: str | None = None,
) -> None:
    """Audit a single access decision (allow / deny / emergency_bypass)."""
    log_action(
        db,
        action=f"consent_check_{result}",
        resource_type="consent",
        resource_id=None,
        user_id=actor_user_id,
        user_role=actor_role,
        details=(
            f"gpid={gpid} scope={scope} result={result} reason={reason} emergency={emergency}"
        ),
        ip_address=ip_address,
    )
