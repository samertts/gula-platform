"""Shared, dependency-free primitives for Health Core development."""

from app.health_core.common.errors import (
    DuplicateEntityError,
    ForbiddenSyntheticOperationError,
    HealthCoreError,
    InvalidStateTransitionError,
    InvalidSyntheticReferenceError,
    TenantMismatchError,
    UnknownPatientError,
)
from app.health_core.common.event_types import (
    LEGACY_DIAGNOSIS_RESOLVE_ACTION,
    LEGACY_ENCOUNTER_START_STATUS,
    LEGACY_EVENT_TYPE_MAP,
    LEGACY_TRANSITION_KEY,
    AggregateType,
    EventType,
    canonical_event_type,
)
from app.health_core.common.events import (
    EVENT_SCHEMA_VERSION,
    DomainEvent,
    new_event,
)
from app.health_core.common.ids import is_synthetic_id, new_synthetic_id, reject_national_identifier

__all__ = [
    "EVENT_SCHEMA_VERSION",
    "LEGACY_DIAGNOSIS_RESOLVE_ACTION",
    "LEGACY_ENCOUNTER_START_STATUS",
    "LEGACY_EVENT_TYPE_MAP",
    "LEGACY_TRANSITION_KEY",
    "AggregateType",
    "DomainEvent",
    "DuplicateEntityError",
    "EventType",
    "ForbiddenSyntheticOperationError",
    "HealthCoreError",
    "InvalidStateTransitionError",
    "InvalidSyntheticReferenceError",
    "TenantMismatchError",
    "UnknownPatientError",
    "canonical_event_type",
    "is_synthetic_id",
    "new_event",
    "new_synthetic_id",
    "reject_national_identifier",
]
