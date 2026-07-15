from datetime import datetime

from app._compat import UTC
from app.national_data.base import BaseEntity
from sqlalchemy import JSON, Column, DateTime, ForeignKey, Index, Integer, String, Text


class DataQualityCheck(BaseEntity):
    __tablename__ = "dp_data_quality_checks"

    rule_id = Column(Integer, ForeignKey("dp_data_quality_rules.id", ondelete="CASCADE"), nullable=False, index=True)
    check_run_id = Column(String(100), nullable=True, index=True)

    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(100), nullable=True)
    field_name = Column(String(100), nullable=True)

    result_status = Column(String(20), nullable=False, index=True)
    result_value = Column(String(500), nullable=True)
    result_details = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    records_checked = Column(Integer, nullable=True)
    records_failed = Column(Integer, nullable=True)
    score = Column(Integer, nullable=True)

    checked_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    checked_by = Column(String(100), nullable=True)

    lab_id = Column(Integer, nullable=True, index=True)

    __table_args__ = (
        Index("ix_dp_quality_check_rule", "rule_id"),
        Index("ix_dp_quality_check_status", "result_status"),
        {"extend_existing": True},
    )
