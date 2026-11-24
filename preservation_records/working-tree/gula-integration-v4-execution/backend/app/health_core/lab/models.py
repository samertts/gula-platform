"""Immutable domain entities for the synthetic laboratory workflow.

Every entity is a frozen dataclass held only in process memory. All patient
references are :class:`PatientRef` objects supplied by the identity port; no
entity stores a real-world identifier of any kind.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Final

from app.health_core.common import EventType
from app.health_core.common.ids import new_synthetic_id
from app.health_core.identity.port import PatientRef

# Aliases of the shared vocabulary: no workstream-local event strings.
SPECIMEN_IN_TESTING_EVENT: Final[str] = str(EventType.SPECIMEN_IN_TESTING)
SPECIMEN_FINAL_EVENT: Final[str] = str(EventType.SPECIMEN_FINAL)
TEST_ENTERED_EVENT: Final[str] = str(EventType.TEST_ENTERED)
TEST_COMPLETED_EVENT: Final[str] = str(EventType.TEST_COMPLETED)
VERIFICATION_PENDING_EVENT: Final[str] = str(EventType.VERIFICATION_PENDING)
RESULT_VERIFICATION_REJECTED_EVENT: Final[str] = str(EventType.RESULT_VERIFICATION_REJECTED)


class Priority(StrEnum):
    """Synthetic laboratory order priority."""

    ROUTINE = "routine"
    URGENT = "urgent"
    STAT = "stat"


class LabOrderStatus(StrEnum):
    """Lifecycle of a synthetic lab order."""

    PLACED = "placed"
    CANCELLED = "cancelled"


class SpecimenStatus(StrEnum):
    """Lifecycle of a synthetic specimen."""

    REGISTERED = "registered"
    COLLECTED = "collected"
    RECEIVED = "received"
    IN_TESTING = "in_testing"
    REJECTED = "rejected"
    FINAL = "final"


class TestExecutionStatus(StrEnum):
    """Lifecycle of a synthetic testing session (no real analyzer)."""

    ENTERED = "entered"
    COMPLETED = "completed"


class VerificationDecision(StrEnum):
    """Decision recorded by a synthetic reviewer."""

    VERIFIED = "verified"
    REJECTED = "rejected"


class VerificationStatus(StrEnum):
    """Lifecycle of a synthetic result verification."""

    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


LEGAL_SPECIMEN_TRANSITIONS: dict[SpecimenStatus, frozenset[SpecimenStatus]] = {
    SpecimenStatus.REGISTERED: frozenset({SpecimenStatus.COLLECTED}),
    SpecimenStatus.COLLECTED: frozenset({SpecimenStatus.RECEIVED}),
    SpecimenStatus.RECEIVED: frozenset({SpecimenStatus.IN_TESTING, SpecimenStatus.REJECTED}),
    SpecimenStatus.IN_TESTING: frozenset({SpecimenStatus.FINAL}),
    SpecimenStatus.REJECTED: frozenset({SpecimenStatus.FINAL}),
    SpecimenStatus.FINAL: frozenset(),
}

LEGAL_VERIFICATION_TRANSITIONS: dict[VerificationStatus, frozenset[VerificationStatus]] = {
    VerificationStatus.PENDING: frozenset(
        {VerificationStatus.VERIFIED, VerificationStatus.REJECTED}
    ),
    VerificationStatus.VERIFIED: frozenset({VerificationStatus.REJECTED}),
    VerificationStatus.REJECTED: frozenset(),
}


def new_synthetic_barcode() -> str:
    """Generate a fresh ``SYN-BAR-`` prefixed synthetic barcode."""
    return new_synthetic_id("BAR")


@dataclass(frozen=True, slots=True)
class LabOrder:
    """A synthetic laboratory order scoped to one synthetic tenant."""

    order_id: str
    idempotency_key: str
    patient: PatientRef
    tenant_id: str
    test_codes: tuple[str, ...]
    priority: Priority
    status: LabOrderStatus
    created_at: str
    cancelled_at: str | None = None
    cancellation_reason: str | None = None


@dataclass(frozen=True, slots=True)
class CustodyEntry:
    """One immutable chain-of-custody record with actor and timestamp."""

    entry_id: str
    specimen_id: str
    tenant_id: str
    from_status: SpecimenStatus | None
    to_status: SpecimenStatus
    actor_id: str
    occurred_at: str
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class Specimen:
    """A synthetic specimen registered against a synthetic order."""

    specimen_id: str
    barcode: str
    order_id: str
    tenant_id: str
    patient: PatientRef
    status: SpecimenStatus
    registered_at: str
    rejection_reason: str | None = None


@dataclass(frozen=True, slots=True)
class TestExecution:
    """A synthetic testing session. There is no analyzer connection."""

    execution_id: str
    specimen_id: str
    order_id: str
    tenant_id: str
    status: TestExecutionStatus
    entered_at: str
    actor_id: str
    completed_at: str | None = None


@dataclass(frozen=True, slots=True)
class ResultAmendment:
    """An immutable correction record attached to a synthetic result."""

    amendment_id: str
    result_id: str
    tenant_id: str
    previous_value: float
    new_value: float
    reason: str
    actor_id: str
    occurred_at: str
    version: int


@dataclass(frozen=True, slots=True)
class LabResult:
    """A synthetic result recorded against a synthetic order and specimen."""

    result_id: str
    idempotency_key: str
    order_id: str
    specimen_id: str
    patient: PatientRef
    tenant_id: str
    test_code: str
    value: float
    unit: str
    reference_low: float
    reference_high: float
    critical_flag: bool
    recorded_at: str
    version: int = 1
    amendments: tuple[ResultAmendment, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class Verification:
    """A synthetic review decision with a full lifecycle."""

    verification_id: str
    result_id: str
    tenant_id: str
    reviewer_id: str
    decision: VerificationDecision
    status: VerificationStatus
    idempotency_key: str
    created_at: str
    reason: str | None = None
