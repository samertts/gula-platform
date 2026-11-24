"""Composition root for the synthetic clinical workstream.

A :class:`ClinicalContext` wires every service to the same identity port, event
log and set of process-local repositories. It is deliberately not imported by
``app.factory`` or ``app.main``: constructing it never activates a route.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.health_core.clinical.ports import EventSink
from app.health_core.clinical.repositories import InMemoryEventLog
from app.health_core.clinical.services import (
    DiagnosisService,
    EncounterService,
    MedicalRecordService,
    ObservationService,
    OrganizationRegistry,
    PractitionerRegistry,
)
from app.health_core.common import DomainEvent
from app.health_core.identity import PatientIdentityPort

__all__ = ["ClinicalContext"]


@dataclass(slots=True)
class ClinicalContext:
    """In-memory, synthetic-only wiring of all six clinical domains."""

    identity: PatientIdentityPort
    events: EventSink = field(default_factory=InMemoryEventLog)
    practitioners: PractitionerRegistry = field(init=False)
    organizations: OrganizationRegistry = field(init=False)
    encounters: EncounterService = field(init=False)
    diagnoses: DiagnosisService = field(init=False)
    observations: ObservationService = field(init=False)
    medical_records: MedicalRecordService = field(init=False)

    def __post_init__(self) -> None:
        self.practitioners = PractitionerRegistry(events=self.events)
        self.organizations = OrganizationRegistry(events=self.events)
        self.encounters = EncounterService(
            identity=self.identity,
            practitioners=self.practitioners,
            organizations=self.organizations,
            events=self.events,
        )
        self.diagnoses = DiagnosisService(
            identity=self.identity,
            encounters=self.encounters,
            events=self.events,
        )
        self.observations = ObservationService(
            identity=self.identity,
            encounters=self.encounters,
            events=self.events,
        )
        self.medical_records = MedicalRecordService(
            identity=self.identity,
            encounters=self.encounters,
            diagnoses=self.diagnoses,
            observations=self.observations,
            events=self.events,
        )

    def event_history(self) -> tuple[DomainEvent, ...]:
        """Return all emitted synthetic events in emission order."""
        return self.events.all()
