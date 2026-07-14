from app.national.base import TenantAuditEntity
from sqlalchemy import Boolean, Column, Index, String, Text


class Communication(TenantAuditEntity):
    __tablename__ = "national_communications"

    comm_type = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(26), nullable=False, index=True)

    value = Column(String(500), nullable=False)
    is_primary = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    preferred_time = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_national_communications_entity", "entity_type", "entity_id"),
        Index("ix_national_communications_type", "comm_type"),
        {"extend_existing": True},
    )
