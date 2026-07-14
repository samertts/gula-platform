from app.national.base import TenantAuditEntity
from app.national.enums import InsuranceType
from sqlalchemy import Boolean, Column, Enum as SAEnum, ForeignKey, Index, String, Text


class Insurance(TenantAuditEntity):
    __tablename__ = "national_insurances"

    insurance_type = Column(SAEnum(InsuranceType), nullable=False)
    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    code = Column(String(50), nullable=False, unique=True, index=True)

    organization_id = Column(String(26), ForeignKey("national_organizations.id", ondelete="RESTRICT"), nullable=True, index=True)

    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(500), nullable=True)

    address_line = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    governorate = Column(String(100), nullable=True)

    is_active = Column(Boolean, default=True)
    is_government = Column(Boolean, default=False)

    coverage_details = Column(Text, nullable=True)
    contact_person = Column(String(200), nullable=True)

    __table_args__ = (
        Index("ix_national_insurances_org", "organization_id"),
        Index("ix_national_insurances_type", "insurance_type"),
        {"extend_existing": True},
    )
