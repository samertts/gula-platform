from __future__ import annotations

from dataclasses import dataclass

from app.national.events.base import NationalDomainEvent


@dataclass
class IncidentCreated(NationalDomainEvent):
    event_type: str = "ems.incident.created"
    aggregate_type: str = "EmergencyIncident"
    incident_id: str = ""
    category: str = ""
    priority: str = ""


@dataclass
class IncidentDispatched(NationalDomainEvent):
    event_type: str = "ems.incident.dispatched"
    aggregate_type: str = "EmergencyIncident"
    incident_id: str = ""
    ambulance_id: str = ""


@dataclass
class IncidentResolved(NationalDomainEvent):
    event_type: str = "ems.incident.resolved"
    aggregate_type: str = "EmergencyIncident"
    incident_id: str = ""
    outcome: str = ""


@dataclass
class AmbulanceDispatched(NationalDomainEvent):
    event_type: str = "ems.ambulance.dispatched"
    aggregate_type: str = "Ambulance"
    ambulance_id: str = ""
    incident_id: str = ""


@dataclass
class AmbulanceEnRoute(NationalDomainEvent):
    event_type: str = "ems.ambulance.en_route"
    aggregate_type: str = "Ambulance"
    ambulance_id: str = ""
    incident_id: str = ""
    location_lat: float = 0.0
    location_lng: float = 0.0


@dataclass
class AmbulanceArrivedOnScene(NationalDomainEvent):
    event_type: str = "ems.ambulance.on_scene"
    aggregate_type: str = "Ambulance"
    ambulance_id: str = ""
    incident_id: str = ""


@dataclass
class PatientTransportStarted(NationalDomainEvent):
    event_type: str = "ems.patient.transport_started"
    aggregate_type: str = "EmergencyIncident"
    incident_id: str = ""
    destination_facility: str = ""


@dataclass
class TriagePerformed(NationalDomainEvent):
    event_type: str = "ems.triage.performed"
    aggregate_type: str = "TriageAssessment"
    triage_id: str = ""
    incident_id: str = ""
    category: str = ""


@dataclass
class DisasterDeclared(NationalDomainEvent):
    event_type: str = "ems.disaster.declared"
    aggregate_type: str = "DisasterEvent"
    disaster_event_id: str = ""
    disaster_type: str = ""
    severity_level: int = 3


@dataclass
class MassCasualtyActivated(NationalDomainEvent):
    event_type: str = "ems.mass_casualty.activated"
    aggregate_type: str = "MassCasualtyIncident"
    mass_casualty_id: str = ""
    total_patients: int = 0


@dataclass
class HospitalCapacityChanged(NationalDomainEvent):
    event_type: str = "ems.hospital.capacity_changed"
    aggregate_type: str = "HospitalStatus"
    facility_id: str = ""
    available_beds: int = 0
    diversion_status: bool = False


@dataclass
class ePCRCompleted(NationalDomainEvent):
    event_type: str = "ems.epcr.completed"
    aggregate_type: str = "ePCR"
    epcr_id: str = ""
    incident_id: str = ""
