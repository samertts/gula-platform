from app.national_data.base import BaseEntity
from sqlalchemy import JSON, Column, Index, Integer, String, Text


class SyntheticDataJob(BaseEntity):
    __tablename__ = "dp_synthetic_data_jobs"

    job_name = Column(String(200), nullable=False)
    source_dataset_id = Column(Integer, nullable=True)
    model_type = Column(String(50), nullable=False)
    target_records = Column(Integer, nullable=False)

    parameters = Column(JSON, nullable=True)
    column_config = Column(JSON, nullable=True)
    privacy_budget = Column(Integer, nullable=True)

    status = Column(String(20), default="pending", nullable=False, index=True)
    output_path = Column(String(500), nullable=True)
    output_records = Column(Integer, nullable=True)

    quality_score = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)

    requested_by = Column(Integer, nullable=True)

    __table_args__ = (
        Index("ix_dp_synthetic_status", "status"),
        {"extend_existing": True},
    )
