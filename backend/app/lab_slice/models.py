"""Synthetic-only data contracts for the laboratory vertical slice.

These records contain no real patient data, national identifiers, card images,
credentials, or durable storage. They are intentionally narrow inputs for
composing existing LIMS, QC, FHIR, offline, and analytics primitives.
"""

from __future__ import annotations

from dataclasses import dataclass

SYNTHETIC_ID_PREFIX = "synthetic-"
RELEASE_PENDING = "pending_review"
RELEASE_RELEASED = "released"
RELEASE_QUARANTINED = "quarantined"
RELEASE_REJECTED = "rejected"


def require_synthetic_id(value: str, field_name: str) -> str:
    """Reject caller-supplied non-synthetic identifiers at the boundary."""
    if (
        not isinstance(value, str)
        or not value.startswith(SYNTHETIC_ID_PREFIX)
        or len(value) > 128
        or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-" for character in value)
    ):
        raise ValueError(f"{field_name} must be a bounded synthetic identifier")
    return value


@dataclass(frozen=True, slots=True)
class SyntheticPatient:
    patient_id: str
    age_years: int
    gender: str = "unknown"
    region: str = "synthetic-region"

    def __post_init__(self) -> None:
        require_synthetic_id(self.patient_id, "patient_id")
        if not 0 <= self.age_years <= 120:
            raise ValueError("age_years must be between 0 and 120")


@dataclass(frozen=True, slots=True)
class SyntheticOrder:
    order_id: str
    patient_id: str
    test_code: str
    priority: str = "routine"
    status: str = "pending"

    def __post_init__(self) -> None:
        require_synthetic_id(self.order_id, "order_id")
        require_synthetic_id(self.patient_id, "patient_id")
        if not self.test_code.strip():
            raise ValueError("test_code is required")


@dataclass(frozen=True, slots=True)
class CustodyEvent:
    event_id: str
    location: str
    actor: str
    recorded_at: str

    def __post_init__(self) -> None:
        require_synthetic_id(self.event_id, "event_id")


@dataclass(frozen=True, slots=True)
class SyntheticSpecimen:
    specimen_id: str
    order_id: str
    patient_id: str
    specimen_type: str
    state: str = "ordered"
    custody: tuple[CustodyEvent, ...] = ()

    def __post_init__(self) -> None:
        require_synthetic_id(self.specimen_id, "specimen_id")
        require_synthetic_id(self.order_id, "order_id")
        require_synthetic_id(self.patient_id, "patient_id")


@dataclass(frozen=True, slots=True)
class SyntheticQCControl:
    control_id: str
    test_code: str
    value: float
    mean: float
    sd: float
    history: tuple[float, ...] = ()

    def __post_init__(self) -> None:
        require_synthetic_id(self.control_id, "control_id")
        if self.sd <= 0:
            raise ValueError("sd must be positive")


@dataclass(frozen=True, slots=True)
class SyntheticResult:
    result_id: str
    order_id: str
    specimen_id: str
    patient_id: str
    test_code: str
    value: float
    unit: str
    reference_low: float
    reference_high: float
    critical_low: float | None = None
    critical_high: float | None = None
    previous_value: float | None = None
    reportable_condition: str | None = None

    def __post_init__(self) -> None:
        require_synthetic_id(self.result_id, "result_id")
        require_synthetic_id(self.order_id, "order_id")
        require_synthetic_id(self.specimen_id, "specimen_id")
        require_synthetic_id(self.patient_id, "patient_id")
        if self.reference_low > self.reference_high:
            raise ValueError("reference_low cannot exceed reference_high")


@dataclass(frozen=True, slots=True)
class ReleaseDecision:
    decision_id: str
    result_id: str
    status: str
    reasons: tuple[str, ...]
    reviewer: str | None = None
    reason: str | None = None
    idempotency_key: str | None = None
    released_at: str | None = None

    def __post_init__(self) -> None:
        require_synthetic_id(self.decision_id, "decision_id")
        require_synthetic_id(self.result_id, "result_id")
        if self.status not in {
            RELEASE_PENDING,
            RELEASE_RELEASED,
            RELEASE_QUARANTINED,
            RELEASE_REJECTED,
        }:
            raise ValueError("unsupported release status")


@dataclass(frozen=True, slots=True)
class SyntheticLabCase:
    patient: SyntheticPatient
    order: SyntheticOrder
    specimen: SyntheticSpecimen
    result: SyntheticResult
    qc: SyntheticQCControl
