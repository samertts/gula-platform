from sqlalchemy import Boolean, Column, Index, Integer, String, Text

from app.national_data.base import BaseEntity


class RetentionPolicy(BaseEntity):
    __tablename__ = "dp_retention_policies"

    policy_name = Column(String(200), nullable=False, unique=True)
    entity_type = Column(String(100), nullable=False, index=True)

    retention_days = Column(Integer, nullable=False)
    archive_after_days = Column(Integer, nullable=True)
    purge_after_days = Column(Integer, nullable=True)

    action_on_expiry = Column(String(20), default="archive", nullable=False)
    allows_extension = Column(Boolean, default=False, nullable=False)
    max_extension_days = Column(Integer, nullable=True)

    legal_hold_enabled = Column(Boolean, default=False, nullable=False)
    legal_hold_reason = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_dp_retention_entity", "entity_type"),
        {"extend_existing": True},
    )
