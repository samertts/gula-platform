from app.national_data.base import BaseEntity
from sqlalchemy import Boolean, Column, Index, Integer, String, Text


class DataSteward(BaseEntity):
    __tablename__ = "dp_data_stewards"

    user_id = Column(Integer, nullable=False, index=True)
    domain = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)

    steward_role = Column(String(50), nullable=False)
    full_name = Column(String(200), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)

    is_primary = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_dp_steward_user_domain", "user_id", "domain"),
        Index("ix_dp_steward_domain", "domain"),
        {"extend_existing": True},
    )
