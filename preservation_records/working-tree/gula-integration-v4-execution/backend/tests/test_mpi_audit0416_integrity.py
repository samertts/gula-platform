"""AUD-04 / AUD-06 / AUD-08 / AUD-13 / AUD-14 / AUD-16 integrity regressions.

Synthetic-only tests: NID re-read under the lock, unordered-pair merge replay,
governance probe wiring, score normalisation before hashing, and fail-closed
fork detection that never hides a split.
"""

from __future__ import annotations

import pytest
from app import database as _database
from app.main import app
from app.models.lab import Lab
from app.models.lab_user import LabUser
from app.models.patient import Patient
from app.security.dependencies import get_current_user
from app.services.mpi import api as mpi_api
from app.services.mpi import resolver
from app.services.mpi.models import Citizen, MergeAudit
from app.services.mpi.reliability import (
    AUDIT_LOCK_KEY,
    CANONICAL_LINK_LOCK_KEY,
    CANONICAL_LINK_LOCK_NAMESPACE,
)
from sqlalchemy.orm import sessionmaker

REASON = "synthetic verified duplicate"
NID_HASH = "fake-hmac-sha256-for-synthetic-nid-only"


def _lab(db, lab_id: int = 909400) -> Lab:
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if lab is None:
        lab = Lab(id=lab_id, name="Synthetic AUD0416 Lab", license_number="SYN-AUD0416-001")
        db.add(lab)
        db.flush()
    return lab


def _actor(db, user_id: int = 909401) -> LabUser:
    u = db.query(LabUser).filter(LabUser.id == user_id).first()
    if u is None:
        u = LabUser(
            id=user_id,
            lab_id=909400,
            name="Synthetic AUD0416 Actor",
            email=f"synthetic-aud0416-{user_id}@example.invalid",
            password_hash="synthetic-not-a-real-hash",
            role="master_admin",
            is_active=True,
        )
        db.add(u)
        db.flush()
    return u


def _citizen(db, suffix: str, *, nid_hash: str | None = None) -> Citizen:
    c = Citizen(
        citizen_ulid=f"01SYNTHAUD0416{suffix}".ljust(26, "0")[:26],
        nid_hash=nid_hash,
        name_canonical=f"synthetic aud0416 {suffix}",
        name_blocking_key=f"synaud0416{suffix}"[:20],
        status="active",
        version=1,
    )
    db.add(c)
    db.flush()
    return c


# ── AUD-04: NID re-read under the advisory lock ──────────────────────────────


def test_same_nid_across_two_patients_resolves_to_one_citizen(db):
    lab = _lab(db)
    for idx, patient_id in enumerate((909410, 909411), start=1):
        patient = Patient(
            id=patient_id,
            lab_id=lab.id,
            full_name=f"Synthetic NID Patient {idx}",
            phone=f"+96470000044{idx}",
        )
        db.add(patient)
        db.flush()
        outcome = resolver.resolve_identity(
            db,
            lab_id=lab.id,
            local_patient_id=patient.id,
            name=patient.full_name,
            phone=patient.phone,
            national_id="1234567890123",  # digits only; synthetic, not a real NID
        )
        db.flush()
        if idx == 1:
            first_ulid = outcome.citizen.citizen_ulid
            # AUD-MPI-001: an NID is authoritative only when nid_verified=True.
            # This test's intent is AUD-04 duplicate-NID idempotency, so mark
            # the synthetic NID verified explicitly before the second resolve.
            outcome.citizen.nid_verified = True
            db.flush()
        else:
            assert outcome.citizen.citizen_ulid == first_ulid
            assert outcome.created is False
            assert outcome.match_method == "nid_exact"
            assert outcome.features.get("nid_hash") is True
            assert outcome.features.get("nid_verified") is True

    citizens = db.query(Citizen).filter(Citizen.nid_hash.isnot(None)).count()
    assert citizens == 1  # no duplicate NID row


def test_locked_nid_reread_is_present_in_create_branch():
    """The pre-lock fast path can miss a concurrently committed NID (AUD-04).

    A single-process test cannot force that interleaving; this structural pin
    plus the PostgreSQL concurrency harness proves the re-read is reached from
    the create branch before any insert.
    """
    source = (resolver.__file__ and __import__("pathlib").Path(resolver.__file__)).read_text()
    assert "locked_nid_hit" in source
    assert "acquire_audit_chain_lock(db)" in source
    assert "nid_reconciled_under_lock" in source


# ── AUD-06: unordered-pair replay inside the locked region ───────────────────


def test_reversed_ulid_merge_replay_returns_original_row(db):
    primary = _citizen(db, "PRI")
    secondary = _citizen(db, "SEC")
    actor = _actor(db)
    first = resolver.merge_citizens(
        db,
        primary_ulid=primary.citizen_ulid,
        secondary_ulid=secondary.citizen_ulid,
        reason=REASON,
        decided_by_user_id=actor.id,
    )
    db.flush()
    before = db.query(MergeAudit).count()

    replay = resolver.merge_citizens(
        db,
        primary_ulid=secondary.citizen_ulid,  # swapped by a reconnecting client
        secondary_ulid=primary.citizen_ulid,
        reason=REASON,
        decided_by_user_id=actor.id,
    )
    assert replay.id == first.id
    assert db.query(MergeAudit).count() == before  # no second audit row


def test_reversed_pair_with_different_reason_is_refused(db):
    primary = _citizen(db, "RPRI")
    secondary = _citizen(db, "RSEC")
    resolver.merge_citizens(
        db,
        primary_ulid=primary.citizen_ulid,
        secondary_ulid=secondary.citizen_ulid,
        reason=REASON,
        decided_by_user_id=None,
    )
    db.flush()
    with pytest.raises(ValueError, match="conflicting merge replay"):
        resolver.merge_citizens(
            db,
            primary_ulid=secondary.citizen_ulid,
            secondary_ulid=primary.citizen_ulid,
            reason="a competing conflicting reason",
            decided_by_user_id=None,
        )


# ── AUD-14: normalise numeric type before hashing ────────────────────────────


def test_score_is_quantized_before_hash_and_still_verifies(db):
    primary = _citizen(db, "QPRI")
    secondary = _citizen(db, "QSEC")
    audit = resolver._write_audit(
        db,
        event_type="manual_merge",
        primary=primary,
        secondary=secondary,
        match_score_val=0.9123456,  # more precision than Numeric(4,3)
        features={"synthetic": True},
        reason=REASON,
        decided_by_user_id=None,
    )
    db.flush()
    assert resolver._quantize_score(0.9123456) == 0.912
    assert round(float(audit.match_score), 3) == 0.912
    result = resolver.verify_merge_audit_chain(db)
    assert result.valid is True, result.errors

    # A tampered score must now break the chain (detection, not repair).
    audit.match_score = 0.5
    db.flush()
    assert resolver.verify_merge_audit_chain(db).valid is False


# ── AUD-16: fail-closed fork policy ──────────────────────────────────────────


def test_segment_verification_raises_fork_error_on_broken_link(db):
    primary = _citizen(db, "FPRI")
    audit = resolver._write_audit(
        db,
        event_type="manual_merge",
        primary=primary,
        secondary=None,
        match_score_val=None,
        features={},
        reason=REASON,
        decided_by_user_id=None,
    )
    db.flush()
    with pytest.raises(resolver.AuditForkError):
        resolver._verify_audit_segment(
            db, first_id=audit.id, expected_prev="f" * 64
        )


def test_fork_is_reported_by_probe_without_rewriting_rows(db):
    primary = _citizen(db, "IPRI")
    secondary = _citizen(db, "ISEC")
    audit = resolver.merge_citizens(
        db,
        primary_ulid=primary.citizen_ulid,
        secondary_ulid=secondary.citizen_ulid,
        reason=REASON,
        decided_by_user_id=None,
    )
    db.flush()
    original_hash = audit.entry_hash
    audit.prev_hash = "b" * 64  # simulate a fork / tampering
    db.flush()

    probe = resolver.mpi_integrity_probe(db)
    assert probe["valid"] is False
    assert probe["status"] == "forked"
    assert probe["merge_audit"]["valid"] is False
    assert "detection_only" in probe["policy"]
    # The split is NOT hidden / auto-repaired.
    assert audit.prev_hash == "b" * 64
    assert audit.entry_hash == original_hash


# ── AUD-02/AUD-08: advisory key separation + governance probe host ───────────


def test_canonical_link_lock_key_is_stable_distinct_and_versioned():
    assert CANONICAL_LINK_LOCK_NAMESPACE.endswith(":v1")
    assert isinstance(CANONICAL_LINK_LOCK_KEY, int)
    assert CANONICAL_LINK_LOCK_KEY != AUDIT_LOCK_KEY
    assert 0 <= CANONICAL_LINK_LOCK_KEY <= 0x7FFF_FFFF_FFFF_FFFF


def test_audit_integrity_endpoint_exposes_mpi_probe(client, db):
    actor = _actor(db)
    app.dependency_overrides[get_current_user] = lambda: actor
    try:
        r = client.get("/compliance/audit-integrity?limit=50")
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "mpi_integrity" in body
    assert body["mpi_integrity"]["valid"] is True
    assert body["mpi_integrity"]["status"] == "intact"
