from app.national.events.base import NationalDomainEvent
from dataclasses import dataclass


@dataclass
class IdentityResolved(NationalDomainEvent):
    event_type: str = "national.identity.resolved"
    aggregate_type: str = "IdentityResolution"


@dataclass
class IdentityMergeRequested(NationalDomainEvent):
    event_type: str = "national.identity.merge_requested"
    aggregate_type: str = "MergeRecord"


@dataclass
class IdentityMergeApproved(NationalDomainEvent):
    event_type: str = "national.identity.merge_approved"
    aggregate_type: str = "MergeRecord"


@dataclass
class IdentityMergeRejected(NationalDomainEvent):
    event_type: str = "national.identity.merge_rejected"
    aggregate_type: str = "MergeRecord"


@dataclass
class BreakGlassAccessed(NationalDomainEvent):
    event_type: str = "national.identity.break_glass"
    aggregate_type: str = "IdentityAuditLog"
