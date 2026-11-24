"""Event catalogue contract for every shared synthetic ``EventType``.

The catalogue maps each event to its aggregate type and required payload keys.
It is a validation-only contract: no broker, outbox or publisher is created.
Event names and the event envelope are imported from ``app.health_core.common``
and never redefined.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.health_core.common import (
    EVENT_SCHEMA_VERSION,
    LEGACY_DIAGNOSIS_RESOLVE_ACTION,
    LEGACY_ENCOUNTER_START_STATUS,
    LEGACY_EVENT_TYPE_MAP,
    LEGACY_TRANSITION_KEY,
    AggregateType,
    DomainEvent,
    EventType,
    canonical_event_type,
    is_synthetic_id,
)

__all__ = [
    "EVENT_CATALOGUE",
    "EVENT_SCHEMA_VERSION",
    "LEGACY_DIAGNOSIS_RESOLVE_ACTION",
    "LEGACY_ENCOUNTER_START_STATUS",
    "LEGACY_EVENT_TYPE_MAP",
    "LEGACY_TRANSITION_KEY",
    "EventContractViolation",
    "EventDefinition",
    "canonical_event_type",
    "validate_domain_event",
]


@dataclass(frozen=True, slots=True)
class EventDefinition:
    """Required shape of a single synthetic domain event."""

    event_type: EventType
    aggregate_type: AggregateType
    required_payload_keys: frozenset[str]
    description: str


EVENT_CATALOGUE: dict[EventType, EventDefinition] = {
    EventType.PATIENT_REGISTERED: EventDefinition(
        EventType.PATIENT_REGISTERED,
        AggregateType.PATIENT,
        frozenset({"patient_ref", "tenant_id"}),
        "A synthetic patient was registered in the in-memory registry.",
    ),
    EventType.PRACTITIONER_REGISTERED: EventDefinition(
        EventType.PRACTITIONER_REGISTERED,
        AggregateType.PRACTITIONER,
        frozenset({"practitioner_ref", "tenant_id"}),
        "A synthetic practitioner was registered.",
    ),
    EventType.FACILITY_REGISTERED: EventDefinition(
        EventType.FACILITY_REGISTERED,
        AggregateType.FACILITY,
        frozenset({"facility_ref", "tenant_id"}),
        "A synthetic facility was registered.",
    ),
    EventType.ORGANIZATION_REGISTERED: EventDefinition(
        EventType.ORGANIZATION_REGISTERED,
        AggregateType.ORGANIZATION,
        frozenset({"organization_ref", "tenant_id"}),
        "A synthetic organisation was registered. emitter handoff tracked in WS_B report.",
    ),
    EventType.PRACTITIONER_DEACTIVATED: EventDefinition(
        EventType.PRACTITIONER_DEACTIVATED,
        AggregateType.PRACTITIONER,
        frozenset({"practitioner_ref", "tenant_id"}),
        "A synthetic practitioner was deactivated. emitter handoff tracked in WS_B report.",
    ),
    EventType.ENCOUNTER_CREATED: EventDefinition(
        EventType.ENCOUNTER_CREATED,
        AggregateType.ENCOUNTER,
        frozenset({"encounter_ref", "patient_ref", "tenant_id"}),
        "A synthetic encounter was created in the planned state (legacy create event).",
    ),
    EventType.ENCOUNTER_STARTED: EventDefinition(
        EventType.ENCOUNTER_STARTED,
        AggregateType.ENCOUNTER,
        frozenset({"encounter_ref", "tenant_id", "patient_ref", "from_status", "to_status"}),
        "A planned synthetic encounter started (explicit lifecycle event).",
    ),
    EventType.ENCOUNTER_ADMITTED: EventDefinition(
        EventType.ENCOUNTER_ADMITTED,
        AggregateType.ENCOUNTER,
        frozenset({"encounter_ref", "facility_ref"}),
        "A synthetic encounter was admitted to a facility.",
    ),
    EventType.ENCOUNTER_TRANSFERRED: EventDefinition(
        EventType.ENCOUNTER_TRANSFERRED,
        AggregateType.ENCOUNTER,
        frozenset({"encounter_ref", "from_facility_ref", "to_facility_ref"}),
        "A synthetic encounter was transferred between facilities.",
    ),
    EventType.ENCOUNTER_DISCHARGED: EventDefinition(
        EventType.ENCOUNTER_DISCHARGED,
        AggregateType.ENCOUNTER,
        frozenset({"encounter_ref", "disposition"}),
        "A synthetic encounter was discharged.",
    ),
    EventType.ENCOUNTER_CANCELLED: EventDefinition(
        EventType.ENCOUNTER_CANCELLED,
        AggregateType.ENCOUNTER,
        frozenset({"encounter_ref", "reason"}),
        "A synthetic encounter was cancelled.",
    ),
    EventType.DIAGNOSIS_RECORDED: EventDefinition(
        EventType.DIAGNOSIS_RECORDED,
        AggregateType.DIAGNOSIS,
        frozenset({"diagnosis_ref", "encounter_ref"}),
        "A synthetic diagnosis was recorded against an encounter (legacy record event).",
    ),
    EventType.DIAGNOSIS_RESOLVED: EventDefinition(
        EventType.DIAGNOSIS_RESOLVED,
        AggregateType.DIAGNOSIS,
        frozenset({"diagnosis_ref", "encounter_ref", "patient_ref", "status"}),
        "An active synthetic diagnosis was resolved (explicit lifecycle event).",
    ),
    EventType.OBSERVATION_RECORDED: EventDefinition(
        EventType.OBSERVATION_RECORDED,
        AggregateType.OBSERVATION,
        frozenset({"observation_ref", "patient_ref"}),
        "A synthetic observation was recorded for a patient.",
    ),
    EventType.NOTE_ADDED: EventDefinition(
        EventType.NOTE_ADDED,
        AggregateType.ENCOUNTER,
        frozenset({"note_ref", "medical_record_ref"}),
        "A synthetic note was added to an encounter's medical record.",
    ),
    EventType.MEDICAL_RECORD_OPENED: EventDefinition(
        EventType.MEDICAL_RECORD_OPENED,
        AggregateType.MEDICAL_RECORD,
        frozenset({"medical_record_ref", "patient_ref"}),
        "A synthetic medical record was opened.",
    ),
    EventType.LAB_ORDER_PLACED: EventDefinition(
        EventType.LAB_ORDER_PLACED,
        AggregateType.LAB_ORDER,
        frozenset({"order_ref", "patient_ref", "practitioner_ref"}),
        "A synthetic laboratory order was placed.",
    ),
    EventType.LAB_ORDER_CANCELLED: EventDefinition(
        EventType.LAB_ORDER_CANCELLED,
        AggregateType.LAB_ORDER,
        frozenset({"order_ref", "reason"}),
        "A synthetic laboratory order was cancelled.",
    ),
    EventType.SPECIMEN_REGISTERED: EventDefinition(
        EventType.SPECIMEN_REGISTERED,
        AggregateType.SPECIMEN,
        frozenset({"specimen_ref", "order_ref"}),
        "A synthetic specimen was registered.",
    ),
    EventType.SPECIMEN_COLLECTED: EventDefinition(
        EventType.SPECIMEN_COLLECTED,
        AggregateType.SPECIMEN,
        frozenset({"specimen_ref", "collected_at"}),
        "A synthetic specimen was collected.",
    ),
    EventType.SPECIMEN_RECEIVED: EventDefinition(
        EventType.SPECIMEN_RECEIVED,
        AggregateType.SPECIMEN,
        frozenset({"specimen_ref", "received_at"}),
        "A synthetic specimen was received by the laboratory.",
    ),
    EventType.SPECIMEN_REJECTED: EventDefinition(
        EventType.SPECIMEN_REJECTED,
        AggregateType.SPECIMEN,
        frozenset({"specimen_ref", "reason"}),
        "A synthetic specimen was rejected.",
    ),
    EventType.RESULT_RECORDED: EventDefinition(
        EventType.RESULT_RECORDED,
        AggregateType.LAB_RESULT,
        frozenset({"result_ref", "order_ref", "specimen_ref"}),
        "A synthetic laboratory result was recorded.",
    ),
    EventType.RESULT_VERIFIED: EventDefinition(
        EventType.RESULT_VERIFIED,
        AggregateType.VERIFICATION,
        frozenset({"result_ref", "verifier_ref"}),
        "A synthetic laboratory result was verified.",
    ),
    EventType.RESULT_CORRECTED: EventDefinition(
        EventType.RESULT_CORRECTED,
        AggregateType.LAB_RESULT,
        frozenset({"result_ref", "reason"}),
        "A synthetic laboratory result was corrected.",
    ),
    EventType.SPECIMEN_IN_TESTING: EventDefinition(
        EventType.SPECIMEN_IN_TESTING,
        AggregateType.SPECIMEN,
        frozenset({"specimen_ref", "from_status", "to_status"}),
        "A synthetic specimen entered the testing lifecycle.",
    ),
    EventType.SPECIMEN_FINAL: EventDefinition(
        EventType.SPECIMEN_FINAL,
        AggregateType.SPECIMEN,
        frozenset({"specimen_ref", "from_status", "to_status"}),
        "A synthetic specimen reached its final lifecycle state.",
    ),
    EventType.TEST_ENTERED: EventDefinition(
        EventType.TEST_ENTERED,
        AggregateType.SPECIMEN,
        frozenset({"execution_ref", "specimen_ref"}),
        "A synthetic test-execution session was entered.",
    ),
    EventType.TEST_COMPLETED: EventDefinition(
        EventType.TEST_COMPLETED,
        AggregateType.SPECIMEN,
        frozenset({"execution_ref", "specimen_ref"}),
        "A synthetic test-execution session was completed.",
    ),
    EventType.VERIFICATION_PENDING: EventDefinition(
        EventType.VERIFICATION_PENDING,
        AggregateType.VERIFICATION,
        frozenset({"result_ref", "verifier_ref"}),
        "A synthetic verification was queued for a reviewer.",
    ),
    EventType.RESULT_VERIFICATION_REJECTED: EventDefinition(
        EventType.RESULT_VERIFICATION_REJECTED,
        AggregateType.VERIFICATION,
        frozenset({"result_ref", "verifier_ref"}),
        "A synthetic result verification was rejected by its reviewer.",
    ),
}


class EventContractViolation(ValueError):
    """Raised when a synthetic event does not match its catalogue definition."""


def validate_domain_event(event: DomainEvent) -> None:
    """Validate an event against the catalogue; fail closed on any deviation."""
    try:
        event_type = EventType(event.event_type)
    except ValueError as exc:
        raise EventContractViolation(f"unregistered event type: {event.event_type!r}") from exc

    definition = EVENT_CATALOGUE.get(event_type)
    if definition is None:
        raise EventContractViolation(f"event type has no catalogue definition: {event_type.value}")

    if event.aggregate_type != definition.aggregate_type.value:
        raise EventContractViolation(
            f"{event_type.value} requires aggregate "
            f"{definition.aggregate_type.value!r}, got {event.aggregate_type!r}"
        )
    missing = definition.required_payload_keys.difference(event.payload)
    if missing:
        raise EventContractViolation(
            f"{event_type.value} missing payload keys: {sorted(missing)}"
        )
    for label, value in (
        ("event_id", event.event_id),
        ("aggregate_id", event.aggregate_id),
        ("tenant_id", event.tenant_id),
    ):
        if not is_synthetic_id(value):
            raise EventContractViolation(f"{label} must be a SYN- prefixed synthetic reference")
