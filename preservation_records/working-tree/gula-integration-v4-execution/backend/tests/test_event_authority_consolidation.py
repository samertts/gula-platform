"""C09 consolidation evidence: one authoritative event fabric + adapters."""
from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

import app.models.integration_inbox  # noqa: F401 - register inbox table
from app._compat import UTC as GULA_UTC
from app.contracts.integration import IntegrationEventEnvelope
from app.core.events import EventBus
from app.core.sync_engine import SyncEvent
from app.database import Base
from app.eventing.adapters import (
    from_health_domain_event,
    from_kernel_event,
    from_offline_operation,
    from_sync_engine_event,
)
from app.eventing.authority import CanonicalEventEnvelope, NationalEventAuthority
from app.health_core.common.events import new_event
from app.kernel.event_bus.events import Event as KernelEvent
from app.models.outbox import OutboxEvent
from app.services.offline_sync_service import SyncOperation
from app.services.outbox_service import OutboxWorker, emit_to_outbox


@pytest.fixture()
def db():
    import app.models.lab  # noqa: F401
    import app.models.lab_user  # noqa: F401
    import app.models.outbox  # noqa: F401
    from app.services.mpi.models import Citizen, IdentityClaim  # noqa: F401

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


def canonical(**overrides: Any) -> CanonicalEventEnvelope:
    values: dict[str, Any] = {
        "event_id": "evt-contract-0001",
        "event_type": "order.created",
        "schema_version": 1,
        "source_service": "contract-test",
        "tenant_id": "lab-1",
        "occurred_at": datetime.now(GULA_UTC),
        "actor_id": "user-1",
        "entity_id": "order-1",
        "correlation_id": "corr-1",
        "idempotency_key": "idem-1",
        "payload": {"order_id": 1},
        "aggregate_type": "order",
        "aggregate_id": "order-1",
        "sequence": 1,
    }
    values.update(overrides)
    return CanonicalEventEnvelope.model_validate(values)


def test_legacy_emit_and_drain_are_adapters_over_the_authority(db, monkeypatch):
    emit_to_outbox(db, "order.created", {"order_id": 7}, "order", 7)
    db.commit()

    row = db.query(OutboxEvent).one()
    assert row.event_id.startswith("legacy-")
    assert row.tenant_id == "system"
    assert row.correlation_id.startswith("legacy-")
    assert row.source_service == "legacy-outbox"

    bus = EventBus()
    received: list[dict[str, Any]] = []
    bus.subscribe("order.created", received.append)
    monkeypatch.setattr("app.services.outbox_service.events", bus)

    assert OutboxWorker.run_once(db) == {"processed": 1, "failed": 0, "skipped": 0}
    db.refresh(row)
    assert row.status == "done"
    assert received == [{"order_id": 7}]


def test_legacy_zero_handler_acknowledgement_is_preserved(db, monkeypatch):
    emit_to_outbox(db, "unhandled.event", {})
    db.commit()
    monkeypatch.setattr("app.services.outbox_service.events", EventBus())

    summary = OutboxWorker.run_once(db)
    assert summary == {"processed": 1, "failed": 0, "skipped": 0}
    assert db.query(OutboxEvent).one().status == "done"


def test_canonical_drain_does_not_acknowledge_an_event_without_a_handler(db, monkeypatch):
    NationalEventAuthority.publish(db, canonical(event_type="delivery.strict"))
    db.commit()

    bus = EventBus()
    monkeypatch.setattr("app.eventing.authority.default_bus", bus)

    first = NationalEventAuthority.drain(db, require_handler=True)
    assert first == {"processed": 0, "failed": 0, "skipped": 1}
    row = db.query(OutboxEvent).one()
    assert row.status == "failed"
    assert "no registered handler" in row.last_error

    delivered: list[dict[str, Any]] = []
    bus.subscribe("delivery.strict", delivered.append)
    second = NationalEventAuthority.drain(db, require_handler=True)
    assert second == {"processed": 1, "failed": 0, "skipped": 0}
    db.refresh(row)
    assert row.status == "done"
    assert row.attempts == 2
    assert delivered == [{"order_id": 1}]


def test_canonical_publish_is_atomic_and_idempotent(db):
    envelope = canonical()
    NationalEventAuthority.publish(db, envelope)
    db.rollback()
    assert db.query(OutboxEvent).count() == 0

    NationalEventAuthority.publish(db, envelope)
    db.commit()
    with pytest.raises(IntegrityError):
        NationalEventAuthority.publish(db, envelope)
        db.commit()
    db.rollback()
    assert db.query(OutboxEvent).count() == 1


def test_all_historical_stack_shapes_translate_to_one_canonical_envelope():
    kernel = KernelEvent(
        name="kernel.order.created",
        data={"order_id": 1},
        version=3,
        id="kernel-evt-1",
        timestamp=1_700_000_000.0,
        correlation_id="kernel-corr",
        tenant_id="lab-1",
    )
    health = new_event(
        event_type="encounter.started",
        aggregate_type="encounter",
        aggregate_id="enc-1",
        tenant_id="lab-1",
        payload={"encounter_id": "enc-1"},
    )
    sync = SyncEvent("patient", "pat-1", "UPDATE", {"name": "A"})
    offline = SyncOperation(
        operation_id="offline-op-1",
        entity_type="observation",
        entity_id="obs-1",
        operation="CREATE",
        data={"value": 1},
        vector_clock={"device-a": 2},
        device_id="device-a",
        user_id="user-9",
        timestamp=1_700_000_100.0,
    )

    translated = [
        from_kernel_event(kernel),
        from_health_domain_event(health),
        from_sync_engine_event(sync, tenant_id="lab-1"),
        from_offline_operation(offline, tenant_id="lab-1"),
    ]

    for event in translated:
        assert isinstance(event, CanonicalEventEnvelope)
        assert len(event.event_id) <= 120
        assert event.occurred_at.tzinfo is not None
        assert event.tenant_id

    assert translated[0].event_type == "kernel.order.created"
    assert translated[0].sequence == 3
    assert translated[1].aggregate_id == "enc-1"
    assert translated[1].payload["source_schema_version"] == "1.1.0"
    assert translated[2].event_type == "sync.patient.update"
    assert translated[3].event_type == "offline.observation.create"
    assert translated[3].sequence == 2

    # Stable source identifiers produce stable canonical ids for replay safety.
    assert from_kernel_event(kernel).event_id == translated[0].event_id


def test_inbound_events_share_the_authoritative_inbox(db):
    payload = {
        "event_id": "inbound-1",
        "event_type": "frontend.sync.requested",
        "schema_version": 1,
        "source_service": "frontend-v3",
        "tenant_id": "lab-1",
        "occurred_at": datetime.now(GULA_UTC),
        "actor_id": "user-1",
        "entity_id": "action-1",
        "correlation_id": "corr-1",
        "idempotency_key": "idem-inbound-1",
        "payload": {"action_id": "a1", "action_type": "sync", "payload": {}},
    }
    envelope = IntegrationEventEnvelope.model_validate(payload)
    first = NationalEventAuthority.stage_inbound(db, envelope)
    second = NationalEventAuthority.stage_inbound(db, dict(payload))
    db.commit()

    assert first.status == "staged"
    assert second.status == "duplicate"
    assert first.inbox_id == second.inbox_id
