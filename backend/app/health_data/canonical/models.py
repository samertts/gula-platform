from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass
class PatientCanonical:
    id: str
    version: int = 1
    active: bool = True

    identifiers: list[dict] = field(default_factory=list)
    names: list[dict] = field(default_factory=list)
    telecoms: list[dict] = field(default_factory=list)
    gender: str | None = None
    birth_date: date | None = None
    deceased: bool = False
    deceased_datetime: datetime | None = None

    addresses: list[dict] = field(default_factory=list)
    marital_status: str | None = None
    multiple_birth: bool = False
    birth_order: int | None = None

    general_practitioners: list[str] = field(default_factory=list)
    managing_organization: str | None = None
    links: list[dict] = field(default_factory=list)

    national_id_hash: str | None = None
    health_number: str | None = None

    source_system: str | None = None
    source_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    extension: dict[str, Any] = field(default_factory=dict)


@dataclass
class EncounterCanonical:
    id: str
    version: int = 1

    patient_id: str | None = None
    patient_canonical_id: str | None = None

    status: str = "planned"
    encounter_class: str | None = None
    encounter_type: str | None = None

    period_start: datetime | None = None
    period_end: datetime | None = None

    service_provider: str | None = None
    facility_id: str | None = None
    department: str | None = None

    participants: list[dict] = field(default_factory=list)
    diagnoses: list[dict] = field(default_factory=list)

    reason_code: str | None = None
    reason_description: str | None = None
    priority: int | None = None

    source_system: str | None = None
    source_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    extension: dict[str, Any] = field(default_factory=dict)


@dataclass
class ObservationCanonical:
    id: str
    version: int = 1

    patient_id: str | None = None
    encounter_id: str | None = None
    performer_id: str | None = None

    status: str = "final"
    category: str | None = None
    code: str | None = None
    code_display: str | None = None
    code_system: str = "http://loinc.org"

    value_quantity: dict | None = None
    value_string: str | None = None
    value_concept: dict | None = None
    data_absent_reason: str | None = None

    interpretation: list[dict] = field(default_factory=list)
    reference_range: list[dict] = field(default_factory=list)

    issued: datetime | None = None
    effective_datetime: datetime | None = None

    source_system: str | None = None
    source_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    extension: dict[str, Any] = field(default_factory=dict)


@dataclass
class MedicationCanonical:
    id: str
    version: int = 1

    patient_id: str | None = None
    encounter_id: str | None = None
    prescriber_id: str | None = None

    status: str = "active"
    medication_code: str | None = None
    medication_display: str | None = None

    dosage_instructions: list[dict] = field(default_factory=list)
    timing: dict | None = None
    route: str | None = None
    quantity: dict | None = None

    authored_on: datetime | None = None
    reason_code: str | None = None

    source_system: str | None = None
    source_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    extension: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConditionCanonical:
    id: str
    version: int = 1

    patient_id: str | None = None
    encounter_id: str | None = None
    recorder_id: str | None = None

    status: str = "active"
    severity: str | None = None
    code: str | None = None
    code_display: str | None = None
    code_system: str = "http://snomed.info/sct"
    body_site: str | None = None

    onset_datetime: datetime | None = None
    abatement_datetime: datetime | None = None
    recorded_date: datetime | None = None

    clinical_status: str | None = None
    verification_status: str | None = None

    source_system: str | None = None
    source_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    extension: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcedureCanonical:
    id: str
    version: int = 1

    patient_id: str | None = None
    encounter_id: str | None = None
    performer_id: str | None = None

    status: str = "completed"
    code: str | None = None
    code_display: str | None = None

    performed_datetime: datetime | None = None
    performed_end: datetime | None = None

    body_site: str | None = None
    outcome: str | None = None
    complications: list[str] = field(default_factory=list)

    reason_code: str | None = None

    source_system: str | None = None
    source_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    extension: dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentCanonical:
    id: str
    version: int = 1

    patient_id: str | None = None
    encounter_id: str | None = None
    author_id: str | None = None

    status: str = "current"
    doc_type: str | None = None
    category: str | None = None

    title: str | None = None
    content_type: str = "text/plain"
    content: str | None = None
    content_url: str | None = None
    size_bytes: int | None = None

    created: datetime | None = None
    indexed: datetime | None = None

    source_system: str | None = None
    source_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    extension: dict[str, Any] = field(default_factory=dict)
