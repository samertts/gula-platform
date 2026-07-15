from datetime import datetime

from app._compat import UTC
from app.national_data.base import BaseEntity
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text


class MergeAction(BaseEntity):
    __tablename__ = "dp_merge_actions"

    golden_record_id = Column(Integer, ForeignKey("dp_golden_records.id", ondelete="CASCADE"), nullable=False, index=True)
    source_patient_id = Column(Integer, nullable=True)
    target_patient_id = Column(Integer, nullable=True)

    merge_type = Column(String(20), nullable=False)
    merge_reason = Column(Text, nullable=True)
    merge_fields = Column(Text, nullable=True)
    conflict_resolution = Column(Text, nullable=True)

    merged_by = Column(Integer, nullable=True)
    merged_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    rollback_at = Column(DateTime(timezone=True), nullable=True)
    rollback_reason = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_dp_merge_golden", "golden_record_id"),
        {"extend_existing": True},
    )
