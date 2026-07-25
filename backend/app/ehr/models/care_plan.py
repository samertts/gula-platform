from sqlalchemy import JSON, Column, Date, ForeignKey, Index, Integer, String, Text
from sqlalchemy import Enum as SAEnum

from app.ehr.base import EHRBaseEntity
from app.ehr.enums import CarePlanStatus


class CarePlan(EHRBaseEntity):
    __tablename__ = "ehr_care_plans"

    patient_id = Column(
        String(26),
        ForeignKey("national_patients.id", ondelete="CASCADE"),
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
    practitioner_id = Column(
        String(26),
        ForeignKey("national_practitioners.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status = Column(SAEnum(CarePlanStatus), nullable=False, default=CarePlanStatus.DRAFT)
    intent = Column(String(50), nullable=False, default="plan")
    title = Column(String(300), nullable=False)
    title_ar = Column(String(300), nullable=True)
    description = Column(Text, nullable=True)

    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)

    category = Column(String(100), nullable=True)
    contributor = Column(JSON, nullable=True)
    supporting_info = Column(JSON, nullable=True)

    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_ehr_careplan_patient", "patient_id", "status"),
        Index("ix_ehr_careplan_citizen", "citizen_id"),
        Index("ix_ehr_careplan_practitioner", "practitioner_id"),
        Index("ix_ehr_careplan_period", "period_start", "period_end"),
        Index("ix_ehr_careplan_not_deleted", "is_deleted", "patient_id"),
        {"extend_existing": True},
    )


class CarePlanGoal(EHRBaseEntity):
    __tablename__ = "ehr_care_plan_goals"

    care_plan_id = Column(
        String(26), ForeignKey("ehr_care_plans.id", ondelete="CASCADE"), nullable=False, index=True,
    )

    description = Column(String(500), nullable=False)
    description_ar = Column(String(500), nullable=True)
    status = Column(String(50), nullable=False, default="in_progress")
    priority = Column(Integer, default=0)

    target_date = Column(Date, nullable=True)
    achievement_date = Column(Date, nullable=True)
    achievement_notes = Column(Text, nullable=True)

    outcome = Column(String(500), nullable=True)
    measured_by = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_ehr_goal_careplan", "care_plan_id"),
        Index("ix_ehr_goal_status", "status"),
        {"extend_existing": True},
    )


class CarePlanActivity(EHRBaseEntity):
    __tablename__ = "ehr_care_plan_activities"

    care_plan_id = Column(
        String(26), ForeignKey("ehr_care_plans.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    goal_id = Column(
        String(26),
        ForeignKey("ehr_care_plan_goals.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    activity_code = Column(String(50), nullable=True)
    activity_code_system = Column(String(20), nullable=True)
    description = Column(String(500), nullable=False)
    description_ar = Column(String(500), nullable=True)
    status = Column(String(50), nullable=False, default="not_started")

    scheduled_start = Column(Date, nullable=True)
    scheduled_end = Column(Date, nullable=True)
    actual_start = Column(Date, nullable=True)
    actual_end = Column(Date, nullable=True)

    performer = Column(String(200), nullable=True)
    performer_id = Column(
        String(26),
        ForeignKey("national_practitioners.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    location = Column(String(200), nullable=True)

    outcome = Column(String(500), nullable=True)
    progress_notes = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_ehr_activity_careplan", "care_plan_id"),
        Index("ix_ehr_activity_goal", "goal_id"),
        Index("ix_ehr_activity_status", "status"),
        {"extend_existing": True},
    )
