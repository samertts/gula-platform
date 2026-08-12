from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import Enum as SAEnum

from app.care_continuum.base import CareContinuumTenantAuditEntity
from app.care_continuum.enums import CareProgramStatus, ChronicDiseaseType, DiseaseSeverity


class ChronicDiseaseRegistry(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_chronic_disease_registry"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    episode_of_care_id = Column(String(26), ForeignKey("national_episodes_of_care.id", ondelete="SET NULL"), nullable=True, index=True)

    disease_type = Column(SAEnum(ChronicDiseaseType), nullable=False, index=True)
    severity = Column(SAEnum(DiseaseSeverity), nullable=False, default=DiseaseSeverity.MILD)
    status = Column(SAEnum(CareProgramStatus), nullable=False, default=CareProgramStatus.ACTIVE)

    diagnosed_by = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=True, index=True)
    diagnosed_at = Column(DateTime(timezone=True), nullable=False)
    diagnosing_facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="SET NULL"), nullable=True)

    icd10_code = Column(String(20), nullable=True)
    diagnosis_description = Column(Text, nullable=True)
    onset_date = Column(Date, nullable=True)
    duration_years = Column(Integer, nullable=True)

    complications = Column(JSON, nullable=True)
    comorbidities = Column(JSON, nullable=True)
    risk_factors = Column(JSON, nullable=True)

    last_review_date = Column(DateTime(timezone=True), nullable=True)
    next_review_date = Column(Date, nullable=True)
    review_interval_days = Column(Integer, nullable=True)

    care_manager_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True)
    is_controlled = Column(Boolean, nullable=True)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_chronic_registry_patient", "patient_id"),
        Index("ix_cc_chronic_registry_disease", "disease_type"),
        Index("ix_cc_chronic_registry_severity", "severity"),
        Index("ix_cc_chronic_registry_patient_disease", "patient_id", "disease_type", unique=True),
        {"extend_existing": True},
    )


class DiseaseManagementPlan(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_disease_management_plans"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    registry_id = Column(String(26), ForeignKey("cc_chronic_disease_registry.id", ondelete="CASCADE"), nullable=True, index=True)

    disease_type = Column(SAEnum(ChronicDiseaseType), nullable=False)
    severity = Column(SAEnum(DiseaseSeverity), nullable=True)

    plan_date = Column(DateTime(timezone=True), nullable=False)
    review_date = Column(Date, nullable=True)
    status = Column(SAEnum(CareProgramStatus), nullable=False, default=CareProgramStatus.ACTIVE)

    created_by = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=False, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="SET NULL"), nullable=True)

    treatment_goals = Column(JSON, nullable=True)
    medications = Column(JSON, nullable=True)
    lifestyle_modifications = Column(JSON, nullable=True)
    monitoring_parameters = Column(JSON, nullable=True)
    target_values = Column(JSON, nullable=True)
    follow_up_schedule = Column(JSON, nullable=True)

    self_management_education = Column(JSON, nullable=True)
    dietary_plan = Column(Text, nullable=True)
    exercise_plan = Column(Text, nullable=True)
    smoking_cessation = Column(Boolean, default=False)

    specialist_referrals = Column(JSON, nullable=True)
    allied_health_referrals = Column(JSON, nullable=True)
    community_support_services = Column(JSON, nullable=True)

    patient_goals = Column(JSON, nullable=True)
    barriers_to_adherence = Column(JSON, nullable=True)
    outcomes = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_disease_mgmt_patient", "patient_id"),
        Index("ix_cc_disease_mgmt_registry", "registry_id"),
        Index("ix_cc_disease_mgmt_creator", "created_by"),
        {"extend_existing": True},
    )


class ClinicalPathwayEnrollment(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_clinical_pathway_enrollments"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    registry_id = Column(String(26), ForeignKey("cc_chronic_disease_registry.id", ondelete="SET NULL"), nullable=True, index=True)

    pathway_code = Column(String(50), nullable=False, index=True)
    pathway_name = Column(String(200), nullable=False)
    pathway_version = Column(String(20), nullable=True)

    enrolled_by = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=False, index=True)
    enrolled_at = Column(DateTime(timezone=True), nullable=False)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="SET NULL"), nullable=True)

    status = Column(SAEnum(CareProgramStatus), nullable=False, default=CareProgramStatus.ACTIVE)
    current_step = Column(String(100), nullable=True)
    step_progress = Column(JSON, nullable=True)

    milestones = Column(JSON, nullable=True)
    expected_duration_days = Column(Integer, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completed_by = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True)

    outcomes = Column(JSON, nullable=True)
    deviation_reason = Column(Text, nullable=True)
    adverse_events = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_pathway_enrollment_patient", "patient_id"),
        Index("ix_cc_pathway_enrollment_pathway", "pathway_code"),
        Index("ix_cc_pathway_enrollment_status", "status"),
        {"extend_existing": True},
    )


class RiskStratification(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_risk_stratification"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    registry_id = Column(String(26), ForeignKey("cc_chronic_disease_registry.id", ondelete="SET NULL"), nullable=True, index=True)

    assessment_date = Column(DateTime(timezone=True), nullable=False)
    stratification_type = Column(String(100), nullable=False)
    risk_model = Column(String(100), nullable=True)
    risk_score = Column(Float, nullable=True)
    risk_category = Column(String(50), nullable=False, index=True)

    assessed_by = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=True, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="SET NULL"), nullable=True)

    risk_factors = Column(JSON, nullable=True)
    protective_factors = Column(JSON, nullable=True)
    biometric_data = Column(JSON, nullable=True)
    lab_results = Column(JSON, nullable=True)
    medication_adherence = Column(String(50), nullable=True)

    ed_visits_last_6mo = Column(Integer, default=0)
    hospitalizations_last_6mo = Column(Integer, default=0)
    missed_appointments_last_6mo = Column(Integer, default=0)

    recommended_interventions = Column(JSON, nullable=True)
    care_intensity = Column(String(50), nullable=True)
    review_date = Column(Date, nullable=True)
    next_assessment_date = Column(Date, nullable=True)

    is_high_risk = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_risk_strat_patient", "patient_id"),
        Index("ix_cc_risk_strat_category", "risk_category"),
        Index("ix_cc_risk_strat_date", "assessment_date"),
        {"extend_existing": True},
    )


class SelfMonitoringRecord(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_self_monitoring_records"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    registry_id = Column(String(26), ForeignKey("cc_chronic_disease_registry.id", ondelete="SET NULL"), nullable=True, index=True)
    care_plan_id = Column(String(26), ForeignKey("cc_disease_management_plans.id", ondelete="SET NULL"), nullable=True)

    recorded_at = Column(DateTime(timezone=True), nullable=False)
    recording_method = Column(String(100), nullable=True)

    metric_type = Column(String(100), nullable=False, index=True)
    metric_value = Column(String(100), nullable=False)
    metric_unit = Column(String(50), nullable=True)
    metric_category = Column(String(50), nullable=True)

    blood_glucose_mgdl = Column(Float, nullable=True)
    blood_pressure_systolic = Column(Integer, nullable=True)
    blood_pressure_diastolic = Column(Integer, nullable=True)
    heart_rate = Column(Integer, nullable=True)
    weight_kg = Column(Float, nullable=True)
    temperature_celsius = Column(Float, nullable=True)
    oxygen_saturation = Column(Float, nullable=True)
    peak_flow = Column(Integer, nullable=True)
    pain_level = Column(Integer, nullable=True)

    symptoms = Column(JSON, nullable=True)
    medication_taken = Column(Boolean, nullable=True)
    medication_dose = Column(String(50), nullable=True)
    exercise_minutes = Column(Integer, nullable=True)
    calories_consumed = Column(Integer, nullable=True)
    sleep_hours = Column(Float, nullable=True)
    mood = Column(String(50), nullable=True)

    notes = Column(Text, nullable=True)
    device_id = Column(String(100), nullable=True)
    device_reading_raw = Column(Text, nullable=True)

    is_flagged = Column(Boolean, default=False)
    flag_reason = Column(String(200), nullable=True)
    reviewed_by = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_self_monitor_patient", "patient_id"),
        Index("ix_cc_self_monitor_metric", "metric_type"),
        Index("ix_cc_self_monitor_time", "recorded_at"),
        Index("ix_cc_self_monitor_flagged", "is_flagged"),
        {"extend_existing": True},
    )
