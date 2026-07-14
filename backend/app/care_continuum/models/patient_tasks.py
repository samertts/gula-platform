from app.care_continuum.base import CareContinuumTenantAuditEntity
from app.care_continuum.enums import FollowUpStatus
from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Enum as SAEnum, ForeignKey, Index, Integer, String, Text


class PatientTask(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_patient_tasks"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)
    care_journey_id = Column(String(26), ForeignKey("cc_care_journeys.id", ondelete="SET NULL"), nullable=True, index=True)

    assigned_by = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=False, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    task_type = Column(String(100), nullable=False, index=True)
    category = Column(String(100), nullable=True)

    status = Column(SAEnum(FollowUpStatus), nullable=False, default=FollowUpStatus.SCHEDULED)
    priority = Column(String(20), default="routine")

    due_date = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completed_by = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True)
    completion_notes = Column(Text, nullable=True)
    outcome = Column(String(200), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_reason = Column(Text, nullable=True)

    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime(timezone=True), nullable=True)
    reminder_channel = Column(String(50), nullable=True)
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)

    is_patient_facing = Column(Boolean, default=True)
    requires_verification = Column(Boolean, default=False)
    verified_by = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    parent_task_id = Column(String(26), ForeignKey("cc_patient_tasks.id", ondelete="SET NULL"), nullable=True)
    related_task_ids = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_patient_task_patient", "patient_id"),
        Index("ix_cc_patient_task_type", "task_type"),
        Index("ix_cc_patient_task_status", "status"),
        Index("ix_cc_patient_task_due", "due_date"),
        Index("ix_cc_patient_task_assigner", "assigned_by"),
        {"extend_existing": True},
    )


class EducationalMaterialAssignment(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_educational_material_assignments"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    task_id = Column(String(26), ForeignKey("cc_patient_tasks.id", ondelete="SET NULL"), nullable=True, index=True)

    assigned_by = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=False, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)

    material_title = Column(String(200), nullable=False)
    material_type = Column(String(100), nullable=False)
    material_url = Column(String(500), nullable=True)
    language = Column(String(10), default="ar")
    content_summary = Column(Text, nullable=True)
    topics = Column(JSON, nullable=True)

    assigned_date = Column(DateTime(timezone=True), nullable=False)
    due_date = Column(Date, nullable=True)
    status = Column(SAEnum(FollowUpStatus), nullable=False, default=FollowUpStatus.SCHEDULED)

    delivery_channel = Column(String(50), nullable=True)
    format = Column(String(50), nullable=True)
    estimated_read_time_minutes = Column(Integer, nullable=True)

    viewed = Column(Boolean, default=False)
    viewed_at = Column(DateTime(timezone=True), nullable=True)
    time_spent_seconds = Column(Integer, nullable=True)
    comprehension_quiz_score = Column(Float, nullable=True)
    quiz_passed = Column(Boolean, nullable=True)

    feedback = Column(Text, nullable=True)
    discussed_with_practitioner = Column(Boolean, default=False)
    discussed_at = Column(DateTime(timezone=True), nullable=True)
    follow_up_needed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_edu_material_patient", "patient_id"),
        Index("ix_cc_edu_material_task", "task_id"),
        Index("ix_cc_edu_material_type", "material_type"),
        {"extend_existing": True},
    )


class SelfFollowUpTask(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_self_follow_up_tasks"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    parent_task_id = Column(String(26), ForeignKey("cc_patient_tasks.id", ondelete="SET NULL"), nullable=True, index=True)

    created_by = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=False, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    task_type = Column(String(100), nullable=False)
    category = Column(String(100), nullable=True)

    status = Column(SAEnum(FollowUpStatus), nullable=False, default=FollowUpStatus.SCHEDULED)

    scheduled_date = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completion_notes = Column(Text, nullable=True)
    outcome = Column(String(200), nullable=True)

    self_reported_data = Column(JSON, nullable=True)
    adherence_level = Column(String(50), nullable=True)
    barriers_encountered = Column(JSON, nullable=True)
    patient_feedback = Column(Text, nullable=True)
    needs_follow_up = Column(Boolean, default=False)
    follow_up_scheduled = Column(Boolean, default=False)
    follow_up_date = Column(Date, nullable=True)

    reminder_channel = Column(String(50), nullable=True)
    reminder_frequency = Column(String(50), nullable=True)
    reminder_count = Column(Integer, default=0)

    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String(100), nullable=True)
    recurrence_end_date = Column(Date, nullable=True)

    verified_by = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verification_notes = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_self_follow_up_patient", "patient_id"),
        Index("ix_cc_self_follow_up_type", "task_type"),
        Index("ix_cc_self_follow_up_status", "status"),
        Index("ix_cc_self_follow_up_date", "scheduled_date"),
        {"extend_existing": True},
    )
