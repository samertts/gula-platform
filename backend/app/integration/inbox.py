from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.contracts.integration import IntegrationEventEnvelope
from app.models.integration_inbox import IntegrationInboxEvent


SUPPORTED_EVENT_TYPES = {
    "sample.custody.transitioned",
    "device.observation.pending",
}


@dataclass(frozen=True)
class InboxResult:
    status: str
    event_id: str
    idempotency_key: str
    inbox_id: int | None


def _validate_payload(envelope: IntegrationEventEnvelope) -> None:
    payload = envelope.payload
    if envelope.event_type == "sample.custody.transitioned":
        required = {"sample_id", "from_state", "to_state"}
    elif envelope.event_type == "device.observation.pending":
        required = {"sample_id", "observation_id", "status"}
        if payload.get("status") != "pending_review":
            raise ValueError("device observations must remain pending_review")
    elif envelope.event_type == "identity.subject.mapped":
        required = {"subject_id", "credential_id", "credential_version", "credential_state", "claims", "key_id"}
        if not isinstance(payload.get("claims"), dict):
            raise ValueError("identity claims must be an object")
    elif envelope.event_type == "workforce.attendance.recorded":
        required = {"event_id", "event_type"}
    elif envelope.event_type == "workforce.assignment.changed":
        required = {"assignment_id", "subject_id", "assignment_version", "change_type"}
    else:
        raise ValueError(f"unsupported integration event type: {envelope.event_type}")

    missing = sorted(field for field in required if not str(payload.get(field, "")).strip())
    if missing:
        raise ValueError(f"payload is missing required fields: {', '.join(missing)}")


def stage_event(db: Session, envelope: IntegrationEventEnvelope) -> InboxResult:
    """Persist a validated event without applying clinical side effects."""
    _validate_payload(envelope)

    by_event = (
        db.query(IntegrationInboxEvent)
        .filter(IntegrationInboxEvent.event_id == envelope.event_id)
        .first()
    )
    if by_event is not None:
        if by_event.idempotency_key != envelope.idempotency_key:
            raise ValueError("event_id already exists with a different idempotency_key")
        return InboxResult("duplicate", envelope.event_id, envelope.idempotency_key, by_event.id)

    by_key = (
        db.query(IntegrationInboxEvent)
        .filter(IntegrationInboxEvent.idempotency_key == envelope.idempotency_key)
        .first()
    )
    if by_key is not None:
        if by_key.event_id != envelope.event_id:
            raise ValueError("idempotency_key already belongs to a different event_id")
        return InboxResult("duplicate", envelope.event_id, envelope.idempotency_key, by_key.id)

    record = IntegrationInboxEvent(
        event_id=envelope.event_id,
        event_type=envelope.event_type,
        schema_version=envelope.schema_version,
        source_service=envelope.source_service,
        tenant_id=envelope.tenant_id,
        entity_id=envelope.entity_id,
        correlation_id=envelope.correlation_id,
        idempotency_key=envelope.idempotency_key,
        actor_id=envelope.actor_id,
        payload=json.dumps(envelope.payload, ensure_ascii=False, sort_keys=True, default=str),
        status="pending_review",
        received_at=envelope.occurred_at.astimezone(timezone.utc),
    )
    db.add(record)
    db.flush()
    return InboxResult("staged", envelope.event_id, envelope.idempotency_key, record.id)
