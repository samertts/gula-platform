from sqlalchemy import JSON, Column, DateTime, ForeignKey, Index, String, Text

from app.national.base import TenantAuditEntity


class AdvanceDirective(TenantAuditEntity):
    __tablename__ = "national_advance_directives"

    patient_id = Column(
        String(26),
        ForeignKey("national_patients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    citizen_id = Column(
        String(26),
        ForeignKey("national_citizens.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    directive_type = Column(String(50), nullable=False)
    status = Column(String(20), default="active")

    title = Column(String(300), nullable=True)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)

    witness_name = Column(String(200), nullable=True)
    witness_relationship = Column(String(100), nullable=True)
    witness_signature = Column(Text, nullable=True)

    legal_representative_id = Column(String(26), nullable=True)
    legal_representative_name = Column(String(200), nullable=True)
    legal_representative_relationship = Column(String(100), nullable=True)

    effective_date = Column(DateTime(timezone=True), nullable=True)
    expiration_date = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by = Column(String(26), nullable=True)
    revocation_reason = Column(Text, nullable=True)

    document_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_national_advance_directives_patient", "patient_id"),
        Index("ix_national_advance_directives_citizen", "citizen_id"),
        Index("ix_national_advance_directives_type", "directive_type"),
        Index("ix_national_advance_directives_status", "status"),
        {"extend_existing": True},
    )
