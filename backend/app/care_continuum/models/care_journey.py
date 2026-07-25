from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import Enum as SAEnum

from app.care_continuum.base import CareContinuumTenantAuditEntity
from app.care_continuum.enums import CareProgramStatus, FollowUpStatus


class CareJourney(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_care_journeys"

    patient_id = Column(
        String(26),
        ForeignKey("national_patients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    citizen_id = Column(
        String(26),
        ForeignKey("national_citizens.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    episode_of_care_id = Column(
        String(26),
        ForeignKey("national_episodes_of_care.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    care_coordinator_id = Column(
        String(26),
        ForeignKey("national_practitioners.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    organization_id = Column(
        String(26),
        ForeignKey("national_organizations.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(SAEnum(CareProgramStatus), nullable=False, default=CareProgramStatus.ACTIVE)

    journey_type = Column(String(100), nullable=False)
    diagnosis_code = Column(String(50), nullable=True)
    icd10_code = Column(String(20), nullable=True)
    diagnosis_description = Column(Text, nullable=True)

    milestones = Column(JSON, nullable=True)
    care_team = Column(JSON, nullable=True)
    goals = Column(JSON, nullable=True)
    outcomes = Column(JSON, nullable=True)

    barriers_to_care = Column(JSON, nullable=True)
    social_determinants = Column(JSON, nullable=True)
    patient_feedback = Column(Text, nullable=True)
    patient_satisfaction_score = Column(Integer, nullable=True)

    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_care_journey_patient", "patient_id"),
        Index("ix_cc_care_journey_coordinator", "care_coordinator_id"),
        Index("ix_cc_care_journey_status", "status"),
        {"extend_existing": True},
    )


class FollowUpPlan(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_follow_up_plans"

    patient_id = Column(
        String(26),
        ForeignKey("national_patients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    citizen_id = Column(
        String(26),
        ForeignKey("national_citizens.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    encounter_id = Column(
        String(26),
        ForeignKey("national_encounters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    care_journey_id = Column(
        String(26),
        ForeignKey("cc_care_journeys.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    practitioner_id = Column(
        String(26),
        ForeignKey("national_practitioners.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    facility_id = Column(
        String(26),
        ForeignKey("national_facilities.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    plan_date = Column(DateTime(timezone=True), nullable=False)
    follow_up_date = Column(DateTime(timezone=True), nullable=False)
    follow_up_type = Column(String(100), nullable=False)

    status = Column(SAEnum(FollowUpStatus), nullable=False, default=FollowUpStatus.SCHEDULED)
    priority = Column(String(20), default="routine")

    instructions = Column(Text, nullable=True)
    clinical_checks_required = Column(JSON, nullable=True)
    medications_to_review = Column(JSON, nullable=True)
    tests_required = Column(JSON, nullable=True)
    referrals_required = Column(JSON, nullable=True)

    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime(timezone=True), nullable=True)
    reminder_channel = Column(String(50), nullable=True)

    completed_at = Column(DateTime(timezone=True), nullable=True)
    completion_notes = Column(Text, nullable=True)
    outcome = Column(String(200), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_reason = Column(Text, nullable=True)

    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_follow_up_patient", "patient_id"),
        Index("ix_cc_follow_up_practitioner", "practitioner_id"),
        Index("ix_cc_follow_up_date", "follow_up_date"),
        Index("ix_cc_follow_up_status", "status"),
        {"extend_existing": True},
    )


class CareCoordination(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_care_coordination"

    patient_id = Column(
        String(26),
        ForeignKey("national_patients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    citizen_id = Column(
        String(26),
        ForeignKey("national_citizens.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    care_journey_id = Column(
        String(26),
        ForeignKey("cc_care_journeys.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    coordinator_id = Column(
        String(26),
        ForeignKey("national_practitioners.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    organization_id = Column(
        String(26),
        ForeignKey("national_organizations.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    coordination_type = Column(String(100), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), nullable=False, default="active")

    involved_providers = Column(JSON, nullable=True)
    involved_facilities = Column(JSON, nullable=True)
    communication_log = Column(JSON, nullable=True)
    shared_care_plan = Column(JSON, nullable=True)

    appointments_booked = Column(JSON, nullable=True)
    referrals_placed = Column(JSON, nullable=True)
    tests_coordinated = Column(JSON, nullable=True)

    barriers_identified = Column(JSON, nullable=True)
    interventions_done = Column(JSON, nullable=True)
    outcomes = Column(JSON, nullable=True)

    next_review_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_coordination_patient", "patient_id"),
        Index("ix_cc_coordination_coordinator", "coordinator_id"),
        Index("ix_cc_coordination_status", "status"),
        {"extend_existing": True},
    )


class TransitionsOfCare(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_transitions_of_care"

    patient_id = Column(
        String(26),
        ForeignKey("national_patients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    citizen_id = Column(
        String(26),
        ForeignKey("national_citizens.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    admission_id = Column(
        String(26),
        ForeignKey("national_admissions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    discharge_id = Column(
        String(26),
        ForeignKey("national_discharges.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    encounter_id = Column(
        String(26),
        ForeignKey("national_encounters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    transition_type = Column(String(100), nullable=False)
    transition_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(50), nullable=False, default="pending")

    from_facility_id = Column(
        String(26),
        ForeignKey("national_facilities.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    from_department_id = Column(
        String(26), ForeignKey("national_departments.id", ondelete="SET NULL"), nullable=True,
    )
    from_practitioner_id = Column(
        String(26),
        ForeignKey("national_practitioners.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    to_facility_id = Column(
        String(26),
        ForeignKey("national_facilities.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    to_department_id = Column(
        String(26), ForeignKey("national_departments.id", ondelete="SET NULL"), nullable=True,
    )
    to_practitioner_id = Column(
        String(26),
        ForeignKey("national_practitioners.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    discharge_summary_id = Column(String(26), nullable=True)
    medication_reconciliation_done = Column(Boolean, default=False)
    follow_up_appointment_made = Column(Boolean, default=False)
    follow_up_appointment_id = Column(
        String(26), ForeignKey("national_appointments.id", ondelete="SET NULL"), nullable=True,
    )

    handover_documents = Column(JSON, nullable=True)
    care_plan_transferred = Column(Boolean, default=False)
    equipment_needs_assessed = Column(Boolean, default=False)
    home_care_arranged = Column(Boolean, default=False)

    completed_at = Column(DateTime(timezone=True), nullable=True)
    outcome = Column(String(200), nullable=True)
    issues_encountered = Column(JSON, nullable=True)
    readmission_risk_score = Column(String(20), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_transitions_patient", "patient_id"),
        Index("ix_cc_transitions_from", "from_facility_id"),
        Index("ix_cc_transitions_to", "to_facility_id"),
        Index("ix_cc_transitions_date", "transition_date"),
        {"extend_existing": True},
    )


class ClinicalHandover(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_clinical_handovers"

    patient_id = Column(
        String(26),
        ForeignKey("national_patients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    citizen_id = Column(
        String(26),
        ForeignKey("national_citizens.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    encounter_id = Column(
        String(26),
        ForeignKey("national_encounters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    transition_id = Column(
        String(26),
        ForeignKey("cc_transitions_of_care.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    handover_date = Column(DateTime(timezone=True), nullable=False)
    handover_type = Column(String(100), nullable=False)

    from_practitioner_id = Column(
        String(26),
        ForeignKey("national_practitioners.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    to_practitioner_id = Column(
        String(26),
        ForeignKey("national_practitioners.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    clinical_summary = Column(Text, nullable=True)
    medications = Column(JSON, nullable=True)
    pending_results = Column(JSON, nullable=True)
    tasks_pending = Column(JSON, nullable=True)
    contingency_plans = Column(Text, nullable=True)
    code_status = Column(String(50), nullable=True)
    allergies = Column(JSON, nullable=True)

    is_verified = Column(Boolean, default=False)
    verified_by = Column(
        String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True,
    )
    verified_at = Column(DateTime(timezone=True), nullable=True)

    duration_minutes = Column(Integer, nullable=True)
    is_emergency_handover = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_handover_patient", "patient_id"),
        Index("ix_cc_handover_from", "from_practitioner_id"),
        Index("ix_cc_handover_to", "to_practitioner_id"),
        Index("ix_cc_handover_date", "handover_date"),
        {"extend_existing": True},
    )


class HomeCarePlan(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_home_care_plans"

    patient_id = Column(
        String(26),
        ForeignKey("national_patients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    citizen_id = Column(
        String(26),
        ForeignKey("national_citizens.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    care_journey_id = Column(
        String(26),
        ForeignKey("cc_care_journeys.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    practitioner_id = Column(
        String(26),
        ForeignKey("national_practitioners.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    facility_id = Column(
        String(26),
        ForeignKey("national_facilities.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    plan_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(SAEnum(CareProgramStatus), nullable=False, default=CareProgramStatus.ACTIVE)

    care_type = Column(String(100), nullable=False)
    diagnosis_code = Column(String(50), nullable=True)
    icd10_code = Column(String(20), nullable=True)

    visit_frequency = Column(String(100), nullable=True)
    visiting_practitioner_id = Column(
        String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True,
    )
    caregiver_instructions = Column(Text, nullable=True)

    medications = Column(JSON, nullable=True)
    wound_care = Column(Text, nullable=True)
    mobility_assistance = Column(Text, nullable=True)
    equipment_provided = Column(JSON, nullable=True)
    nursing_procedures = Column(JSON, nullable=True)
    rehabilitation_exercises = Column(JSON, nullable=True)

    emergency_contact_name = Column(String(200), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    primary_caregiver_name = Column(String(200), nullable=True)
    primary_caregiver_relation = Column(String(100), nullable=True)

    next_visit_date = Column(DateTime(timezone=True), nullable=True)
    review_date = Column(Date, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_home_care_patient", "patient_id"),
        Index("ix_cc_home_care_practitioner", "practitioner_id"),
        Index("ix_cc_home_care_status", "status"),
        {"extend_existing": True},
    )


class CommunityCareRecord(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_community_care_records"

    patient_id = Column(
        String(26),
        ForeignKey("national_patients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    citizen_id = Column(
        String(26),
        ForeignKey("national_citizens.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    facility_id = Column(
        String(26),
        ForeignKey("national_facilities.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    practitioner_id = Column(
        String(26),
        ForeignKey("national_practitioners.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    visit_date = Column(DateTime(timezone=True), nullable=False)
    visit_type = Column(String(100), nullable=False)

    location_latitude = Column(String(20), nullable=True)
    location_longitude = Column(String(20), nullable=True)
    location_address = Column(String(500), nullable=True)
    community_name = Column(String(200), nullable=True)
    catchment_area = Column(String(200), nullable=True)

    household_visit = Column(Boolean, default=False)
    household_id = Column(
        String(26), ForeignKey("national_families.id", ondelete="SET NULL"), nullable=True,
    )

    services_provided = Column(JSON, nullable=True)
    health_education_provided = Column(JSON, nullable=True)
    screening_done = Column(JSON, nullable=True)
    referrals_made = Column(JSON, nullable=True)

    environmental_observations = Column(JSON, nullable=True)
    social_concerns = Column(JSON, nullable=True)
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(Date, nullable=True)

    outcome = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_community_care_patient", "patient_id"),
        Index("ix_cc_community_care_date", "visit_date"),
        Index("ix_cc_community_care_type", "visit_type"),
        {"extend_existing": True},
    )
