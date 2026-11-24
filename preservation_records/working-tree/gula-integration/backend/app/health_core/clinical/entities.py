"""Immutable domain entities for synthetic clinical development.

Every entity carries a synthetic identifier, a synthetic tenant and no
real-world patient attribute. Entities are frozen: state changes produce a new
version through the services, never an in-place mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.health_core.clinical.validation import require_synthetic_ref
from app.health_core.common import ForbiddenSyntheticOperationError

__all__ = [
    "LEGAL_ENCOUNTER_TRANSITIONS",
    "ClinicalNote",
    "Diagnosis",
    "DiagnosisStatus",
    "Encounter",
    "EncounterStatus",
    "Facility",
    "FacilityType",
    "MedicalRecordView",
    "Observation",
    "Organization",
    "Practitioner",
    "PractitionerRole",
    "RecordScope",
    "Severity",
]


class PractitionerRole(StrEnum):
    """Synthetic clinical roles; no real licence or registry is consulted."""

    PHYSICIAN = "physician"
    NURSE = "nurse"
    LAB_TECHNICIAN = "lab_technician"
    RADIOLOGIST = "radiologist"
    PHARMACIST = "pharmacist"


class FacilityType(StrEnum):
    """Synthetic facility types used for hierarchy validation."""

    HOSPITAL = "hospital"
    CLINIC = "clinic"
    LABORATORY = "laboratory"


class EncounterStatus(StrEnum):
    """Legal states of a synthetic encounter lifecycle."""

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    ADMITTED = "admitted"
    TRANSFERRED = "transferred"
    DISCHARGED = "discharged"
    CANCELLED = "cancelled"


class DiagnosisStatus(StrEnum):
    """Assertion status of a synthetic problem entry."""

    ACTIVE = "active"
    RESOLVED = "resolved"


class Severity(StrEnum):
    """Synthetic clinical severity; not a triage or treatment decision."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class Practitioner:
    """A synthetic practitioner with qualification, tenant and active status."""

    practitioner_id: str
    tenant_id: str
    role: PractitionerRole
    qualification: str
    active: bool = True


@dataclass(frozen=True, slots=True)
class Organization:
    """A synthetic organisation that owns facilities within one tenant."""

    organization_id: str
    tenant_id: str
    label: str
    active: bool = True


@dataclass(frozen=True, slots=True)
class Facility:
    """A synthetic facility belonging to exactly one synthetic organisation."""

    facility_id: str
    tenant_id: str
    organization_id: str
    label: str
    facility_type: FacilityType
    active: bool = True


@dataclass(frozen=True, slots=True)
class Encounter:
    """A synthetic encounter scoped to one patient and one facility."""

    encounter_id: str
    tenant_id: str
    patient_ref: str
    practitioner_id: str
    facility_id: str
    status: EncounterStatus
    reason: str
    version: int
    created_at: str

    def can_transition_to(self, target: EncounterStatus) -> bool:
        """Return whether ``target`` is a legal next state."""
        return target in LEGAL_ENCOUNTER_TRANSITIONS[self.status]

    def is_open(self) -> bool:
        """Return whether the encounter is still in an active state."""
        return self.status not in (EncounterStatus.DISCHARGED, EncounterStatus.CANCELLED)


LEGAL_ENCOUNTER_TRANSITIONS: dict[EncounterStatus, frozenset[EncounterStatus]] = {
    EncounterStatus.PLANNED: frozenset({EncounterStatus.IN_PROGRESS, EncounterStatus.CANCELLED}),
    EncounterStatus.IN_PROGRESS: frozenset(
        {EncounterStatus.ADMITTED, EncounterStatus.TRANSFERRED, EncounterStatus.CANCELLED}
    ),
    EncounterStatus.ADMITTED: frozenset(
        {EncounterStatus.TRANSFERRED, EncounterStatus.DISCHARGED, EncounterStatus.CANCELLED}
    ),
    EncounterStatus.TRANSFERRED: frozenset(
        {EncounterStatus.ADMITTED, EncounterStatus.DISCHARGED, EncounterStatus.CANCELLED}
    ),
    EncounterStatus.DISCHARGED: frozenset(),
    EncounterStatus.CANCELLED: frozenset(),
}


@dataclass(frozen=True, slots=True)
class ClinicalNote:
    """A synthetic note attached to one encounter and its patient."""

    note_id: str
    tenant_id: str
    encounter_id: str
    patient_ref: str
    author_practitioner_id: str
    text: str
    created_at: str


@dataclass(frozen=True, slots=True)
class Diagnosis:
    """A synthetic coded problem linked to exactly one synthetic encounter."""

    diagnosis_id: str
    tenant_id: str
    patient_ref: str
    encounter_id: str
    code: str
    description: str
    severity: Severity
    status: DiagnosisStatus
    asserted_at: str
    resolved_at: str | None
    version: int

    def is_active(self) -> bool:
        """Return whether this problem is still asserted as active."""
        return self.status is DiagnosisStatus.ACTIVE


@dataclass(frozen=True, slots=True)
class Observation:
    """A synthetic coded vital or observation with a validated UCUM-style unit."""

    observation_id: str
    tenant_id: str
    patient_ref: str
    encounter_id: str
    code: str
    display: str
    value: float
    unit: str
    recorded_at: str


@dataclass(frozen=True, slots=True)
class RecordScope:
    """Explicit single-patient scope for a medical-record request."""

    tenant_id: str
    patient_refs: tuple[str, ...]

    def assert_single_patient(self) -> str:
        """Return the sole patient reference or refuse a spanning request."""
        tenant = require_synthetic_ref(self.tenant_id, field="tenant_id")
        distinct = tuple(dict.fromkeys(self.patient_refs))
        if len(distinct) != 1:
            raise ForbiddenSyntheticOperationError(
                "medical record scope must address exactly one synthetic patient",
                details={"tenant_id": tenant, "patient_count": len(distinct)},
            )
        return require_synthetic_ref(distinct[0], field="patient_ref", prefix="SYN-PAT-")


@dataclass(frozen=True, slots=True)
class MedicalRecordView:
    """An immutable aggregate of one synthetic patient's clinical data."""

    tenant_id: str
    patient_ref: str
    encounters: tuple[Encounter, ...]
    diagnoses: tuple[Diagnosis, ...]
    observations: tuple[Observation, ...]
    notes: tuple[ClinicalNote, ...]
    opened_at: str

    @property
    def item_count(self) -> int:
        """Total number of aggregated clinical items."""
        return len(self.encounters) + len(self.diagnoses) + len(self.observations) + len(self.notes)
