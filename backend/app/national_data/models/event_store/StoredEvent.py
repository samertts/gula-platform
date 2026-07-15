from datetime import datetime

from app._compat import UTC
from app.national_data.base import BaseEntity
from sqlalchemy import JSON, Column, DateTime, Index, Integer, String


class StoredEvent(BaseEntity):
    __tablename__ = "dp_stored_events"

    event_type = Column(String(100), nullable=False, index=True)
    aggregate_type = Column(String(100), nullable=False, index=True)
    aggregate_id = Column(String(100), nullable=False, index=True)
    event_data = Column(JSON, nullable=False)
    metadata_ = Column("metadata", JSON, nullable=True)

    version = Column(Integer, nullable=False, default=1)
    partition_key = Column(String(50), nullable=True, index=True)

    occurred_at = Column(DateTime(timezone=True), nullable=False)
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    causation_id = Column(String(100), nullable=True)
    correlation_id = Column(String(100), nullable=True)
    recorded_by = Column(String(100), nullable=True)

    __table_args__ = (
        Index("ix_dp_events_aggregate", "aggregate_type", "aggregate_id", "version"),
        Index("ix_dp_events_type_occurred", "event_type", "occurred_at"),
        Index("ix_dp_events_partition", "partition_key", "occurred_at"),
        {"extend_existing": True},
    )
