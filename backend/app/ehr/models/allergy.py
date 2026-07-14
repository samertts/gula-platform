from datetime import date

from app.ehr.base import EHRBaseEntity
from app.ehr.enums import AllergySeverity, AllergyStatus
from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Enum as SAEnum, ForeignKey, Index, String, Text


class AllergyIntolerance(EHRBaseEntity):
    __tablename__ = "ehr_allergies"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="CASCADE"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)
    practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True, index=True)

    allergy_type = Column(String(50), nullable=True)
    category = Column(String(50), nullable=True)
    criticality = Column(String(50), nullable=True)

    code = Column(String(50), nullable=True, index=True)
    code_system = Column(String(20), nullable=True)
    code_display = Column(String(300), nullable=False)
    code_display_ar = Column(String(300), nullable=True)

    severity = Column(SAEnum(AllergySeverity), nullable=True)
    status = Column(SAEnum(AllergyStatus), nullable=False, default=AllergyStatus.ACTIVE)
    verification_status = Column(String(50), nullable=True)

    reaction = Column(String(500), nullable=True)
    reaction_details = Column(JSON, nullable=True)
    onset_date = Column(Date, nullable=True)
    recorded_date = Column(DateTime(timezone=True), nullable=True)

    last_occurrence_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_ehr_allergy_patient", "patient_id", "status"),
        Index("ix_ehr_allergy_citizen", "citizen_id"),
        Index("ix_ehr_allergy_code", "code"),
        Index("ix_ehr_allergy_severity", "severity"),
        Index("ix_ehr_allergy_not_deleted", "is_deleted", "patient_id"),
        {"extend_existing": True},
    )
