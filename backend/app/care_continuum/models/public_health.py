from app.care_continuum.base import CareContinuumTenantAuditEntity
from app.care_continuum.enums import CareProgramStatus, HealthProgramType
from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Enum as SAEnum, Float, ForeignKey, Index, Integer, String, Text


class HealthProgram(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_health_programs"

    program_type = Column(SAEnum(HealthProgramType), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    code = Column(String(50), nullable=True, unique=True, index=True)
    description = Column(Text, nullable=True)

    organization_id = Column(String(26), ForeignKey("national_organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)
    coordinator_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=True, index=True)

    status = Column(SAEnum(CareProgramStatus), nullable=False, default=CareProgramStatus.ACTIVE)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    target_population = Column(Text, nullable=True)
    target_geographic_area = Column(JSON, nullable=True)
    target_age_group_min = Column(Integer, nullable=True)
    target_age_group_max = Column(Integer, nullable=True)
    target_gender = Column(String(20), nullable=True)

    funding_source = Column(String(200), nullable=True)
    budget_amount = Column(Float, nullable=True)
    budget_currency = Column(String(10), default="IQD")

    kpis = Column(JSON, nullable=True)
    milestones = Column(JSON, nullable=True)
    outcomes = Column(JSON, nullable=True)
    evaluation_report = Column(Text, nullable=True)

    is_national_program = Column(Boolean, default=False)
    parent_program_id = Column(String(26), ForeignKey("cc_health_programs.id", ondelete="SET NULL"), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_health_program_type", "program_type"),
        Index("ix_cc_health_program_code", "code"),
        Index("ix_cc_health_program_org", "organization_id"),
        Index("ix_cc_health_program_status", "status"),
        {"extend_existing": True},
    )


class ScreeningCampaign(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_screening_campaigns"

    program_id = Column(String(26), ForeignKey("cc_health_programs.id", ondelete="CASCADE"), nullable=True, index=True)
    organization_id = Column(String(26), ForeignKey("national_organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)
    coordinator_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=True, index=True)

    campaign_name = Column(String(200), nullable=False)
    campaign_type = Column(String(100), nullable=False)
    screening_type = Column(String(100), nullable=False)

    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(SAEnum(CareProgramStatus), nullable=False, default=CareProgramStatus.ACTIVE)

    target_condition = Column(String(200), nullable=True)
    icd10_code = Column(String(20), nullable=True)
    screening_tool = Column(String(200), nullable=True)

    target_population = Column(Integer, nullable=True)
    total_screened = Column(Integer, default=0)
    total_positive = Column(Integer, default=0)
    total_referred = Column(Integer, default=0)
    total_confirmed = Column(Integer, default=0)

    locations = Column(JSON, nullable=True)
    teams = Column(JSON, nullable=True)
    equipment_used = Column(JSON, nullable=True)

    results_summary = Column(JSON, nullable=True)
    follow_up_plan = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_screening_campaign_program", "program_id"),
        Index("ix_cc_screening_campaign_type", "screening_type"),
        Index("ix_cc_screening_campaign_org", "organization_id"),
        Index("ix_cc_screening_campaign_date", "start_date"),
        {"extend_existing": True},
    )


class SchoolHealthVisit(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_school_health_visits"

    program_id = Column(String(26), ForeignKey("cc_health_programs.id", ondelete="SET NULL"), nullable=True, index=True)
    organization_id = Column(String(26), ForeignKey("national_organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)
    team_lead_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=True, index=True)

    school_name = Column(String(200), nullable=False)
    school_code = Column(String(50), nullable=True)
    school_address = Column(String(500), nullable=True)
    school_governorate = Column(String(100), nullable=True)
    school_district = Column(String(100), nullable=True)
    school_type = Column(String(50), nullable=True)
    grade_levels_covered = Column(JSON, nullable=True)

    visit_date = Column(DateTime(timezone=True), nullable=False)
    visit_type = Column(String(100), nullable=False)

    total_students_screened = Column(Integer, default=0)
    total_male = Column(Integer, default=0)
    total_female = Column(Integer, default=0)

    screening_types_done = Column(JSON, nullable=True)
    screenings_by_type = Column(JSON, nullable=True)
    positive_screens = Column(JSON, nullable=True)
    referrals_made = Column(Integer, default=0)
    referrals_by_condition = Column(JSON, nullable=True)

    vaccinations_given = Column(JSON, nullable=True)
    health_education_topics = Column(JSON, nullable=True)
    deworming_given = Column(Boolean, default=False)
    deworming_count = Column(Integer, nullable=True)
    vitamin_supplement_given = Column(Boolean, default=False)
    vitamin_supplement_count = Column(Integer, nullable=True)

    environmental_assessment = Column(JSON, nullable=True)
    water_sanitation_issues = Column(JSON, nullable=True)
    findings_summary = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    follow_up_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_school_health_visit_program", "program_id"),
        Index("ix_cc_school_health_visit_school", "school_name"),
        Index("ix_cc_school_health_visit_date", "visit_date"),
        {"extend_existing": True},
    )


class OccupationalHealthRecord(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_occupational_health_records"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)
    practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=True, index=True)

    employer_name = Column(String(200), nullable=True)
    employer_address = Column(String(500), nullable=True)
    occupation = Column(String(200), nullable=True)
    industry = Column(String(200), nullable=True)
    years_in_occupation = Column(Integer, nullable=True)
    employment_status = Column(String(50), nullable=True)
    work_schedule = Column(String(100), nullable=True)

    assessment_date = Column(DateTime(timezone=True), nullable=False)
    assessment_type = Column(String(100), nullable=False)

    workplace_hazards = Column(JSON, nullable=True)
    exposure_type = Column(String(100), nullable=True)
    exposure_duration_years = Column(Float, nullable=True)
    ppe_used = Column(Boolean, default=True)
    ppe_types = Column(JSON, nullable=True)

    physical_exam_findings = Column(Text, nullable=True)
    hearing_test_result = Column(JSON, nullable=True)
    vision_test_result = Column(JSON, nullable=True)
    lung_function_test = Column(JSON, nullable=True)
    blood_test_results = Column(JSON, nullable=True)
    dermatological_findings = Column(Text, nullable=True)

    occupational_injury = Column(Boolean, default=False)
    injury_type = Column(String(100), nullable=True)
    injury_date = Column(Date, nullable=True)
    injury_description = Column(Text, nullable=True)
    lost_work_days = Column(Integer, nullable=True)

    fitness_for_work = Column(String(50), nullable=True)
    restrictions = Column(Text, nullable=True)
    accommodations_recommended = Column(JSON, nullable=True)
    follow_up_required = Column(Boolean, default=False)
    next_assessment_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_occupational_health_patient", "patient_id"),
        Index("ix_cc_occupational_health_date", "assessment_date"),
        Index("ix_cc_occupational_health_industry", "industry"),
        {"extend_existing": True},
    )


class CommunityVisit(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_community_visits"

    program_id = Column(String(26), ForeignKey("cc_health_programs.id", ondelete="SET NULL"), nullable=True, index=True)
    organization_id = Column(String(26), ForeignKey("national_organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)
    visit_lead_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=True, index=True)

    visit_date = Column(DateTime(timezone=True), nullable=False)
    visit_type = Column(String(100), nullable=False)

    community_name = Column(String(200), nullable=True)
    catchment_area = Column(String(200), nullable=True)
    location_latitude = Column(String(20), nullable=True)
    location_longitude = Column(String(20), nullable=True)
    location_address = Column(String(500), nullable=True)

    total_households_visited = Column(Integer, default=0)
    total_individuals_screened = Column(Integer, default=0)
    total_male = Column(Integer, default=0)
    total_female = Column(Integer, default=0)
    total_children_under_5 = Column(Integer, default=0)
    total_pregnant_women = Column(Integer, default=0)
    total_elderly = Column(Integer, default=0)

    services_provided = Column(JSON, nullable=True)
    health_education_topics = Column(JSON, nullable=True)
    screenings_done = Column(JSON, nullable=True)
    vaccinations_given = Column(JSON, nullable=True)
    treatments_given = Column(JSON, nullable=True)
    referrals_made = Column(Integer, default=0)
    referrals_details = Column(JSON, nullable=True)

    environmental_observations = Column(JSON, nullable=True)
    social_concerns_identified = Column(JSON, nullable=True)
    community_health_issues = Column(JSON, nullable=True)
    findings_summary = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    follow_up_required = Column(Boolean, default=False)
    next_visit_date = Column(Date, nullable=True)
    team_members = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_community_visit_program", "program_id"),
        Index("ix_cc_community_visit_date", "visit_date"),
        Index("ix_cc_community_visit_community", "community_name"),
        {"extend_existing": True},
    )


class HealthPromotionActivity(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_health_promotion_activities"

    program_id = Column(String(26), ForeignKey("cc_health_programs.id", ondelete="SET NULL"), nullable=True, index=True)
    organization_id = Column(String(26), ForeignKey("national_organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)

    activity_date = Column(DateTime(timezone=True), nullable=False)
    activity_type = Column(String(100), nullable=False)
    topic = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    facilitator_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True)
    location = Column(String(500), nullable=True)
    venue_type = Column(String(100), nullable=True)

    target_audience = Column(String(200), nullable=True)
    total_participants = Column(Integer, default=0)
    total_male = Column(Integer, default=0)
    total_female = Column(Integer, default=0)
    age_group_children = Column(Integer, default=0)
    age_group_adults = Column(Integer, default=0)
    age_group_elderly = Column(Integer, default=0)

    materials_distributed = Column(JSON, nullable=True)
    topics_covered = Column(JSON, nullable=True)
    key_messages = Column(JSON, nullable=True)
    interactive_sessions = Column(Boolean, default=False)
    demonstration_done = Column(Boolean, default=False)
    q_and_a_session = Column(Boolean, default=False)

    feedback_received = Column(Text, nullable=True)
    participant_satisfaction = Column(Float, nullable=True)
    effectiveness_rating = Column(String(20), nullable=True)
    outcomes = Column(Text, nullable=True)
    follow_up_planned = Column(Boolean, default=False)
    next_activity_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_health_promotion_program", "program_id"),
        Index("ix_cc_health_promotion_date", "activity_date"),
        Index("ix_cc_health_promotion_topic", "topic"),
        {"extend_existing": True},
    )


class ProgramEnrollment(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_program_enrollments"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    program_id = Column(String(26), ForeignKey("cc_health_programs.id", ondelete="CASCADE"), nullable=False, index=True)
    screening_campaign_id = Column(String(26), ForeignKey("cc_screening_campaigns.id", ondelete="SET NULL"), nullable=True)

    enrolled_by = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=False, index=True)
    enrolled_at = Column(DateTime(timezone=True), nullable=False)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)

    status = Column(SAEnum(CareProgramStatus), nullable=False, default=CareProgramStatus.ACTIVE)
    enrollment_reason = Column(String(500), nullable=True)
    eligibility_criteria_met = Column(JSON, nullable=True)

    consented = Column(Boolean, default=True)
    consent_id = Column(String(26), ForeignKey("national_consents.id", ondelete="SET NULL"), nullable=True)
    withdrawn_at = Column(DateTime(timezone=True), nullable=True)
    withdrawal_reason = Column(Text, nullable=True)

    baseline_assessment = Column(JSON, nullable=True)
    progress_notes = Column(JSON, nullable=True)
    outcomes = Column(JSON, nullable=True)

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completed_by = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True)
    graduation_criteria_met = Column(Boolean, nullable=True)

    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_program_enrollment_patient", "patient_id"),
        Index("ix_cc_program_enrollment_program", "program_id"),
        Index("ix_cc_program_enrollment_status", "status"),
        Index("ix_cc_program_enrollment_patient_program", "patient_id", "program_id", unique=True),
        {"extend_existing": True},
    )
