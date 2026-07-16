from sqlalchemy import Boolean, Column, Float, ForeignKey, Index, Integer, String

from app.national_data.base import BaseEntity


class LocationRegistry(BaseEntity):
    __tablename__ = "dp_location_registry"

    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="SET NULL"), nullable=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="SET NULL"), nullable=True)

    location_code = Column(String(20), nullable=False, unique=True, index=True)
    location_name = Column(String(200), nullable=False)
    location_name_ar = Column(String(200), nullable=True)
    location_type = Column(String(50), nullable=False)

    address_line = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    governorate = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    subdistrict = Column(String(100), nullable=True)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    operating_hours = Column(String(500), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    contact_email = Column(String(255), nullable=True)

    __table_args__ = (
        Index("ix_dp_location_type", "location_type"),
        Index("ix_dp_location_governorate", "governorate"),
        {"extend_existing": True},
    )
