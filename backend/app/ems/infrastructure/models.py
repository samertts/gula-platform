from __future__ import annotations

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)

from app.national.base import TenantAuditEntity, TenantEntity


class EmergencyIncidentModel(TenantEntity):
    __tablename__ = "ems_incidents"

    caller_name = Column(String(200), nullable=True)
    caller_phone = Column(String(50), nullable=True)
    caller_relationship = Column(String(100), nullable=True)
    location_lat = Column(Float, nullable=True)
    location_lng = Column(Float, nullable=True)
    location_address = Column(Text, nullable=True)
    location_description = Column(Text, nullable=True)
    category = Column(String(50), default="medical")
    priority = Column(String(50), default="bravo")
    status = Column(String(50), default="pending")
    description = Column(Text, nullable=True)
    symptoms = Column(Text, nullable=True)
    patient_count = Column(Integer, default=1)
    patient_age = Column(Integer, nullable=True)
    patient_gender = Column(String(20), nullable=True)
    patient_name = Column(String(200), nullable=True)
    patient_phone = Column(String(50), nullable=True)
    patient_condition = Column(Text, nullable=True)
    is_conscious = Column(Boolean, default=True)
    is_breathing = Column(Boolean, default=True)
    has_pulse = Column(Boolean, default=True)
    has_allergies = Column(Boolean, default=False)
    has_bleeding = Column(Boolean, default=False)
    has_chest_pain = Column(Boolean, default=False)
    has_difficulty_breathing = Column(Boolean, default=False)
    is_pregnant = Column(Boolean, default=False)
    is_diabetic = Column(Boolean, default=False)
    has_seizure = Column(Boolean, default=False)
    dispatcher_notes = Column(Text, nullable=True)
    dispatch_time = Column(DateTime(timezone=True), nullable=True)
    scene_arrival_time = Column(DateTime(timezone=True), nullable=True)
    scene_departure_time = Column(DateTime(timezone=True), nullable=True)
    destination_arrival_time = Column(DateTime(timezone=True), nullable=True)
    completion_time = Column(DateTime(timezone=True), nullable=True)
    destination_facility_id = Column(String(100), nullable=True)
    destination_facility_name = Column(String(200), nullable=True)
    destination_type = Column(String(50), default="emergency_department")
    incident_command_id = Column(String(100), nullable=True)
    disaster_event_id = Column(String(100), nullable=True)
    mass_casualty_id = Column(String(100), nullable=True)
    created_by = Column(String(100), nullable=True)


class DispatchAssignmentModel(TenantEntity):
    __tablename__ = "ems_dispatch_assignments"

    incident_id = Column(String(100), ForeignKey("ems_incidents.id"), nullable=False, index=True)
    ambulance_id = Column(String(100), ForeignKey("ems_ambulances.id"), nullable=True)
    status = Column(String(50), default="pending")
    assigned_at = Column(DateTime(timezone=True), nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    en_route_at = Column(DateTime(timezone=True), nullable=True)
    on_scene_at = Column(DateTime(timezone=True), nullable=True)
    transporting_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=True)


class AmbulanceModel(TenantEntity):
    __tablename__ = "ems_ambulances"

    vehicle_id = Column(String(100), nullable=True, index=True)
    registration_number = Column(String(50), nullable=True, unique=True)
    call_sign = Column(String(50), nullable=True, unique=True)
    type = Column(String(50), default="bls")
    status = Column(String(50), default="available")
    status_reason = Column(Text, nullable=True)
    current_location_lat = Column(Float, nullable=True)
    current_location_lng = Column(Float, nullable=True)
    current_location_updated = Column(DateTime(timezone=True), nullable=True)
    station_id = Column(String(100), nullable=True)
    station_name = Column(String(200), nullable=True)
    facility_id = Column(String(100), nullable=True)
    is_gps_enabled = Column(Boolean, default=True)
    fuel_level = Column(Float, default=100.0)
    mileage_km = Column(Float, default=0.0)
    last_maintenance_date = Column(DateTime(timezone=True), nullable=True)
    next_maintenance_due = Column(DateTime(timezone=True), nullable=True)
    vehicle_status = Column(String(50), default="active")
    equipment_inventory = Column(JSON, nullable=True)


class AmbulanceCrewModel(TenantEntity):
    __tablename__ = "ems_ambulance_crew"

    user_id = Column(String(100), nullable=True)
    full_name = Column(String(200), nullable=False)
    role = Column(String(50), default="emt")
    is_available = Column(Boolean, default=True)
    station_id = Column(String(100), nullable=True)
    facility_id = Column(String(100), nullable=True)
    certifications = Column(JSON, nullable=True)
    phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)


class CrewShiftModel(TenantEntity):
    __tablename__ = "ems_crew_shifts"

    crew_id = Column(String(100), ForeignKey("ems_ambulance_crew.id"), nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="scheduled")
    station_id = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)


class TriageAssessmentModel(TenantEntity):
    __tablename__ = "ems_triage_assessments"

    incident_id = Column(String(100), ForeignKey("ems_incidents.id"), nullable=True, index=True)
    patient_id = Column(String(100), nullable=True)
    patient_name = Column(String(200), nullable=True)
    patient_age = Column(Integer, nullable=True)
    patient_gender = Column(String(20), nullable=True)
    category = Column(String(50), default="minor")
    system = Column(String(50), default="start")
    respiratory_rate = Column(Integer, nullable=True)
    capillary_refill = Column(Float, nullable=True)
    heart_rate = Column(Integer, nullable=True)
    systolic_bp = Column(Integer, nullable=True)
    mental_status = Column(String(100), nullable=True)
    ambulatory = Column(Boolean, default=True)
    external_bleeding = Column(Boolean, default=False)
    burns_percentage = Column(Float, nullable=True)
    trauma_score = Column(Integer, nullable=True)
    glasgow_coma_scale = Column(Integer, nullable=True)
    priority_score = Column(Integer, default=0)
    assessed_by = Column(String(100), nullable=True)
    assessed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)


class ePCRModel(TenantAuditEntity):
    __tablename__ = "ems_epcr"

    incident_id = Column(String(100), ForeignKey("ems_incidents.id"), nullable=False, index=True)
    patient_id = Column(String(100), nullable=True)
    patient_name = Column(String(200), nullable=True)
    patient_dob = Column(String(20), nullable=True)
    patient_gender = Column(String(20), nullable=True)
    patient_address = Column(Text, nullable=True)
    patient_phone = Column(String(50), nullable=True)
    patient_blood_group = Column(String(10), nullable=True)
    patient_allergies = Column(JSON, nullable=True)
    patient_medications = Column(JSON, nullable=True)
    patient_medical_history = Column(JSON, nullable=True)
    dispatch_call_time = Column(DateTime(timezone=True), nullable=True)
    scene_arrival_time = Column(DateTime(timezone=True), nullable=True)
    patient_assessment_time = Column(DateTime(timezone=True), nullable=True)
    scene_departure_time = Column(DateTime(timezone=True), nullable=True)
    destination_arrival_time = Column(DateTime(timezone=True), nullable=True)
    transfer_of_care_time = Column(DateTime(timezone=True), nullable=True)
    incident_description = Column(Text, nullable=True)
    chief_complaint = Column(Text, nullable=True)
    history_of_present_illness = Column(Text, nullable=True)
    mechanism_of_injury = Column(Text, nullable=True)
    injury_type = Column(String(100), nullable=True)
    injury_location = Column(String(100), nullable=True)
    initial_vital_signs = Column(JSON, nullable=True)
    serial_vitals = Column(JSON, nullable=True)
    physical_exam_findings = Column(Text, nullable=True)
    neurological_assessment = Column(Text, nullable=True)
    pain_assessment = Column(Text, nullable=True)
    pain_scale = Column(Integer, nullable=True)
    interventions = Column(JSON, nullable=True)
    medications_administered = Column(JSON, nullable=True)
    procedures_performed = Column(JSON, nullable=True)
    ecg_interpretation = Column(Text, nullable=True)
    cardiac_rhythm = Column(String(100), nullable=True)
    oxygen_saturation = Column(Float, nullable=True)
    end_tidal_co2 = Column(Float, nullable=True)
    blood_glucose = Column(Float, nullable=True)
    etco2 = Column(Float, nullable=True)
    stroke_scale = Column(String(100), nullable=True)
    trauma_score = Column(Integer, nullable=True)
    glasgow_coma_scale = Column(Integer, nullable=True)
    revised_trauma_score = Column(Integer, nullable=True)
    prehospital_index = Column(Integer, nullable=True)
    destination_facility = Column(String(200), nullable=True)
    destination_reason = Column(Text, nullable=True)
    transport_mode = Column(String(50), default="ground")
    crew_members = Column(JSON, nullable=True)
    submitting_crew_member = Column(String(200), nullable=True)
    signatures = Column(JSON, nullable=True)
    narrative = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(50), default="draft")


class DisasterEventModel(TenantAuditEntity):
    __tablename__ = "ems_disaster_events"

    event_name = Column(String(200), nullable=False)
    disaster_type = Column(String(50), default="other")
    phase = Column(String(50), default="response")
    severity_level = Column(Integer, default=3)
    location_lat = Column(Float, nullable=True)
    location_lng = Column(Float, nullable=True)
    location_address = Column(Text, nullable=True)
    region = Column(String(200), nullable=True)
    governorate = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    casualties_count = Column(Integer, default=0)
    fatalities_count = Column(Integer, default=0)
    missing_count = Column(Integer, default=0)
    displaced_count = Column(Integer, default=0)
    affected_population = Column(Integer, default=0)
    incident_command_id = Column(String(100), nullable=True)
    declared_state_of_emergency = Column(Boolean, default=False)
    declared_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String(100), nullable=True)


class IncidentCommandModel(TenantAuditEntity):
    __tablename__ = "ems_incident_commands"

    disaster_event_id = Column(String(100), ForeignKey("ems_disaster_events.id"), nullable=True)
    incident_name = Column(String(200), nullable=True)
    incident_number = Column(String(100), nullable=True)
    location = Column(Text, nullable=True)
    command_post_location = Column(Text, nullable=True)
    operational_period = Column(String(100), nullable=True)
    mission_statement = Column(Text, nullable=True)
    objectives = Column(JSON, nullable=True)
    command_staff = Column(JSON, nullable=True)
    status = Column(String(50), default="active")


class MassCasualtyIncidentModel(TenantAuditEntity):
    __tablename__ = "ems_mass_casualty_incidents"

    disaster_event_id = Column(String(100), ForeignKey("ems_disaster_events.id"), nullable=True)
    incident_location = Column(Text, nullable=True)
    incident_type = Column(String(100), nullable=True)
    total_patients = Column(Integer, default=0)
    immediate_count = Column(Integer, default=0)
    delayed_count = Column(Integer, default=0)
    minor_count = Column(Integer, default=0)
    expectant_count = Column(Integer, default=0)
    deceased_count = Column(Integer, default=0)
    transported_count = Column(Integer, default=0)
    hospitals_notified = Column(JSON, nullable=True)
    resources_deployed = Column(JSON, nullable=True)
    triage_officer = Column(String(200), nullable=True)
    status = Column(String(50), default="active")


class ShelterModel(TenantEntity):
    __tablename__ = "ems_shelters"

    name = Column(String(200), nullable=False)
    disaster_event_id = Column(String(100), ForeignKey("ems_disaster_events.id"), nullable=True)
    location_lat = Column(Float, nullable=True)
    location_lng = Column(Float, nullable=True)
    address = Column(Text, nullable=True)
    capacity = Column(Integer, default=0)
    current_occupants = Column(Integer, default=0)
    shelter_type = Column(String(100), nullable=True)
    contact_name = Column(String(200), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    supplies_level = Column(String(50), nullable=True)
    status = Column(String(50), default="active")


class HospitalStatusModel(TenantEntity):
    __tablename__ = "ems_hospital_status"

    facility_id = Column(String(100), nullable=False, index=True)
    facility_name = Column(String(200), nullable=True)
    capabilities = Column(JSON, nullable=True)
    total_beds = Column(Integer, default=0)
    available_beds = Column(Integer, default=0)
    icu_beds = Column(Integer, default=0)
    available_icu_beds = Column(Integer, default=0)
    ventilators_total = Column(Integer, default=0)
    ventilators_available = Column(Integer, default=0)
    emergency_room_status = Column(String(50), default="normal")
    trauma_bays_available = Column(Integer, default=0)
    operating_rooms_available = Column(Integer, default=0)
    diversion_status = Column(Boolean, default=False)
    diversion_reason = Column(Text, nullable=True)
    last_updated = Column(DateTime(timezone=True), nullable=True)
