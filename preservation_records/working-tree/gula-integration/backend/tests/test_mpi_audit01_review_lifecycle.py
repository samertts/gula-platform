"""AUD-01 / AUD-11 — wrong-patient linkage review lifecycle (synthetic only).

Pins the four distinct review decisions, the "reject never reuses the rejected
citizen" invariant, replay safety, chained reviewer provenance, and fail-closed
behaviour on a broken canonical chain.  No real patient data is used.
"""

from __future__ import annotations

import pytest
from app import database as _database
from app.models.lab import Lab
from app.models.lab_user import LabUser
from app.models.patient import Patient
from app.services.mpi import api as mpi_api
from app.services.mpi import resolver
from app.services.mpi.models import (
    BrokenCanonicalChainError,
    Citizen,
    IdentityClaim,
    MergeAudit,
)
from app.services.mpi.schemas import ResolveDecision
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import sessionmaker

REASON = "synthetic review: names collide but NIDs differ"


def _lab(db, lab_id: int = 909100) -> Lab:
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if lab is None:
        lab = Lab(id=lab_id, name="Synthetic AUD01 Lab", license_number="SYN-AUD01-001")
        db.add(lab)
        db.flush()
    return lab


def _reviewer(db, user_id: int = 909101) -> LabUser:
    u = db.query(LabUser).filter(LabUser.id == user_id).first()
    if u is None:
        u = LabUser(
            id=user_id,
            lab_id=909100,
            name="Synthetic Reviewer",
            email=f"synthetic-reviewer-{user_id}@example.invalid",
            password_hash="synthetic-not-a-real-hash",
            role="master_admin",
            is_active=True,
        )
        db.add(u)
        db.flush()
    return u


def _citizen(db, suffix: str, *, nid_hash: str | None = None) -> Citizen:
    c = Citizen(
        citizen_ulid=f"01SYNTHAUD01{suffix}"[:26],
        nid_hash=nid_hash,
        name_canonical=f"synthetic aud01 {suffix}",
        name_blocking_key=f"synaud01{suffix}"[:20],
        status="active",
        version=1,
    )
    db.add(c)
    db.flush()
    return c


def _pending_claim(db, *, suffix: str = "CLM", nid_hash: str = " nid-A ") -> tuple[Patient, Citizen, IdentityClaim]:
    lab = _lab(db)
    patient = Patient(
        lab_id=lab.id,
        full_name="Synthetic Ambiguous Patient",
        phone="+964700000111",
    )
    db.add(patient)
    db.flush()
    rejected = _citizen(db, suffix, nid_hash=nid_hash)
    claim = IdentityClaim(
        citizen_id=rejected.id,
        lab_id=lab.id,
        local_patient_id=patient.id,
        match_method="pending_review",
        match_score=0.82,
        match_features={"nid_hash": False},
    )
    db.add(claim)
    db.flush()
    return patient, rejected, claim


# ── Decision taxonomy / API contract ────────────────────────────────────────


def test_four_canonical_decisions_are_distinct_and_accepted():
    expected = {
        "ACCEPT_MATCH",
        "REJECT_MATCH",
        "CREATE_NEW_IDENTITY",
        "NEEDS_MANUAL_REVIEW",
    }
    assert sorted(resolver.REVIEW_DECISIONS) == sorted(expected)
    for value in sorted(resolver.REVIEW_DECISIONS):
        model = ResolveDecision(decision=value, reason=REASON)
        assert model.decision == value


def test_decision_reject_match_is_not_a_match_decision():
    """A reject must never be reinterpreted as ACCEPT_MATCH (AUD-01)."""
    assert resolver.normalize_review_decision("REJECT_MATCH") == "REJECT_MATCH"
    assert resolver.normalize_review_decision("ACCEPT_MATCH") == "ACCEPT_MATCH"
    assert (
        resolver.normalize_review_decision("CREATE_NEW_IDENTITY")
        == "CREATE_NEW_IDENTITY"
    )
    assert (
        resolver.normalize_review_decision("NEEDS_MANUAL_REVIEW")
        == "NEEDS_MANUAL_REVIEW"
    )


def test_legacy_decision_values_remain_backward_compatible():
    assert resolver.normalize_review_decision("confirm") == "ACCEPT_MATCH"
    assert resolver.normalize_review_decision("reject") == "REJECT_MATCH"
    assert ResolveDecision(decision="confirm", reason=REASON).decision == "ACCEPT_MATCH"
    assert ResolveDecision(decision="reject", reason=REASON).decision == "REJECT_MATCH"


def test_unknown_decision_is_rejected_not_defaulted():
    with pytest.raises(ValueError):
        resolver.normalize_review_decision("MATCH_ANYWAY")
    with pytest.raises(ValidationError):
        ResolveDecision(decision="MATCH_ANYWAY", reason=REASON)
    with pytest.raises(ValueError):
        resolver.create_detached_citizen(
            None,  # type: ignore[arg-type]
            claim_id=1,
            name="x",
            decision="ACCEPT_MATCH",
            reason=REASON,
        )


# ── REJECT_MATCH mints a BRAND-NEW citizen ───────────────────────────────────


def test_reject_match_mints_new_citizen_and_never_reuses_rejected(db):
    patient, rejected, claim = _pending_claim(db)
    reviewer = _reviewer(db)
    assert rejected.nid_hash is not None

    outcome = resolver.create_detached_citizen(
        db,
        claim_id=claim.id,
        name=patient.full_name,
        phone=patient.phone,
        rejected_citizen_id=rejected.id,
        claimed_by_user_id=reviewer.id,
        decision="REJECT_MATCH",
        reason=REASON,
    )
    db.flush()

    assert outcome.citizen.id != rejected.id
    assert outcome.citizen.citizen_ulid != rejected.citizen_ulid
    # Disputed NID is deliberately NOT transferred to the new record.
    assert outcome.citizen.nid_hash is None
    # SAME claim row is re-pointed (no delete → UNIQUE key preserved).
    assert db.query(IdentityClaim).filter(IdentityClaim.id == claim.id).one().citizen_id == (
        outcome.citizen.id
    )
    assert claim.match_method == "new"
    assert db.query(IdentityClaim).count() == 1

    audit = (
        db.query(MergeAudit)
        .filter(MergeAudit.event_type == resolver.AUDIT_EVENT_REVIEW_REJECT)
        .one()
    )
    assert audit.primary_citizen_id == outcome.citizen.id
    assert audit.secondary_citizen_id == rejected.id
    assert audit.decided_by_user_id == reviewer.id
    assert audit.decision_reason == REASON
    assert audit.match_features["decision"] == "REJECT_MATCH"
    assert audit.match_features["rejected_citizen_id"] == rejected.id
    assert audit.match_features["reviewed_by_user_id"] == reviewer.id
    assert "reviewed_at" in audit.match_features


def test_create_new_identity_uses_dedicated_audit_event(db):
    patient, rejected, claim = _pending_claim(db, suffix="NEWID")
    outcome = resolver.create_detached_citizen(
        db,
        claim_id=claim.id,
        name=patient.full_name,
        rejected_citizen_id=rejected.id,
        claimed_by_user_id=None,
        decision="CREATE_NEW_IDENTITY",
        reason=REASON,
    )
    db.flush()
    audit = (
        db.query(MergeAudit)
        .filter(MergeAudit.event_type == resolver.AUDIT_EVENT_REVIEW_NEW_ID)
        .one()
    )
    assert audit.primary_citizen_id == outcome.citizen.id
    assert audit.match_features["decision"] == "CREATE_NEW_IDENTITY"


def test_reject_requires_a_reason():
    with pytest.raises(ValueError, match="reason"):
        resolver.create_detached_citizen(
            None,  # type: ignore[arg-type]
            claim_id=1,
            name="Synthetic Name",
            decision="REJECT_MATCH",
            reason="   ",
        )


# ── Replay / concurrency safety ──────────────────────────────────────────────


def test_decision_is_replay_safe_second_application_refused(db):
    patient, rejected, claim = _pending_claim(db, suffix="REPLAY")
    resolver.create_detached_citizen(
        db,
        claim_id=claim.id,
        name=patient.full_name,
        rejected_citizen_id=rejected.id,
        decision="REJECT_MATCH",
        reason=REASON,
    )
    db.flush()
    first_ulid = claim.citizen.citizen_ulid
    audit_count = db.query(MergeAudit).count()

    with pytest.raises(ValueError, match="no longer pending"):
        resolver.create_detached_citizen(
            db,
            claim_id=claim.id,
            name=patient.full_name,
            rejected_citizen_id=rejected.id,
            decision="REJECT_MATCH",
            reason=REASON,
        )
    assert claim.citizen.citizen_ulid == first_ulid
    assert db.query(MergeAudit).count() == audit_count


def test_review_decision_reconcile_returns_original_after_in_doubt_commit(
    db, _savepoint_conn, monkeypatch
):
    patient, rejected, claim = _pending_claim(db, suffix="RECON")
    resolver.create_detached_citizen(
        db,
        claim_id=claim.id,
        name=patient.full_name,
        rejected_citizen_id=rejected.id,
        decision="REJECT_MATCH",
        reason=REASON,
    )
    db.commit()
    expected_ulid = claim.citizen.citizen_ulid

    monkeypatch.setattr(
        _database, "SessionLocal", sessionmaker(bind=_savepoint_conn, autoflush=False)
    )
    reconciled = mpi_api._decision_reconcile(
        claim_id=claim.id, canonical_decision="REJECT_MATCH"
    )
    assert reconciled is not None
    assert reconciled["status"] == "rejected"
    assert reconciled["new_citizen_ulid"] == expected_ulid
    assert reconciled["previous_citizen_id"] == rejected.id


def test_review_decision_reconcile_none_when_not_committed(db, _savepoint_conn, monkeypatch):
    monkeypatch.setattr(
        _database, "SessionLocal", sessionmaker(bind=_savepoint_conn, autoflush=False)
    )
    assert (
        mpi_api._decision_reconcile(claim_id=999991, canonical_decision="ACCEPT_MATCH")
        is None
    )


# ── ACCEPT_MATCH and NEEDS_MANUAL_REVIEW ─────────────────────────────────────


def test_accept_match_preserves_citizen_and_writes_chained_audit(db):
    _patient, reviewed, claim = _pending_claim(db, suffix="ACCEPT")
    reviewer = _reviewer(db)
    outcome = resolver.confirm_reviewed_match(
        db,
        claim_id=claim.id,
        reason=REASON,
        reviewer_user_id=reviewer.id,
    )
    db.flush()
    assert outcome.citizen.id == reviewed.id
    assert claim.match_method == "manual"
    audit = (
        db.query(MergeAudit)
        .filter(MergeAudit.event_type == resolver.AUDIT_EVENT_REVIEW_ACCEPT)
        .one()
    )
    assert audit.primary_citizen_id == reviewed.id
    assert audit.match_features["decision"] == "ACCEPT_MATCH"


def test_accept_match_replay_refused(db):
    _patient, _reviewed, claim = _pending_claim(db, suffix="ACCREPLAY")
    resolver.confirm_reviewed_match(
        db, claim_id=claim.id, reason=REASON, reviewer_user_id=None
    )
    db.flush()
    with pytest.raises(ValueError, match="no longer pending"):
        resolver.confirm_reviewed_match(
            db, claim_id=claim.id, reason=REASON, reviewer_user_id=None
        )


def test_needs_manual_review_endpoint_is_an_explicit_noop(
    db, _savepoint_conn, monkeypatch
):
    """The fourth decision must leave the claim pending, untouched."""
    _, rejected, claim = _pending_claim(db, suffix="NOOP")
    reviewer = _reviewer(db)
    monkeypatch.setattr(
        _database, "SessionLocal", sessionmaker(bind=_savepoint_conn, autoflush=False)
    )
    response = mpi_api.decide_pending_review(
        claim_id=claim.id,
        decision=ResolveDecision(decision="NEEDS_MANUAL_REVIEW", reason=REASON),
        current_user=reviewer,
        db=db,
    )
    assert response["status"] == "needs_manual_review"
    assert response["match_method"] == "pending_review"
    # db.close() was called by the endpoint; use a fresh session on the same conn.
    check = sessionmaker(bind=_savepoint_conn, autoflush=False)()
    try:
        still = check.query(IdentityClaim).filter(IdentityClaim.id == claim.id).one()
        assert still.match_method == "pending_review"
        assert still.citizen_id == rejected.id
        assert check.query(MergeAudit).count() == 0
    finally:
        check.close()


# ── Chained audit + broken-chain detection (AUD-11 / AUD-13) ─────────────────


def test_review_audit_rows_form_a_valid_hash_chain(db):
    p1, r1, c1 = _pending_claim(db, suffix="CHN1")
    _, _, c2 = _pending_claim(db, suffix="CHN2")
    resolver.create_detached_citizen(
        db, claim_id=c1.id, name=p1.full_name, rejected_citizen_id=r1.id,
        decision="REJECT_MATCH", reason=REASON,
    )
    resolver.confirm_reviewed_match(
        db, claim_id=c2.id, reason=REASON, reviewer_user_id=None
    )
    db.flush()
    result = resolver.verify_merge_audit_chain(db)
    assert result.valid is True, result.errors
    assert result.checked == 2


def test_broken_canonical_chain_is_detected_not_silently_followed(db):
    a = _citizen(db, "BROKA")
    b = _citizen(db, "BROKB")
    b.merged_into_id = a.id
    db.flush()
    # Point a at a non-existent citizen → broken chain.
    a.merged_into_id = 999_999
    db.flush()

    assert resolver.verify_canonical_chains(db).valid is False
    with pytest.raises(BrokenCanonicalChainError):
        b.canonical(strict=True)
    # Read paths keep the safe fallback but no longer pretend it is canonical.
    assert b.canonical() is b


def test_integrity_probe_reports_fork_without_repairing(db):
    a = _citizen(db, "PROBEA")
    b = _citizen(db, "PROBEB")
    b.merged_into_id = a.id
    a.merged_into_id = 999_999
    db.flush()

    probe = resolver.mpi_integrity_probe(db)
    assert probe["valid"] is False
    assert probe["status"] == "forked"
    assert probe["canonical_chains"]["valid"] is False
    assert probe["policy"].startswith("detection_only")
    # Detection only: no rows were rewritten / deleted.
    assert a.merged_into_id == 999_999
    assert b.merged_into_id == a.id


def test_decide_endpoint_rejects_unknown_claim(db, _savepoint_conn, monkeypatch):
    monkeypatch.setattr(
        _database, "SessionLocal", sessionmaker(bind=_savepoint_conn, autoflush=False)
    )
    with pytest.raises(HTTPException) as exc:
        mpi_api.decide_pending_review(
            claim_id=999992,
            decision=ResolveDecision(decision="ACCEPT_MATCH", reason=REASON),
            current_user=_reviewer(db),
            db=db,
        )
    assert exc.value.status_code == 404
