from dataclasses import dataclass

from app.national.events.base import NationalDomainEvent


@dataclass
class ComponentRegistered(NationalDomainEvent):
    event_type: str = "lifecycle.component.registered"
    component_id: str = ""
    name: str = ""
    component_type: str = ""
    version: str = ""


@dataclass
class ComponentDeprecated(NationalDomainEvent):
    event_type: str = "lifecycle.component.deprecated"
    component_id: str = ""
    name: str = ""
    deprecation_policy: str = ""
    sunset_date: str = ""


@dataclass
class ReleaseCreated(NationalDomainEvent):
    event_type: str = "lifecycle.release.created"
    release_id: str = ""
    component_id: str = ""
    version: str = ""
    channel: str = ""


@dataclass
class ReleaseApproved(NationalDomainEvent):
    event_type: str = "lifecycle.release.approved"
    release_id: str = ""
    approved_by: str = ""
    certification_level: str = ""


@dataclass
class CompatibilityVerified(NationalDomainEvent):
    event_type: str = "lifecycle.compatibility.verified"
    component_a: str = ""
    component_b: str = ""
    version_a: str = ""
    version_b: str = ""
    level: str = ""
