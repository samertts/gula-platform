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
    patient_name: str = ""
    vaccine: str = ""
    vaccine_code: str = ""
    dose_number: int = 1
    total_doses: int = 1
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
