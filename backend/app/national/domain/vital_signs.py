from sqlalchemy import JSON, Column, Index, Integer, String

from app.national.base import TenantAuditEntity


class VitalSignsReference(TenantAuditEntity):
    __tablename__ = "national_vital_signs_reference"

    vital_sign_code = Column(String(50), nullable=False, unique=True)
    vital_sign_name = Column(String(200), nullable=False)
    vital_sign_name_ar = Column(String(200), nullable=True)

    unit = Column(String(50), nullable=True)
    normal_range_low = Column(String(50), nullable=True)
    normal_range_high = Column(String(50), nullable=True)
    critical_low = Column(String(50), nullable=True)
    critical_high = Column(String(50), nullable=True)

    display_order = Column(Integer, default=0)
    category = Column(String(50), nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_national_vital_signs_reference_code", "vital_sign_code"),
        Index("ix_national_vital_signs_reference_category", "category"),
        {"extend_existing": True},
    )
