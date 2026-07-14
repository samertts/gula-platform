from app.national.base import TenantAuditEntity
from sqlalchemy import Boolean, Column, Index, String, Text


class Address(TenantAuditEntity):
    __tablename__ = "national_addresses"

    address_type = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(26), nullable=False, index=True)

    line1 = Column(String(200), nullable=True)
    line2 = Column(String(200), nullable=True)
    city = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    subdistrict = Column(String(100), nullable=True)
    governorate = Column(String(100), nullable=True)
    country = Column(String(100), default="IQ")
    postal_code = Column(String(20), nullable=True)

    latitude = Column(String(20), nullable=True)
    longitude = Column(String(20), nullable=True)

    is_primary = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_national_addresses_entity", "entity_type", "entity_id"),
        Index("ix_national_addresses_gov", "governorate"),
        {"extend_existing": True},
    )
