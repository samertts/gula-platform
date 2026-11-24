"""Synthetic clinical foundation — DEVELOPMENT ONLY, NOT PRODUCTION-ACTIVATED.

This package implements practitioner, organisation/facility, encounter,
diagnosis, observation and medical-record aggregate behaviour entirely in
memory. All patient references come from :mod:`app.health_core.identity`; no
canonical identity, NHID, MPI, database or network operation exists here.
"""

from __future__ import annotations

from app.health_core.clinical.context import ClinicalContext
from app.health_core.clinical.entities import (
    LEGAL_ENCOUNTER_TRANSITIONS,
    ClinicalNote,
    Diagnosis,
    DiagnosisStatus,
    Encounter,
    EncounterStatus,
    Facility,
    FacilityType,
    MedicalRecordView,
    Observation,
    Organization,
    Practitioner,
    PractitionerRole,
    RecordScope,
    Severity,
)
from app.health_core.clinical.errors import ClinicalValidationError, UnknownClinicalEntityError
from app.health_core.clinical.ports import ClinicalRepository, EventSink
from app.health_core.clinical.repositories import InMemoryEventLog, InMemoryRepository
from app.health_core.clinical.services import (
    TRANSITION_EVENTS,
    DiagnosisService,
    EncounterService,
    MedicalRecordService,
    ObservationService,
    OrganizationRegistry,
    PractitionerRegistry,
)

__all__ = [
    "LEGAL_ENCOUNTER_TRANSITIONS",
    "TRANSITION_EVENTS",
    "ClinicalContext",
    "ClinicalNote",
    "ClinicalRepository",
    "ClinicalValidationError",
    "Diagnosis",
    "DiagnosisService",
    "DiagnosisStatus",
    "Encounter",
    "EncounterService",
    "EncounterStatus",
    "EventSink",
    "Facility",
    "FacilityType",
    "InMemoryEventLog",
    "InMemoryRepository",
    "MedicalRecordService",
    "MedicalRecordView",
    "Observation",
    "ObservationService",
    "Organization",
    "OrganizationRegistry",
    "Practitioner",
    "PractitionerRegistry",
    "PractitionerRole",
    "RecordScope",
    "Severity",
    "UnknownClinicalEntityError",
]
