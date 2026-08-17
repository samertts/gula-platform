from datetime import UTC, datetime, timedelta

from app.models.outbox import OutboxEvent
from app.services.outbox_service import outbox_metrics, replay_outbox_event


def test_outbox_metrics_are_non_pii_and_include_backlog_age(db):
    now = datetime.now(UTC)
    db.add(OutboxEvent(event_type="ehr.immunization.completed", payload="{}", status="pending", attempts=1, created_at=now - timedelta(minutes=4), next_attempt_at=now))
    db.add(OutboxEvent(event_type="ehr.immunization.completed", payload="{}", status="failed", attempts=5, dead_letter_reason="synthetic failure", created_at=now - timedelta(minutes=8)))
    db.flush()
    metrics = outbox_metrics(db, event_type_prefix="ehr.")
    assert metrics["pending"] == 1
    assert metrics["dead_letter"] == 1
    assert metrics["oldest_pending_age_seconds"] >= 240
    assert "payload" not in metrics


def test_replay_resets_attempts_without_changing_payload(db):
    event = OutboxEvent(event_type="ehr.immunization.completed", payload='{"synthetic":true}', status="failed", attempts=5, dead_letter_reason="synthetic failure")
    db.add(event)
    db.flush()
    original_payload = event.payload
    replayed = replay_outbox_event(db, event.id, "operator-synthetic")
    assert replayed.status == "pending"
    assert replayed.attempts == 0
    assert replayed.dead_letter_reason is None
    assert replayed.payload == original_payload
    assert replayed.replayed_by == "operator-synthetic"


def test_completed_event_cannot_be_replayed(db):
    event = OutboxEvent(event_type="ehr.immunization.completed", payload="{}", status="done", attempts=1)
    db.add(event)
    db.flush()
    try:
        replay_outbox_event(db, event.id, "operator-synthetic")
    except ValueError as exc:
        assert "Completed" in str(exc)
    else:
        raise AssertionError("completed outbox event must not be replayable")
