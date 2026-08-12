from dataclasses import dataclass

from app.national.events.base import NationalDomainEvent


@dataclass
class EncounterCreated(NationalDomainEvent):
    event_type: str = "national.encounter.created"
    aggregate_type: str = "Encounter"


@dataclass
class EncounterCompleted(NationalDomainEvent):
    event_type: str = "national.encounter.completed"
    aggregate_type: str = "Encounter"


@dataclass
class EncounterCancelled(NationalDomainEvent):
    event_type: str = "national.encounter.cancelled"
    aggregate_type: str = "Encounter"
