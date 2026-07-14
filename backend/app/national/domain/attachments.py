from app.national.base import TenantAuditEntity
from sqlalchemy import Boolean, Column, Index, Integer, String, Text


class Attachment(TenantAuditEntity):
    __tablename__ = "national_attachments"

    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(26), nullable=False, index=True)

    file_name = Column(String(255), nullable=False)
    file_type = Column(String(100), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    file_url = Column(String(1000), nullable=False)
    file_hash = Column(String(255), nullable=True)

    category = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)

    uploaded_by = Column(String(26), nullable=True)
    is_public = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    tags = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_national_attachments_entity", "entity_type", "entity_id"),
        {"extend_existing": True},
    )
