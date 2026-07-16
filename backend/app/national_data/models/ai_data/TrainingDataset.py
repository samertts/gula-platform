from datetime import datetime

from sqlalchemy import JSON, BigInteger, Column, DateTime, Index, Integer, String, Text

from app._compat import UTC
from app.national_data.base import BaseEntity


class TrainingDataset(BaseEntity):
    __tablename__ = "dp_training_datasets"

    dataset_name = Column(String(200), nullable=False)
    dataset_version = Column(String(20), nullable=False)
    dataset_type = Column(String(50), nullable=False)

    description = Column(Text, nullable=True)
    feature_list = Column(JSON, nullable=True)
    target_variable = Column(String(100), nullable=True)

    total_records = Column(Integer, nullable=True)
    training_records = Column(Integer, nullable=True)
    validation_records = Column(Integer, nullable=True)
    test_records = Column(Integer, nullable=True)

    file_path = Column(String(500), nullable=True)
    file_format = Column(String(20), nullable=True)
    file_size_bytes = Column(BigInteger, nullable=True)

    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    is_active = Column(Integer, default=1, nullable=False)
    status = Column(String(20), default="preparing", nullable=False)

    tags = Column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_dp_dataset_name_ver", "dataset_name", "dataset_version"),
        Index("ix_dp_dataset_type", "dataset_type"),
        Index("ix_dp_dataset_status", "status"),
        {"extend_existing": True},
    )
