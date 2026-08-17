from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Index, Integer, String, Text

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
    __table_args__ = (
        Index("ix_ph_immunization_records_lab_date_status", "lab_id", "administration_date", "status"),
        Index("ix_ph_immunization_records_lab_patient", "lab_id", "patient_id"),
    )

    patient_id = Column(String(100), nullable=False, index=True)
    health_number = Column(String(20), nullable=True, index=True)
    newborn_id = Column(String(26), nullable=True, index=True)
    schedule_id = Column(String(26), nullable=True, unique=True, index=True)
    patient_name = Column(String(200), nullable=True)
    vaccine = Column(String(200), nullable=False)
    vaccine_code = Column(String(40), nullable=True)
    dose_number = Column(Integer, default=1)
    total_doses = Column(Integer, default=1)
    scheduled_date = Column(DateTime(timezone=True), nullable=True, index=True)
    due_date = Column(DateTime(timezone=True), nullable=True, index=True)
    status = Column(String(32), nullable=False, default="administered", index=True)
    appointment_id = Column(String(100), nullable=True, index=True)
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
    reminder_sent = Column(Boolean, nullable=False, default=False)
    reminder_sent_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)


class ImmunizationScheduleDefinitionModel(TenantEntity):
    """Facility-scoped, Ministry-approved reference definition; never hard-code EPI doses."""

    __tablename__ = "ph_immunization_schedule_definitions"

    schedule_version = Column(String(40), nullable=False, index=True)
    vaccine = Column(String(200), nullable=False)
    vaccine_code = Column(String(40), nullable=False, index=True)
    dose_number = Column(Integer, nullable=False)
    total_doses = Column(Integer, nullable=False)
    minimum_age_days = Column(Integer, nullable=False, default=0)
    recommended_age_days = Column(Integer, nullable=False)
    grace_period_days = Column(Integer, nullable=False, default=0)
    route = Column(String(50), nullable=True)
    site = Column(String(50), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    source_reference = Column(String(500), nullable=True)
    effective_from = Column(DateTime(timezone=True), nullable=True, index=True)
    effective_to = Column(DateTime(timezone=True), nullable=True, index=True)
    approval_status = Column(String(24), nullable=False, default="approved")
    approval_reference = Column(String(200), nullable=True)


class ImmunizationScheduleModel(TenantEntity):
    """A patient-specific planned dose generated from an approved reference schedule."""

    __tablename__ = "ph_immunization_schedules"
    __table_args__ = (
        Index("ix_ph_immunization_schedules_lab_status_due", "lab_id", "status", "due_date"),
        Index("ix_ph_immunization_schedules_lab_patient_due", "lab_id", "patient_id", "due_date"),
    )

    patient_id = Column(String(100), nullable=False, index=True)
    health_number = Column(String(20), nullable=False, index=True)
    newborn_id = Column(String(26), nullable=True, index=True)
    schedule_definition_id = Column(String(26), nullable=False, index=True)
    schedule_version = Column(String(40), nullable=False, index=True)
    vaccine = Column(String(200), nullable=False)
    vaccine_code = Column(String(40), nullable=False, index=True)
    dose_number = Column(Integer, nullable=False)
    total_doses = Column(Integer, nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=False, index=True)
    scheduled_date = Column(DateTime(timezone=True), nullable=True, index=True)
    status = Column(String(32), nullable=False, default="scheduled", index=True)
    facility_id = Column(String(100), nullable=True)
    appointment_id = Column(String(100), nullable=True, index=True)
    reminder_sent = Column(Boolean, nullable=False, default=False)
    reminder_sent_at = Column(DateTime(timezone=True), nullable=True)
    reminder_count = Column(Integer, nullable=False, default=0)
    contraindication_reason = Column(Text, nullable=True)
    refusal_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    follow_up_status = Column(String(24), nullable=False, default="not_required", index=True)
    follow_up_priority = Column(String(16), nullable=False, default="normal")
    next_follow_up_date = Column(DateTime(timezone=True), nullable=True, index=True)
    non_administration_reason = Column(String(32), nullable=True)
    non_administration_notes = Column(Text, nullable=True)


class ImmunizationFollowUpTaskModel(TenantEntity):
    __tablename__ = "ph_immunization_follow_up_tasks"
    __table_args__ = (
        Index("ix_ph_immunization_followup_lab_status_action", "lab_id", "status", "next_action_at"),
    )

    schedule_id = Column(String(26), nullable=False, index=True)
    patient_id = Column(String(100), nullable=False, index=True)
    health_number = Column(String(20), nullable=False, index=True)
    vaccine = Column(String(200), nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(String(24), nullable=False, default="pending", index=True)
    priority = Column(String(16), nullable=False, default="normal", index=True)
    reason = Column(String(32), nullable=True)
    next_action_at = Column(DateTime(timezone=True), nullable=True, index=True)
    consent_verified = Column(Boolean, nullable=False, default=False)
    preferred_channel = Column(String(24), nullable=True)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completed_by = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)


class ImmunizationAdverseEventModel(TenantEntity):
    __tablename__ = "ph_immunization_adverse_events"

    record_id = Column(String(26), nullable=False, index=True)
    schedule_id = Column(String(26), nullable=True, index=True)
    patient_id = Column(String(100), nullable=False, index=True)
    health_number = Column(String(20), nullable=True, index=True)
    vaccine = Column(String(200), nullable=False)
    onset_at = Column(DateTime(timezone=True), nullable=True)
    severity = Column(String(24), nullable=False, default="unknown")
    symptoms = Column(JSON, nullable=False, default=list)
    treatment = Column(Text, nullable=True)
    outcome = Column(String(32), nullable=True)
    investigation_status = Column(String(24), nullable=False, default="reported", index=True)
    reported_by = Column(String(100), nullable=False)
    reported_at = Column(DateTime(timezone=True), nullable=False)
    notes = Column(Text, nullable=True)


class VaccineCatalogModel(TenantEntity):
    __tablename__ = "ph_vaccine_catalog"

    vaccine_code = Column(String(40), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    unit = Column(String(24), nullable=False, default="dose")
    manufacturer = Column(String(200), nullable=True)
    storage_min_c = Column(Float, nullable=True)
    storage_max_c = Column(Float, nullable=True)
    source_reference = Column(String(500), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)


class VaccineLotModel(TenantEntity):
    __tablename__ = "ph_vaccine_lots"

    catalog_id = Column(String(26), nullable=False, index=True)
    lot_number = Column(String(100), nullable=False, index=True)
    expiry_date = Column(DateTime(timezone=True), nullable=False, index=True)
    received_at = Column(DateTime(timezone=True), nullable=True)
    received_quantity = Column(Integer, nullable=False, default=0)
    available_quantity = Column(Integer, nullable=False, default=0)
    quarantined = Column(Boolean, nullable=False, default=False, index=True)
    quarantine_reason = Column(Text, nullable=True)
    storage_equipment_id = Column(String(100), nullable=True)


class VaccineStockMovementModel(TenantEntity):
    __tablename__ = "ph_vaccine_stock_movements"

    lot_id = Column(String(26), nullable=False, index=True)
    movement_type = Column(String(24), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    reference_type = Column(String(40), nullable=True)
    reference_id = Column(String(100), nullable=True, index=True)
    idempotency_key = Column(String(160), nullable=False, unique=True, index=True)
    reason = Column(Text, nullable=True)
    performed_by = Column(String(100), nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False, index=True)


class ColdChainReadingModel(TenantEntity):
    __tablename__ = "ph_cold_chain_readings"

    equipment_id = Column(String(100), nullable=False, index=True)
    reading_at = Column(DateTime(timezone=True), nullable=False, index=True)
    temperature_c = Column(Float, nullable=False)
    minimum_allowed_c = Column(Float, nullable=True)
    maximum_allowed_c = Column(Float, nullable=True)
    status = Column(String(24), nullable=False, default="within_range", index=True)
    source = Column(String(24), nullable=False, default="manual")
    recorded_by = Column(String(100), nullable=False)
    alert_acknowledged = Column(Boolean, nullable=False, default=False)
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
