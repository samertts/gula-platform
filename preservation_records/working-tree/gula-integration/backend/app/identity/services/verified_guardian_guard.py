"""B3 — verified guardian / minor / NHID access policy (fail-closed).

Owner directive GULA-MASTER-AUTH-2026-11-19 §5/B3 (AUD-PRV-005).

This module is a thin POLICY layer over canonical primitives. It introduces no
new identity store, no new authorization engine and, critically, **no new
national identifier**: a canonical NHID is `NEEDS_OWNER_DECISION / BLOCKED`
(`GOVERNANCE/IDENTITY_REMEDIATION/NHID_CANONICALIZATION_READINESS.md`). The only
sanctioned identifier input contract used here is the canonical NID
normalization/hash in ``app.services.identity``.

Canonical primitives reused:

* ``CitizenRelationship`` / ``CitizenRelationshipWorkflow`` — explicit, verified,
  revocable account-to-citizen linkage (no matching/backfill/dual-write).
* ``GuardianRulesService`` — the canonical action-level guardian rule table.
* ``Citizen`` (``national_citizens``) — DOB, identity status, merge/decease state.
* ``hash_national_id`` / ``normalize_national_id`` — the only sanctioned NHID
  input contract.

Protected decisions (HOLD, MPI REJECT, MP-001, ODR-001…004, D-020/D-021,
ADR-A…J, AUD-02/07/16) are never touched by this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from app.identity.models.citizen_relationship import CitizenRelationship
from app.national.domain.citizen import Citizen
from app.national.security.guardian_rules import GuardianRulesService
from app.services.identity import hash_national_id, normalize_national_id

# ── Policy constants (technology-neutral; jurisdiction specifics are deps) ───

AGE_OF_MAJORITY = 18
AGE_OF_REASONING = 16
REVERIFICATION_WINDOW_DAYS = 90

# The only relationship type that confers guardian authority, and the only
# purposes under which such a relationship may be used for access.
GUARDIAN_RELATIONSHIP_TYPE = "guardian"
GUARDIAN_PURPOSES = frozenset({"guardian_access", "minor_guardian"})

# Canonical authorization actions -> canonical GuardianRulesService actions.
# Any action absent from this map is DENIED (fail closed): guardians never get
# export/delete/financial/user-management authority by default.
_GUARDIAN_ACTION_MAP = {
    "read": "access_records",
    "list": "access_records",
    "view": "access_records",
    "access_records": "access_records",
    "receive_results": "receive_results",
    "consent": "consent",
    "appointments": "appointments",
    "authorize_treatment": "authorize_treatment",
}

_VERIFIER_ROLES = frozenset(
    {
        "master_admin", "security_administrator", "ministry_admin",
        "organization_administrator", "compliance_officer",
    }
)


class GuardianPolicyError(ValueError):
    """Fail-closed policy violation with a stable reason code."""


@dataclass(frozen=True)
class GuardianAccessDecision:
    allowed: bool
    reason: str
    age: int | None = None
    transition: str | None = None
    guardian_type: str | None = None
    requires_reverification: bool = False


def _deny(
    reason: str,
    *,
    age: int | None = None,
    transition: str | None = None,
    guardian_type: str | None = None,
) -> GuardianAccessDecision:
    return GuardianAccessDecision(
        allowed=False, reason=reason, age=age, transition=transition,
        guardian_type=guardian_type,
    )


# ── Age derivation & transitions ─────────────────────────────────────────────


def derive_age(
    birth_date: date | datetime | None,
    *,
    today: date | None = None,
) -> int:
    """Derive whole years from a server-side DOB. Never trusts a client flag.

    Fails closed (raises :class:`GuardianPolicyError`) on missing, future or
    implausible dates rather than guessing an age.
    """
    if birth_date is None:
        raise GuardianPolicyError("birth_date_missing")
    if isinstance(birth_date, datetime):
        birth_date = birth_date.date()
    today = today or date.today()
    if birth_date > today:
        raise GuardianPolicyError("birth_date_in_future")
    age = (
        today.year
        - birth_date.year
        - ((today.month, today.day) < (birth_date.month, birth_date.day))
    )
    if age < 0 or age > 130:
        raise GuardianPolicyError("birth_date_implausible")
    return age


def _days_until_next_birthday(birth_date: date, today: date) -> int:
    next_birthday = date(today.year, birth_date.month, birth_date.day)
    if next_birthday < today:
        next_birthday = date(today.year + 1, birth_date.month, birth_date.day)
    return (next_birthday - today).days


def age_transition(
    birth_date: date | datetime | None,
    *,
    today: date | None = None,
) -> str:
    """Classify a minor's age-transition state.

    * ``adult`` (≥18): guardian authority has ended.
    * ``near_majority`` (17, within the re-verification window): authority is
      about to end and must be re-verified before it can be exercised.
    * ``reasoning`` (16-17): limited autonomy; canonical guardian rules apply.
    * ``pre_reasoning`` (<16): full guardian authority where the rule table allows.
    """
    today = today or date.today()
    age = derive_age(birth_date, today=today)
    if age >= AGE_OF_MAJORITY:
        return "adult"
    if (
        age == AGE_OF_MAJORITY - 1
        and isinstance(birth_date, (date, datetime))
        and _days_until_next_birthday(
            birth_date.date() if isinstance(birth_date, datetime) else birth_date, today,
        )
        <= REVERIFICATION_WINDOW_DAYS
    ):
        return "near_majority"
    if age >= AGE_OF_REASONING:
        return "reasoning"
    return "pre_reasoning"


# ── NHID input contract (canonical only; no identifier is minted) ────────────


def canonical_nid_hash(nid_input: str | None) -> str:
    """Validate an NHID/NID *input* through the single canonical contract.

    Returns the canonical HMAC hash for correlation only. It never persists or
    mints an identifier and never treats the raw input as proof of identity.
    """
    if not nid_input:
        raise GuardianPolicyError("nid_input_missing")
    normalized = normalize_national_id(nid_input)
    if not normalized:
        raise GuardianPolicyError("nid_input_invalid")
    digest = hash_national_id(nid_input)
    if not digest:
        raise GuardianPolicyError("nid_input_invalid")
    # A canonical NID is a digit string; separators and digit-script variants
    # must all collapse to the same normalized form.
    if not normalized.isdigit():
        raise GuardianPolicyError("nid_input_invalid")
    return digest


def assert_no_twin_merge(citizen_a: Citizen, citizen_b: Citizen) -> None:
    """TWINS-NEVER-MERGED: fail closed on weak-identity collisions.

    Two *distinct* citizen records must never be auto-merged merely because
    their blocking key and DOB match, or because a canonical NID hash collides.
    Identity resolution for guardian linkage is deterministic and conservative.
    """
    a_id = getattr(citizen_a, "id", None)
    b_id = getattr(citizen_b, "id", None)
    if a_id is not None and a_id == b_id:
        return  # same record — not a merge
    a_hash = getattr(citizen_a, "national_id_hash", None)
    b_hash = getattr(citizen_b, "national_id_hash", None)
    if a_hash and b_hash and a_hash == b_hash:
        raise GuardianPolicyError("ambiguous_identity_twins_never_merged")
    a_block = getattr(citizen_a, "name_blocking_key", None)
    b_block = getattr(citizen_b, "name_blocking_key", None)
    a_dob = getattr(citizen_a, "date_of_birth", None)
    b_dob = getattr(citizen_b, "date_of_birth", None)
    if a_block and a_block == b_block and a_dob is not None and a_dob == b_dob:
        raise GuardianPolicyError("ambiguous_identity_twins_never_merged")


def subject_is_linkable(subject: Citizen | None) -> bool:
    """A merged, deceased or non-active citizen cannot be a guardian subject."""
    if subject is None:
        return False
    if getattr(subject, "merged_into_id", None):
        return False
    if getattr(subject, "is_deceased", False):
        return False
    status = getattr(subject, "identity_status", None)
    return status is None or str(getattr(status, "value", status)).lower() == "active"


def is_authorized_verifier_role(role: str | None) -> bool:
    """Guardian relationships require an explicitly authorized verifier role.

    The subject themselves can never self-assert guardianship.
    """
    return bool(role) and role in _VERIFIER_ROLES


# ── Main decision ────────────────────────────────────────────────────────────


def evaluate_guardian_access(
    *,
    subject: Citizen | None,
    relationship: CitizenRelationship | None,
    action: str,
    guardian_type: str | None = None,
    nhid_input: str | None = None,
    today: date | None = None,
    now: datetime | None = None,
    reverified_at_transition: bool = False,
) -> GuardianAccessDecision:
    """Fail-closed decision for guardian access to a minor's data.

    Every check must pass; any missing/ambiguous condition denies with a stable
    reason code. No legal entitlement is fabricated — jurisdiction-specific
    Iraqi rules remain documented policy dependencies.
    """
    # 1. Subject integrity (merged/deceased/inactive/unknown -> deny).
    if not subject_is_linkable(subject):
        return _deny("subject_not_linkable")

    # 2. Age is derived server-side from DOB, never from a client `is_minor` flag.
    try:
        age = derive_age(subject.date_of_birth, today=today)  # type: ignore[union-attr]
        transition = age_transition(subject.date_of_birth, today=today)  # type: ignore[arg-type]
    except GuardianPolicyError as exc:
        return _deny(str(exc))
    if age >= AGE_OF_MAJORITY:
        return _deny("guardian_authority_ended", age=age, transition="adult")

    # 3. An explicit, verified, active guardian relationship is mandatory.
    if relationship is None:
        return _deny("no_guardian_relationship", age=age, transition=transition)
    if relationship.relationship_type != GUARDIAN_RELATIONSHIP_TYPE:
        return _deny("not_guardian_relationship", age=age, transition=transition)
    if not relationship.is_active_at(now=now):
        return _deny("guardian_relationship_not_active", age=age, transition=transition)
    if relationship.verified_at is None:
        return _deny("guardian_relationship_unverified", age=age, transition=transition)
    metadata = relationship.metadata_ if isinstance(relationship.metadata_, dict) else {}
    if metadata.get("source_verified") is not True and metadata.get("guardian_verified") is not True:
        return _deny("guardian_not_verified", age=age, transition=transition)
    if relationship.purpose not in GUARDIAN_PURPOSES:
        return _deny("guardian_purpose_invalid", age=age, transition=transition)

    # 4. Guardian type must be explicit; canonical rule table decides the action.
    gtype = guardian_type or metadata.get("guardian_type")
    if not gtype:
        return _deny("guardian_type_missing", age=age, transition=transition)
    canonical_action = _GUARDIAN_ACTION_MAP.get(action)
    if canonical_action is None:
        return _deny("action_not_permitted_for_guardian", age=age, transition=transition, guardian_type=gtype)
    rules_service = GuardianRulesService()
    if not rules_service.validate_guardian_action(gtype, age, canonical_action):
        return _deny("guardian_action_denied_by_rule_table", age=age, transition=transition, guardian_type=gtype)

    # 5. NHID input (if supplied) is validated only through the canonical
    #    contract. No identifier is created, changed, or correlated as proof.
    if nhid_input is not None:
        try:
            canonical_nid_hash(nhid_input)
        except GuardianPolicyError as exc:
            return _deny(str(exc), age=age, transition=transition, guardian_type=gtype)

    # 6. Age transition: near-majority requires fresh re-verification (fail closed).
    if transition == "near_majority" and not reverified_at_transition:
        return _deny("reverification_required_at_age_transition", age=age, transition=transition, guardian_type=gtype)

    return GuardianAccessDecision(
        allowed=True,
        reason="verified_guardian_access",
        age=age,
        transition=transition,
        guardian_type=gtype,
        requires_reverification=transition in {"reasoning", "near_majority"},
    )


def guardian_relationship_permits(
    relationship: CitizenRelationship,
    *,
    action: str,
    resource_type: str,
    subject: Citizen | None,
    now: datetime | None = None,
) -> bool:
    """Adapter used by canonical ``AuthorizationDecisionService``.

    Adds an explicit, fail-closed guard to the existing relationship check for
    guardian relationships. Scope wildcards are never accepted for guardians.
    """
    decision = evaluate_guardian_access(
        subject=subject, relationship=relationship, action=action, now=now,
    )
    if not decision.allowed:
        return False
    scope = relationship.scope if isinstance(relationship.scope, dict) else {}
    resources = scope.get("resources", [])
    if not isinstance(resources, list) or not resources or "*" in resources:
        return False
    requested = f"{resource_type}:write" if action not in {"read", "list", "view"} else resource_type
    return (
        resource_type in resources
        or f"{resource_type}:read" in resources
        or requested in resources
    )


__all__ = [
    "AGE_OF_MAJORITY",
    "AGE_OF_REASONING",
    "GUARDIAN_PURPOSES",
    "GUARDIAN_RELATIONSHIP_TYPE",
    "REVERIFICATION_WINDOW_DAYS",
    "GuardianAccessDecision",
    "GuardianPolicyError",
    "age_transition",
    "assert_no_twin_merge",
    "canonical_nid_hash",
    "derive_age",
    "evaluate_guardian_access",
    "guardian_relationship_permits",
    "is_authorized_verifier_role",
    "subject_is_linkable",
]
