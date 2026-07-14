from app.national.events.base import NationalDomainEvent
from dataclasses import dataclass


@dataclass
class CitizenCreated(NationalDomainEvent):
    event_type: str = "national.citizen.created"
    aggregate_type: str = "Citizen"


@dataclass
class CitizenUpdated(NationalDomainEvent):
    event_type: str = "national.citizen.updated"
    aggregate_type: str = "Citizen"


@dataclass
class CitizenVerified(NationalDomainEvent):
    event_type: str = "national.citizen.verified"
    aggregate_type: str = "Citizen"


@dataclass
class CitizenMerged(NationalDomainEvent):
    event_type: str = "national.citizen.merged"
    aggregate_type: str = "Citizen"


@dataclass
class CitizenDeceased(NationalDomainEvent):
    event_type: str = "national.citizen.deceased"
    aggregate_type: str = "Citizen"


@dataclass
class HealthNumberAssigned(NationalDomainEvent):
    event_type: str = "national.health_number.assigned"
    aggregate_type: str = "Citizen"
