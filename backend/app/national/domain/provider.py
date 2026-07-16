from sqlalchemy import Boolean, Column, ForeignKey, Index, String

from app.national.base import AuditEntity


class Provider(AuditEntity):
    __tablename__ = "national_providers"

    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    provider_type = Column(String(50), nullable=False)

    license_number = Column(String(100), nullable=True, index=True)
    organization_id = Column(String(26), ForeignKey("national_organizations.id", ondelete="RESTRICT"), nullable=True, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)

    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(500), nullable=True)

    address_line = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    governorate = Column(String(100), nullable=True)

    specialty = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    accepts_insurance = Column(Boolean, default=False)

    __table_args__ = (
        Index("ix_national_providers_org", "organization_id"),
        Index("ix_national_providers_facility", "facility_id"),
        {"extend_existing": True},
    )
