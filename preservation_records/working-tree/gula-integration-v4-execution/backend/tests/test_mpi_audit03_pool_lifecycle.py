"""AUD-03 / AUD-05 / AUD-15 — request connection lifecycle and pool proof.

Pins: the request-scoped DB connection is released before bounded_retry opens
its operation session (never two held connections per request); ambiguous-commit
reconciliation runs on a FRESH session and is returned without replaying; no
semaphore was introduced; the accepted request volume was not reduced.
"""

from __future__ import annotations

import pathlib

import pytest
from app import database as _database
from app.main import app
from app.models.lab import Lab
from app.models.lab_user import LabUser
from app.models.patient import Patient
from app.security.dependencies import get_current_user
from app.services.mpi import api as mpi_api
from app.services.mpi import resolver
from app.services.mpi.models import Citizen, IdentityClaim
from app.services.mpi.schemas import ResolveDecision
from sqlalchemy.orm import sessionmaker

MPI_DIR = pathlib.Path(mpi_api.__file__).parent
DATABASE_FILE = pathlib.Path(_database.__file__)


class _TransientError(Exception):
    """Simulates SQLSTATE 40001 (serialization_failure)."""

    pgcode = "40001"


def _lab(db, lab_id: int = 909300) -> Lab:
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if lab is None:
        lab = Lab(id=lab_id, name="Synthetic AUD03 Lab", license_number="SYN-AUD03-001")
        db.add(lab)
        db.flush()
    return lab


def _actor(db, user_id: int = 909301, role: str = "master_admin") -> LabUser:
    u = db.query(LabUser).filter(LabUser.id == user_id).first()
    if u is None:
        u = LabUser(
            id=user_id,
            lab_id=909300,
            name="Synthetic AUD03 Actor",
            email=f"synthetic-aud03-{user_id}@example.invalid",
            password_hash="synthetic-not-a-real-hash",
            role=role,
            is_active=True,
        )
        db.add(u)
        db.flush()
    return u


def _patient(db, patient_id: int = 909310) -> Patient:
    p = Patient(
        id=patient_id,
        lab_id=909300,
        full_name="Synthetic AUD03 Patient",
        phone="+964700000333",
    )
    db.add(p)
    db.flush()
    return p


def _citizen(db, suffix: str) -> Citizen:
    c = Citizen(
        citizen_ulid=f"01SYNTHAUD03{suffix}".ljust(26, "0")[:26],
        name_canonical=f"synthetic aud03 {suffix}",
        name_blocking_key=f"synaud03{suffix}"[:20],
        status="active",
        version=1,
    )
    db.add(c)
    db.flush()
    return c


def _trace_sessions(db, savepoint_conn, monkeypatch) -> list[str]:
    """Track the exact order of request-session close vs operation open."""
    events: list[str] = []
    real_close = db.close

    def tracked_close():
        events.append("request_close")
        return real_close()

    monkeypatch.setattr(db, "close", tracked_close)
    base_factory = sessionmaker(bind=savepoint_conn, autoflush=False)

    def tracked_factory():
        events.append("operation_session_open")
        return base_factory()

    monkeypatch.setattr(_database, "SessionLocal", tracked_factory)
    return events


def test_resolve_releases_request_connection_before_operation_session(
    client, db, _savepoint_conn, monkeypatch
):
    _lab(db)
    actor = _actor(db)
    patient = _patient(db)
    trace = _trace_sessions(db, _savepoint_conn, monkeypatch)

    app.dependency_overrides[get_current_user] = lambda: actor
    try:
        r = client.post(
            "/mpi/resolve",
            json={
                "lab_id": 909300,
                "patient_id": patient.id,
                "name": patient.full_name,
                "phone": patient.phone,
            },
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert r.status_code == 200, r.text
    assert trace[0] == "request_close", trace
    assert "operation_session_open" in trace
    assert trace.index("request_close") < trace.index("operation_session_open")
    assert trace.count("operation_session_open") == 1  # no retries on success


def test_decision_releases_request_connection_before_operation_session(
    db, _savepoint_conn, monkeypatch
):
    _lab(db)
    actor = _actor(db)
    patient = _patient(db, 909311)
    rejected = _citizen(db, "DEC")

    claim = IdentityClaim(
        citizen_id=rejected.id,
        lab_id=909300,
        local_patient_id=patient.id,
        match_method="pending_review",
        match_score=0.81,
    )
    db.add(claim)
    db.flush()

    trace = _trace_sessions(db, _savepoint_conn, monkeypatch)

    response = mpi_api.decide_pending_review(
        claim_id=claim.id,
        decision=ResolveDecision(decision="REJECT_MATCH", reason="synthetic review evidence text"),
        current_user=actor,
        db=db,
    )
    assert response["status"] == "rejected"
    assert trace[0] == "request_close", trace
    assert trace.index("request_close") < trace.index("operation_session_open")


def test_merge_ambiguous_commit_reconciles_without_replay(
    client, db, _savepoint_conn, monkeypatch
):
    """A transient error after a committed merge returns the original audit.

    AUD-05: reconciliation must run on a fresh session; replaying the merge on
    the failed session would create a second audit row / wrong linkage.
    """
    actor = _actor(db, 909302, "master_admin")
    primary = _citizen(db, "MPRI")
    secondary = _citizen(db, "MSEC")
    seeded_audit = resolver.merge_citizens(
        db,
        primary_ulid=primary.citizen_ulid,
        secondary_ulid=secondary.citizen_ulid,
        reason="synthetic verified duplicate",
        decided_by_user_id=actor.id,
    )
    db.flush()

    real_replay = mpi_api._find_merge_replay

    def patched_replay(session, **kwargs):
        # The request-session pre-check deliberately returns None to simulate a
        # commit whose acknowledgement was lost.  The fresh reconcile session
        # must still find the persisted audit row.
        if session is db:
            return None
        return real_replay(session, **kwargs)

    calls: list[dict] = []

    def failing_merge(session, **kwargs):
        calls.append(kwargs)
        raise _TransientError("lost acknowledgement after commit")

    monkeypatch.setattr(_database, "SessionLocal", sessionmaker(bind=_savepoint_conn, autoflush=False))
    monkeypatch.setattr(mpi_api, "_find_merge_replay", patched_replay)
    monkeypatch.setattr(resolver, "merge_citizens", failing_merge)

    app.dependency_overrides[get_current_user] = lambda: actor
    try:
        r = client.post(
            "/mpi/merge",
            json={
                "primary_ulid": primary.citizen_ulid,
                "secondary_ulid": secondary.citizen_ulid,
                "reason": "synthetic verified duplicate",
            },
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert r.status_code == 200, r.text
    assert len(calls) == 1  # operation attempted once; reconcile prevented replay
    assert r.json()["event_id"] == seeded_audit.id


def test_no_global_semaphore_introduced_in_mpi():
    sources = "\n".join(p.read_text() for p in MPI_DIR.glob("*.py"))
    assert "Semaphore" not in sources
    assert "threading.BoundedSemaphore" not in sources
    assert "asyncio.Semaphore" not in sources


def test_accepted_request_volume_not_reduced():
    sources = (MPI_DIR / "api.py").read_text()
    # 60/min per authenticated user was the shipped contract; the remediation
    # must not throttle accepted volume to compensate for pool pressure.
    assert "max_per_minute=60" in sources
    db_source = DATABASE_FILE.read_text()
    assert "_WORKERS" in db_source  # pool sizing still configured from workers
