"""NR-027 — what the Blood Bank actually records, proven rather than asserted.

BATCH-2.5 recorded NR-027 as "no Blood Bank mutation writes an audit log entry",
on the evidence that ``blood_bank/application/service.py`` contains no reference
to audit. That evidence was real but the conclusion did not follow: the audit
write lives in the route layer, in ``ClinicalCommandGuard.complete()``, which
calls ``log_action`` into the SHA-256 hash chain with the actor, tenant,
state transition, versions and idempotency key — inside the caller's
transaction.

These tests establish the true state:

  * a guarded mutation produces exactly one clinical effect AND exactly one
    hash-chained audit row;
  * an idempotent replay produces neither a second effect nor a second audit
    row;
  * a failure rolls back the effect and the audit row together;
  * the audit row carries the state transition, not merely the fact of a write.

The remaining gap is narrower than NR-027 first claimed and is covered by
``test_unguarded_routes_are_the_known_audit_gap``.
"""
from __future__ import annotations

import os
from typing import Any

import pytest
from app.blood_bank.infrastructure.models import BloodReservationModel
from app.main import app
from app.models.audit_log import AuditLog
from sqlalchemy import func
from test_http_idempotency_postgres import (  # type: ignore[import-not-found]
    ACTOR_ID,
    LAB_ID,
    _claims,
    _client,
    _counts,
    _payload,
    _prepare,
    _session_factory,
)

POSTGRES_URL = os.getenv("BLOOD_BANK_POSTGRES_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL, reason="BLOOD_BANK_POSTGRES_URL is not configured"
)

OPERATION = "blood.reservation.create"
AUDIT_ACTION = f"clinical.{OPERATION}"


def _audit_watermark(Session: Any) -> int:
    """Highest audit id before the command under test.

    audit_logs is append-only — a database trigger rejects DELETE and UPDATE —
    so these tests measure the rows a command *adds* rather than cleaning up
    after themselves. Deleting from the chain would break it, which is exactly
    what the trigger exists to prevent.
    """
    with Session() as session:
        return session.query(func.coalesce(func.max(AuditLog.id), 0)).scalar() or 0


def _audit_rows_since(Session: Any, watermark: int) -> list[AuditLog]:
    with Session() as session:
        return (
            session.query(AuditLog)
            .filter(
                AuditLog.id > watermark,
                AuditLog.lab_id == LAB_ID,
                AuditLog.action == AUDIT_ACTION,
            )
            .order_by(AuditLog.id.asc())
            .all()
        )


def _cleanup(Session: Any) -> None:
    """Remove only the clinical effect. The audit chain is never touched."""
    app.dependency_overrides.clear()
    with Session() as session:
        session.query(BloodReservationModel).filter(
            BloodReservationModel.lab_id == LAB_ID
        ).delete(synchronize_session=False)
        session.commit()
    Session.kw["bind"].dispose()


def test_one_mutation_writes_one_effect_and_one_audit_event() -> None:
    Session = _session_factory()
    _prepare(Session)
    watermark = _audit_watermark(Session)
    try:
        with _client(Session) as client:
            response = client.post(
                "/blood-bank/reservations",
                headers={"Idempotency-Key": "AUDIT-ONE-EFFECT-001"},
                json=_payload(),
            )
        assert response.status_code == 201, response.text
        assert _counts(Session)["reservations"] == 1

        rows = _audit_rows_since(Session, watermark)
        assert len(rows) == 1, f"expected exactly one audit row, found {len(rows)}"

        entry = rows[0]
        assert entry.lab_id == LAB_ID           # tenant
        assert entry.user_id == ACTOR_ID        # actor
        assert entry.chain_hash                 # chained, not a bare insert
        assert len(entry.chain_hash) == 64
        assert entry.details is not None
        for field in ("state_before", "state_after", "idempotency_key", "resource_id"):
            assert field in entry.details, f"audit detail is missing {field}"
    finally:
        _cleanup(Session)


def test_idempotent_replay_adds_no_second_audit_event() -> None:
    """Replay protection must cover the audit chain, not only the side effect."""
    Session = _session_factory()
    _prepare(Session)
    key = "AUDIT-REPLAY-001"
    watermark = _audit_watermark(Session)
    try:
        with _client(Session) as client:
            first = client.post(
                "/blood-bank/reservations", headers={"Idempotency-Key": key}, json=_payload()
            )
        with _client(Session) as client:
            replay = client.post(
                "/blood-bank/reservations", headers={"Idempotency-Key": key}, json=_payload()
            )
        assert first.status_code == 201, first.text
        assert replay.status_code != 201

        assert _counts(Session)["reservations"] == 1
        assert len(_claims(Session, OPERATION, key)) == 1
        assert len(_audit_rows_since(Session, watermark)) == 1, (
            "a replayed command wrote a second audit event; the chain would "
            "record a clinical action that never happened"
        )
    finally:
        _cleanup(Session)


def test_failure_rolls_back_the_effect_and_the_audit_event_together() -> None:
    """Audit and clinical effect share one transaction, so they fail together."""
    Session = _session_factory()
    _prepare(Session)
    watermark = _audit_watermark(Session)
    os.environ["GULA_TEST_FAILURE_STAGE"] = "after_audit_preparation"
    try:
        with _client(Session) as client:
            failed = client.post(
                "/blood-bank/reservations",
                headers={"Idempotency-Key": "AUDIT-ROLLBACK-001"},
                json=_payload(),
            )
        assert failed.status_code == 500
        assert _counts(Session)["reservations"] == 0, "clinical effect survived a failure"
        assert _audit_rows_since(Session, watermark) == [], (
            "audit event survived a rolled-back mutation"
        )
    finally:
        os.environ.pop("GULA_TEST_FAILURE_STAGE", None)
        _cleanup(Session)
