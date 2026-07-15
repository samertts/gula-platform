from app.national_data.base import BaseEntity
from sqlalchemy import Boolean, Column, Integer, String, Text


class EventRetentionPolicy(BaseEntity):
    __tablename__ = "dp_event_retention_policies"

    event_type = Column(String(100), nullable=False, unique=True, index=True)
    retention_days = Column(Integer, nullable=False, default=365)
    max_snapshots = Column(Integer, nullable=False, default=10)
    allow_archive = Column(Boolean, default=True, nullable=False)
    archive_after_days = Column(Integer, nullable=True)

    compression_enabled = Column(Boolean, default=False, nullable=False)
    description = Column(Text, nullable=True)

    __table_args__ = {"extend_existing": True}
