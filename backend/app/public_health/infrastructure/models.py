from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String, Text

from app.national.base import TenantEntity


class DiseaseCaseModel(TenantEntity):
    __tablename__ = "ph_disease_cases"

    disease_code = Column(String(40), nullable=False, index=True)
    disease_name = Column(String(200), nullable=True)
    category = Column(String(50), default="reportable")
    region = Column(String(100), nullable=False, index=True)
    district = Column(String(100), nullable=True)
    location_lat = Column(Float, nullable=True)
    location_lng = Column(Float, nullable=True)
    patient_age = Column(Integer, nullable=True)
    patient_gender = Column(String(20), nullable=True)
    patient_national_id = Column(String(100), nullable=True)
    is_confirmed = Column(Boolean, default=False)
    confirmation_method = Column(String(100), nullable=True)
    confirmation_date = Column(DateTime(timezone=True), nullable=True)
    source = Column(String(50), default="laboratory")
    reported_by = Column(String(200), nullable=True)
    reported_at = Column(DateTime(timezone=True), nullable=False)
    outcome = Column(String(100), nullable=True)
    severity = Column(String(50), default="moderate")
    symptoms = Column(JSON, nullable=True)
    risk_factors = Column(JSON, nullable=True)
    exposure_history = Column(Text, nullable=True)
    travel_history = Column(Text, nullable=True)
    contact_tracing_completed = Column(Boolean, default=False)
    contact_count = Column(Integer, default=0)
    notes = Column(Text, nullable=True)


class OutbreakAlertModel(TenantEntity):
    __tablename__ = "ph_outbreak_alerts"

    disease = Column(String(200), nullable=False)
    disease_code = Column(String(40), nullable=True)
    region = Column(String(100), nullable=False, index=True)
    district = Column(String(100), nullable=True)
    confirmed_cases = Column(Integer, default=0)
    suspected_cases = Column(Integer, default=0)
    recovered_cases = Column(Integer, default=0)
    fatalities = Column(Integer, default=0)
    attack_rate = Column(Float, default=0.0)
    transmission_type = Column(String(50), default="unknown")
    alert_level = Column(String(50), default="information")
    status = Column(String(50), default="monitoring")
    first_detected = Column(DateTime(timezone=True), nullable=False)
    last_updated = Column(DateTime(timezone=True), nullable=True)
    investigation_notes = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    control_measures = Column(JSON, nullable=True)
    declared_by = Column(String(200), nullable=True)
    declared_over_at = Column(DateTime(timezone=True), nullable=True)
    lab_confirmed = Column(Boolean, default=False)


class ImmunizationRecordModel(TenantEntity):
    __tablename__ = "ph_immunization_records"

    patient_id = Column(String(100), nullable=False, index=True)
    patient_name = Column(String(200), nullable=True)
    vaccine = Column(String(200), nullable=False)
    vaccine_code = Column(String(40), nullable=True)
    dose_number = Column(Integer, default=1)
    total_doses = Column(Integer, default=1)
    administration_date = Column(DateTime(timezone=True), nullable=False)
    administered_by = Column(String(200), nullable=True)
    facility_id = Column(String(100), nullable=True)
    lot_number = Column(String(100), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    route = Column(String(50), default="intramuscular")
    site = Column(String(50), default="deltoid")
    batch_number = Column(String(100), nullable=True)
    manufacturer = Column(String(200), nullable=True)
    is_boosted = Column(Boolean, default=False)
    adverse_event = Column(Text, nullable=True)
    consent_obtained = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)


class PublicHealthReportModel(TenantEntity):
    __tablename__ = "ph_reports"

    report_type = Column(String(50), default="weekly")
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    region = Column(String(100), nullable=True)
    total_cases = Column(Integer, default=0)
    total_deaths = Column(Integer, default=0)
    diseases_reported = Column(JSON, nullable=True)
    outbreaks_active = Column(Integer, default=0)
    alerts_raised = Column(Integer, default=0)
    vaccination_coverage_pct = Column(Float, default=0.0)
    key_findings = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    published_by = Column(String(200), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="draft")


class SurveillanceSignalModel(TenantEntity):
    __tablename__ = "ph_surveillance_signals"

    disease = Column(String(200), nullable=False)
    disease_code = Column(String(40), nullable=True)
    region = Column(String(100), nullable=False, index=True)
    case_count = Column(Integer, default=0)
    expected_count = Column(Integer, default=0)
    baseline_period_days = Column(Integer, default=30)
    z_score = Column(Float, default=0.0)
    alert_level = Column(String(50), default="information")
    detected_at = Column(DateTime(timezone=True), nullable=False)
    recommendation = Column(Text, nullable=True)
    acknowledged_by = Column(String(200), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)


class EnvironmentalHealthModel(TenantEntity):
    __tablename__ = "ph_environmental_health"

    sample_type = Column(String(50), nullable=False)
    location_lat = Column(Float, nullable=True)
    location_lng = Column(Float, nullable=True)
    region = Column(String(100), nullable=True, index=True)
    district = Column(String(100), nullable=True)
    collection_date = Column(DateTime(timezone=True), nullable=False)
    tested_for = Column(String(200), nullable=True)
    result = Column(String(100), nullable=True)
    value = Column(Float, nullable=True)
    unit = Column(String(50), nullable=True)
    laboratory = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
