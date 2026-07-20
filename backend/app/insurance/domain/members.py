"""Extended member/citizen insurance models.

Tracks insurance membership, physical and electronic cards, family
dependents, and explicit coverage periods with premium and grace tracking.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Enum as SAEnum, Float, ForeignKey,
    Index, Integer, JSON, String, Text,
)
from sqlalchemy.orm import relationship

from app._compat import UTC
from app.insurance.domain.enums import (
    CardStatus, MemberStatus, RelationType,
)
from app.insurance.domain.models import InsBase


def _utcnow() -> datetime:
    return datetime.now(UTC)


class InsuranceMember(InsBase):
    """Links a citizen/patient to an insurance provider as a member.

    Captures enrollment, biometric verification, and membership lifecycle.
    """

    __tablename__ = "ins_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)

    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    provider_id = Column(Integer, ForeignKey("ins_providers.id"), nullable=False, index=True)

    member_number = Column(String(100), nullable=False, unique=True, index=True)
    status = Column(SAEnum(MemberStatus), nullable=False, default=MemberStatus.PENDING)

    enrollment_date = Column(Date, nullable=False)
    termination_date = Column(Date, nullable=True)
    biometric_verified = Column(Boolean, default=False)
    biometric_data = Column(JSON, nullable=True)

    metadata = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_ins_members_number", "member_number"),
        Index("ix_ins_members_patient", "patient_id"),
        Index("ix_ins_members_provider", "provider_id"),
        Index("ix_ins_members_status", "status"),
        {"extend_existing": True},
    )

    patient = relationship("Patient", backref="insurance_members")
    provider = relationship("InsuranceProvider", backref="members")


class InsuranceCard(InsBase):
    """Physical or digital insurance card issued to a member.

    Supports QR-code verification, chip identification, and full lifecycle
    tracking including lost/stolen reporting.
    """

    __tablename__ = "ins_cards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)

    member_id = Column(Integer, ForeignKey("ins_members.id"), nullable=False, index=True)

    card_number = Column(String(100), nullable=False, unique=True, index=True)
    card_type = Column(String(50), default="physical")

    issue_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)
    status = Column(SAEnum(CardStatus), nullable=False, default=CardStatus.ACTIVE)

    qr_code = Column(Text, nullable=True)
    chip_id = Column(String(100), nullable=True)
    barcode = Column(String(100), nullable=True)

    issued_by = Column(Integer, nullable=True)
    replaced_by_card_id = Column(Integer, nullable=True)
    reported_stolen_at = Column(DateTime(timezone=True), nullable=True)
    reported_lost_at = Column(DateTime(timezone=True), nullable=True)

    metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_ins_cards_number", "card_number"),
        Index("ix_ins_cards_member", "member_id"),
        Index("ix_ins_cards_status", "status"),
        {"extend_existing": True},
    )

    member = relationship("InsuranceMember", backref="cards")


class ElectronicCard(InsBase):
    """Virtual wallet-based insurance card for mobile/digital access.

    Supports PIN-protected access, device binding, and automatic lockout
    after failed PIN attempts.
    """

    __tablename__ = "ins_electronic_cards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)

    member_id = Column(Integer, ForeignKey("ins_members.id"), nullable=False, index=True)
    card_id = Column(Integer, ForeignKey("ins_cards.id"), nullable=True, index=True)

    token = Column(String(255), nullable=False, unique=True, index=True)
    device_id = Column(String(255), nullable=True)
    device_type = Column(String(50), nullable=True)

    pin_hash = Column(String(255), nullable=True)
    pin_attempts = Column(Integer, default=0)
    max_pin_attempts = Column(Integer, default=5)
    locked_until = Column(DateTime(timezone=True), nullable=True)

    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    last_access_ip = Column(String(50), nullable=True)

    is_active = Column(Boolean, default=True)
    metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_ins_electronic_cards_token", "token"),
        Index("ix_ins_electronic_cards_member", "member_id"),
        Index("ix_ins_electronic_cards_device", "device_id"),
        {"extend_existing": True},
    )

    member = relationship("InsuranceMember", backref="electronic_cards")
    card = relationship("InsuranceCard", backref="electronic_cards")


class Dependent(InsBase):
    """Family dependents linked to a primary insurance member.

    Each dependent inherits coverage at a defined percentage and priority
    level relative to the primary member.
    """

    __tablename__ = "ins_dependents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)

    member_id = Column(Integer, ForeignKey("ins_members.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)

    relation_type = Column(SAEnum(RelationType), nullable=False)
    relation_description = Column(String(255), nullable=True)

    coverage_percentage = Column(Float, default=100.0)
    priority = Column(Integer, default=1)

    is_active = Column(Boolean, default=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)

    metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_ins_dependents_member", "member_id"),
        Index("ix_ins_dependents_patient", "patient_id"),
        Index("ix_ins_dependents_relation", "relation_type"),
        {"extend_existing": True},
    )

    member = relationship("InsuranceMember", backref="dependents")
    patient = relationship("Patient", backref="insurance_dependents")


class CoveragePeriod(InsBase):
    """Explicit coverage period tracking for a member's insurance.

    Tracks effective windows, renewals, premium payments, and grace periods
    to support continuous coverage enforcement.
    """

    __tablename__ = "ins_coverage_periods"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)

    member_id = Column(Integer, ForeignKey("ins_members.id"), nullable=False, index=True)
    coverage_id = Column(Integer, ForeignKey("ins_coverages.id"), nullable=True, index=True)

    effective_start = Column(Date, nullable=False)
    effective_end = Column(Date, nullable=True)
    renewal_date = Column(Date, nullable=True)

    premium_amount = Column(Float, nullable=True)
    premium_paid = Column(Boolean, default=False)
    premium_paid_date = Column(Date, nullable=True)
    premium_currency = Column(String(3), default="IQD")

    grace_period_end = Column(Date, nullable=True)
    in_grace_period = Column(Boolean, default=False)
    lapsed_at = Column(Date, nullable=True)

    period_type = Column(String(50), default="annual")
    is_active = Column(Boolean, default=True)

    metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_ins_coverage_periods_member", "member_id"),
        Index("ix_ins_coverage_periods_coverage", "coverage_id"),
        Index("ix_ins_coverage_periods_effective", "effective_start", "effective_end"),
        {"extend_existing": True},
    )

    member = relationship("InsuranceMember", backref="coverage_periods")
