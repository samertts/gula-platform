from dataclasses import dataclass, field
from typing import Any


@dataclass
class DiseaseCase:
    id: str = ""
    disease_code: str = ""
    disease_name: str = ""
    category: str = "reportable"
    region: str = ""
    district: str = ""
    location_lat: float = 0.0
    location_lng: float = 0.0
    patient_age: int = 0
    patient_gender: str = ""
    patient_national_id: str = ""
    is_confirmed: bool = False
    confirmation_method: str = ""
    source: str = "laboratory"
    reported_by: str = ""
    reported_at: str = ""
    outcome: str = ""
    notes: str = ""


@dataclass
class OutbreakAlert:
    id: str = ""
    disease: str = ""
    disease_code: str = ""
    region: str = ""
    district: str = ""
    confirmed_cases: int = 0
    suspected_cases: int = 0
    recovered_cases: int = 0
    fatalities: int = 0
    attack_rate: float = 0.0
    transmission_type: str = "unknown"
    alert_level: str = "information"
    status: str = "monitoring"
    first_detected: str = ""
    last_updated: str = ""
    investigation_notes: str = ""
    recommendations: str = ""
    declared_by: str = ""
    declared_over_at: str = ""


@dataclass
class SurveillanceSignal:
    id: str = ""
    disease: str = ""
    region: str = ""
    case_count: int = 0
    expected_count: int = 0
    baseline_period_days: int = 30
    z_score: float = 0.0
    alert_level: str = "information"
    detected_at: str = ""
    recommendation: str = ""


@dataclass
class ImmunizationRecord:
    id: str = ""
    patient_id: str = ""
    health_number: str = ""
    newborn_id: str = ""
    schedule_id: str = ""
    patient_name: str = ""
    vaccine: str = ""
    vaccine_code: str = ""
    dose_number: int = 1
    total_doses: int = 1
    scheduled_date: str = ""
    due_date: str = ""
    status: str = "administered"
    appointment_id: str = ""
    administration_date: str = ""
    administered_by: str = ""
    facility_id: str = ""
    lot_number: str = ""
    expiry_date: str = ""
    route: str = "intramuscular"
    site: str = "deltoid"
    batch_number: str = ""
    manufacturer: str = ""
    is_boosted: bool = False
    adverse_event: str = ""
    reminder_sent: bool = False
    reminder_sent_at: str = ""
    notes: str = ""


@dataclass
class ImmunizationSchedule:
    id: str = ""
    patient_id: str = ""
    health_number: str = ""
    newborn_id: str = ""
    schedule_definition_id: str = ""
    schedule_version: str = ""
    vaccine: str = ""
    vaccine_code: str = ""
    dose_number: int = 1
    total_doses: int = 1
    due_date: str = ""
    scheduled_date: str = ""
    status: str = "scheduled"
    facility_id: str = ""
    appointment_id: str = ""
    reminder_sent: bool = False
    reminder_sent_at: str = ""
    reminder_count: int = 0
    contraindication_reason: str = ""
    refusal_reason: str = ""
    notes: str = ""
    follow_up_status: str = "not_required"
    follow_up_priority: str = "normal"
    next_follow_up_date: str = ""
    non_administration_reason: str = ""
    non_administration_notes: str = ""


@dataclass
class ImmunizationFollowUpTask:
    id: str = ""
    schedule_id: str = ""
    patient_id: str = ""
    health_number: str = ""
    vaccine: str = ""
    due_date: str = ""
    status: str = "pending"
    priority: str = "normal"
    reason: str = ""
    next_action_at: str = ""
    consent_verified: bool = False
    preferred_channel: str = ""
    last_attempt_at: str = ""
    completed_at: str = ""
    completed_by: str = ""
    notes: str = ""


@dataclass
class ImmunizationAdverseEvent:
    id: str = ""
    record_id: str = ""
    schedule_id: str = ""
    patient_id: str = ""
    health_number: str = ""
    vaccine: str = ""
    onset_at: str = ""
    severity: str = "unknown"
    symptoms: list[str] = field(default_factory=list)
    treatment: str = ""
    outcome: str = ""
    investigation_status: str = "reported"
    reported_by: str = ""
    reported_at: str = ""
    notes: str = ""


@dataclass
class VaccineCatalog:
    id: str = ""
    vaccine_code: str = ""
    name: str = ""
    name_ar: str = ""
    unit: str = "dose"
    manufacturer: str = ""
    storage_min_c: float | None = None
    storage_max_c: float | None = None
    source_reference: str = ""
    is_active: bool = True


@dataclass
class VaccineLot:
    id: str = ""
    catalog_id: str = ""
    lot_number: str = ""
    expiry_date: str = ""
    received_at: str = ""
    received_quantity: int = 0
    available_quantity: int = 0
    quarantined: bool = False
    quarantine_reason: str = ""
    storage_equipment_id: str = ""


@dataclass
class ColdChainReading:
    id: str = ""
    equipment_id: str = ""
    reading_at: str = ""
    temperature_c: float = 0.0
    minimum_allowed_c: float | None = None
    maximum_allowed_c: float | None = None
    status: str = "within_range"
    source: str = "manual"
    recorded_by: str = ""
    alert_acknowledged: bool = False
    notes: str = ""


@dataclass
class PublicHealthReport:
    id: str = ""
    report_type: str = "weekly"
    period_start: str = ""
    period_end: str = ""
    region: str = ""
    total_cases: int = 0
    total_deaths: int = 0
    diseases_reported: list[dict[str, Any]] = field(default_factory=list)
    outbreaks_active: int = 0
    alerts_raised: int = 0
    vaccination_coverage_pct: float = 0.0
    key_findings: str = ""
    recommendations: str = ""
    published_by: str = ""
    published_at: str = ""


@dataclass
class MosquitoTrap:
    id: str = ""
    trap_id: str = ""
    location_lat: float = 0.0
    location_lng: float = 0.0
    region: str = ""
    district: str = ""
    species: str = ""
    mosquito_count: int = 0
    collection_date: str = ""
    temperature_c: float = 0.0
    humidity_pct: float = 0.0
    rainfall_mm: float = 0.0
    virus_tested: str = ""
    virus_positive: bool = False


@dataclass
class EnvironmentalSample:
    id: str = ""
    sample_id: str = ""
    sample_type: str = "water"
    location_lat: float = 0.0
    location_lng: float = 0.0
    region: str = ""
    collection_date: str = ""
    tested_for: str = ""
    result: str = ""
    value: float = 0.0
    unit: str = ""
    laboratory: str = ""
