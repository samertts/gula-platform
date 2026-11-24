"""MPI resolver — orchestrates: block → match → claim/merge/review.

Main entry point: `resolve_identity()` - called by the `/mpi/resolve`
endpoint whenever a lab registers or updates a patient.

Algorithm:
  1. Normalize inputs (name, phone, NID hash, family hash).
  2. Fast path: if NID is present, look up citizen by nid_hash directly.
  3. Otherwise compute blocking_key + birth_year band + gender, fetch ≤50
     candidates.
  4. Score each candidate via matcher.score().
  5. Best score >= 0.90  -> auto-claim to that citizen.
     Best score 0.70-0.90 -> create claim with method='pending_review'.
     Best score < 0.70   → mint a new citizen.
  6. Write IdentityClaim row (one per lab/patient).
  7. On merge decisions, append an immutable MergeAudit entry.

The IdentityClaim UNIQUE(lab_id, local_patient_id) constraint makes
this operation idempotent — re-calling resolve for the same LIMS
patient returns the existing claim.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import secrets
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app._compat import UTC

from ..identity import (
    hash_family_id,
    hash_national_id,
    normalize_name,
)
from .blocking import blocking_key, phone_last10
from .matcher import (
    Candidate,
    build_profile,
    classify,
    score,
)
from .models import BrokenCanonicalChainError, Citizen, IdentityClaim, MergeAudit
from .reliability import (
    acquire_audit_chain_lock,
    atomic_increment_version,
)

logger = logging.getLogger("gula.services.mpi.resolver")

# ── ULID (Crockford base32, 26 chars) ────────────────────────────────────────
# Implemented inline to avoid adding a dependency.
_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def _ulid() -> str:
    """Generate a 26-char Crockford-base32 ULID.

    48-bit millisecond timestamp + 80-bit random. Time-sortable.
    """
    ms = int(time.time() * 1000) & ((1 << 48) - 1)
    rand = secrets.randbits(80)
    value = (ms << 80) | rand
    out = []
    for _ in range(26):
        out.append(_CROCKFORD[value & 0x1F])
        value >>= 5
    return "".join(reversed(out))


# ── Result object ────────────────────────────────────────────────────────────


@dataclass
class ResolveOutcome:
    citizen: Citizen
    claim: IdentityClaim
    created: bool  # True if a new Citizen was minted
    match_method: str  # 'nid_exact' | 'probabilistic' | 'pending_review' | 'new'
    match_score: float | None
    features: dict


# ── Helpers ──────────────────────────────────────────────────────────────────


def _canonical_json(row_dict: dict) -> str:
    """Deterministic JSON encoding for hash-chain continuity."""
    return json.dumps(row_dict, sort_keys=True, separators=(",", ":"), default=str)


def _quantize_score(value: float | int | str | None) -> float | None:
    """Normalise a match score to the persisted Numeric(4,3) representation.

    AUD-14: hashing a raw float (e.g. 0.91234) and storing it in Numeric(4,3)
    makes the stored row fail its own hash verification.  Quantising here, on
    BOTH the write and the verify side, guarantees round-trip reproducibility
    regardless of the Python type the caller supplied.
    """
    if value is None:
        return None
    return float(round(float(value), 3))


def _occurred_at_iso(value: datetime | str | None) -> str | None:
    """Normalise a MPI audit timestamp to one canonical UTC ISO-8601 string.

    The same function is used when hashing a new entry and when re-computing a
    hash from a persisted row. SQLite drops the ``tzinfo`` on a DateTime
    round-trip while PostgreSQL preserves it; treating a naive value as UTC
    makes verification backend-independent without changing the API contract.
    """
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()


def _last_audit_hash(db: Session) -> str:
    """Fetch the previous merge-audit entry_hash, or genesis zeros."""
    row = db.query(MergeAudit).order_by(MergeAudit.id.desc()).limit(1).first()
    if row is None:
        return "0" * 64
    return row.entry_hash


def _write_audit(
    db: Session,
    *,
    event_type: str,
    primary: Citizen,
    secondary: Citizen | None,
    match_score_val: float | None,
    features: dict,
    reason: str,
    decided_by_user_id: int | None,
) -> MergeAudit:
    """Append a hash-chained audit row. Caller commits the transaction."""
    prev = _last_audit_hash(db)
    # One timestamp instance feeds BOTH the hashed payload and the persisted
    # column. Previously `datetime.now(UTC)` was called for the hash while the
    # ORM column default produced a different value, so no stored row could
    # reproduce its own entry_hash.
    occurred_at = datetime.now(UTC)
    # One normalised score value feeds BOTH the hashed payload and the column.
    score_value = _quantize_score(match_score_val)
    row_dict = {
        "event_type": event_type,
        "primary_citizen_id": primary.id,
        "secondary_citizen_id": secondary.id if secondary else None,
        "match_score": score_value,
        "match_features": features,
        "decision_reason": reason,
        "decided_by_user_id": decided_by_user_id,
        "occurred_at": _occurred_at_iso(occurred_at),
        "prev_hash": prev,
    }
    entry_hash = hashlib.sha256((prev + _canonical_json(row_dict)).encode()).hexdigest()

    audit = MergeAudit(
        event_type=event_type,
        primary_citizen_id=primary.id,
        secondary_citizen_id=secondary.id if secondary else None,
        match_score=score_value,
        match_features=features,
        decision_reason=reason,
        decided_by_user_id=decided_by_user_id,
        occurred_at=occurred_at,
        prev_hash=prev,
        entry_hash=entry_hash,
    )
    db.add(audit)
    db.flush()
    return audit


@dataclass(frozen=True)
class ChainVerificationResult:
    """Deterministic result of re-walking the stored MPI audit hash chain."""

    valid: bool
    checked: int
    errors: tuple[str, ...]


def _audit_row_dict(row: MergeAudit) -> dict[str, object]:
    """The exact column set that feeds an ``MergeAudit.entry_hash``.

    Shared by the full-chain verifier and the in-SAVEPOINT segment verifier so
    the two can never drift apart. Floats are normalised via ``float()``
    because SQLite and PostgreSQL return different numeric representations.
    """
    return {
        "event_type": row.event_type,
        "primary_citizen_id": row.primary_citizen_id,
        "secondary_citizen_id": row.secondary_citizen_id,
        "match_score": _quantize_score(
            float(row.match_score) if row.match_score is not None else None
        ),
        "match_features": row.match_features,
        "decision_reason": row.decision_reason,
        "decided_by_user_id": row.decided_by_user_id,
        "occurred_at": _occurred_at_iso(row.occurred_at),
        "prev_hash": row.prev_hash,
    }


def _audit_entry_hash(row: MergeAudit) -> str:
    return hashlib.sha256(
        ((row.prev_hash or "") + _canonical_json(_audit_row_dict(row))).encode()
    ).hexdigest()


class AuditForkError(RuntimeError):
    """A hash-chain fork/tamper was detected; fail closed, never hide it (AUD-16).

    Policy (engineering default pending D-MPI-3/4 owner ratification): any
    detected fork ABORTS the in-flight append (SAVEPOINT rollback, no commit)
    and is surfaced to the governance probe.  No auto-repair and no silent
    fallback are performed -- a split is never concealed to keep a request alive.
    """


def _verify_audit_segment(db: Session, *, first_id: int, expected_prev: str) -> None:
    """Verify only the audit rows appended by the current locked operation.

    Runs *inside* the SAVEPOINT, before the caller's outer commit. It proves
    the freshly appended segment links to the tail we read under the advisory
    lock and that every stored hash reproduces from its persisted columns.
    A fork raises :class:`AuditForkError` -> the caller's SAVEPOINT rolls back
    (fail-closed); it is never swallowed or hidden.
    """
    rows = (
        db.query(MergeAudit)
        .filter(MergeAudit.id >= first_id)
        .order_by(MergeAudit.id.asc())
        .all()
    )
    if not rows:
        raise RuntimeError("post-merge audit verification failed: no audit row persisted")
    prev = expected_prev
    for row in rows:
        if row.prev_hash != prev:
            raise AuditForkError("post-merge audit verification failed: prev_hash does not link")
        if _audit_entry_hash(row) != row.entry_hash:
            raise AuditForkError("post-merge audit verification failed: entry_hash mismatch")
        prev = row.entry_hash


def verify_merge_audit_chain(db: Session) -> ChainVerificationResult:
    """Re-compute every stored ``MergeAudit`` hash from its persisted columns.

    Scope of this control (important): it is a *detection* mechanism. It proves
    that the stored chain is internally consistent at the moment of the walk and
    detects field tampering and forked ``prev_hash`` values. It does **not**
    prevent a privileged actor from rewriting the whole chain consistently, and
    it does **not** serialise concurrent appenders — see the remediation report
    for the still-open serialization decision.
    """
    rows = db.query(MergeAudit).order_by(MergeAudit.id.asc()).all()
    errors: list[str] = []
    expected_prev: str | None = "0" * 64
    for row in rows:
        if row.prev_hash != expected_prev:
            errors.append(f"audit {row.id}: prev_hash does not link to the preceding entry")
        if _audit_entry_hash(row) != row.entry_hash:
            errors.append(f"audit {row.id}: entry_hash does not match persisted columns")
        expected_prev = row.entry_hash
    return ChainVerificationResult(valid=not errors, checked=len(rows), errors=tuple(errors))


def verify_canonical_chains(db: Session) -> ChainVerificationResult:
    """Detect broken/cyclic/too-deep ``merged_into`` chains (AUD-13).

    Detection-only: returns a structured result; it never mutates identities or
    attempts an unmerge (which is an owner/legal decision, out of scope).
    """
    roots = db.query(Citizen).filter(Citizen.merged_into_id.isnot(None)).all()
    errors: list[str] = []
    for citizen in roots:
        try:
            citizen.canonical(strict=True)
        except BrokenCanonicalChainError as exc:
            errors.append(str(exc))
    return ChainVerificationResult(valid=not errors, checked=len(roots), errors=tuple(errors))


def mpi_integrity_probe(db: Session) -> dict[str, Any]:
    """Governance probe over MPI integrity controls (AUD-08/AUD-13/AUD-16).

    Wires the previously test-only verifiers into a callable, admin-reachable
    check that emits an alertable warning on failure.  It is DETECTION ONLY:
    no auto-repair, no chain rewrite, no hiding of a split.  The response is
    non-PII (counts, booleans, error codes) and safe for the compliance audit
    endpoint.  Owners decide fork response under D-MPI-3/4 (decision request
    raised, not executed).
    """
    audit = verify_merge_audit_chain(db)
    chains = verify_canonical_chains(db)
    valid = audit.valid and chains.valid
    result = {
        "valid": valid,
        "status": "intact" if valid else "forked",
        "merge_audit": {
            "valid": audit.valid,
            "checked": audit.checked,
            "errors": list(audit.errors),
        },
        "canonical_chains": {
            "valid": chains.valid,
            "checked": chains.checked,
            "errors": list(chains.errors),
        },
        "policy": "detection_only_fail_closed_no_repair_pending_D_MPI_3_4",
    }
    if not valid:
        logger.warning(
            "mpi_integrity_fork_detected audit_errors=%d chain_errors=%d",
            len(audit.errors),
            len(chains.errors),
        )
    return result


def _candidate_from_citizen(c: Citizen) -> Candidate:
    return Candidate(
        id=c.id,
        citizen_ulid=c.citizen_ulid,
        name_canonical=c.name_canonical,
        phone_last10=c.phone_last10,
        birth_year=c.birth_year,
        birth_month=c.birth_month,
        birth_day=c.birth_day,
        gender=c.gender,
        nid_hash=c.nid_hash,
        family_id_hash=c.family_id_hash,
    )


# ── Main entry ───────────────────────────────────────────────────────────────

_MAX_CANDIDATES = int(os.getenv("MPI_MAX_CANDIDATES", "50"))


def resolve_identity(
    db: Session,
    *,
    lab_id: int,
    local_patient_id: int,
    name: str,
    phone: str | None = None,
    birth_year: int | None = None,
    birth_month: int | None = None,
    birth_day: int | None = None,
    gender: str | None = None,
    national_id: str | None = None,  # RAW — hashed here, never persisted
    family_id: str | None = None,  # RAW — hashed here, never persisted
    claimed_by_user_id: int | None = None,
) -> ResolveOutcome:
    """Resolve (or create) the canonical citizen for a LIMS patient.

    Idempotent: re-calling with the same (lab_id, local_patient_id)
    returns the existing claim without re-scoring.
    """
    # ── Idempotency: existing claim? ─────────────────────────────────────────
    existing_claim = (
        db.query(IdentityClaim).filter_by(lab_id=lab_id, local_patient_id=local_patient_id).first()
    )
    if existing_claim is not None:
        citizen = db.query(Citizen).filter(Citizen.id == existing_claim.citizen_id).first()
        # Follow merge chain — if the canonical has been absorbed, return the survivor
        survivor = citizen.canonical(strict=True) if citizen else None
        return ResolveOutcome(
            citizen=survivor or citizen,
            claim=existing_claim,
            created=False,
            match_method=existing_claim.match_method,
            match_score=float(existing_claim.match_score)
            if existing_claim.match_score is not None
            else None,
            features=existing_claim.match_features or {},
        )

    # ── Normalize inputs ─────────────────────────────────────────────────────
    name_canonical = normalize_name(name)
    phone_norm = phone_last10(phone)
    nid_hash = hash_national_id(national_id) if national_id else None
    family_hash = hash_family_id(family_id) if family_id else None
    bkey = blocking_key(name)

    profile = build_profile(
        name=name,
        phone_last10=phone_norm,
        birth_year=birth_year,
        birth_month=birth_month,
        birth_day=birth_day,
        gender=(gender.upper() if gender else None),
        nid_hash=nid_hash,
        family_id_hash=family_hash,
    )

    # ── Fast path: deterministic NID lookup ──────────────────────────────────
    # AUD-MPI-001: a lab-supplied national ID is only an AUTHORITATIVE identity
    # signal when the matching citizen carries nid_verified=True. Every MPI
    # write path (genesis, detach, register) persists nid_verified=False, so an
    # unverified hash equality must never short-circuit into an auto-claim —
    # a wrong or stale NID would bind the patient to another person's record.
    best_candidate: Citizen | None = None
    best_score = 0.0
    best_features: dict = {}
    best_method = "probabilistic"

    if nid_hash:
        hit = (
            db.query(Citizen)
            .filter(Citizen.nid_hash == nid_hash, Citizen.status.in_(("active", "review")))
            .first()
        )
        if hit is not None:
            canonical_hit = hit.canonical(strict=True)
            if canonical_hit.nid_verified:
                best_candidate = canonical_hit
                best_score = 1.0
                best_features = {"nid_hash": True, "nid_verified": True}
                best_method = "nid_exact"
            else:
                # Drop the unverified hash from the scoring profile so score()
                # cannot re-create the 1.0 short-circuit through the back door.
                profile = build_profile(
                    name=name,
                    phone_last10=phone_norm,
                    birth_year=birth_year,
                    birth_month=birth_month,
                    birth_day=birth_day,
                    gender=(gender.upper() if gender else None),
                    family_id_hash=family_hash,
                )

    # ── Probabilistic path: block → score ────────────────────────────────────
    if best_candidate is None:
        q = (
            db.query(Citizen)
            .filter(Citizen.status.in_(("active", "review")))
            .filter(Citizen.name_blocking_key == bkey)
        )
        if birth_year is not None:
            q = q.filter(
                or_(
                    Citizen.birth_year.is_(None),
                    and_(
                        Citizen.birth_year >= birth_year - 1, Citizen.birth_year <= birth_year + 1,
                    ),
                ),
            )
        if gender:
            q = q.filter(or_(Citizen.gender.is_(None), Citizen.gender == gender.upper()))

        candidates = q.limit(_MAX_CANDIDATES).all()

        # Fallback: if blocking returned nothing AND we have a phone, try phone
        if not candidates and phone_norm:
            candidates = (
                db.query(Citizen)
                .filter(
                    Citizen.status.in_(("active", "review")), Citizen.phone_last10 == phone_norm,
                )
                .limit(_MAX_CANDIDATES)
                .all()
            )

        for c in candidates:
            survivor = c.canonical(strict=True)
            result = score(profile, _candidate_from_citizen(survivor))
            if result.score > best_score:
                best_score = result.score
                best_candidate = survivor
                best_features = result.features
                best_method = result.method

    # ── Decide ───────────────────────────────────────────────────────────────
    decision = classify(best_score) if best_candidate else "no_match"

    if best_candidate and decision == "auto_match":
        citizen = best_candidate
        # nid_exact is retained ONLY when the stored NID is verified. An
        # unverified hash is already excluded from scoring above, so any
        # remaining auto-match is genuinely probabilistic/demographic.
        if best_method == "nid_exact" and best_candidate.nid_verified:
            claim_method = "nid_exact"
            claim_score = 1.0
        else:
            claim_method = "probabilistic"
            claim_score = best_score
        created = False

    elif best_candidate and decision == "review":
        citizen = best_candidate
        claim_method = "pending_review"
        claim_score = best_score
        created = False

    else:
        # GENESIS / CREATE AUDIT SERIALIZATION (MPI-01): hold the transaction-
        # scoped advisory lock before minting a new canonical identity and
        # before `_write_audit` reads the tail. Two concurrent creates therefore
        # cannot both observe genesis ("0"*64) and fork the hash chain. No
        # SAVEPOINT is open here, so acquisition order is trivially correct.
        acquire_audit_chain_lock(db)

        # AUD-04: the NID fast-path read above happened BEFORE this lock, so two
        # concurrent first-registrations with the same NID both saw "no hit".
        # Re-read under the lock: if the winner already committed its citizen,
        # reuse it (idempotent NID registration) instead of inserting a duplicate
        # that would raise 23505 and surface as HTTP 503.  READ COMMITTED sees the
        # winner's committed row once we hold the same advisory lock.
        locked_nid_hit = None
        if nid_hash:
            locked_nid_hit = (
                db.query(Citizen)
                .filter(
                    Citizen.nid_hash == nid_hash,
                    Citizen.status.in_(("active", "review")),
                )
                .first()
            )
        if locked_nid_hit is not None:
            locked_citizen = locked_nid_hit.canonical(strict=True)
            if locked_citizen.nid_verified:
                citizen = locked_citizen
                claim_method = "nid_exact"
                claim_score = 1.0
                created = False
                best_features = {
                    "nid_hash": True,
                    "nid_verified": True,
                    "nid_reconciled_under_lock": True,
                }
            else:
                # AUD-MPI-001: reuse the existing row (no duplicate NID record)
                # but do NOT auto-claim it on an unverified identifier. Human
                # review is mandatory; provenance is persisted on the claim.
                citizen = locked_citizen
                claim_method = "pending_review"
                claim_score = 0.0
                created = False
                best_features = {
                    "nid_hash": True,
                    "nid_verified": False,
                    "nid_not_authoritative": True,
                    "nid_reconciled_under_lock": True,
                }
        else:
            citizen = Citizen(
                citizen_ulid=_ulid(),
                nid_hash=nid_hash,
                nid_verified=False,
                phone_last10=phone_norm,
                birth_year=birth_year,
                birth_month=birth_month,
                birth_day=birth_day,
                gender=(gender.upper() if gender else None),
                name_canonical=name_canonical,
                name_blocking_key=bkey,
                family_id_hash=family_hash,
                status="active",
                version=1,
            )
            db.add(citizen)
            db.flush()
            _write_audit(
                db,
                event_type="create",
                primary=citizen,
                secondary=None,
                match_score_val=None,
                features={"name_canonical": name_canonical, "blocking_key": bkey},
                reason="MPI: no candidate above review threshold",
                decided_by_user_id=claimed_by_user_id,
            )
            # No candidate above review threshold → fresh canonical record.
            claim_method = "new"
            claim_score = None
            created = True
            best_features = {}

    # ── Write the claim ──────────────────────────────────────────────────────
    claim = IdentityClaim(
        citizen_id=citizen.id,
        lab_id=lab_id,
        local_patient_id=local_patient_id,
        match_method=claim_method,
        match_score=claim_score,
        match_features=best_features,
        claimed_by_user_id=claimed_by_user_id,
    )
    db.add(claim)
    db.flush()

    return ResolveOutcome(
        citizen=citizen,
        claim=claim,
        created=created,
        match_method=claim_method,
        match_score=float(claim_score) if claim_score is not None else None,
        features=best_features,
    )


# ── Review-decision lifecycle (AUD-01 / AUD-11) ──────────────────────────────
# A review decision is NOT a match decision.  The four canonical decisions are
# deliberately distinct so a "reject" can never be silently reinterpreted as
# "match this patient to somebody else":
#
#   ACCEPT_MATCH        keep the reviewed claim, flip it to 'manual'
#   REJECT_MATCH        detach from the rejected citizen, mint a NEW one
#   CREATE_NEW_IDENTITY explicitly mint a NEW one (no candidate is implied)
#   NEEDS_MANUAL_REVIEW leave the claim pending (no mutation)
#
# Legacy values 'confirm'/'reject' remain accepted and normalise to the first
# two canonical values so the shipped API contract keeps working (see the
# compatibility note in schemas.py and the AUD-01 remediation report).

REVIEW_DECISIONS = frozenset(
    {"ACCEPT_MATCH", "REJECT_MATCH", "CREATE_NEW_IDENTITY", "NEEDS_MANUAL_REVIEW"}
)
_LEGACY_REVIEW_DECISIONS = {"confirm": "ACCEPT_MATCH", "reject": "REJECT_MATCH"}

# Audit event_type strings.  MergeAudit.event_type is a String(20) column with
# no DB enum, so these fit without DDL.  Formal taxonomy sign-off is tracked as
# owner decision D-MPI-4 (an Owner Decision Request was raised, not executed).
AUDIT_EVENT_REVIEW_ACCEPT = "review_accept"
AUDIT_EVENT_REVIEW_REJECT = "review_reject"
AUDIT_EVENT_REVIEW_NEW_ID = "review_new_id"


def normalize_review_decision(value: str) -> str:
    """Normalise a submitted review decision to one canonical REVIEW_DECISIONS value.

    Raises ``ValueError`` for an unknown decision (surfaced as HTTP 400 by the
    API layer).  Both canonical upper-case values and legacy 'confirm'/'reject'
    are accepted, so this is backward compatible with existing clients.
    """
    if not isinstance(value, str):
        raise ValueError("decision must be a string")
    stripped = value.strip()
    if stripped in REVIEW_DECISIONS:
        return stripped
    if stripped in _LEGACY_REVIEW_DECISIONS:
        return _LEGACY_REVIEW_DECISIONS[stripped]
    upper = stripped.upper()
    if upper in REVIEW_DECISIONS:
        return upper
    raise ValueError(f"unknown review decision: {value!r}")


def _review_features(
    *,
    decision: str,
    claim_id: int,
    rejected_citizen: Citizen | None,
    reviewer_user_id: int | None,
) -> dict[str, object]:
    """Stable provenance stored on both the claim and its chained audit row."""
    return {
        "decision": decision,
        "claim_id": claim_id,
        "rejected_citizen_id": rejected_citizen.id if rejected_citizen else None,
        "rejected_citizen_ulid": (
            rejected_citizen.citizen_ulid if rejected_citizen else None
        ),
        "reviewed_by_user_id": reviewer_user_id,
        "reviewed_at": _occurred_at_iso(datetime.now(UTC)),
    }


def create_detached_citizen(
    db: Session,
    *,
    claim_id: int,
    name: str,
    phone: str | None = None,
    birth_year: int | None = None,
    birth_month: int | None = None,
    birth_day: int | None = None,
    gender: str | None = None,
    claimed_by_user_id: int | None = None,
    rejected_citizen_id: int | None = None,
    decision: str = "REJECT_MATCH",
    reason: str = "",
) -> ResolveOutcome:
    """Mint a fresh canonical citizen for a rejected ambiguous claim (AUD-01).

    Unlike :func:`resolve_identity`, this function NEVER scores candidates and
    NEVER reuses an existing citizen.  A reject decision means the patient must
    not be (re)linked to the rejected candidate -- nor auto-linked to some
    other high-scoring candidate merely because it crossed a threshold.  The
    disputed NID is deliberately NOT copied onto the new record (it may belong
    to the rejected person); a later resolve for this claim returns this new
    citizen via the claim idempotency key, never the rejected one.

    Safety invariants:
      * the advisory chain lock is taken before reading the claim tail;
      * the claim is re-read under the lock and must still be 'pending_review'
        -- a second execution (concurrent or replayed) is refused;
      * the SAME claim row is re-pointed (never deleted), preserving the
        UNIQUE(lab_id, local_patient_id) key and giving a stable replay sentinel;
      * one hash-chained audit row records decision, reviewer, reason,
        rejected candidate and decision time;
      * the caller owns the outer transaction (``bounded_retry``).
    """
    if decision not in ("REJECT_MATCH", "CREATE_NEW_IDENTITY"):
        raise ValueError("create_detached_citizen requires REJECT_MATCH or CREATE_NEW_IDENTITY")
    if not reason or not reason.strip():
        raise ValueError("a review reason is required")

    acquire_audit_chain_lock(db)

    claim = db.query(IdentityClaim).filter(IdentityClaim.id == claim_id).first()
    if claim is None:
        raise ValueError("claim not found")
    if claim.match_method != "pending_review":
        # Idempotency / replay guard: a decision has already been applied.
        raise ValueError("claim is no longer pending — decision already applied")

    rejected = (
        db.query(Citizen).filter(Citizen.id == rejected_citizen_id).first()
        if rejected_citizen_id is not None
        else None
    )

    name_canonical = normalize_name(name)
    bkey = blocking_key(name)
    citizen = Citizen(
        citizen_ulid=_ulid(),
        nid_hash=None,  # disputed NID is never transferred on a reject
        nid_verified=False,
        phone_last10=phone_last10(phone),
        birth_year=birth_year,
        birth_month=birth_month,
        birth_day=birth_day,
        gender=(gender.upper() if gender else None),
        name_canonical=name_canonical,
        name_blocking_key=bkey,
        status="active",
        version=1,
    )
    db.add(citizen)
    db.flush()

    features = _review_features(
        decision=decision,
        claim_id=claim_id,
        rejected_citizen=rejected,
        reviewer_user_id=claimed_by_user_id,
    )
    event_type = (
        AUDIT_EVENT_REVIEW_NEW_ID
        if decision == "CREATE_NEW_IDENTITY"
        else AUDIT_EVENT_REVIEW_REJECT
    )
    _write_audit(
        db,
        event_type=event_type,
        primary=citizen,
        secondary=rejected,
        match_score_val=None,
        features=features,
        reason=reason[:500],
        decided_by_user_id=claimed_by_user_id,
    )

    # Re-point the existing claim; never delete it.  This is the atomic flip
    # that makes the patient land on the brand-new citizen only.
    claim.citizen_id = citizen.id
    claim.match_method = "new"
    claim.match_score = None
    claim.match_features = features
    db.flush()

    return ResolveOutcome(
        citizen=citizen,
        claim=claim,
        created=True,
        match_method="new",
        match_score=None,
        features=features,
    )


def confirm_reviewed_match(
    db: Session,
    *,
    claim_id: int,
    reason: str,
    reviewer_user_id: int | None,
) -> ResolveOutcome:
    """Confirm an ambiguous claim as ACCEPT_MATCH (AUD-11), with a chained audit.

    Same replay guard as :func:`create_detached_citizen`: the claim must still
    be 'pending_review' under the advisory lock.
    """
    if not reason or not reason.strip():
        raise ValueError("a review reason is required")

    acquire_audit_chain_lock(db)

    claim = db.query(IdentityClaim).filter(IdentityClaim.id == claim_id).first()
    if claim is None:
        raise ValueError("claim not found")
    if claim.match_method != "pending_review":
        raise ValueError("claim is no longer pending — decision already applied")
    citizen = db.query(Citizen).filter(Citizen.id == claim.citizen_id).first()
    if citizen is None:
        raise ValueError("reviewed citizen not found")

    features = _review_features(
        decision="ACCEPT_MATCH",
        claim_id=claim_id,
        rejected_citizen=None,
        reviewer_user_id=reviewer_user_id,
    )
    claim.match_method = "manual"
    claim.match_features = features
    db.flush()

    _write_audit(
        db,
        event_type=AUDIT_EVENT_REVIEW_ACCEPT,
        primary=citizen,
        secondary=None,
        match_score_val=None,
        features=features,
        reason=reason[:500],
        decided_by_user_id=reviewer_user_id,
    )

    return ResolveOutcome(
        citizen=citizen,
        claim=claim,
        created=False,
        match_method="manual",
        match_score=float(claim.match_score) if claim.match_score is not None else None,
        features=features,
    )


# ── Manual merge (admin only — endpoint calls this) ──────────────────────────


def merge_citizens(
    db: Session,
    *,
    primary_ulid: str,
    secondary_ulid: str,
    reason: str,
    decided_by_user_id: int,
) -> MergeAudit:
    """Manually merge `secondary` into `primary`. Caller must be admin.

    P0-E integrity guarantees (all-or-nothing; caller still owns the commit):
      * self / already-same-identity / merge-cycle inputs are rejected;
      * a retry of an already-applied merge returns its original audit row
        (idempotent) instead of creating a duplicate;
      * every ``IdentityClaim`` of the secondary is re-pointed to the primary,
        with provenance recorded in the claim's match features;
      * a hash-chained ``MergeAudit`` entry records the decision;
      * post-merge consistency is verified *inside the SAVEPOINT, before the
        caller's outer commit*; a failure there rolls back this merge only.
        There is no post-commit verification — the caller owns the outer commit
        and no post-commit atomicity claim is made here.

    Historical event data / unmerge (P0-E2) is intentionally out of scope and
    remains blocked pending an ownership and schema decision.
    """
    if not primary_ulid or not secondary_ulid:
        raise ValueError("citizen ULIDs are required")
    if primary_ulid == secondary_ulid:
        raise ValueError("cannot merge a citizen with itself")
    if not reason or not reason.strip():
        raise ValueError("a merge reason is required")

    # LOCK ORDER (MPI-01/02): advisory chain lock → Citizen rows by id ASC
    # (FOR UPDATE) → SAVEPOINT work. Acquiring here, before the ordered row-lock
    # SELECT and before `begin_nested()`, guarantees no SAVEPOINT is opened while
    # waiting for the chain lock and serialises every tail read/append. The lock
    # is transaction-scoped, so it is released only by the caller's outer commit
    # or rollback — never by the SAVEPOINT release.
    acquire_audit_chain_lock(db)

    # ONE row-lock statement, ordered by the immutable primary key. Every merge
    # therefore acquires the two citizen locks in the same order regardless of
    # which ULID the caller supplied as "primary", removing the A→B / B→A
    # acquisition cycle. Locks are taken on the outer transaction and held until
    # the caller commits. (SQLite emits no FOR UPDATE; see remediation report.)
    locked = (
        db.query(Citizen)
        .filter(Citizen.citizen_ulid.in_((primary_ulid, secondary_ulid)))
        .order_by(Citizen.id.asc())
        .with_for_update()
        .all()
    )
    by_ulid = {c.citizen_ulid: c for c in locked}
    primary = by_ulid.get(primary_ulid)
    secondary = by_ulid.get(secondary_ulid)
    if primary is None or secondary is None:
        raise ValueError("citizen not found")

    # AUD-06: unordered-pair idempotency INSIDE the locked region.  A client
    # that reconnects while the original merge is still in flight may swap
    # primary/secondary.  The pre-check outside the lock cannot see the audit
    # row yet, and the directed checks below would treat the swapped pair as a
    # cycle (HTTP 400).  Resolve the pair in BOTH directions against the ledger
    # here and return the original result regardless of caller order.  A
    # different reason is a genuine conflict, not an idempotent replay.
    prior = (
        db.query(MergeAudit)
        .filter(MergeAudit.event_type == "manual_merge")
        .filter(
            or_(
                and_(
                    MergeAudit.primary_citizen_id == primary.id,
                    MergeAudit.secondary_citizen_id == secondary.id,
                ),
                and_(
                    MergeAudit.primary_citizen_id == secondary.id,
                    MergeAudit.secondary_citizen_id == primary.id,
                ),
            ),
        )
        .order_by(MergeAudit.id.desc())
        .first()
    )
    if prior is not None:
        if (prior.decision_reason or "") != reason[:500]:
            raise ValueError("conflicting merge replay")
        return prior  # idempotent retry (original caller order preserved in row)

    # Idempotency fallback: after a successful merge, secondary.canonical()
    # already resolves to primary, so the cycle check below would otherwise
    # reject a legitimate retry. Returning the original audit row makes retries
    # safe even if a historical row lacks the pair index used above.
    if secondary.status == "merged" and secondary.merged_into_id == primary.id:
        previous = (
            db.query(MergeAudit)
            .filter(
                MergeAudit.event_type == "manual_merge",
                MergeAudit.primary_citizen_id == primary.id,
                MergeAudit.secondary_citizen_id == secondary.id,
            )
            .order_by(MergeAudit.id.desc())
            .first()
        )
        if previous is not None:
            return previous  # idempotent retry
        raise ValueError("secondary already merged into primary without an audit entry")

    # Reject merges that would form a cycle or are already effectively applied.
    if primary.canonical(strict=True).id == secondary.canonical(strict=True).id:
        raise ValueError("citizens already resolve to the same canonical identity")

    if primary.status != "active":
        raise ValueError(f"primary is not active (status={primary.status})")
    if secondary.status == "merged":
        raise ValueError("secondary already merged")
    if secondary.merged_into_id is not None:
        raise ValueError("secondary is not a valid merge source")

    claims = db.query(IdentityClaim).filter(IdentityClaim.citizen_id == secondary.id).all()
    # Use a nested SAVEPOINT so a failure rolls back only this merge and does
    # not destroy any unrelated pending work in the caller's transaction.
    savepoint = db.begin_nested()
    try:
        for claim in claims:
            features = dict(claim.match_features or {})
            features["merged_from_citizen_ulid"] = secondary.citizen_ulid
            features["merge_reason"] = reason[:200]
            claim.match_features = features
            claim.citizen_id = primary.id

        secondary.merged_into_id = primary.id
        secondary.status = "merged"
        # MPI-03: increment in the database, never a blind read-modify-write.
        atomic_increment_version(db, secondary, Citizen)

        # Read the tail under the advisory lock and remember it, then append and
        # verify the freshly written segment inside this SAVEPOINT. If the hash
        # does not reproduce from the persisted columns, the SAVEPOINT is rolled
        # back and no merge/audit becomes visible.
        expected_prev = _last_audit_hash(db)
        audit = _write_audit(
            db,
            event_type="manual_merge",
            primary=primary,
            secondary=secondary,
            match_score_val=None,
            features={"repointed_claim_ids": [c.id for c in claims]},
            reason=reason[:500],
            decided_by_user_id=decided_by_user_id,
        )
        db.flush()
        assert audit.id is not None  # just flushed; PK is assigned
        _verify_audit_segment(db, first_id=audit.id, expected_prev=expected_prev)

        if db.query(IdentityClaim).filter(IdentityClaim.citizen_id == secondary.id).count():
            raise RuntimeError("post-merge verification failed: claims still reference secondary")
        if secondary.merged_into_id != primary.id or secondary.status != "merged":
            raise RuntimeError("post-merge verification failed: secondary state inconsistent")
        if primary.canonical(strict=True).id != primary.id:
            raise RuntimeError("post-merge verification failed: primary canonical chain inconsistent")
        savepoint.commit()
    except Exception:
        savepoint.rollback()
        raise

    return audit
