from datetime import datetime

from app._compat import UTC
from app.national_data.base import BaseEntity
from sqlalchemy import JSON, Column, DateTime, Index, Integer, String


class EventSnapshot(BaseEntity):
    __tablename__ = "dp_event_snapshots"

    aggregate_type = Column(String(100), nullable=False, index=True)
    aggregate_id = Column(String(100), nullable=False, index=True)
    snapshot_data = Column(JSON, nullable=False)
    version = Column(Integer, nullable=False)

    snapshot_type = Column(String(50), default="full", nullable=False)
    created_by = Column(String(100), nullable=True)
    snapshot_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    __table_args__ = (
        Index("ix_dp_snapshots_aggregate", "aggregate_type", "aggregate_id", "version"),
        {"extend_existing": True},
    )
