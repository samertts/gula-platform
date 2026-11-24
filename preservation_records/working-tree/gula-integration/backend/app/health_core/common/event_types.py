"""Canonical development event and aggregate vocabulary.

Shared by every workstream so events are consistent without cross-importing
workstream modules. Values are stable strings suitable for contract tests.
These are SYNTHETIC development events, never published to a real broker.

The vocabulary is additive. Event schema version ``1.1.0`` introduced four
explicit lifecycle values (WS-E finding F-01); the two previously overloaded
legacy values are retained unchanged for backward compatibility. See
:data:`LEGACY_EVENT_TYPE_MAP` and :func:`canonical_event_type`.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from types import MappingProxyType


class EventType(StrEnum):
    """Event types emitted by synthetic Health Core components."""

    PATIENT_REGISTERED = "patient.registered"
    PRACTITIONER_REGISTERED = "practitioner.registered"
    # Explicit lifecycle semantics added in event schema 1.1.0. No synthetic
    # deactivation emitter exists yet; the value is reserved so no workstream
    # invents a local string for it.
    PRACTITIONER_DEACTIVATED = "practitioner.deactivated"
    FACILITY_REGISTERED = "facility.registered"
    # Explicit lifecycle semantics added in event schema 1.1.0. No synthetic
    # organisation emitter exists yet (see the WS_B report handoff request).
    ORGANIZATION_REGISTERED = "organization.registered"
    # LEGACY (pre-1.1.0, ambiguous): still emitted for the genuine planned
    # creation of an encounter, but MUST NOT be used for the transition into
    # IN_PROGRESS any more. Use ENCOUNTER_STARTED for that lifecycle change.
    ENCOUNTER_CREATED = "encounter.created"
    ENCOUNTER_STARTED = "encounter.started"
    ENCOUNTER_ADMITTED = "encounter.admitted"
    ENCOUNTER_TRANSFERRED = "encounter.transferred"
    ENCOUNTER_DISCHARGED = "encounter.discharged"
    ENCOUNTER_CANCELLED = "encounter.cancelled"
    # LEGACY (pre-1.1.0, ambiguous): still emitted when a diagnosis is first
    # recorded, but MUST NOT be used for resolution any more. Use
    # DIAGNOSIS_RESOLVED for the active -> resolved transition.
    DIAGNOSIS_RECORDED = "diagnosis.recorded"
    DIAGNOSIS_RESOLVED = "diagnosis.resolved"
    OBSERVATION_RECORDED = "observation.recorded"
    NOTE_ADDED = "note.added"
    MEDICAL_RECORD_OPENED = "medical_record.opened"
    LAB_ORDER_PLACED = "lab_order.placed"
    LAB_ORDER_CANCELLED = "lab_order.cancelled"
    SPECIMEN_REGISTERED = "specimen.registered"
    SPECIMEN_COLLECTED = "specimen.collected"
    SPECIMEN_RECEIVED = "specimen.received"
    SPECIMEN_REJECTED = "specimen.rejected"
    RESULT_RECORDED = "result.recorded"
    RESULT_VERIFIED = "result.verified"
    RESULT_CORRECTED = "result.corrected"

    # Synthetic laboratory workflow transitions. These were previously
    # local string constants in the lab workstream; they are promoted here so
    # that the shared vocabulary is the single source of truth for every event
    # emitted by any workstream (cross-module conformance requirement).
    SPECIMEN_IN_TESTING = "specimen.in_testing"
    SPECIMEN_FINAL = "specimen.final"
    TEST_ENTERED = "test.entered"
    TEST_COMPLETED = "test.completed"
    VERIFICATION_PENDING = "verification.pending"
    RESULT_VERIFICATION_REJECTED = "result.verification_rejected"


class AggregateType(StrEnum):
    """Aggregate names used as the ``aggregate_type`` of a domain event."""

    PATIENT = "patient"
    PRACTITIONER = "practitioner"
    ORGANIZATION = "organization"
    FACILITY = "facility"
    ENCOUNTER = "encounter"
    DIAGNOSIS = "diagnosis"
    OBSERVATION = "observation"
    MEDICAL_RECORD = "medical_record"
    LAB_ORDER = "lab_order"
    SPECIMEN = "specimen"
    LAB_RESULT = "lab_result"
    VERIFICATION = "verification"


# --- Backward-compatibility mapping (documented, not a data migration) -------
#
# The two legacy names below were overloaded: the same value denoted a genuine
# create/record AND a lifecycle transition, distinguishable only by payload.
# The mapping records the intended target of each overload. It is deliberately
# NOT a blind 1:1 rename: an unchanged ENCOUNTER_CREATED event is still a real
# creation, and an unchanged DIAGNOSIS_RECORDED event is still a real recording.
# Consumers must call canonical_event_type(event.event_type,
# payload=event.payload) to disambiguate before replaying or projecting events.
LEGACY_EVENT_TYPE_MAP: Mapping[EventType, tuple[EventType, ...]] = MappingProxyType(
    {
        EventType.ENCOUNTER_CREATED: (EventType.ENCOUNTER_STARTED,),
        EventType.DIAGNOSIS_RECORDED: (EventType.DIAGNOSIS_RESOLVED,),
    }
)

LEGACY_TRANSITION_KEY = "transition"
LEGACY_ENCOUNTER_START_STATUS = "in_progress"
LEGACY_DIAGNOSIS_RESOLVE_ACTION = "resolve"


def canonical_event_type(
    event_type: str | EventType,
    *,
    payload: Mapping[str, object] | None = None,
) -> EventType:
    """Return the unambiguous event type for a legacy or current event.

    Current event types are returned unchanged. A legacy overloaded type is
    remapped only when its historical ``transition`` payload marker is present;
    without that marker it keeps its genuine create/record meaning. Unknown
    values fail closed with :class:`ValueError`.
    """
    resolved = EventType(event_type)
    if resolved not in LEGACY_EVENT_TYPE_MAP:
        return resolved

    marker = None if payload is None else payload.get(LEGACY_TRANSITION_KEY)
    if resolved is EventType.ENCOUNTER_CREATED and marker:
        to_status = None if payload is None else payload.get("to_status")
        if to_status == LEGACY_ENCOUNTER_START_STATUS:
            return EventType.ENCOUNTER_STARTED
    if resolved is EventType.DIAGNOSIS_RECORDED and marker == LEGACY_DIAGNOSIS_RESOLVE_ACTION:
        return EventType.DIAGNOSIS_RESOLVED
    return resolved
