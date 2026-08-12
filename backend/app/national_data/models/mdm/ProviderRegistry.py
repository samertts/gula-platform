from sqlalchemy import Boolean, Column, ForeignKey, Index, Integer, String

from app.national_data.base import BaseEntity


class ProviderRegistry(BaseEntity):
    __tablename__ = "dp_provider_registry"

    practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True, index=True)
    lab_user_id = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)

    national_id_hash = Column(String(255), nullable=True, index=True)
    license_number = Column(String(100), nullable=False, index=True)
    full_name = Column(String(200), nullable=False)
    full_name_ar = Column(String(200), nullable=True)
    specialty = Column(String(200), nullable=True)
    sub_specialty = Column(String(200), nullable=True)

    provider_type = Column(String(50), nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_source = Column(String(50), nullable=True)

    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    facility_id = Column(String(26), nullable=True)
    organization_id = Column(String(26), nullable=True)

    digital_signature_key = Column(String(500), nullable=True)

    __table_args__ = (
        Index("ix_dp_provider_license", "license_number"),
        Index("ix_dp_provider_type", "provider_type"),
        {"extend_existing": True},
    )
