from sqlalchemy import Boolean, Column, Index, Integer, String

from app.national_data.base import BaseEntity


class DimFacility(BaseEntity):
    __tablename__ = "dw_dim_facility"

    source_facility_id = Column(String(26), nullable=True)
    lab_id = Column(Integer, nullable=True)

    facility_code = Column(String(20), nullable=True, index=True)
    facility_name = Column(String(200), nullable=False)
    facility_name_ar = Column(String(200), nullable=True)
    facility_type = Column(String(50), nullable=False)

    governorate = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index("ix_dw_dim_facility_type", "facility_type"),
        Index("ix_dw_dim_facility_governorate", "governorate"),
        {"extend_existing": True},
    )
