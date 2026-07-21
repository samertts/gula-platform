"""Service catalog, benefit items, deductible tracking, and utilization models.

Provides the data model for the medical service catalog (with standard
coding systems), benefit-package line items, annual deductible tracking,
and benefit-utilization monitoring.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Enum as SAEnum, Float, ForeignKey,
    Index, Integer, JSON, Numeric, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app._compat import UTC
from app.insurance.domain.enums import ServiceCategory
from app.insurance.domain.models import InsBase


def _utcnow() -> datetime:
    return datetime.now(UTC)


class MedicalService(InsBase):
    """Medical service catalog item with standard coding system mappings.

    Each service can be identified by LOINC, CPT, ICD-10, or SNOMED codes
    and is categorized for benefit matching.
    """

    __tablename__ = "ins_medical_services"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)

    code = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    name_ar = Column(String(255), nullable=True)
    category = Column(SAEnum(ServiceCategory), nullable=True)
    description = Column(Text, nullable=True)

    loinc_code = Column(String(20), nullable=True)
    cpt_code = Column(String(20), nullable=True)
    icd10_code = Column(String(20), nullable=True)
    snomed_code = Column(String(20), nullable=True)

    default_price = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(3), default="IQD")

    is_active = Column(Boolean, default=True)
    requires_pre_auth = Column(Boolean, default=False)
    requires_referral = Column(Boolean, default=False)

    metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_ins_medical_services_code", "code"),
        Index("ix_ins_medical_services_loinc", "loinc_code"),
        Index("ix_ins_medical_services_cpt", "cpt_code"),
        Index("ix_ins_medical_services_category", "category"),
        {"extend_existing": True},
    )


class BenefitPackageItem(InsBase):
    """Individual service-level item within a benefit package.

    Defines per-service coverage rules that override or supplement the
    benefit-package defaults, including coverage percentage, copay,
    deductible application, pre-authorization requirements, and usage caps.
    """

    __tablename__ = "ins_benefit_package_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)

    package_id = Column(Integer, ForeignKey("ins_benefit_packages.id", ondelete="CASCADE"), nullable=False, index=True)
    service_code = Column(String(50), nullable=False, index=True)

    coverage_percentage = Column(Float, nullable=True)
    copay = Column(Float, nullable=True)
    copay_amount = Column(Numeric(12, 2), nullable=True)
    deductible_applies = Column(Boolean, default=True)
    requires_pre_auth = Column(Boolean, default=False)

    max_quantity = Column(Integer, nullable=True)
    max_visits = Column(Integer, nullable=True)
    max_benefit_amount = Column(Numeric(12, 2), nullable=True)
    max_age = Column(Integer, nullable=True)
    min_age = Column(Integer, nullable=True)

    is_active = Column(Boolean, default=True)
    effective_from = Column(Date, nullable=True)
    effective_until = Column(Date, nullable=True)

    metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_ins_benefit_package_items_package", "package_id"),
        Index("ix_ins_benefit_package_items_service", "service_code"),
        {"extend_existing": True},
    )

    package = relationship("BenefitPackage", backref="items")


class DeductibleTracking(InsBase):
    """Annual deductible tracking for a member or coverage.

    Records the total, applied, and remaining deductible for each calendar
    year to enforce annual deductible limits before coverage kicks in.
    """

    __tablename__ = "ins_deductible_tracking"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)

    coverage_id = Column(Integer, ForeignKey("ins_coverages.id"), nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("ins_members.id"), nullable=True, index=True)

    calendar_year = Column(Integer, nullable=False, index=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    total_deductible = Column(Numeric(12, 2), nullable=False, default=0)
    applied_deductible = Column(Numeric(12, 2), nullable=False, default=0)
    remaining_deductible = Column(Numeric(12, 2), nullable=False, default=0)
    reset_date = Column(Date, nullable=True)

    deductible_type = Column(String(50), default="individual")
    is_met = Column(Boolean, default=False)

    metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_ins_deductible_tracking_coverage", "coverage_id"),
        Index("ix_ins_deductible_tracking_year", "calendar_year"),
        UniqueConstraint("coverage_id", "calendar_year", name="uq_ins_deductible_tracking"),
        {"extend_existing": True},
    )

    coverage = relationship("Coverage", backref="deductible_tracking")


class BenefitUtilization(InsBase):
    """Tracking of benefit usage against annual or per-period limits.

    Monitors utilization percentage and remaining benefit for a coverage
    or member within a defined period, enabling proactive notifications
    when benefits are nearing exhaustion.
    """

    __tablename__ = "ins_benefit_utilization"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)

    coverage_id = Column(Integer, ForeignKey("ins_coverages.id"), nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("ins_members.id"), nullable=True, index=True)
    service_code = Column(String(50), nullable=True, index=True)

    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    benefit_type = Column(String(50), default="general")

    total_used = Column(Numeric(14, 2), nullable=False, default=0)
    total_remaining = Column(Numeric(14, 2), nullable=False, default=0)
    max_limit = Column(Numeric(14, 2), nullable=False, default=0)

    visit_count = Column(Integer, default=0)
    max_visits = Column(Integer, nullable=True)

    utilization_percentage = Column(Float, default=0.0)
    is_exhausted = Column(Boolean, default=False)

    metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_ins_benefit_utilization_coverage", "coverage_id"),
        Index("ix_ins_benefit_utilization_period", "period_start", "period_end"),
        {"extend_existing": True},
    )

    coverage = relationship("Coverage", backref="benefit_utilization")
