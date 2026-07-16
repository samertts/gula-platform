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
from app.care_continuum.enums import PregnancyStatus


class PregnancyRecord(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_pregnancy_records"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)

    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)
    practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=True, index=True)

    status = Column(SAEnum(PregnancyStatus), nullable=False, default=PregnancyStatus.FIRST_TRIMESTER)
    parity = Column(Integer, nullable=True)
    gravida = Column(Integer, nullable=True)
    live_births = Column(Integer, nullable=True)
    stillbirths = Column(Integer, nullable=True)
    miscarriages = Column(Integer, nullable=True)
    previous_c_sections = Column(Integer, nullable=True)

    last_menstrual_period = Column(Date, nullable=True)
    estimated_delivery_date = Column(Date, nullable=True)
    gestational_age_weeks = Column(Integer, nullable=True)
    gestational_age_days = Column(Integer, nullable=True)

    blood_group = Column(String(5), nullable=True)
    rh_factor = Column(String(10), nullable=True)
    hb_level = Column(Float, nullable=True)

    high_risk = Column(Boolean, default=False)
    risk_factors = Column(JSON, nullable=True)
    complications = Column(JSON, nullable=True)
    chronic_conditions = Column(JSON, nullable=True)

    registration_date = Column(DateTime(timezone=True), nullable=False)
    booked_for_delivery = Column(Boolean, default=False)
    delivery_facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="SET NULL"), nullable=True)

    expected_delivery_place = Column(String(200), nullable=True)
    birth_plan = Column(JSON, nullable=True)
    partner_name = Column(String(200), nullable=True)
    partner_phone = Column(String(20), nullable=True)
    emergency_contact = Column(Text, nullable=True)

    anc_visits_completed = Column(Integer, default=0)
    anc_visits_required = Column(Integer, default=8)
    is_completed = Column(Boolean, default=False)
    delivery_date = Column(DateTime(timezone=True), nullable=True)
    outcome = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_pregnancy_patient", "patient_id"),
        Index("ix_cc_pregnancy_status", "status"),
        Index("ix_cc_pregnancy_edd", "estimated_delivery_date"),
        Index("ix_cc_pregnancy_registration", "registration_date"),
        {"extend_existing": True},
    )


class AntenatalCareVisit(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_antenatal_care_visits"

    pregnancy_id = Column(String(26), ForeignKey("cc_pregnancy_records.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)

    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)
    practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=True, index=True)

    visit_number = Column(Integer, nullable=False)
    visit_date = Column(DateTime(timezone=True), nullable=False)
    gestational_age_weeks = Column(Integer, nullable=True)

    weight_kg = Column(Float, nullable=True)
    height_cm = Column(Float, nullable=True)
    bmi = Column(Float, nullable=True)
    blood_pressure_systolic = Column(Integer, nullable=True)
    blood_pressure_diastolic = Column(Integer, nullable=True)
    fundal_height_cm = Column(Float, nullable=True)
    fetal_heart_rate = Column(Integer, nullable=True)
    fetal_presentation = Column(String(50), nullable=True)
    uterine_contractions = Column(Boolean, nullable=True)

    urine_test_done = Column(Boolean, default=False)
    urine_protein = Column(String(20), nullable=True)
    urine_glucose = Column(String(20), nullable=True)
    hemoglobin_gdl = Column(Float, nullable=True)
    blood_glucose = Column(Float, nullable=True)
    syphilis_test = Column(String(20), nullable=True)
    hiv_test = Column(String(20), nullable=True)
    hepatitis_b_test = Column(String(20), nullable=True)

    ultrasound_done = Column(Boolean, default=False)
    ultrasound_findings = Column(Text, nullable=True)

    tetanus_toxoid_dose = Column(Integer, nullable=True)
    iron_supplementation = Column(Boolean, default=False)
    folic_acid = Column(Boolean, default=False)
    calcium_supplementation = Column(Boolean, default=False)

    danger_signs_screened = Column(Boolean, default=False)
    danger_signs_present = Column(JSON, nullable=True)
    health_education_given = Column(JSON, nullable=True)
    complaints = Column(Text, nullable=True)
    examination_findings = Column(Text, nullable=True)
    diagnosis = Column(Text, nullable=True)
    treatment = Column(Text, nullable=True)
    referral_made = Column(Boolean, default=False)
    referral_reason = Column(Text, nullable=True)
    next_visit_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_anc_visit_pregnancy", "pregnancy_id"),
        Index("ix_cc_anc_visit_patient", "patient_id"),
        Index("ix_cc_anc_visit_date", "visit_date"),
        Index("ix_cc_anc_visit_number", "pregnancy_id", "visit_number", unique=True),
        {"extend_existing": True},
    )


class DeliveryRecord(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_delivery_records"

    pregnancy_id = Column(String(26), ForeignKey("cc_pregnancy_records.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)

    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=False, index=True)
    attending_practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=True, index=True)
    midwife_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True)

    delivery_date = Column(DateTime(timezone=True), nullable=False)
    delivery_type = Column(String(50), nullable=False)

    labor_duration_hours = Column(Float, nullable=True)
    induction = Column(Boolean, default=False)
    induction_method = Column(String(100), nullable=True)
    analgesia_used = Column(String(200), nullable=True)
    episiotomy = Column(Boolean, default=False)
    perineal_tear_degree = Column(String(20), nullable=True)
    blood_loss_ml = Column(Integer, nullable=True)
    placenta_complete = Column(Boolean, default=True)
    cord_clamping_delayed = Column(Boolean, default=True)
    skin_to_skin = Column(Boolean, default=True)

    complications = Column(JSON, nullable=True)
    maternal_outcome = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_delivery_pregnancy", "pregnancy_id"),
        Index("ix_cc_delivery_patient", "patient_id"),
        Index("ix_cc_delivery_date", "delivery_date"),
        Index("ix_cc_delivery_type", "delivery_type"),
        {"extend_existing": True},
    )


class PostnatalCareVisit(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_postnatal_care_visits"

    pregnancy_id = Column(String(26), ForeignKey("cc_pregnancy_records.id", ondelete="CASCADE"), nullable=True, index=True)
    delivery_id = Column(String(26), ForeignKey("cc_delivery_records.id", ondelete="SET NULL"), nullable=True, index=True)
    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)

    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)
    practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=True, index=True)

    visit_number = Column(Integer, nullable=False)
    visit_date = Column(DateTime(timezone=True), nullable=False)
    days_postpartum = Column(Integer, nullable=True)

    maternal_weight_kg = Column(Float, nullable=True)
    blood_pressure_systolic = Column(Integer, nullable=True)
    blood_pressure_diastolic = Column(Integer, nullable=True)
    temperature_celsius = Column(Float, nullable=True)
    pulse_rate = Column(Integer, nullable=True)
    uterine_involution = Column(String(100), nullable=True)
    lochia_description = Column(String(200), nullable=True)
    perineal_wound_healing = Column(String(100), nullable=True)
    c_section_wound_healing = Column(String(100), nullable=True)
    breast_exam_findings = Column(Text, nullable=True)

    breast_feeding_established = Column(Boolean, nullable=True)
    breastfeeding_difficulties = Column(Text, nullable=True)
    family_planning_discussed = Column(Boolean, default=False)
    family_planning_method = Column(String(100), nullable=True)
    contraception_provided = Column(Boolean, default=False)
    contraception_method = Column(String(100), nullable=True)

    danger_signs_screened = Column(Boolean, default=False)
    danger_signs_present = Column(JSON, nullable=True)
    mental_health_screened = Column(Boolean, default=False)
    postpartum_depression_score = Column(Integer, nullable=True)
    complaints = Column(Text, nullable=True)
    examination_findings = Column(Text, nullable=True)
    treatment = Column(Text, nullable=True)
    referral_made = Column(Boolean, default=False)
    referral_reason = Column(Text, nullable=True)
    next_visit_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_pnc_visit_pregnancy", "pregnancy_id"),
        Index("ix_cc_pnc_visit_patient", "patient_id"),
        Index("ix_cc_pnc_visit_date", "visit_date"),
        Index("ix_cc_pnc_visit_number", "pregnancy_id", "visit_number", unique=True),
        {"extend_existing": True},
    )


class GrowthMonitoring(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_growth_monitoring"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)

    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)
    practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=True, index=True)

    measurement_date = Column(DateTime(timezone=True), nullable=False)
    age_months = Column(Integer, nullable=True)

    weight_kg = Column(Float, nullable=True)
    height_cm = Column(Float, nullable=True)
    head_circumference_cm = Column(Float, nullable=True)
    mid_upper_arm_circumference_cm = Column(Float, nullable=True)
    bmi = Column(Float, nullable=True)

    weight_for_age_z_score = Column(Float, nullable=True)
    height_for_age_z_score = Column(Float, nullable=True)
    weight_for_height_z_score = Column(Float, nullable=True)
    bmi_for_age_z_score = Column(Float, nullable=True)
    head_circumference_z_score = Column(Float, nullable=True)

    nutritional_status = Column(String(50), nullable=True)
    stunting = Column(Boolean, nullable=True)
    wasting = Column(Boolean, nullable=True)
    underweight = Column(Boolean, nullable=True)
    overweight = Column(Boolean, nullable=True)
    obesity = Column(Boolean, nullable=True)

    who_growth_percentile = Column(Float, nullable=True)
    growth_trend = Column(String(50), nullable=True)
    feeding_type = Column(String(50), nullable=True)
    deworming_given = Column(Boolean, default=False)
    vitamin_a_supplement = Column(Boolean, default=False)
    iron_supplement = Column(Boolean, default=False)

    concerns = Column(Text, nullable=True)
    intervention = Column(Text, nullable=True)
    referral_made = Column(Boolean, default=False)
    follow_up_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_growth_patient", "patient_id"),
        Index("ix_cc_growth_date", "measurement_date"),
        Index("ix_cc_growth_age", "age_months"),
        {"extend_existing": True},
    )


class BreastfeedingRecord(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_breastfeeding_records"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    pregnancy_id = Column(String(26), ForeignKey("cc_pregnancy_records.id", ondelete="SET NULL"), nullable=True, index=True)

    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)
    practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=True, index=True)

    assessment_date = Column(DateTime(timezone=True), nullable=False)
    is_currently_breastfeeding = Column(Boolean, nullable=True)

    initiation_time_hours = Column(Float, nullable=True)
    exclusive_breastfeeding = Column(Boolean, nullable=True)
    duration_weeks = Column(Integer, nullable=True)
    frequency_per_day = Column(Integer, nullable=True)
    bottle_feeding = Column(Boolean, default=False)
    formula_feeding = Column(Boolean, default=False)
    complementary_feeding_started = Column(Boolean, default=False)
    complementary_feeding_age_months = Column(Integer, nullable=True)

    latch_assessment = Column(String(100), nullable=True)
    milk_supply_adequate = Column(Boolean, nullable=True)
    sore_nipples = Column(Boolean, default=False)
    mastitis = Column(Boolean, default=False)
    engorgement = Column(Boolean, default=False)
    tongue_tie = Column(Boolean, nullable=True)

    maternal_nutrition_advice = Column(Boolean, default=False)
    breastfeeding_education = Column(Boolean, default=False)
    support_referral = Column(Boolean, default=False)
    difficulties = Column(Text, nullable=True)
    plan = Column(Text, nullable=True)
    next_follow_up = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_breastfeeding_patient", "patient_id"),
        Index("ix_cc_breastfeeding_date", "assessment_date"),
        {"extend_existing": True},
    )


class ChildDevelopmentRecord(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_child_development_records"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)
    pregnancy_id = Column(String(26), ForeignKey("cc_pregnancy_records.id", ondelete="SET NULL"), nullable=True, index=True)

    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)
    practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=True, index=True)

    assessment_date = Column(DateTime(timezone=True), nullable=False)
    age_months = Column(Integer, nullable=True)

    gross_motor = Column(JSON, nullable=True)
    fine_motor = Column(JSON, nullable=True)
    language = Column(JSON, nullable=True)
    social_emotional = Column(JSON, nullable=True)
    cognitive = Column(JSON, nullable=True)

    developmental_age_months = Column(Integer, nullable=True)
    developmental_quotient = Column(Float, nullable=True)
    developmental_screening_tool = Column(String(100), nullable=True)
    screening_score = Column(Float, nullable=True)
    screening_result = Column(String(50), nullable=True)
    developmental_delay_suspected = Column(Boolean, default=False)
    delay_domain = Column(String(100), nullable=True)

    hearing_screening_done = Column(Boolean, default=False)
    hearing_screening_result = Column(String(50), nullable=True)
    vision_screening_done = Column(Boolean, default=False)
    vision_screening_result = Column(String(50), nullable=True)
    autism_screening_done = Column(Boolean, default=False)
    autism_screening_score = Column(Integer, nullable=True)
    autism_screening_result = Column(String(50), nullable=True)

    early_intervention_referral = Column(Boolean, default=False)
    early_intervention_services = Column(JSON, nullable=True)
    parent_guidance_provided = Column(Boolean, default=False)
    concerns = Column(Text, nullable=True)
    plan = Column(Text, nullable=True)
    follow_up_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_child_dev_patient", "patient_id"),
        Index("ix_cc_child_dev_date", "assessment_date"),
        Index("ix_cc_child_dev_age", "age_months"),
        {"extend_existing": True},
    )
