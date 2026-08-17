from datetime import timedelta
from types import SimpleNamespace

import pytest

from app.domain.exceptions import ConflictError
from app.national.sync_models import NationalSyncOutboxModel
from app.national.api.routes.sync import _select_escalation_recipient
from app.services.sync_conflict_service import _assert_device_scope, create_device_session, ingest_operation
from app.tasks import sync_outbox
from tests.conftest import auth_headers


def test_sync_status_requires_device_session_header(client, make_lab, make_lab_user):
    lab = make_lab()
    user = make_lab_user(lab.id, role="admin")
    headers = auth_headers(user.id, lab.id, role="admin")
    missing = client.get("/national/sync/status", params={"device_id": "er-api-001"}, headers=headers)
    assert missing.status_code == 422


def test_device_session_requires_matching_secret_and_scope(db, make_lab, make_lab_user):
    lab = make_lab()
    user = make_lab_user(lab.id, role="doctor")
    session, token = create_device_session(
        db,
        current_user=user,
        device_id="er-device-001",
        hospital_id=101,
    )
    assert session.device_id == "er-device-001"
    assert token
    assert _assert_device_scope(db, user, "er-device-001", token, 101).id == session.id
    with pytest.raises(ConflictError, match="not active"):
        _assert_device_scope(db, user, "er-device-001", "wrong-token", 101)
    with pytest.raises(ConflictError, match="not active"):
        _assert_device_scope(db, SimpleNamespace(id=user.id, lab_id=lab.id + 999), "er-device-001", token, 101)


def test_escalation_recipient_is_selected_within_lab(db, make_lab, make_lab_user):
    lab = make_lab()
    current_user = make_lab_user(lab.id, role="doctor")
    supervisor = make_lab_user(lab.id, role="admin")
    other_lab = make_lab()
    foreign_admin = make_lab_user(other_lab.id, role="admin")
    assert _select_escalation_recipient(db, current_user) == str(supervisor.id)
    assert _select_escalation_recipient(db, current_user, supervisor.id) == str(supervisor.id)
    with pytest.raises(ConflictError, match="outside institutional scope"):
        _select_escalation_recipient(db, current_user, foreign_admin.id)


def test_expired_device_session_is_rejected(db, make_lab, make_lab_user):
    lab = make_lab()
    user = make_lab_user(lab.id, role="doctor")
    session, token = create_device_session(db, current_user=user, device_id="er-device-002", hospital_id=202)
    session.expires_at = sync_outbox._now() - timedelta(minutes=1)
    db.flush()
    with pytest.raises(ConflictError, match="not active"):
        _assert_device_scope(db, user, "er-device-002", token, 202)


def test_sync_operation_is_idempotent_under_repeated_delivery(db, make_lab, make_lab_user):
    lab = make_lab()
    user = make_lab_user(lab.id, role="doctor")
    _, token = create_device_session(db, current_user=user, device_id="er-idempotent-001", hospital_id=303)
    operation = {
        "operation_id": "op-idempotent-001",
        "idempotency_key": "idem-idempotent-001",
        "operation_type": "encounter.note",
        "entity_type": "Encounter",
        "entity_id": "encounter-local-001",
        "priority": "routine",
        "payload": {"hospital_id": 303, "note": "synthetic repeated delivery"},
    }
    first = ingest_operation(db, current_user=user, device_id="er-idempotent-001", device_token=token, operation=operation)
    second = ingest_operation(db, current_user=user, device_id="er-idempotent-001", device_token=token, operation=operation)
    assert first["status"] == "accepted"
    assert second["status"] == "duplicate"
    assert db.query(NationalSyncOutboxModel).count() == 1


def test_outbox_log_sink_is_rejected_in_production(monkeypatch):
    monkeypatch.setenv("IS_PRODUCTION", "true")
    monkeypatch.delenv("GULA_SYNC_OUTBOX_DELIVERY", raising=False)
    with pytest.raises(RuntimeError, match="delivery backend is not configured"):
        sync_outbox.deliver_outbox_event(SimpleNamespace(event_id="evt-prod", event_type="clinical.conflict.created"))


def test_outbox_failure_is_retried_with_backoff(db, monkeypatch):
    row = NationalSyncOutboxModel(
        event_id="evt-retry-001",
        event_type="clinical.conflict.created",
        aggregate_type="SyncConflict",
        aggregate_id="conflict-001",
        lab_id=1,
        payload={},
        status="pending",
        attempts=0,
    )
    db.add(row)
    db.flush()
    monkeypatch.setattr(sync_outbox, "SessionLocal", lambda: db)
    monkeypatch.setattr(sync_outbox, "deliver_outbox_event", lambda _: (_ for _ in ()).throw(RuntimeError("temporary delivery failure")))
    result = __import__("asyncio").run(sync_outbox.handle_sync_outbox({"limit": 10}))
    assert result["retried"] == 1
    refreshed = db.query(NationalSyncOutboxModel).filter_by(event_id="evt-retry-001").one()
    assert refreshed.status == "failed"
    assert refreshed.attempts == 1
    assert refreshed.next_attempt_at is not None
    assert refreshed.last_error == "temporary delivery failure"


def test_outbox_does_not_retry_before_backoff_deadline(db, monkeypatch):
    row = NationalSyncOutboxModel(
        event_id="evt-retry-future",
        event_type="clinical.conflict.created",
        aggregate_type="SyncConflict",
        aggregate_id="conflict-future",
        lab_id=1,
        payload={},
        status="failed",
        attempts=1,
        next_attempt_at=sync_outbox._now() + timedelta(hours=1),
    )
    db.add(row)
    db.flush()
    monkeypatch.setattr(sync_outbox, "SessionLocal", lambda: db)
    result = __import__("asyncio").run(sync_outbox.handle_sync_outbox({"limit": 10}))
    assert result["selected"] == 0
    refreshed = db.query(NationalSyncOutboxModel).filter_by(event_id="evt-retry-future").one()
    assert refreshed.status == "failed"


def test_outbox_dead_letters_after_max_attempts(db, monkeypatch):
    row = NationalSyncOutboxModel(
        event_id="evt-retry-002",
        event_type="clinical.conflict.created",
        aggregate_type="SyncConflict",
        aggregate_id="conflict-002",
        lab_id=1,
        payload={},
        status="failed",
        attempts=sync_outbox.MAX_ATTEMPTS - 1,
    )
    db.add(row)
    db.flush()
    monkeypatch.setattr(sync_outbox, "SessionLocal", lambda: db)
    monkeypatch.setattr(sync_outbox, "deliver_outbox_event", lambda _: (_ for _ in ()).throw(RuntimeError("permanent delivery failure")))
    result = __import__("asyncio").run(sync_outbox.handle_sync_outbox({"limit": 10}))
    assert result["dead_lettered"] == 1
    refreshed = db.query(NationalSyncOutboxModel).filter_by(event_id="evt-retry-002").one()
    assert refreshed.status == "dead_letter"
    assert refreshed.attempts == sync_outbox.MAX_ATTEMPTS
