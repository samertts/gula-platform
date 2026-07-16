from dataclasses import dataclass

from app.national.events.base import NationalDomainEvent


@dataclass
class EmergencyDeclared(NationalDomainEvent):
    event_type: str = "command_center.emergency.declared"
    emergency_id: str = ""
    emergency_type: str = ""
    level: str = ""
    region: str = ""
    declared_by: str = ""


@dataclass
class EmergencyResolved(NationalDomainEvent):
    event_type: str = "command_center.emergency.resolved"
    emergency_id: str = ""
    previous_level: str = ""
    resolved_by: str = ""


@dataclass
class ResourceMobilized(NationalDomainEvent):
    event_type: str = "command_center.resource.mobilized"
    request_id: str = ""
    resource_type: str = ""
    quantity: int = 0
    source: str = ""
    destination: str = ""


@dataclass
class SituationUpdatePublished(NationalDomainEvent):
    event_type: str = "command_center.situation_update.published"
    update_id: str = ""
    emergency_id: str = ""
    summary: str = ""
    published_by: str = ""


@dataclass
class AfterActionReportCompleted(NationalDomainEvent):
    event_type: str = "command_center.after_action.completed"
    report_id: str = ""
    emergency_id: str = ""
    overall_rating: str = ""
