"""Contract tests: event catalogue completeness and payload validation."""

from __future__ import annotations

import pytest
from app.health_core.common import (
    AggregateType,
    DomainEvent,
    EventType,
    new_event,
    new_synthetic_id,
)
from app.health_core.contracts.events import (
    EVENT_CATALOGUE,
    EventContractViolation,
    validate_domain_event,
)


def _sample_event(event_type: EventType) -> DomainEvent:
    definition = EVENT_CATALOGUE[event_type]
    payload: dict[str, object] = {
        key: new_synthetic_id("PLD") for key in definition.required_payload_keys
    }
    return new_event(
        event_type=event_type.value,
        aggregate_type=definition.aggregate_type.value,
        aggregate_id=new_synthetic_id("AGG"),
        tenant_id=new_synthetic_id("LAB"),
        payload=payload,
    )


def test_every_event_type_has_a_catalogue_definition() -> None:
    assert set(EVENT_CATALOGUE) == set(EventType)


def test_catalogue_definitions_use_known_aggregates() -> None:
    for definition in EVENT_CATALOGUE.values():
        assert isinstance(definition.aggregate_type, AggregateType)
        assert definition.required_payload_keys
        assert definition.description


@pytest.mark.parametrize("event_type", list(EventType))
def test_sample_event_validates_for_every_event_type(event_type: EventType) -> None:
    event = _sample_event(event_type)
    validate_domain_event(event)


def test_missing_payload_key_is_rejected() -> None:
    event = _sample_event(EventType.RESULT_VERIFIED)
    event.payload.pop("verifier_ref")
    with pytest.raises(EventContractViolation, match="missing payload keys"):
        validate_domain_event(event)


def test_wrong_aggregate_type_is_rejected() -> None:
    event = _sample_event(EventType.ENCOUNTER_CREATED)
    wrong = DomainEvent(
        event_id=event.event_id,
        event_type=event.event_type,
        aggregate_type=AggregateType.SPECIMEN.value,
        aggregate_id=event.aggregate_id,
        tenant_id=event.tenant_id,
        occurred_at=event.occurred_at,
        payload=event.payload,
    )
    with pytest.raises(EventContractViolation, match="requires aggregate"):
        validate_domain_event(wrong)


def test_unregistered_event_type_is_rejected() -> None:
    event = _sample_event(EventType.PATIENT_REGISTERED)
    unregistered = DomainEvent(
        event_id=event.event_id,
        event_type="unknown.event",
        aggregate_type=event.aggregate_type,
        aggregate_id=event.aggregate_id,
        tenant_id=event.tenant_id,
        occurred_at=event.occurred_at,
        payload=event.payload,
    )
    with pytest.raises(EventContractViolation, match="unregistered event type"):
        validate_domain_event(unregistered)


def test_non_synthetic_aggregate_id_is_rejected() -> None:
    event = _sample_event(EventType.PATIENT_REGISTERED)
    bad = DomainEvent(
        event_id=event.event_id,
        event_type=event.event_type,
        aggregate_type=event.aggregate_type,
        aggregate_id="123456789012",
        tenant_id=event.tenant_id,
        occurred_at=event.occurred_at,
        payload=event.payload,
    )
    with pytest.raises(EventContractViolation, match="SYN- prefixed"):
        validate_domain_event(bad)


def test_event_dict_serialisation_is_stable() -> None:
    event = _sample_event(EventType.LAB_ORDER_PLACED)
    encoded = event.to_dict()
    assert encoded["event_type"] == EventType.LAB_ORDER_PLACED.value
    assert encoded["payload"] == event.payload
