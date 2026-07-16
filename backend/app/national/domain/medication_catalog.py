from sqlalchemy import JSON, Boolean, Column, Index, Integer, String

from app.national.base import TenantAuditEntity


class MedicationCatalog(TenantAuditEntity):
    __tablename__ = "national_medication_catalog"

    medication_code = Column(String(50), nullable=False, unique=True)
    medication_code_system = Column(String(50), nullable=True)

    medication_name = Column(String(300), nullable=False)
    medication_name_ar = Column(String(300), nullable=True)
    generic_name = Column(String(300), nullable=True)
    brand_name = Column(String(300), nullable=True)
    manufacturer = Column(String(200), nullable=True)

    form = Column(String(100), nullable=True)
    strength_value = Column(String(50), nullable=True)
    strength_unit = Column(String(50), nullable=True)
    route = Column(String(100), nullable=True)

    category = Column(String(100), nullable=True)
    therapeutic_class = Column(String(200), nullable=True)
    atc_code = Column(String(20), nullable=True)
    atc_description = Column(String(300), nullable=True)

    is_controlled = Column(Boolean, default=False)
    is_narcotic = Column(Boolean, default=False)
    requires_prescription = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)

    max_daily_dose = Column(String(50), nullable=True)
    min_age_years = Column(Integer, nullable=True)
    pregnancy_category = Column(String(10), nullable=True)

    ingredients = Column(JSON, nullable=True)
    contraindications = Column(JSON, nullable=True)
    side_effects = Column(JSON, nullable=True)
    interactions = Column(JSON, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_national_medication_catalog_code", "medication_code"),
        Index("ix_national_medication_catalog_name", "medication_name"),
        Index("ix_national_medication_catalog_atc", "atc_code"),
        Index("ix_national_medication_catalog_category", "category"),
        Index("ix_national_medication_catalog_active", "is_active"),
        {"extend_existing": True},
    )
