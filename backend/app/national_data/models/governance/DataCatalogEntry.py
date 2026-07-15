from app.national_data.base import BaseEntity
from sqlalchemy import Boolean, Column, Integer, String, Text


class DataCatalogEntry(BaseEntity):
    __tablename__ = "dp_data_catalog"

    entry_name = Column(String(200), nullable=False)
    entry_type = Column(String(50), nullable=False, index=True)
    schema_name = Column(String(100), nullable=True)
    table_name = Column(String(100), nullable=True)
    column_name = Column(String(100), nullable=True)

    description = Column(Text, nullable=True)
    classification = Column(String(50), nullable=True)
    sensitivity_level = Column(String(20), nullable=True)

    source_system = Column(String(100), nullable=True)
    owner = Column(String(100), nullable=True)
    steward = Column(String(100), nullable=True)

    is_sensitive = Column(Boolean, default=False, nullable=False)
    is_pii = Column(Boolean, default=False, nullable=False)
    is_phi = Column(Boolean, default=False, nullable=False)

    retention_days = Column(Integer, nullable=True)
    data_quality_score = Column(Integer, nullable=True)

    tags = Column(String(500), nullable=True)

    __table_args__ = (
        {"extend_existing": True},
    )
