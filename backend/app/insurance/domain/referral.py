"""Insurance referral system — electronic referrals between practitioners and facilities.

Supports the full referral lifecycle: creation, transmission, acceptance,
completion, and cancellation. Includes QR-code and digital-signature
verification for audit-grade integrity.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Enum as SAEnum, ForeignKey, Index,
    Integer, JSON, String, Text,
)
from sqlalchemy.orm import relationship

from app._compat import UTC
from app.insurance.domain.enums import (
    ReferralPriority, ReferralStatus, ReferralType, ValidationMethod,
)
from app.insurance.domain.models import InsBase


def _utcnow() -> datetime:
    return datetime.now(UTC)


class InsuranceReferral(InsBase):
    """Electronic referral documenting a request from one practitioner or facility to another.

    Supports doctor, laboratory, radiology, and specialist referrals with
    clinical reasoning, diagnosis coding, digital signing, and QR-code
    based verification.
    """

    __tablename__ = "ins_referrals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)

    coverage_id = Column(Integer, ForeignKey("ins_coverages.id"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    authorization_id = Column(Integer, ForeignKey("ins_authorizations.id"), nullable=True, index=True)

    from_practitioner_id = Column(Integer, nullable=True, index=True)
    to_practitioner_id = Column(Integer, nullable=True, index=True)
    from_facility_id = Column(Integer, nullable=True, index=True)
    to_facility_id = Column(Integer, nullable=True, index=True)

    referral_number = Column(String(100), nullable=False, unique=True, index=True)
    referral_type = Column(SAEnum(ReferralType), nullable=False)
    status = Column(SAEnum(ReferralStatus), nullable=False, default=ReferralStatus.DRAFT)
    priority = Column(SAEnum(ReferralPriority), nullable=False, default=ReferralPriority.ROUTINE)

    clinical_reason = Column(Text, nullable=True)
    diagnosis_code = Column(String(20), nullable=True)
    diagnosis_description = Column(String(500), nullable=True)
    icd10_code = Column(String(20), nullable=True)
    service_code = Column(String(50), nullable=True)
    service_description = Column(String(500), nullable=True)
    quantity = Column(Integer, default=1)

    notes = Column(Text, nullable=True)
    clinical_notes = Column(Text, nullable=True)
    expiration_date = Column(Date, nullable=True)

    qr_code = Column(Text, nullable=True)
    digital_signature = Column(Text, nullable=True)
    signature_algorithm = Column(String(50), nullable=True)
    signed_by = Column(Integer, nullable=True)
    signed_at = Column(DateTime(timezone=True), nullable=True)

    completed_at = Column(DateTime(timezone=True), nullable=True)
    completed_notes = Column(Text, nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_reason = Column(Text, nullable=True)

    metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_ins_referrals_number", "referral_number"),
        Index("ix_ins_referrals_patient", "patient_id"),
        Index("ix_ins_referrals_from", "from_practitioner_id"),
        Index("ix_ins_referrals_to", "to_practitioner_id"),
        Index("ix_ins_referrals_status", "status"),
        Index("ix_ins_referrals_type", "referral_type"),
        {"extend_existing": True},
    )

    coverage = relationship("Coverage", backref="referrals")
    history = relationship("ReferralHistory", back_populates="referral", cascade="all, delete-orphan")
    validations = relationship("ReferralValidation", back_populates="referral", cascade="all, delete-orphan")


class ReferralHistory(InsBase):
    """Audit trail of all status changes on a referral.

    Captures the complete state-machine transition history for compliance
    and dispute resolution.
    """

    __tablename__ = "ins_referral_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)

    referral_id = Column(Integer, ForeignKey("ins_referrals.id", ondelete="CASCADE"), nullable=False, index=True)

    from_status = Column(SAEnum(ReferralStatus), nullable=True)
    to_status = Column(SAEnum(ReferralStatus), nullable=False)
    changed_by = Column(Integer, nullable=True, index=True)
    change_reason = Column(Text, nullable=True)

    metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        Index("ix_ins_referral_history_referral", "referral_id"),
        Index("ix_ins_referral_history_created", "created_at"),
        {"extend_existing": True},
    )

    referral = relationship("InsuranceReferral", back_populates="history")


class ReferralValidation(InsBase):
    """Validation and verification record for a referral.

    Documents multi-factor verification including QR-code scanning,
    digital signature verification, and identity confirmation.
    """

    __tablename__ = "ins_referral_validations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)

    referral_id = Column(Integer, ForeignKey("ins_referrals.id", ondelete="CASCADE"), nullable=False, index=True)

    validated_by = Column(Integer, nullable=True, index=True)
    validation_method = Column(SAEnum(ValidationMethod), nullable=False, default=ValidationMethod.QR_SCAN)

    qr_verified = Column(Boolean, default=False)
    signature_verified = Column(Boolean, default=False)
    identity_verified = Column(Boolean, default=False)
    identity_document = Column(String(100), nullable=True)

    verified_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    valid_until = Column(Date, nullable=True)
    is_valid = Column(Boolean, default=False)

    failure_reason = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        Index("ix_ins_referral_validations_referral", "referral_id"),
        Index("ix_ins_referral_validations_validator", "validated_by"),
        {"extend_existing": True},
    )

    referral = relationship("InsuranceReferral", back_populates="validations")
