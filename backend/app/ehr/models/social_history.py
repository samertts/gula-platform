from datetime import date, datetime

from app._compat import UTC
from app.ehr.base import EHRBaseEntity
from app.ehr.enums import AlcoholStatus, DisabilityType, SmokingStatus
from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Enum as SAEnum, ForeignKey, Index, String, Text


class SocialHistoryRecord(EHRBaseEntity):
    __tablename__ = "ehr_social_history"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="CASCADE"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)
    practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True, index=True)

    smoking_status = Column(SAEnum(SmokingStatus), nullable=True)
    smoking_pack_years = Column(Integer, nullable=True)
    smoking_quit_date = Column(Date, nullable=True)
    smoking_start_age = Column(Integer, nullable=True)
    smoking_frequency = Column(String(50), nullable=True)

    alcohol_status = Column(SAEnum(AlcoholStatus), nullable=True)
    alcohol_frequency = Column(String(100), nullable=True)
    alcohol_quit_date = Column(Date, nullable=True)
    alcohol_start_age = Column(Integer, nullable=True)

    occupation = Column(String(200), nullable=True)
    occupation_history = Column(JSON, nullable=True)
    occupational_hazards = Column(Text, nullable=True)

    disability_type = Column(SAEnum(DisabilityType), nullable=True)
    disability_detail = Column(String(500), nullable=True)
    disability_since = Column(Date, nullable=True)

    exercise_frequency = Column(String(50), nullable=True)
    diet_notes = Column(Text, nullable=True)
    lifestyle_factors = Column(JSON, nullable=True)

    recorded_date = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_ehr_social_patient", "patient_id"),
        Index("ix_ehr_social_citizen", "citizen_id"),
        Index("ix_ehr_social_encounter", "encounter_id"),
        Index("ix_ehr_social_smoking", "smoking_status"),
        Index("ix_ehr_social_not_deleted", "is_deleted", "patient_id"),
        {"extend_existing": True},
    )
