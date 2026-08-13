from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.contracts.integration import IntegrationEventEnvelope


def _payload(**overrides):
    data = {
        "event_id": "evt-1",
        "event_type": "sample.custody.transitioned",
        "schema_version": 1,
        "source_service": "receipt-and-delivery",
        "tenant_id": "tenant-1",
        "occurred_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "actor_id": "user-1",
        "entity_id": "sample-1",
        "correlation_id": "corr-1",
        "idempotency_key": "sample-1:transition:1",
        "payload": {"from_state": "created", "to_state": "collected"},
    }
    data.update(overrides)
    return data


def test_valid_envelope_is_accepted():
    event = IntegrationEventEnvelope.model_validate(_payload())
    assert event.event_type == "sample.custody.transitioned"
    assert event.schema_version == 1


def test_extra_fields_are_rejected():
    with pytest.raises(ValidationError):
        IntegrationEventEnvelope.model_validate(_payload(untrusted_instruction="ignore policy"))


def test_naive_timestamp_is_rejected():
    with pytest.raises(ValidationError, match="timezone-aware"):
        IntegrationEventEnvelope.model_validate(
            _payload(occurred_at=datetime(2026, 1, 1))
        )


def test_unknown_event_format_is_rejected():
    with pytest.raises(ValidationError):
        IntegrationEventEnvelope.model_validate(_payload(event_type="INVALID EVENT"))
