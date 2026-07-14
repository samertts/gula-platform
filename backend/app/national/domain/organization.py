from app.national.base import AuditEntity
from app.national.enums import OrganizationType
from sqlalchemy import Boolean, Column, Enum as SAEnum, Index, String, Text


class Organization(AuditEntity):
    __tablename__ = "national_organizations"

    org_type = Column(SAEnum(OrganizationType), nullable=False)
    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    short_name = Column(String(50), nullable=True)

    license_number = Column(String(100), nullable=True, index=True)
    tax_id = Column(String(100), nullable=True)

    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(500), nullable=True)

    address_line = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    governorate = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    subdistrict = Column(String(100), nullable=True)
    country = Column(String(100), default="IQ")

    is_active = Column(Boolean, default=True)
    is_government = Column(Boolean, default=False)
    parent_organization_id = Column(String(26), nullable=True, index=True)
    nhop_code = Column(String(50), nullable=True, unique=True)

    metadata_ = Column("metadata", Text, nullable=True)

    __table_args__ = (
        Index("ix_national_organizations_type", "org_type"),
        Index("ix_national_organizations_parent", "parent_organization_id"),
        {"extend_existing": True},
    )
