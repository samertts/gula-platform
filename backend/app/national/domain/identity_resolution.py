from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text

from app.national.base import AuditEntity


class IdentityResolution(AuditEntity):
    __tablename__ = "national_identity_resolutions"

    source_type = Column(String(50), nullable=False)
    source_id = Column(String(100), nullable=False)
    target_citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    target_patient_id = Column(String(26), nullable=True, index=True)

    method = Column(String(50), nullable=False)
    confidence_score = Column(Integer, nullable=True)
    match_details = Column(JSON, nullable=True)

    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(26), nullable=True)
    is_resolved = Column(Boolean, default=False)
    requires_review = Column(Boolean, default=True)

    review_notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_national_id_resolutions_source", "source_type", "source_id"),
        Index("ix_national_id_resolutions_target", "target_citizen_id"),
        Index("ix_national_id_resolutions_method", "method"),
        {"extend_existing": True},
    )
