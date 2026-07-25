from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy import Enum as SAEnum

from app.ehr.base import EHRBaseEntity
from app.ehr.enums import TimelineEventType


class PatientTimelineEvent(EHRBaseEntity):
    __tablename__ = "ehr_patient_timeline"

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

    event_type = Column(SAEnum(TimelineEventType), nullable=False, index=True)
    event_date = Column(DateTime(timezone=True), nullable=False, index=True)

    source_type = Column(String(50), nullable=False)
    source_id = Column(String(26), nullable=False, index=True)

    title = Column(String(300), nullable=False)
    title_ar = Column(String(300), nullable=True)
    description = Column(Text, nullable=True)

    facility_id = Column(
        String(26),
        ForeignKey("national_facilities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    practitioner_id = Column(
        String(26),
        ForeignKey("national_practitioners.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    encounter_id = Column(
        String(26),
        ForeignKey("national_encounters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    severity = Column(String(50), nullable=True)
    is_highlighted = Column(Boolean, default=False)
    is_critical = Column(Boolean, default=False)

    icon = Column(String(50), nullable=True)
    color = Column(String(20), nullable=True)

    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_ehr_timeline_patient", "patient_id", "event_date"),
        Index("ix_ehr_timeline_citizen", "citizen_id"),
        Index("ix_ehr_timeline_type", "event_type", "event_date"),
        Index("ix_ehr_timeline_source", "source_type", "source_id"),
        Index("ix_ehr_timeline_facility", "facility_id"),
        Index("ix_ehr_timeline_critical", "is_critical", "event_date"),
        Index("ix_ehr_timeline_not_deleted", "is_deleted", "patient_id"),
        {"extend_existing": True},
    )
