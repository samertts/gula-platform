"""POST /samples/{id}/transition — the idempotency contract it now actually keeps.

The route required an ``Idempotency-Key``, then discarded the value without
claiming a receipt. A reused key was neither honoured nor rejected, and the
transition left no entry in the audit chain — the only guarded Blood Bank route
with that gap.

Replay was never able to apply the transition twice: the service takes a row
lock and validates against a strict map (collected -> identified -> received ->
testing -> validated), so a second call fails the state check. That is a refusal,
not the canonical replay answer, and it says nothing about a reused key carrying
a *different* payload.

These tests prove the four properties the canonical mechanism gives, using the
same ClinicalCommandGuard the route's thirteen siblings use.
"""
from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from app.blood_bank.infrastructure.models import PatientBloodSampleModel
from app.main import app
from app.models.audit_log import AuditLog
from app.models.clinical_command import ClinicalCommandReceipt
from sqlalchemy import func, text
from test_http_idempotency_postgres import (  # type: ignore[import-not-found]
    ACTOR_ID,
    FACILITY_ID,
    LAB_ID,
    PATIENT_ID,
    _client,
    _session_factory,
)

POSTGRES_URL = os.getenv("BLOOD_BANK_POSTGRES_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL, reason="BLOOD_BANK_POSTGRES_URL is not configured"
)

SAMPLE_ID = "http-sample-transition"
OPERATION = "blood.sample.transition"


def _prepare_sample(Session: Any) -> None:
    now = datetime.now(UTC)
    with Session() as session:
        session.query(ClinicalCommandReceipt).filter(
            ClinicalCommandReceipt.lab_id == LAB_ID
        ).delete(synchronize_session=False)
        session.query(PatientBloodSampleModel).filter(
            PatientBloodSampleModel.lab_id == LAB_ID
        ).delete(synchronize_session=False)
        session.commit()
    engine = Session.kw["bind"]
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO labs (id, name, is_active) VALUES (:id, :n, true) "
                 "ON CONFLICT (id) DO NOTHING"),
            {"id": LAB_ID, "n": "Synthetic HTTP Blood Bank Lab"},
        )
        conn.execute(
            text("INSERT INTO lab_users (id, lab_id, name, email, password_hash, role, "
                 "is_active, perm_version) VALUES (:id, :lab, :n, :e, :p, :r, true, 1) "
                 "ON CONFLICT (id) DO NOTHING"),
            {"id": ACTOR_ID, "lab": LAB_ID, "n": "Synthetic HTTP Verifier",
             "e": "http-verifier@example.invalid", "p": "!synthetic-only", "r": "master_admin"},
        )
    with Session() as session:
        session.add(PatientBloodSampleModel(
            id=SAMPLE_ID, lab_id=LAB_ID, patient_id=PATIENT_ID, facility_id=FACILITY_ID,
            specimen_identifier="SPEC-TRANSITION-1", status="collected",
            collected_by=str(ACTOR_ID), collected_at=now,
            expires_at=now + timedelta(days=2),
        ))
        session.commit()


def _version(Session: Any) -> int:
    with Session() as session:
        return session.query(PatientBloodSampleModel.version).filter(
            PatientBloodSampleModel.id == SAMPLE_ID
        ).scalar()


def _status(Session: Any) -> str:
    with Session() as session:
        return session.query(PatientBloodSampleModel.status).filter(
            PatientBloodSampleModel.id == SAMPLE_ID
        ).scalar()


def _receipts(Session: Any, key: str) -> list[str]:
    with Session() as session:
        return [
            r.status for r in session.query(ClinicalCommandReceipt).filter(
                ClinicalCommandReceipt.lab_id == LAB_ID,
                ClinicalCommandReceipt.operation == OPERATION,
                ClinicalCommandReceipt.idempotency_key == key,
            ).all()
        ]


def _audit_watermark(Session: Any) -> int:
    with Session() as session:
        return session.query(func.coalesce(func.max(AuditLog.id), 0)).scalar() or 0


def _audit_since(Session: Any, mark: int) -> int:
    with Session() as session:
        return session.query(AuditLog).filter(
            AuditLog.id > mark, AuditLog.lab_id == LAB_ID,
            AuditLog.action == f"clinical.{OPERATION}",
        ).count()


def _cleanup(Session: Any) -> None:
    app.dependency_overrides.clear()
    with Session() as session:
        session.query(PatientBloodSampleModel).filter(
            PatientBloodSampleModel.lab_id == LAB_ID
        ).delete(synchronize_session=False)
        session.commit()
    Session.kw["bind"].dispose()


def test_a_valid_transition_succeeds_and_claims_one_receipt() -> None:
    Session = _session_factory()
    _prepare_sample(Session)
    mark = _audit_watermark(Session)
    try:
        with _client(Session) as client:
            response = client.post(
                f"/blood-bank/samples/{SAMPLE_ID}/transition",
                headers={"Idempotency-Key": "SAMPLE-TRANSITION-001", "If-Match": str(_version(Session))},
                json={"target": "identified"},
            )
        assert response.status_code == 200, response.text
        assert _status(Session) == "identified"
        assert _receipts(Session, "SAMPLE-TRANSITION-001") == ["completed"]
        assert _audit_since(Session, mark) == 1, (
            "the transition wrote no entry to the audit chain"
        )
    finally:
        _cleanup(Session)


def test_an_exact_replay_produces_no_second_effect_and_no_second_audit_event() -> None:
    Session = _session_factory()
    _prepare_sample(Session)
    key = "SAMPLE-TRANSITION-REPLAY"
    body = {"target": "identified"}
    mark = _audit_watermark(Session)
    try:
        with _client(Session) as client:
            first = client.post(f"/blood-bank/samples/{SAMPLE_ID}/transition",
                                headers={"Idempotency-Key": key, "If-Match": str(_version(Session))}, json=body)
        with _client(Session) as client:
            replay = client.post(f"/blood-bank/samples/{SAMPLE_ID}/transition",
                                 headers={"Idempotency-Key": key, "If-Match": str(_version(Session))}, json=body)
        assert first.status_code == 200, first.text
        assert replay.status_code != 200
        assert _status(Session) == "identified", "the replay advanced the sample again"
        assert _receipts(Session, key) == ["completed"], "the replay claimed a second receipt"
        assert _audit_since(Session, mark) == 1, "the replay wrote a second audit event"
    finally:
        _cleanup(Session)


def test_the_same_key_with_a_different_payload_is_refused() -> None:
    """The property the discarded key could not provide at all."""
    Session = _session_factory()
    _prepare_sample(Session)
    key = "SAMPLE-TRANSITION-COLLIDE"
    try:
        with _client(Session) as client:
            first = client.post(f"/blood-bank/samples/{SAMPLE_ID}/transition",
                                headers={"Idempotency-Key": key, "If-Match": str(_version(Session))}, json={"target": "identified"})
        with _client(Session) as client:
            collided = client.post(f"/blood-bank/samples/{SAMPLE_ID}/transition",
                                   headers={"Idempotency-Key": key, "If-Match": str(_version(Session))}, json={"target": "rejected"})
        assert first.status_code == 200, first.text
        assert collided.status_code != 200
        assert _status(Session) == "identified", (
            "a reused key carrying a different target changed the sample"
        )
    finally:
        _cleanup(Session)


def test_a_missing_idempotency_key_is_still_refused() -> None:
    Session = _session_factory()
    _prepare_sample(Session)
    try:
        with _client(Session) as client:
            response = client.post(f"/blood-bank/samples/{SAMPLE_ID}/transition",
                                   headers={"If-Match": str(_version(Session))},
                                   json={"target": "identified"})
        assert response.status_code == 400
        assert _status(Session) == "collected"
    finally:
        _cleanup(Session)
