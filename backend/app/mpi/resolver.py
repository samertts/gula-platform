"""MPI resolver — orchestrates: block → match → claim/merge/review.

Main entry point: `resolve_identity()` — called by the `/mpi/resolve`
endpoint whenever a lab registers or updates a patient.

Algorithm:
  1. Normalize inputs (name, phone, NID hash, family hash).
  2. Fast path: if NID is present, look up citizen by nid_hash directly.
  3. Otherwise compute blocking_key + birth_year band + gender, fetch ≤50
     candidates.
  4. Score each candidate via matcher.score().
  5. Best score ≥ 0.90  → auto-claim to that citizen.
     Best score 0.70–0.90 → create claim with method='pending_review'.
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
import os
import secrets
import time
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app._compat import UTC

from ..models.mpi import Citizen, IdentityClaim, MergeAudit
from ..services.identity import (
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
    row_dict = {
        "event_type": event_type,
        "primary_citizen_id": primary.id,
        "secondary_citizen_id": secondary.id if secondary else None,
        "match_score": match_score_val,
        "match_features": features,
        "decision_reason": reason,
        "decided_by_user_id": decided_by_user_id,
        "occurred_at": datetime.now(UTC).isoformat(),
        "prev_hash": prev,
    }
    entry_hash = hashlib.sha256((prev + _canonical_json(row_dict)).encode()).hexdigest()

    audit = MergeAudit(
        event_type=event_type,
        primary_citizen_id=primary.id,
        secondary_citizen_id=secondary.id if secondary else None,
        match_score=match_score_val,
        match_features=features,
        decision_reason=reason,
        decided_by_user_id=decided_by_user_id,
        prev_hash=prev,
        entry_hash=entry_hash,
    )
    db.add(audit)
    db.flush()
    return audit


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
        survivor = citizen.canonical() if citizen else None
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
            best_candidate = hit.canonical()
            best_score = 1.0
            best_features = {"nid_hash": True}
            best_method = "nid_exact"

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
                        Citizen.birth_year >= birth_year - 1,
                        Citizen.birth_year <= birth_year + 1,
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
                    Citizen.status.in_(("active", "review")),
                    Citizen.phone_last10 == phone_norm,
                )
                .limit(_MAX_CANDIDATES)
                .all()
            )

        for c in candidates:
            survivor = c.canonical()
            result = score(profile, _candidate_from_citizen(survivor))
            if result.score > best_score:
                best_score = result.score
                best_candidate = survivor
                best_features = result.features
                best_method = result.method

    # ── Decide ───────────────────────────────────────────────────────────────
    decision = classify(best_score) if best_candidate else "no_match"

    if best_candidate and (best_method == "nid_exact" or decision == "auto_match"):
        citizen = best_candidate
        claim_method = best_method if best_method == "nid_exact" else "probabilistic"
        claim_score = 1.0 if best_method == "nid_exact" else best_score
        created = False

    elif best_candidate and decision == "review":
        citizen = best_candidate
        claim_method = "pending_review"
        claim_score = best_score
        created = False

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

    Effect:
      - secondary.merged_into_id = primary.id
      - secondary.status = 'merged'
      - all secondary.claims re-point to primary (NOT done here — deferred
        to a follow-up migration so individual labs can review first)
      - one MergeAudit row appended
    """
    if primary_ulid == secondary_ulid:
        raise ValueError("cannot merge a citizen with itself")

    primary = (
        db.query(Citizen).filter(Citizen.citizen_ulid == primary_ulid).with_for_update().first()
    )
    secondary = (
        db.query(Citizen).filter(Citizen.citizen_ulid == secondary_ulid).with_for_update().first()
    )
    if primary is None or secondary is None:
        raise ValueError("citizen not found")
    if primary.status != "active":
        raise ValueError(f"primary is not active (status={primary.status})")
    if secondary.status == "merged":
        raise ValueError("secondary already merged")

    secondary.merged_into_id = primary.id
    secondary.status = "merged"
    secondary.version += 1

    return _write_audit(
        db,
        event_type="manual_merge",
        primary=primary,
        secondary=secondary,
        match_score_val=None,
        features={},
        reason=reason[:500],
        decided_by_user_id=decided_by_user_id,
    )
