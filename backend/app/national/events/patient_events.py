from app.national.events.base import NationalDomainEvent
from dataclasses import dataclass


@dataclass
class PatientRegistered(NationalDomainEvent):
    event_type: str = "national.patient.registered"
    aggregate_type: str = "Patient"


@dataclass
class PatientMerged(NationalDomainEvent):
    event_type: str = "national.patient.merged"
    aggregate_type: str = "Patient"


@dataclass
class PatientGuardianAssigned(NationalDomainEvent):
    event_type: str = "national.patient.guardian_assigned"
    aggregate_type: str = "Patient"
