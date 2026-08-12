from dataclasses import dataclass

from app.national.events.base import NationalDomainEvent


@dataclass
class FamilyCreated(NationalDomainEvent):
    event_type: str = "national.family.created"
    aggregate_type: str = "Family"


@dataclass
class FamilyMemberAdded(NationalDomainEvent):
    event_type: str = "national.family.member_added"
    aggregate_type: str = "Family"


@dataclass
class FamilyMemberRemoved(NationalDomainEvent):
    event_type: str = "national.family.member_removed"
    aggregate_type: str = "Family"
