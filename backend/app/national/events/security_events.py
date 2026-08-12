from dataclasses import dataclass

from app.national.events.base import NationalDomainEvent


@dataclass
class ConsentGranted(NationalDomainEvent):
    event_type: str = "national.consent.granted"
    aggregate_type: str = "Consent"


@dataclass
class ConsentRevoked(NationalDomainEvent):
    event_type: str = "national.consent.revoked"
    aggregate_type: str = "Consent"


@dataclass
class ConsentExpired(NationalDomainEvent):
    event_type: str = "national.consent.expired"
    aggregate_type: str = "Consent"


@dataclass
class AccessDenied(NationalDomainEvent):
    event_type: str = "national.security.access_denied"
    aggregate_type: str = "Security"


@dataclass
class EmergencyAccessGranted(NationalDomainEvent):
    event_type: str = "national.security.emergency_access"
    aggregate_type: str = "Security"
