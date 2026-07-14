from app.national.base import AuditEntity
from sqlalchemy import Boolean, Column, DateTime, Index, JSON, String, Text


class IdentityAuditLog(AuditEntity):
    __tablename__ = "national_identity_audit_logs"

    event_type = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(26), nullable=False, index=True)

    action = Column(String(50), nullable=False)
    performed_by = Column(String(26), nullable=False)
    performed_by_role = Column(String(50), nullable=True)
    performed_at = Column(DateTime(timezone=True), nullable=False)

    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    session_id = Column(String(100), nullable=True)

    previous_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    reason = Column(Text, nullable=True)

    is_break_glass = Column(Boolean, default=False)
    break_glass_reason = Column(Text, nullable=True)
    purpose_of_use = Column(String(100), nullable=True)

    consent_verified = Column(Boolean, default=True)
    access_granted = Column(Boolean, default=True)

    __table_args__ = (
        Index("ix_national_identity_audit_entity", "entity_type", "entity_id"),
        Index("ix_national_identity_audit_event", "event_type"),
        Index("ix_national_identity_audit_performed", "performed_at"),
        Index("ix_national_identity_audit_by", "performed_by"),
        {"extend_existing": True},
    )
