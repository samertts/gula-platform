from sqlalchemy import Boolean, Column, Index, Integer, String

from app.national_data.base import BaseEntity


class DimProvider(BaseEntity):
    __tablename__ = "dw_dim_provider"

    source_practitioner_id = Column(String(26), nullable=True)
    lab_user_id = Column(Integer, nullable=True)

    full_name = Column(String(200), nullable=False)
    full_name_ar = Column(String(200), nullable=True)
    license_number = Column(String(100), nullable=True, index=True)
    specialty = Column(String(200), nullable=True)
    provider_type = Column(String(50), nullable=False)

    is_verified = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        Index("ix_dw_dim_provider_license", "license_number"),
        Index("ix_dw_dim_provider_type", "provider_type"),
        {"extend_existing": True},
    )
