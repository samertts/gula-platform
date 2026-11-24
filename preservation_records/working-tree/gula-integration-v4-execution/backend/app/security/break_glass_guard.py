"""B2 — server-verified, fail-closed break-glass authorization.

Owner directive GULA-MASTER-AUTH-2026-11-19 §5/B2 (AUD-PRV-002).

The previous consent dependency allowed any caller who set the client-supplied
``X-Emergency-Access: true`` header and happened to hold ``role == 'doctor'``
to bypass consent entirely. A header is an *intent signal*, never proof of an
emergency. This module replaces that check with verification of a
server-persisted ``BreakGlassSession``.

Security invariants:

1. Consent and break-glass are SEPARATE. A break-glass session never creates or
   implies a consent row, and a consent grant never activates break-glass.
2. Break-glass requires an active, unexpired, non-deactivated session bound to
   the authenticated actor and to the specific subject being accessed.
3. Only eligible clinical roles may break glass; only read scopes are eligible
   (the policy explicitly excludes export/delete/financial/user-management).
4. Justification, emergency category and duration are policy-validated.
5. Fail closed: any missing, ambiguous, expired, deactivated, mismatched or
   malformed condition denies with a specific reason code.
6. Iraqi legal rule dependencies (eligible categories, review windows and
   Ministry ratification) are declared here as POLICY DEPENDENCIES. This module
   enforces only the technology-neutral invariants; it does not fabricate a
   legal entitlement. See ``BREAK_GLASS_POLICY.md`` and the B2 report.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app._compat import UTC
from app.models.authorization import BreakGlassSession
from app.services.mpi.models import BrokenCanonicalChainError, Citizen, IdentityClaim

# ── Policy (technology-neutral invariants) ────────────────────────────────────

# Clinical roles eligible for break-glass. Kept conservative: administrative,
# finance, service-account and auditor roles are intentionally excluded.
ELIGIBLE_CLINICAL_ROLES = frozenset(
    {
        "doctor", "physician", "specialist", "consultant", "surgeon", "resident",
        "intern", "dentist", "pathologist", "microbiologist", "radiologist",
        "paramedic", "nurse",
    }
)

# Break-glass grants READ-ONLY access. Export/delete/financial/user-management
# operations are never eligible (BREAK_GLASS_POLICY.md §4.1).
BREAK_GLASS_SCOPE_PREFIX = "read:"

# Emergency categories aligned with BREAK_GLASS_POLICY.md §2. Jurisdiction-
# specific extensions are a POLICY DEPENDENCY and must be ratified by the
# Ministry; they are never inferred from a client value.
ALLOWED_EMERGENCY_CATEGORIES = frozenset(
    {
        "patient_critical", "missing_physician", "system_failure",
        "natural_disaster", "epidemic_outbreak", "time_sensitive_decision",
        "equipment_failure", "emergency",
    }
)

MIN_JUSTIFICATION_LENGTH = 20
MAX_BREAK_GLASS_MINUTES = 240  # 4h clinical default; extensions need approval.


@dataclass(frozen=True)
class BreakGlassAuthorization:
    allowed: bool
    reason: str
    session_id: int | None = None
    category: str | None = None
    has_active_session: bool = False


def _deny(reason: str, *, has_active_session: bool = False) -> BreakGlassAuthorization:
    return BreakGlassAuthorization(
        allowed=False, reason=reason, has_active_session=has_active_session,
    )


def _as_utc(value: datetime | None) -> datetime | None:
    """Normalize a DB timestamp to UTC-aware; treat naive values as UTC.

    PostgreSQL returns tz-aware values while SQLite (disposable tests) returns
    naive ones. Both must be compared safely or a valid session is wrongly
    denied / an expired one wrongly allowed.
    """
    if value is None:
        return None
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def validate_break_glass_activation(
    *,
    role: str,
    emergency_category: str,
    justification: str,
    patient_id: int | None,
    duration_minutes: int,
) -> None:
    """Fail-closed validation at activation time (defense in depth).

    Raises ``ValueError`` with a stable reason code when the requested session
    violates policy. The use-time guard re-checks every invariant, so a session
    that bypassed this function would still be inert.
    """
    if role not in ELIGIBLE_CLINICAL_ROLES:
        raise ValueError("ineligible_role")
    if emergency_category not in ALLOWED_EMERGENCY_CATEGORIES:
        raise ValueError("invalid_emergency_category")
    if not justification or len(justification.strip()) < MIN_JUSTIFICATION_LENGTH:
        raise ValueError("justification_too_short")
    if patient_id is None:
        raise ValueError("patient_id_required")
    if duration_minutes <= 0 or duration_minutes > MAX_BREAK_GLASS_MINUTES:
        raise ValueError("invalid_duration")


def resolve_subject_patient_ids(db: Session, gpid: str) -> set[int]:
    """Resolve a citizen ULID to its local patient ids through canonical MPI.

    Follows ``merged_into`` to the surviving citizen and reads every
    ``IdentityClaim``. An empty set means the subject cannot be resolved and
    callers must fail closed.
    """
    citizen = db.query(Citizen).filter(Citizen.citizen_ulid == gpid).first()
    if citizen is None:
        return set()
    if citizen.status != "active":
        return set()
    try:
        canonical = citizen.canonical(strict=True)
    except BrokenCanonicalChainError:
        # A broken/ambiguous merge chain is never resolved optimistically.
        return set()
    if canonical.id is None:
        return set()
    claims = db.query(IdentityClaim).filter(IdentityClaim.citizen_id == canonical.id).all()
    return {claim.local_patient_id for claim in claims if claim.local_patient_id is not None}


def authorize_break_glass(
    db: Session,
    *,
    user_id: int,
    role: str,
    gpid: str,
    scope: str,
) -> BreakGlassAuthorization:
    """Verify a server-side break-glass session for this actor/subject/scope."""
    # 1. Role eligibility — never trust a client role; this is the authenticated
    #    principal's server-side role from the resolved LabUser.
    if role not in ELIGIBLE_CLINICAL_ROLES:
        return _deny("ineligible_role")

    # 2. Scope eligibility — break-glass is read-only.
    if not scope.startswith(BREAK_GLASS_SCOPE_PREFIX):
        return _deny("scope_ineligible_for_break_glass")

    # 3. Active session for THIS actor.
    now = datetime.now(UTC)
    session = (
        db.query(BreakGlassSession)
        .filter(
            BreakGlassSession.user_id == user_id,
            BreakGlassSession.status == "active",
        )
        .order_by(BreakGlassSession.started_at.desc())
        .first()
    )
    if session is None:
        return _deny("no_active_break_glass_session")

    # An active row exists but may still be invalid — record that signal so the
    # dependency audits an attempted break-glass rather than a plain consent miss.
    invalid_with_session = True

    if session.deactivated_at is not None:
        return _deny("break_glass_deactivated", has_active_session=invalid_with_session)
    expires_at = _as_utc(session.expires_at)
    if expires_at is None or expires_at <= now:
        return _deny("break_glass_expired", has_active_session=invalid_with_session)
    if not session.justification or len(session.justification.strip()) < MIN_JUSTIFICATION_LENGTH:
        return _deny("justification_too_short", has_active_session=invalid_with_session)
    if session.emergency_category not in ALLOWED_EMERGENCY_CATEGORIES:
        return _deny("invalid_emergency_category", has_active_session=invalid_with_session)

    # 4. Patient scoping — the session must be bound to the exact subject.
    patient_ids = resolve_subject_patient_ids(db, gpid)
    if not patient_ids:
        return _deny("subject_unresolvable", has_active_session=invalid_with_session)
    if session.patient_id is None or session.patient_id not in patient_ids:
        return _deny("subject_not_in_break_glass_scope", has_active_session=invalid_with_session)

    return BreakGlassAuthorization(
        allowed=True,
        reason="break_glass_verified",
        session_id=session.id,
        category=session.emergency_category,
        has_active_session=True,
    )
