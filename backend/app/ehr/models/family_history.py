from datetime import date, datetime

from app._compat import UTC
from app.ehr.base import EHRBaseEntity
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Index, Integer, String, Text


class FamilyHistoryRecord(EHRBaseEntity):
    __tablename__ = "ehr_family_history"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="CASCADE"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True, index=True)

    relationship = Column(String(50), nullable=False)
    relationship_detail = Column(String(200), nullable=True)
    relative_name = Column(String(200), nullable=True)
    relative_citizen_id = Column(String(26), nullable=True, index=True)

    condition_code = Column(String(50), nullable=True, index=True)
    condition_code_system = Column(String(20), nullable=True)
    condition_display = Column(String(300), nullable=False)
    condition_display_ar = Column(String(300), nullable=True)

    icd10_code = Column(String(20), nullable=True)
    icd10_description = Column(String(500), nullable=True)

    age_at_onset = Column(Integer, nullable=True)
    age_at_onset_unit = Column(String(20), default="years")
    onset_age_years = Column(Integer, nullable=True)

    is_deceased_due_to = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    recorded_date = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=True)

    __table_args__ = (
        Index("ix_ehr_famhist_patient", "patient_id"),
        Index("ix_ehr_famhist_citizen", "citizen_id"),
        Index("ix_ehr_famhist_condition", "condition_code"),
        Index("ix_ehr_famhist_relative", "relative_citizen_id"),
        Index("ix_ehr_famhist_not_deleted", "is_deleted", "patient_id"),
        {"extend_existing": True},
    )
