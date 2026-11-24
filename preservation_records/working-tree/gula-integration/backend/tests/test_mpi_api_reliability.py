"""MPI API transaction/idempotency regressions (MPI-04/05, synthetic only).

Pins: replay of an already-applied merge returns the original audited result
even with reversed primary/secondary ULIDs; a conflicting replay reason is
rejected; in-doubt `resolve` commits are reconciled by the claim idempotency
key; and merge responses are materialised before commit so `expire_on_commit`
cannot force a post-commit lazy load.
"""

from __future__ import annotations

import pytest
from app import database as _database
from app.models.lab import Lab
from app.models.patient import Patient
from app.services.mpi import api as mpi_api
from app.services.mpi import resolver
from app.services.mpi.models import Citizen, IdentityClaim, MergeAudit
from fastapi import HTTPException
from sqlalchemy.orm import sessionmaker


def _citizen(db, suffix: str) -> Citizen:
    c = Citizen(
        citizen_ulid=f"01SYNTHAPI{suffix}000000000000"[:26],
        name_canonical=f"synthetic api {suffix}",
        name_blocking_key=f"synapi{suffix}"[:20],
        status="active",
        version=1,
    )
    db.add(c)
    db.flush()
    return c


def _merged_pair(db, reason: str = "synthetic verified duplicate"):
    primary = _citizen(db, "PRIM")
    secondary = _citizen(db, "SECO")
    audit = resolver.merge_citizens(
        db,
        primary_ulid=primary.citizen_ulid,
        secondary_ulid=secondary.citizen_ulid,
        reason=reason,
        decided_by_user_id=42,
    )
    db.flush()
    return primary, secondary, audit


def test_merge_replay_reversed_ulids_returns_original_without_new_audit(db):
    primary, secondary, audit = _merged_pair(db)
    before = db.query(MergeAudit).filter(MergeAudit.event_type == "manual_merge").count()

    replay = mpi_api._find_merge_replay(
        db,
        primary_ulid=secondary.citizen_ulid,  # reversed by a reconnecting client
        secondary_ulid=primary.citizen_ulid,
        reason="synthetic verified duplicate",
    )
    assert replay is not None
    assert replay.event_id == audit.id
    assert replay.primary_ulid == primary.citizen_ulid
    assert replay.secondary_ulid == secondary.citizen_ulid
    assert replay.entry_hash == audit.entry_hash
    after = db.query(MergeAudit).filter(MergeAudit.event_type == "manual_merge").count()
    assert after == before  # no new mutation


def test_merge_replay_conflicting_reason_is_rejected(db):
    primary, secondary, _audit = _merged_pair(db)
    with pytest.raises(HTTPException) as exc:
        mpi_api._find_merge_replay(
            db,
            primary_ulid=primary.citizen_ulid,
            secondary_ulid=secondary.citizen_ulid,
            reason="a different competing decision",
        )
    assert exc.value.status_code == 409


def test_merge_response_is_materialised_before_commit(db):
    primary, secondary, audit = _merged_pair(db)
    response = mpi_api._merge_response(
        audit,
        primary_ulid=primary.citizen_ulid,
        secondary_ulid=secondary.citizen_ulid,
    )
    captured = (response.event_id, response.entry_hash, response.occurred_at)
    db.commit()  # expire_on_commit=True detaches/expires all ORM instances
    assert (response.event_id, response.entry_hash, response.occurred_at) == captured


def test_resolve_reconcile_returns_persisted_outcome(db, _savepoint_conn, monkeypatch):
    lab = Lab(id=909771, name="API Reconcile Lab", license_number="API-REC-001")
    db.add(lab)
    db.flush()
    patient = Patient(
        lab_id=lab.id,
        full_name="Synthetic Reconcile Patient",
        phone="+964700000999",
    )
    db.add(patient)
    db.flush()
    outcome = resolver.resolve_identity(
        db,
        lab_id=lab.id,
        local_patient_id=patient.id,
        name=patient.full_name,
    )
    db.commit()
    expected_ulid = outcome.citizen.citizen_ulid

    # Reconciliation must use a FRESH session, never the failed one. In tests
    # the shared savepoint connection is the only one that sees fixture rows.
    monkeypatch.setattr(
        _database, "SessionLocal", sessionmaker(bind=_savepoint_conn, autoflush=False)
    )
    reconciled = mpi_api._resolve_reconcile(
        lab_id=lab.id, local_patient_id=patient.id
    )
    assert reconciled is not None
    assert reconciled.citizen_ulid == expected_ulid
    assert reconciled.created is False


def test_resolve_reconcile_returns_none_when_nothing_committed(db, _savepoint_conn, monkeypatch):
    monkeypatch.setattr(
        _database, "SessionLocal", sessionmaker(bind=_savepoint_conn, autoflush=False)
    )
    assert (
        mpi_api._resolve_reconcile(lab_id=998877, local_patient_id=998877) is None
    )
