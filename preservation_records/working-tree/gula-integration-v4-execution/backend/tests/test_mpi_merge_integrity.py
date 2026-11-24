"""P0-E regression tests — MPI manual-merge integrity (synthetic fixtures only).

Pins defects where a merge left IdentityClaim rows pointing at the merged-away
citizen, had no cycle/idempotency handling, and could leave a partial merge
committed if a later check failed.
"""

from __future__ import annotations

import pytest
from app.models.lab import Lab
from app.models.patient import Patient
from app.services.mpi import resolver
from app.services.mpi.models import Citizen, IdentityClaim, MergeAudit


def _citizen(db, suffix: str, *, status: str = "active", merged_into_id=None) -> Citizen:
    c = Citizen(
        citizen_ulid=f"01SYNTHETIC{suffix}0000000000000"[:26],
        name_canonical=f"synthetic person {suffix}",
        name_blocking_key=f"syn{suffix}"[:20],
        status=status,
        merged_into_id=merged_into_id,
    )
    db.add(c)
    db.flush()
    return c


@pytest.fixture()
def merge_fixture(db):
    lab = Lab(id=909001, name="Merge Test Lab", license_number="MERGE-TEST-001")
    db.add(lab)
    db.flush()
    patients = []
    for i in range(2):
        p = Patient(
            lab_id=lab.id, full_name=f"Merge Patient {i}",
            phone=f"+964700000000{i}",
        )
        db.add(p)
        patients.append(p)
    db.flush()
    primary = _citizen(db, "PRIMARY")
    secondary = _citizen(db, "SECOND")
    claims = []
    for p in patients:
        claim = IdentityClaim(
            citizen_id=secondary.id,
            lab_id=lab.id,
            local_patient_id=p.id,
            match_method="probabilistic",
            match_features={"source": "synthetic"},
        )
        db.add(claim)
        claims.append(claim)
    db.flush()
    return primary, secondary, claims


def test_merge_repoints_claims_records_provenance_and_audits(merge_fixture, db):
    primary, secondary, claims = merge_fixture
    audit = resolver.merge_citizens(
        db,
        primary_ulid=primary.citizen_ulid,
        secondary_ulid=secondary.citizen_ulid,
        reason="synthetic duplicate verified",
        decided_by_user_id=42,
    )
    db.flush()

    assert secondary.status == "merged"
    assert secondary.merged_into_id == primary.id
    db.expire_all()
    for claim in claims:
        fresh = db.query(IdentityClaim).filter(IdentityClaim.id == claim.id).one()
        assert fresh.citizen_id == primary.id
        assert fresh.match_features["merged_from_citizen_ulid"] == secondary.citizen_ulid
        assert fresh.match_features["source"] == "synthetic"

    assert audit.event_type == "manual_merge"
    assert audit.primary_citizen_id == primary.id
    assert audit.secondary_citizen_id == secondary.id
    assert audit.decision_reason == "synthetic duplicate verified"
    assert audit.decided_by_user_id == 42
    assert len(audit.entry_hash) == 64
    assert db.query(Citizen).filter(Citizen.citizen_ulid == primary.citizen_ulid).one().canonical().id == primary.id


def test_merge_is_idempotent_on_retry(merge_fixture, db):
    primary, secondary, _ = merge_fixture
    kwargs = {
        "primary_ulid": primary.citizen_ulid,
        "secondary_ulid": secondary.citizen_ulid,
        "reason": "synthetic duplicate verified",
        "decided_by_user_id": 42,
    }
    first = resolver.merge_citizens(db, **kwargs)
    db.flush()
    second = resolver.merge_citizens(db, **kwargs)
    assert second.id == first.id
    assert db.query(MergeAudit).filter(
        MergeAudit.event_type == "manual_merge",
        MergeAudit.primary_citizen_id == primary.id,
        MergeAudit.secondary_citizen_id == secondary.id,
    ).count() == 1


def test_merge_rejects_self(merge_fixture, db):
    primary, _, _ = merge_fixture
    with pytest.raises(ValueError, match="itself"):
        resolver.merge_citizens(
            db, primary_ulid=primary.citizen_ulid,
            secondary_ulid=primary.citizen_ulid,
            reason="synthetic", decided_by_user_id=42,
        )


def test_merge_rejects_cycle(merge_fixture, db):
    primary, secondary, _ = merge_fixture
    # Both inputs already resolve to a third survivor → merging them would
    # create a cycle and must be rejected (distinct from the idempotent retry).
    survivor = _citizen(db, "SURVIV")
    db.flush()
    for c in (primary, secondary):
        c.merged_into_id = survivor.id
        c.status = "merged"
    db.flush()
    with pytest.raises(ValueError, match="same canonical identity"):
        resolver.merge_citizens(
            db, primary_ulid=primary.citizen_ulid,
            secondary_ulid=secondary.citizen_ulid,
            reason="synthetic", decided_by_user_id=42,
        )


def test_merge_requires_reason(merge_fixture, db):
    primary, secondary, _ = merge_fixture
    with pytest.raises(ValueError, match="reason"):
        resolver.merge_citizens(
            db, primary_ulid=primary.citizen_ulid,
            secondary_ulid=secondary.citizen_ulid,
            reason="   ", decided_by_user_id=42,
        )


def test_merge_rolls_back_on_audit_failure(merge_fixture, db, monkeypatch):
    primary, secondary, claims = merge_fixture

    def _boom(*_args, **_kwargs):
        raise RuntimeError("synthetic audit failure")

    monkeypatch.setattr(resolver, "_write_audit", _boom)
    with pytest.raises(RuntimeError, match="synthetic audit failure"):
        resolver.merge_citizens(
            db, primary_ulid=primary.citizen_ulid,
            secondary_ulid=secondary.citizen_ulid,
            reason="synthetic rollback test", decided_by_user_id=42,
        )
    db.expire_all()
    fresh_secondary = db.query(Citizen).filter(
        Citizen.citizen_ulid == secondary.citizen_ulid,
    ).one()
    assert fresh_secondary.status == "active"
    assert fresh_secondary.merged_into_id is None
    for claim in claims:
        fresh = db.query(IdentityClaim).filter(IdentityClaim.id == claim.id).one()
        assert fresh.citizen_id == secondary.id
