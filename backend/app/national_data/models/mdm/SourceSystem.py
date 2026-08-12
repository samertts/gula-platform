from sqlalchemy import Boolean, Column, Index, Integer, String, Text

from app.national_data.base import BaseEntity


class SourceSystem(BaseEntity):
    __tablename__ = "dp_source_systems"

    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(20), nullable=False, unique=True, index=True)
    system_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    base_url = Column(String(500), nullable=True)
    api_key_hash = Column(String(255), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=0, nullable=False)
    data_quality_score = Column(Integer, default=0, nullable=True)

    contact_info = Column(String(500), nullable=True)

    __table_args__ = (
        Index("ix_dp_source_system_type", "system_type"),
        {"extend_existing": True},
    )
