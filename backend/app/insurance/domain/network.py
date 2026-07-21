"""Provider network models — healthcare facility network management.

Covers network provider enrollment, service pricing, availability
scheduling, accreditation and licensing, and geographic coverage areas
with routing authority.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Enum as SAEnum, ForeignKey,
    Index, Integer, JSON, Numeric, String,
)
from sqlalchemy.orm import relationship

from app._compat import UTC
from app.insurance.domain.enums import (
    AccreditationStatus, CoverageLevel, NetworkTier,
)
from app.insurance.domain.models import InsBase


def _utcnow() -> datetime:
    return datetime.now(UTC)


class NetworkProvider(InsBase):
    """Healthcare facility or provider enrolled in an insurance network.

    Captures contractual relationship, network tier (tier1/tier2/tier3),
    preferred/exclusive status, service area, and geographic coverage.
    """

    __tablename__ = "ins_network_providers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)

    provider_id = Column(Integer, ForeignKey("ins_providers.id"), nullable=False, index=True)
    facility_id = Column(Integer, nullable=False, index=True)
    contract_id = Column(Integer, ForeignKey("ins_provider_contracts.id"), nullable=True, index=True)

    facility_type = Column(String(50), nullable=True)
    network_tier = Column(SAEnum(NetworkTier), nullable=False, default=NetworkTier.TIER2)

    is_preferred = Column(Boolean, default=False)
    is_exclusive = Column(Boolean, default=False)
    is_accepting_new_patients = Column(Boolean, default=True)

    join_date = Column(Date, nullable=False)
    termination_date = Column(Date, nullable=True)
    service_area = Column(String(255), nullable=True)
    geographic_coverage = Column(JSON, nullable=True)

    metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_ins_network_providers_provider", "provider_id"),
        Index("ix_ins_network_providers_facility", "facility_id"),
        Index("ix_ins_network_providers_tier", "network_tier"),
        {"extend_existing": True},
    )

    insurance_provider = relationship("InsuranceProvider", backref="network_providers")


class NetworkService(InsBase):
    """Services offered by network providers with negotiated pricing.

    Defines in-network and out-of-network price schedules for each service
    a network provider offers.
    """

    __tablename__ = "ins_network_services"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)

    network_provider_id = Column(Integer, ForeignKey("ins_network_providers.id", ondelete="CASCADE"), nullable=False, index=True)
    service_code = Column(String(50), nullable=False, index=True)
    service_name = Column(String(255), nullable=True)

    negotiated_rate = Column(Numeric(12, 2), nullable=True)
    contracted_rate = Column(Numeric(12, 2), nullable=True)
    in_network_price = Column(Numeric(12, 2), nullable=True)
    out_of_network_price = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(3), default="IQD")

    is_active = Column(Boolean, default=True)
    effective_from = Column(Date, nullable=True)
    effective_until = Column(Date, nullable=True)

    metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_ins_network_services_network", "network_provider_id"),
        Index("ix_ins_network_services_code", "service_code"),
        {"extend_existing": True},
    )

    network_provider = relationship("NetworkProvider", backref="network_services")


class ProviderAvailability(InsBase):
    """Availability schedule for a network provider.

    Defines weekly recurring availability windows with patient capacity
    tracking per time slot.
    """

    __tablename__ = "ins_provider_availability"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)

    network_provider_id = Column(Integer, ForeignKey("ins_network_providers.id", ondelete="CASCADE"), nullable=False, index=True)

    day_of_week = Column(Integer, nullable=False)
    time_from = Column(String(10), nullable=False)
    time_to = Column(String(10), nullable=False)

    is_available = Column(Boolean, default=True)
    slot_type = Column(String(50), default="general")

    max_patients = Column(Integer, default=10)
    current_patients = Column(Integer, default=0)

    effective_from = Column(Date, nullable=True)
    effective_until = Column(Date, nullable=True)

    metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_ins_provider_availability_network", "network_provider_id"),
        Index("ix_ins_provider_availability_day", "day_of_week"),
        {"extend_existing": True},
    )

    network_provider = relationship("NetworkProvider", backref="availability")


class ProviderAccreditation(InsBase):
    """Accreditation and licensing records for a network provider.

    Tracks accreditation bodies, license numbers, issue and expiry dates,
    and supporting documentation.
    """

    __tablename__ = "ins_provider_accreditations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)

    network_provider_id = Column(Integer, ForeignKey("ins_network_providers.id", ondelete="CASCADE"), nullable=False, index=True)

    accreditation_body = Column(String(255), nullable=False)
    license_number = Column(String(100), nullable=False, index=True)
    accreditation_type = Column(String(100), nullable=True)

    issue_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=True)
    status = Column(SAEnum(AccreditationStatus), nullable=False, default=AccreditationStatus.ACTIVE)

    document_url = Column(String(500), nullable=True)
    document_type = Column(String(50), nullable=True)

    verified_by = Column(String(255), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_ins_provider_accreditations_network", "network_provider_id"),
        Index("ix_ins_provider_accreditations_license", "license_number"),
        Index("ix_ins_provider_accreditations_status", "status"),
        {"extend_existing": True},
    )

    network_provider = relationship("NetworkProvider", backref="accreditations")


class GeographicCoverage(InsBase):
    """Geographic areas covered by a network provider.

    Defines which governorates and districts a provider covers and at what
    level (full/partial/none), with routing authority for referral
    direction.
    """

    __tablename__ = "ins_geographic_coverage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)

    network_provider_id = Column(Integer, ForeignKey("ins_network_providers.id", ondelete="CASCADE"), nullable=False, index=True)

    governorate = Column(String(100), nullable=False, index=True)
    district = Column(String(100), nullable=True)
    service_type = Column(String(50), nullable=True)

    coverage_level = Column(SAEnum(CoverageLevel), nullable=False, default=CoverageLevel.FULL)
    routing_authority = Column(String(50), nullable=True)

    is_active = Column(Boolean, default=True)
    effective_from = Column(Date, nullable=True)
    effective_until = Column(Date, nullable=True)

    metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_ins_geographic_coverage_network", "network_provider_id"),
        Index("ix_ins_geographic_coverage_gov", "governorate"),
        Index("ix_ins_geographic_coverage_level", "coverage_level"),
        {"extend_existing": True},
    )

    network_provider = relationship("NetworkProvider", backref="geographic_coverages")
