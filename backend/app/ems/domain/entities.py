from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.ems.domain.enums import (
    AmbulanceStatus,
    AmbulanceType,
    CrewRole,
    DestinationType,
    DisasterPhase,
    DisasterType,
    DispatchStatus,
    HospitalCapability,
    IncidentCategory,
    IncidentPriority,
    IncidentStatus,
    ShiftStatus,
    TriageCategory,
    TriageSystem,
    VehicleStatus,
)


@dataclass
class EmergencyIncident:
    id: str
    caller_name: str = ""
    caller_phone: str = ""
    caller_relationship: str = ""
    location_lat: float | None = None
    location_lng: float | None = None
    location_address: str = ""
    location_description: str = ""
    category: IncidentCategory = IncidentCategory.MEDICAL
    priority: IncidentPriority = IncidentPriority.BRAVO
    status: IncidentStatus = IncidentStatus.PENDING
    description: str = ""
    symptoms: str = ""
    patient_count: int = 1
    patient_age: int | None = None
    patient_gender: str = ""
    patient_name: str = ""
    patient_phone: str = ""
    patient_condition: str = ""
    is_conscious: bool = True
    is_breathing: bool = True
    has_pulse: bool = True
    has_allergies: bool = False
    has_bleeding: bool = False
    has_chest_pain: bool = False
    has_difficulty_breathing: bool = False
    is_pregnant: bool = False
    is_diabetic: bool = False
    has_seizure: bool = False
    dispatcher_notes: str = ""
    dispatch_time: datetime | None = None
    scene_arrival_time: datetime | None = None
    scene_departure_time: datetime | None = None
    destination_arrival_time: datetime | None = None
    completion_time: datetime | None = None
    destination_facility_id: str = ""
    destination_facility_name: str = ""
    destination_type: DestinationType = DestinationType.EMERGENCY_DEPARTMENT
    incident_command_id: str = ""
    disaster_event_id: str = ""
    mass_casualty_id: str = ""
    created_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def is_active(self) -> bool:
        return self.status in (
            IncidentStatus.PENDING,
            IncidentStatus.DISPATCHED,
            IncidentStatus.EN_ROUTE,
            IncidentStatus.ON_SCENE,
            IncidentStatus.TRANSPORTING,
            IncidentStatus.AT_DESTINATION,
        )

    @property
    def response_time_seconds(self) -> float | None:
        if self.dispatch_time and self.scene_arrival_time:
            return (self.scene_arrival_time - self.dispatch_time).total_seconds()
        return None


@dataclass
class DispatchAssignment:
    id: str
    incident_id: str
    ambulance_id: str = ""
    crew_ids: list[str] = field(default_factory=list)
    status: DispatchStatus = DispatchStatus.PENDING
    assigned_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    acknowledged_at: datetime | None = None
    en_route_at: datetime | None = None
    on_scene_at: datetime | None = None
    transporting_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    cancellation_reason: str = ""
    notes: str = ""
    created_by: str = ""


@dataclass
class Ambulance:
    id: str
    vehicle_id: str = ""
    registration_number: str = ""
    call_sign: str = ""
    type: AmbulanceType = AmbulanceType.BASIC_LIFE_SUPPORT
    status: AmbulanceStatus = AmbulanceStatus.AVAILABLE
    status_reason: str = ""
    current_location_lat: float | None = None
    current_location_lng: float | None = None
    current_location_updated: datetime | None = None
    station_id: str = ""
    station_name: str = ""
    facility_id: str = ""
    is_gps_enabled: bool = True
    fuel_level: float = 100.0
    mileage_km: float = 0.0
    last_maintenance_date: datetime | None = None
    next_maintenance_due: datetime | None = None
    vehicle_status: VehicleStatus = VehicleStatus.ACTIVE
    equipment_inventory: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def is_available(self) -> bool:
        return self.status == AmbulanceStatus.AVAILABLE

    @property
    def is_deployable(self) -> bool:
        return self.vehicle_status == VehicleStatus.ACTIVE and self.fuel_level > 20.0


@dataclass
class AmbulanceCrew:
    id: str
    user_id: str = ""
    full_name: str = ""
    role: CrewRole = CrewRole.EMERGENCY_MEDICAL_TECHNICIAN
    is_available: bool = True
    station_id: str = ""
    facility_id: str = ""
    certifications: list[str] = field(default_factory=list)
    phone: str = ""
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CrewShift:
    id: str
    crew_id: str
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: ShiftStatus = ShiftStatus.SCHEDULED
    station_id: str = ""
    notes: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class TriageAssessment:
    id: str
    incident_id: str = ""
    patient_id: str = ""
    patient_name: str = ""
    patient_age: int | None = None
    patient_gender: str = ""
    category: TriageCategory = TriageCategory.MINOR
    system: TriageSystem = TriageSystem.START
    respiratory_rate: int | None = None
    capillary_refill: float | None = None
    heart_rate: int | None = None
    systolic_bp: int | None = None
    mental_status: str = ""
    ambulatory: bool = True
    external_bleeding: bool = False
    burns_percentage: float | None = None
    trauma_score: int | None = None
    glasgow_coma_scale: int | None = None
    priority_score: int = 0
    assessed_by: str = ""
    assessed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    notes: str = ""


@dataclass
class ePCR:
    id: str
    incident_id: str
    patient_id: str = ""
    patient_name: str = ""
    patient_dob: str = ""
    patient_gender: str = ""
    patient_address: str = ""
    patient_phone: str = ""
    patient_blood_group: str = ""
    patient_allergies: list[str] = field(default_factory=list)
    patient_medications: list[str] = field(default_factory=list)
    patient_medical_history: list[str] = field(default_factory=list)
    dispatch_call_time: datetime | None = None
    scene_arrival_time: datetime | None = None
    patient_assessment_time: datetime | None = None
    scene_departure_time: datetime | None = None
    destination_arrival_time: datetime | None = None
    transfer_of_care_time: datetime | None = None
    incident_description: str = ""
    chief_complaint: str = ""
    history_of_present_illness: str = ""
    mechanism_of_injury: str = ""
    injury_type: str = ""
    injury_location: str = ""
    initial_vital_signs: dict[str, Any] = field(default_factory=dict)
    serial_vitals: list[dict[str, Any]] = field(default_factory=list)
    physical_exam_findings: str = ""
    neurological_assessment: str = ""
    pain_assessment: str = ""
    pain_scale: int | None = None
    interventions: list[dict[str, Any]] = field(default_factory=list)
    medications_administered: list[dict[str, Any]] = field(default_factory=list)
    procedures_performed: list[dict[str, Any]] = field(default_factory=list)
    ecg_interpretation: str = ""
    cardiac_rhythm: str = ""
    oxygen_saturation: float | None = None
    end_tidal_co2: float | None = None
    blood_glucose: float | None = None
    etco2: float | None = None
    stroke_scale: str = ""
    trauma_score: int | None = None
    glasgow_coma_scale: int | None = None
    revised_trauma_score: int | None = None
    prehospital_index: int | None = None
    destination_facility: str = ""
    destination_reason: str = ""
    transport_mode: str = "ground"
    crew_members: list[dict[str, Any]] = field(default_factory=list)
    submitting_crew_member: str = ""
    signatures: list[dict[str, Any]] = field(default_factory=list)
    narrative: str = ""
    notes: str = ""
    status: str = "draft"
    created_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    version: int = 1


@dataclass
class DisasterEvent:
    id: str
    event_name: str
    disaster_type: DisasterType = DisasterType.OTHER
    phase: DisasterPhase = DisasterPhase.RESPONSE
    severity_level: int = 3
    location_lat: float | None = None
    location_lng: float | None = None
    location_address: str = ""
    region: str = ""
    governorate: str = ""
    description: str = ""
    casualties_count: int = 0
    fatalities_count: int = 0
    missing_count: int = 0
    displaced_count: int = 0
    affected_population: int = 0
    incident_command_id: str = ""
    declared_state_of_emergency: bool = False
    declared_at: datetime | None = None
    closed_at: datetime | None = None
    created_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class IncidentCommandSystem:
    id: str
    disaster_event_id: str = ""
    incident_name: str = ""
    incident_number: str = ""
    location: str = ""
    command_post_location: str = ""
    operational_period: str = ""
    mission_statement: str = ""
    objectives: list[str] = field(default_factory=list)
    command_staff: dict[str, str] = field(default_factory=dict)
    status: str = "active"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class MassCasualtyIncident:
    id: str
    disaster_event_id: str = ""
    incident_location: str = ""
    incident_type: str = ""
    total_patients: int = 0
    immediate_count: int = 0
    delayed_count: int = 0
    minor_count: int = 0
    expectant_count: int = 0
    deceased_count: int = 0
    transported_count: int = 0
    hospitals_notified: list[str] = field(default_factory=list)
    resources_deployed: list[dict[str, Any]] = field(default_factory=list)
    triage_officer: str = ""
    status: str = "active"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class Shelter:
    id: str
    name: str
    disaster_event_id: str = ""
    location_lat: float | None = None
    location_lng: float | None = None
    address: str = ""
    capacity: int = 0
    current_occupants: int = 0
    shelter_type: str = ""
    contact_name: str = ""
    contact_phone: str = ""
    supplies_level: str = ""
    status: str = "active"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class HospitalStatus:
    id: str
    facility_id: str
    facility_name: str = ""
    capabilities: list[HospitalCapability] = field(default_factory=list)
    total_beds: int = 0
    available_beds: int = 0
    icu_beds: int = 0
    available_icu_beds: int = 0
    ventilators_total: int = 0
    ventilators_available: int = 0
    emergency_room_status: str = "normal"
    trauma_bays_available: int = 0
    operating_rooms_available: int = 0
    diversion_status: bool = False
    diversion_reason: str = ""
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
