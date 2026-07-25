from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text

from app._compat import UTC
from app.ehr.base import EHRBaseEntity


class ClinicalAttachment(EHRBaseEntity):
    __tablename__ = "ehr_clinical_attachments"

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
    uploaded_by = Column(
        String(26),
        ForeignKey("national_practitioners.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    source_type = Column(String(50), nullable=False)
    source_id = Column(String(26), nullable=False, index=True)

    file_name = Column(String(300), nullable=False)
    file_type = Column(String(100), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    storage_path = Column(String(500), nullable=True)
    storage_bucket = Column(String(100), nullable=True)
    content_hash = Column(String(128), nullable=True)
    mime_type = Column(String(100), nullable=True)

    caption = Column(String(500), nullable=True)
    caption_ar = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)

    is_watermarked = Column(Boolean, default=False)
    is_encrypted = Column(Boolean, default=False)
    is_confidential = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)

    category = Column(String(50), nullable=True)
    sort_order = Column(Integer, default=0)

    uploaded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    facility_id = Column(
        String(26),
        ForeignKey("national_facilities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    __table_args__ = (
        Index("ix_ehr_attachment_patient", "patient_id"),
        Index("ix_ehr_attachment_citizen", "citizen_id"),
        Index("ix_ehr_attachment_source", "source_type", "source_id"),
        Index("ix_ehr_attachment_encounter", "encounter_id"),
        Index("ix_ehr_attachment_uploader", "uploaded_by"),
        Index("ix_ehr_attachment_facility", "facility_id"),
        Index("ix_ehr_attachment_category", "category"),
        Index("ix_ehr_attachment_not_deleted", "is_deleted", "patient_id"),
        {"extend_existing": True},
    )
