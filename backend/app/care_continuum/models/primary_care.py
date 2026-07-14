from app.care_continuum.base import CareContinuumTenantAuditEntity
from app.care_continuum.enums import FollowUpStatus
from app.national.enums import EncounterType
from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Enum as SAEnum, Float, ForeignKey, Index, Integer, String, Text


class PrimaryCareEncounter(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_primary_care_encounters"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)

    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)
    clinic_id = Column(String(26), ForeignKey("national_clinics.id", ondelete="SET NULL"), nullable=True, index=True)
    department_id = Column(String(26), ForeignKey("national_departments.id", ondelete="SET NULL"), nullable=True, index=True)

    practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=True, index=True)

    encounter_type = Column(SAEnum(EncounterType), nullable=False)
    encounter_date = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, nullable=True)

    chief_complaint = Column(String(500), nullable=True)
    presenting_complaint = Column(Text, nullable=True)
    history_of_presenting_illness = Column(Text, nullable=True)

    vital_signs = Column(JSON, nullable=True)
    findings = Column(Text, nullable=True)
    assessment = Column(Text, nullable=True)
    diagnosis_code = Column(String(50), nullable=True)
    icd10_code = Column(String(20), nullable=True)
    diagnosis_description = Column(Text, nullable=True)

    treatment_plan = Column(Text, nullable=True)
    medications_prescribed = Column(JSON, nullable=True)
    procedures_done = Column(JSON, nullable=True)
    lab_orders = Column(JSON, nullable=True)
    imaging_orders = Column(JSON, nullable=True)

    is_telehealth = Column(Boolean, default=False)
    is_emergency = Column(Boolean, default=False)
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(DateTime(timezone=True), nullable=True)
    follow_up_status = Column(SAEnum(FollowUpStatus), nullable=True)

    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_primary_care_patient", "patient_id"),
        Index("ix_cc_primary_care_facility", "facility_id"),
        Index("ix_cc_primary_care_date", "encounter_date"),
        Index("ix_cc_primary_care_practitioner", "practitioner_id"),
        {"extend_existing": True},
    )


class FamilyMedicineRecord(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_family_medicine_records"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    family_id = Column(String(26), ForeignKey("national_families.id", ondelete="SET NULL"), nullable=True, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)

    practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=False, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)

    record_date = Column(DateTime(timezone=True), nullable=False)
    family_history = Column(JSON, nullable=True)
    social_history = Column(JSON, nullable=True)
    lifestyle_factors = Column(JSON, nullable=True)
    occupational_exposures = Column(JSON, nullable=True)

    is_index_patient_for_family = Column(Boolean, default=False)
    relationship_to_head = Column(String(50), nullable=True)
    household_size = Column(Integer, nullable=True)
    housing_conditions = Column(Text, nullable=True)
    water_source = Column(String(100), nullable=True)
    sanitation_type = Column(String(100), nullable=True)

    chronic_disease_screening = Column(JSON, nullable=True)
    risk_factors = Column(JSON, nullable=True)
    health_education_provided = Column(JSON, nullable=True)
    referrals_made = Column(JSON, nullable=True)

    follow_up_plan = Column(Text, nullable=True)
    next_visit_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_family_medicine_patient", "patient_id"),
        Index("ix_cc_family_medicine_family", "family_id"),
        Index("ix_cc_family_medicine_practitioner", "practitioner_id"),
        {"extend_existing": True},
    )


class CommunityClinicRecord(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_community_clinic_records"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)

    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)
    clinic_id = Column(String(26), ForeignKey("national_clinics.id", ondelete="SET NULL"), nullable=True, index=True)

    practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=True, index=True)

    visit_date = Column(DateTime(timezone=True), nullable=False)
    visit_reason = Column(String(500), nullable=True)
    complaint = Column(Text, nullable=True)
    examination_findings = Column(Text, nullable=True)
    diagnosis = Column(Text, nullable=True)

    treatment_given = Column(Text, nullable=True)
    medications_prescribed = Column(JSON, nullable=True)
    vaccinations_given = Column(JSON, nullable=True)
    health_education = Column(Text, nullable=True)

    is_first_visit = Column(Boolean, default=False)
    is_follow_up = Column(Boolean, default=False)
    is_referral_from_hospital = Column(Boolean, default=False)
    referral_source = Column(String(200), nullable=True)

    follow_up_date = Column(Date, nullable=True)
    outcome = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_community_clinic_patient", "patient_id"),
        Index("ix_cc_community_clinic_facility", "facility_id"),
        Index("ix_cc_community_clinic_date", "visit_date"),
        {"extend_existing": True},
    )


class PreventiveCareRecord(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_preventive_care_records"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=True, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)

    service_date = Column(DateTime(timezone=True), nullable=False)
    service_type = Column(String(100), nullable=False)

    is_age_appropriate = Column(Boolean, default=True)
    is_risk_based = Column(Boolean, default=False)
    risk_factor = Column(String(200), nullable=True)

    screening_type = Column(String(100), nullable=True)
    screening_result = Column(String(100), nullable=True)
    screening_details = Column(JSON, nullable=True)

    counseling_provided = Column(JSON, nullable=True)
    immunization_updated = Column(Boolean, default=False)
    chemoprophylaxis_given = Column(Boolean, default=False)
    chemoprophylaxis_details = Column(Text, nullable=True)

    due_date_for_next = Column(Date, nullable=True)
    interval_months = Column(Integer, nullable=True)
    is_completed = Column(Boolean, default=False)
    outcome = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_preventive_care_patient", "patient_id"),
        Index("ix_cc_preventive_care_type", "service_type"),
        Index("ix_cc_preventive_care_date", "service_date"),
        {"extend_existing": True},
    )


class HealthAssessment(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_health_assessments"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)
    practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=True, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)

    assessment_date = Column(DateTime(timezone=True), nullable=False)
    assessment_type = Column(String(100), nullable=False)

    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    bmi = Column(Float, nullable=True)
    bmi_percentile = Column(Float, nullable=True)
    waist_circumference_cm = Column(Float, nullable=True)
    head_circumference_cm = Column(Float, nullable=True)

    blood_pressure_systolic = Column(Integer, nullable=True)
    blood_pressure_diastolic = Column(Integer, nullable=True)
    heart_rate = Column(Integer, nullable=True)
    respiratory_rate = Column(Integer, nullable=True)
    temperature_celsius = Column(Float, nullable=True)
    oxygen_saturation = Column(Float, nullable=True)
    blood_glucose = Column(Float, nullable=True)

    nutritional_status = Column(String(100), nullable=True)
    developmental_screening = Column(JSON, nullable=True)
    mental_health_screening = Column(JSON, nullable=True)
    functional_status = Column(JSON, nullable=True)
    fall_risk = Column(String(50), nullable=True)
    pain_assessment = Column(JSON, nullable=True)

    overall_health_score = Column(Integer, nullable=True)
    risk_category = Column(String(50), nullable=True)
    recommendations = Column(Text, nullable=True)
    care_plan_recommended = Column(Boolean, default=False)
    follow_up_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_health_assessment_patient", "patient_id"),
        Index("ix_cc_health_assessment_date", "assessment_date"),
        Index("ix_cc_health_assessment_type", "assessment_type"),
        {"extend_existing": True},
    )
