from sqlalchemy import JSON, Column, DateTime, Index, Integer, String, Text

from app.national_data.base import BaseEntity


class DeidentificationJob(BaseEntity):
    __tablename__ = "dp_deidentification_jobs"

    job_name = Column(String(200), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_ids = Column(Text, nullable=True)

    techniques = Column(JSON, nullable=False)
    fields_to_deidentify = Column(JSON, nullable=True)
    fields_to_keep = Column(JSON, nullable=True)

    status = Column(String(20), default="pending", nullable=False, index=True)
    progress = Column(Integer, default=0, nullable=True)

    input_dataset_id = Column(Integer, nullable=True)
    output_dataset_id = Column(Integer, nullable=True)

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    requested_by = Column(Integer, nullable=True)
    approved_by = Column(Integer, nullable=True)
    compliance_ref = Column(String(100), nullable=True)

    __table_args__ = (
        Index("ix_dp_deid_status", "status"),
        {"extend_existing": True},
    )
