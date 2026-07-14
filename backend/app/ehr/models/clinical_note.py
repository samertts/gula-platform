from datetime import datetime

from app._compat import UTC
from app.ehr.base import EHRBaseEntity
from app.ehr.enums import ClinicalNoteType
from sqlalchemy import JSON, Boolean, Column, DateTime, Enum as SAEnum, ForeignKey, Index, Integer, String, Text


class ClinicalNote(EHRBaseEntity):
    __tablename__ = "ehr_clinical_notes"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="CASCADE"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)
    practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True, index=True)
    author_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True, index=True)

    note_type = Column(SAEnum(ClinicalNoteType), nullable=False)
    title = Column(String(300), nullable=False)
    title_ar = Column(String(300), nullable=True)

    content = Column(Text, nullable=False)
    content_format = Column(String(20), default="html")

    version = Column(Integer, default=1, nullable=False)
    prior_version_id = Column(String(26), ForeignKey("ehr_clinical_notes.id", ondelete="SET NULL"), nullable=True, index=True)
    superseded_by_id = Column(String(26), ForeignKey("ehr_clinical_notes.id", ondelete="SET NULL"), nullable=True, index=True)

    is_final = Column(Boolean, default=False)
    is_signed = Column(Boolean, default=False)
    is_amended = Column(Boolean, default=False)
    amendment_reason = Column(String(500), nullable=True)

    signed_by = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True)
    signed_at = Column(DateTime(timezone=True), nullable=True)

    cosigned_by = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True)
    cosigned_at = Column(DateTime(timezone=True), nullable=True)

    witnessed_by = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True)
    witnessed_at = Column(DateTime(timezone=True), nullable=True)

    electronic_signature = Column(Text, nullable=True)
    signature_hash = Column(String(128), nullable=True)

    authored_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="SET NULL"), nullable=True, index=True)
    department_id = Column(String(26), ForeignKey("national_departments.id", ondelete="SET NULL"), nullable=True, index=True)

    tags = Column(JSON, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_ehr_note_patient", "patient_id", "note_type"),
        Index("ix_ehr_note_citizen", "citizen_id"),
        Index("ix_ehr_note_encounter", "encounter_id"),
        Index("ix_ehr_note_author", "author_id"),
        Index("ix_ehr_note_practitioner", "practitioner_id"),
        Index("ix_ehr_note_type", "note_type"),
        Index("ix_ehr_note_authored", "authored_at"),
        Index("ix_ehr_note_final", "is_final", "is_deleted"),
        Index("ix_ehr_note_signed", "is_signed", "is_deleted"),
        Index("ix_ehr_note_facility", "facility_id"),
        {"extend_existing": True},
    )
