from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app._compat import UTC
from app.devices.models import DeviceOutboxMessage
from app.models.lab import Lab
from app.devices.outbox import enqueue_message, process_batch, summarize


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Lab.__table__.create(engine)
    DeviceOutboxMessage.__table__.create(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _enqueue(db, *, lab_id=1, key="device-event-001", payload=None):
    return enqueue_message(
        db,
        lab_id=lab_id,
        gateway_ref="synthetic-gateway-001",
        event_type="device.status_changed",
        idempotency_key=key,
        correlation_id=key,
        payload_safe=payload or {"status": "connected", "simulation_only": True},
    )


def test_idempotency_is_scoped_to_lab_and_reuses_same_envelope(db):
    first = _enqueue(db)
    same = _enqueue(db)
    other_lab = _enqueue(db, lab_id=2)
    db.commit()

    assert first.id == same.id
    assert other_lab.id != first.id
    assert db.query(DeviceOutboxMessage).count() == 2

    with pytest.raises(ValueError, match="different device envelope"):
        _enqueue(db, payload={"status": "error", "simulation_only": True})


def test_process_batch_delivers_synthetic_messages_and_reports_summary(db):
    _enqueue(db)
    db.commit()

    result = process_batch(db, 1, limit=10)
    message = db.query(DeviceOutboxMessage).one()

    assert result == {"processed": 1, "recovered": 0, "delivered": 1, "retried": 0, "dead_letter": 0, "simulation_only": True}
    assert message.status == "delivered"
    assert message.delivered_at is not None
    assert summarize(db, 1)["delivered_count"] == 1


def test_failed_dispatch_retries_with_backoff_then_moves_to_dead_letter(db):
    message = _enqueue(db)
    db.commit()
    now = datetime.now(UTC) + timedelta(seconds=1)

    def fail(_message):
        raise RuntimeError("synthetic gateway unavailable")

    result = process_batch(db, 1, now=now, dispatcher=fail)
    db.refresh(message)
    assert result["retried"] == 1
    assert message.status == "retry"
    assert message.attempts == 1
    assert message.next_attempt_at > message.created_at

    for _ in range(message.max_attempts - 1):
        due_at = message.next_attempt_at
        process_batch(db, 1, now=due_at, dispatcher=fail)
        db.refresh(message)

    assert message.status == "dead_letter"
    assert message.attempts == message.max_attempts
    assert summarize(db, 1)["dead_letter_count"] == 1


def test_stale_processing_message_is_recovered_before_delivery(db):
    message = _enqueue(db)
    message.status = "processing"
    message.locked_at = datetime.now(UTC) - timedelta(minutes=10)
    db.commit()

    result = process_batch(db, 1, now=datetime.now(UTC) + timedelta(seconds=1))
    db.refresh(message)

    assert result["recovered"] == 1
    assert result["delivered"] == 1
    assert message.status == "delivered"
    assert message.last_error is None


def test_oldest_age_only_counts_active_messages(db):
    message = _enqueue(db)
    message.created_at = datetime.now(UTC) - timedelta(minutes=7)
    db.commit()

    summary = summarize(db, 1, now=datetime.now(UTC))
    assert summary["oldest_age_seconds"] >= 420
    assert summary["pending_count"] == 1

    process_batch(db, 1)
    assert summarize(db, 1)["oldest_age_seconds"] == 0.0
