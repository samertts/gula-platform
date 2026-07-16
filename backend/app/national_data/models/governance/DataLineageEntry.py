from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Index, Integer, String, Text

from app._compat import UTC
from app.national_data.base import BaseEntity


class DataLineageEntry(BaseEntity):
    __tablename__ = "dp_data_lineage"

    source_entity = Column(String(100), nullable=False)
    source_entity_id = Column(String(100), nullable=False)
    target_entity = Column(String(100), nullable=False)
    target_entity_id = Column(String(100), nullable=False)

    transformation_type = Column(String(50), nullable=True)
    transformation_description = Column(Text, nullable=True)
    transformation_details = Column(JSON, nullable=True)

    pipeline_name = Column(String(100), nullable=True)
    pipeline_run_id = Column(String(100), nullable=True)
    pipeline_version = Column(String(50), nullable=True)

    processed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    processing_duration_ms = Column(Integer, nullable=True)

    status = Column(String(20), default="completed", nullable=False, index=True)
    error_message = Column(Text, nullable=True)

    lab_id = Column(Integer, nullable=True, index=True)

    __table_args__ = (
        Index("ix_dp_lineage_source", "source_entity", "source_entity_id"),
        Index("ix_dp_lineage_target", "target_entity", "target_entity_id"),
        Index("ix_dp_lineage_pipeline", "pipeline_name"),
        {"extend_existing": True},
    )
