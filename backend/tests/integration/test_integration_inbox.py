from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.contracts.integration import IntegrationEventEnvelope
from app.database import Base
from app.integration.inbox import stage_event
from app.models.integration_inbox import IntegrationInboxEvent


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine, tables=[IntegrationInboxEvent.__table__])
    session = sessionmaker(bind=engine, autoflush=False)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def envelope(**overrides):
    data = {
        "event_id": "evt-1",
        "event_type": "device.observation.pending",
        "schema_version": 1,
        "source_service": "lablink-core",
        "tenant_id": "tenant-1",
        "occurred_at": datetime.now(timezone.utc),
        "actor_id": "device-1",
        "entity_id": "sample-1",
        "correlation_id": "corr-1",
        "idempotency_key": "idem-1",
        "payload": {
            "sample_id": "sample-1",
            "observation_id": "obs-1",
            "status": "pending_review",
        },
    }
    data.update(overrides)
    return IntegrationEventEnvelope.model_validate(data)


def test_stage_event_is_pending_review_and_not_approved(db):
    result = stage_event(db, envelope())
    db.commit()

    row = db.query(IntegrationInboxEvent).one()
    assert result.status == "staged"
    assert row.status == "pending_review"
    assert row.processed_at is None


def test_same_event_is_idempotent(db):
    first = stage_event(db, envelope())
    second = stage_event(db, envelope())
    assert first.status == "staged"
    assert second.status == "duplicate"
    assert db.query(IntegrationInboxEvent).count() == 1


def test_reusing_key_for_another_event_is_rejected(db):
    stage_event(db, envelope())
    with pytest.raises(ValueError, match="different event_id"):
        stage_event(db, envelope(event_id="evt-2"))


def test_device_observation_cannot_be_final(db):
    with pytest.raises(ValueError, match="pending_review"):
        stage_event(db, envelope(payload={
            "sample_id": "sample-1",
            "observation_id": "obs-1",
            "status": "final",
        }))


def test_workforce_attendance_event_is_staged_without_clinical_approval(db):
    result = stage_event(
        db,
        envelope(
            event_type="workforce.attendance.recorded",
            entity_id="attendance-1",
            payload={"event_id": "attendance-1", "event_type": "clock_in", "employee_id": "employee-1"},
        ),
    )

    row = db.query(IntegrationInboxEvent).one()
    assert result.status == "staged"
    assert row.status == "pending_review"
    assert row.processed_at is None


def test_workforce_assignment_requires_versioned_payload(db):
    with pytest.raises(ValueError, match="missing required fields"):
        stage_event(
            db,
            envelope(
                event_type="workforce.assignment.changed",
                payload={"subject_id": "subject-1"},
            ),
        )
