from sqlalchemy import Boolean, Column, ForeignKey, Index, Integer, String

from app.national.base import AuditEntity


class Laboratory(AuditEntity):
    __tablename__ = "national_laboratories"

    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    license_number = Column(String(100), nullable=False, unique=True, index=True)

    lab_type = Column(String(50), nullable=False)
    organization_id = Column(String(26), ForeignKey("national_organizations.id", ondelete="RESTRICT"), nullable=True, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)

    director_name = Column(String(200), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)

    address_line = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    governorate = Column(String(100), nullable=True)

    is_active = Column(Boolean, default=True)
    is_mobile = Column(Boolean, default=False)
    accreditation = Column(String(200), nullable=True)

    nhop_lab_code = Column(String(50), nullable=True, unique=True)
    external_lab_id = Column(Integer, nullable=True)

    __table_args__ = (
        Index("ix_national_laboratories_org", "organization_id"),
        Index("ix_national_laboratories_facility", "facility_id"),
        {"extend_existing": True},
    )
