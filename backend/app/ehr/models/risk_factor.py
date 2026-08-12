
from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy import Enum as SAEnum

from app.ehr.base import EHRBaseEntity
from app.ehr.enums import RiskLevel


class RiskFactorRecord(EHRBaseEntity):
    __tablename__ = "ehr_risk_factors"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="CASCADE"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)
    practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True, index=True)

    risk_type = Column(String(100), nullable=False, index=True)
    risk_level = Column(SAEnum(RiskLevel), nullable=True)

    score_name = Column(String(200), nullable=True)
    score_value = Column(Float, nullable=True)
    score_maximum = Column(Float, nullable=True)
    score_percent = Column(Float, nullable=True)
    score_version = Column(String(50), nullable=True)

    factors = Column(JSON, nullable=True)
    recommendations = Column(Text, nullable=True)

    assessment_date = Column(DateTime(timezone=True), nullable=False)
    next_assessment_date = Column(Date, nullable=True)

    is_high_risk = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_ehr_risk_patient", "patient_id", "risk_type"),
        Index("ix_ehr_risk_citizen", "citizen_id"),
        Index("ix_ehr_risk_encounter", "encounter_id"),
        Index("ix_ehr_risk_type", "risk_type", "patient_id"),
        Index("ix_ehr_risk_level", "risk_level"),
        Index("ix_ehr_risk_date", "assessment_date"),
        Index("ix_ehr_risk_not_deleted", "is_deleted", "patient_id"),
        {"extend_existing": True},
    )
