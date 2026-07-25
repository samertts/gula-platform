"""Insurance ORM models — national health insurance data model.

All tables use the `ins_` prefix for clear namespace isolation.
All entities are tenant-scoped via lab_id.
All mutations are audit-logged via the audit service.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import declarative_base, relationship

from app._compat import UTC
from app.insurance.domain.enums import (
    AppealStatus,
    AuthorizationStatus,
    ClaimStatus,
    ClaimType,
    CoverageStatus,
    FraudSeverity,
    FraudStatus,
    InsuranceType,
    PaymentStatus,
    PolicyStatus,
    ProviderContractStatus,
    ServiceCategory,
    SettlementStatus,
)

InsBase = declarative_base()


def _utcnow() -> datetime:
    return datetime.now(UTC)


# =========================================================================
# Insurance Provider / Payer
# =========================================================================


class InsuranceProvider(InsBase):
    """Health insurance company / payer."""

    __tablename__ = "ins_providers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)

    insurance_type = Column(SAEnum(InsuranceType), nullable=False)
    name = Column(String(255), nullable=False)
    name_ar = Column(String(255), nullable=True)
    code = Column(String(50), nullable=False, unique=True, index=True)
    license_number = Column(String(100), nullable=True)
    tax_id = Column(String(100), nullable=True)

    is_government = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(500), nullable=True)

    address_line = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    governorate = Column(String(100), nullable=True)
    country = Column(String(100), default="IQ")

    contact_person = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)

    coverage_notes = Column(Text, nullable=True)
    extra_metadata = Column("metadata", JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_ins_providers_code", "code"),
        Index("ix_ins_providers_type", "insurance_type"),
        {"extend_existing": True},
    )


# =========================================================================
# Insurance Policy (contract between payer and subscriber)
# =========================================================================


class InsurancePolicy(InsBase):
    """Insurance policy — the contract between the payer and the subscriber."""

    __tablename__ = "ins_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)

    provider_id = Column(Integer, ForeignKey("ins_providers.id"), nullable=False, index=True)
    policy_number = Column(String(100), nullable=False, index=True)
    group_number = Column(String(100), nullable=True)
    status = Column(SAEnum(PolicyStatus), nullable=False, default=PolicyStatus.DRAFT)

    policy_holder_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    subscriber_id = Column(String(100), nullable=True)
    subscriber_name = Column(String(255), nullable=True)
    subscriber_relation = Column(String(50), nullable=True)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    grace_period_days = Column(Integer, default=30)

    premium_amount = Column(Numeric(12, 2), nullable=True)
    premium_currency = Column(String(3), default="IQD")
    premium_frequency = Column(String(20), default="monthly")

    copay_percentage = Column(Float, nullable=True)
    deductible_amount = Column(Numeric(12, 2), nullable=True)
    max_out_of_pocket = Column(Numeric(12, 2), nullable=True)
    max_lifetime_benefit = Column(Numeric(14, 2), nullable=True)

    terms_text = Column(Text, nullable=True)
    exclusions_text = Column(Text, nullable=True)
    extra_metadata = Column("metadata", JSON, nullable=True)

    signed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_ins_policies_number", "policy_number"),
        Index("ix_ins_policies_provider", "provider_id"),
        Index("ix_ins_policies_holder", "policy_holder_id"),
        Index("ix_ins_policies_period", "start_date", "end_date"),
        {"extend_existing": True},
    )

    provider = relationship("InsuranceProvider", backref="policies")


# =========================================================================
# Coverage (links a patient to a policy with specific benefit details)
# =========================================================================


class Coverage(InsBase):
    """Patient-level coverage under an insurance policy."""

    __tablename__ = "ins_coverages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)

    policy_id = Column(Integer, ForeignKey("ins_policies.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    dependent_id = Column(Integer, ForeignKey("patients.id"), nullable=True, index=True)

    status = Column(SAEnum(CoverageStatus), nullable=False, default=CoverageStatus.ACTIVE)
    subscriber_relation = Column(String(50), nullable=True)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    verification_date = Column(Date, nullable=True)

    copay_percentage = Column(Float, nullable=True)
    deductible_remaining = Column(Numeric(12, 2), nullable=True)
    deductible_total = Column(Numeric(12, 2), nullable=True)
    max_out_of_pocket_remaining = Column(Numeric(12, 2), nullable=True)
    max_out_of_pocket_total = Column(Numeric(12, 2), nullable=True)
    benefit_remaining = Column(Numeric(14, 2), nullable=True)
    benefit_total = Column(Numeric(14, 2), nullable=True)

    network_status = Column(String(50), default="in_network")
    authorization_required = Column(Boolean, default=False)
    referral_required = Column(Boolean, default=False)
    pre_existing_wait_period = Column(Boolean, default=False)

    extra_metadata = Column("metadata", JSON, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_ins_coverages_policy", "policy_id"),
        Index("ix_ins_coverages_patient", "patient_id"),
        Index("ix_ins_coverages_status", "status"),
        {"extend_existing": True},
    )

    policy = relationship("InsurancePolicy", backref="coverages")


# =========================================================================
# Benefit Package (defines what services are covered)
# =========================================================================


class BenefitPackage(InsBase):
    """Benefit package — defines coverage rules for a policy or plan."""

    __tablename__ = "ins_benefit_packages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)

    provider_id = Column(Integer, ForeignKey("ins_providers.id"), nullable=False, index=True)
    policy_id = Column(Integer, ForeignKey("ins_policies.id"), nullable=True, index=True)

    name = Column(String(255), nullable=False)
    name_ar = Column(String(255), nullable=True)
    code = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)

    service_category = Column(SAEnum(ServiceCategory), nullable=True)
    is_mandatory = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    coverage_percentage = Column(Float, default=100.0)
    copay_percentage = Column(Float, default=0.0)
    deductible_applies = Column(Boolean, default=True)
    max_benefit_per_claim = Column(Numeric(12, 2), nullable=True)
    max_benefit_per_year = Column(Numeric(14, 2), nullable=True)
    max_benefit_lifetime = Column(Numeric(14, 2), nullable=True)
    max_visits_per_year = Column(Integer, nullable=True)
    age_min = Column(Integer, nullable=True)
    age_max = Column(Integer, nullable=True)
    gender_restriction = Column(String(20), nullable=True)

    requires_pre_auth = Column(Boolean, default=False)
    requires_referral = Column(Boolean, default=False)

    clinical_rules = Column(JSON, nullable=True)
    exclusions = Column(JSON, nullable=True)
    extra_metadata = Column("metadata", JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_ins_benefit_packages_code", "code"),
        Index("ix_ins_benefit_packages_provider", "provider_id"),
        {"extend_existing": True},
    )

    provider = relationship("InsuranceProvider", backref="benefit_packages")


# =========================================================================
# Service / Fee Schedule
# =========================================================================


class FeeScheduleItem(InsBase):
    """Fee schedule — defines prices for medical services under a plan."""

    __tablename__ = "ins_fee_schedule"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)

    provider_id = Column(Integer, ForeignKey("ins_providers.id"), nullable=False, index=True)
    service_code = Column(String(50), nullable=False, index=True)
    service_name = Column(String(255), nullable=False)
    service_name_ar = Column(String(255), nullable=True)
    service_category = Column(SAEnum(ServiceCategory), nullable=True)

    loinc_code = Column(String(20), nullable=True)
    cpt_code = Column(String(20), nullable=True)
    icd10_code = Column(String(20), nullable=True)

    negotiated_price = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="IQD")
    allowed_amount = Column(Numeric(12, 2), nullable=True)
    patient_responsibility = Column(Numeric(12, 2), nullable=True)

    copay_amount = Column(Numeric(12, 2), nullable=True)
    coinsurance_percentage = Column(Float, nullable=True)
    deductible_applies = Column(Boolean, default=True)

    is_active = Column(Boolean, default=True)
    effective_from = Column(Date, nullable=True)
    effective_until = Column(Date, nullable=True)

    extra_metadata = Column("metadata", JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_ins_fee_schedule_code", "service_code"),
        Index("ix_ins_fee_schedule_provider", "provider_id"),
        UniqueConstraint("provider_id", "service_code", name="uq_ins_fee_schedule"),
        {"extend_existing": True},
    )


# =========================================================================
# Authorization (pre-authorization for services)
# =========================================================================


class Authorization(InsBase):
    """Pre-authorization for medical services."""

    __tablename__ = "ins_authorizations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)

    coverage_id = Column(Integer, ForeignKey("ins_coverages.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    provider_id = Column(Integer, ForeignKey("ins_providers.id"), nullable=False, index=True)
    requesting_practitioner_id = Column(Integer, nullable=True, index=True)

    authorization_number = Column(String(100), nullable=False, unique=True, index=True)
    status = Column(
        SAEnum(AuthorizationStatus), nullable=False, default=AuthorizationStatus.REQUESTED
    )
    service_category = Column(SAEnum(ServiceCategory), nullable=True)

    service_code = Column(String(50), nullable=True)
    service_description = Column(String(500), nullable=True)
    quantity_requested = Column(Integer, default=1)
    quantity_approved = Column(Integer, nullable=True)

    estimated_cost = Column(Numeric(12, 2), nullable=True)
    approved_cost = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(3), default="IQD")

    clinical_justification = Column(Text, nullable=True)
    diagnosis_code = Column(String(20), nullable=True)
    diagnosis_description = Column(String(500), nullable=True)
    icd10_code = Column(String(20), nullable=True)

    requested_date = Column(Date, nullable=False)
    decision_date = Column(Date, nullable=True)
    effective_from = Column(Date, nullable=True)
    effective_until = Column(Date, nullable=True)
    decision_notes = Column(Text, nullable=True)
    reviewed_by = Column(String(255), nullable=True)

    attachments = Column(JSON, nullable=True)
    extra_metadata = Column("metadata", JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_ins_authorizations_number", "authorization_number"),
        Index("ix_ins_authorizations_coverage", "coverage_id"),
        Index("ix_ins_authorizations_patient", "patient_id"),
        Index("ix_ins_authorizations_status", "status"),
        {"extend_existing": True},
    )

    coverage = relationship("Coverage", backref="authorizations")


# =========================================================================
# Claim (insurance claim for reimbursement)
# =========================================================================


class InsuranceClaim(InsBase):
    """Insurance claim — submitted to payer for reimbursement."""

    __tablename__ = "ins_claims"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)

    coverage_id = Column(Integer, ForeignKey("ins_coverages.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    provider_id = Column(Integer, ForeignKey("ins_providers.id"), nullable=False, index=True)
    order_id = Column(Integer, nullable=True, index=True)
    authorization_id = Column(
        Integer, ForeignKey("ins_authorizations.id"), nullable=True, index=True
    )
    referral_id = Column(Integer, nullable=True, index=True)

    claim_number = Column(String(100), nullable=False, unique=True, index=True)
    claim_type = Column(SAEnum(ClaimType), nullable=False, default=ClaimType.LABORATORY)
    status = Column(SAEnum(ClaimStatus), nullable=False, default=ClaimStatus.DRAFT)

    service_start_date = Column(Date, nullable=True)
    service_end_date = Column(Date, nullable=True)
    submitted_date = Column(Date, nullable=True)
    adjudicated_date = Column(Date, nullable=True)
    paid_date = Column(Date, nullable=True)

    total_billed = Column(Numeric(12, 2), nullable=False, default=0)
    total_allowed = Column(Numeric(12, 2), nullable=True)
    total_paid = Column(Numeric(12, 2), nullable=True)
    total_deductible = Column(Numeric(12, 2), nullable=True)
    total_copay = Column(Numeric(12, 2), nullable=True)
    total_patient_responsibility = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(3), default="IQD")

    diagnosis_code_primary = Column(String(20), nullable=True)
    diagnosis_code_secondary = Column(JSON, nullable=True)
    icd10_code = Column(String(20), nullable=True)

    adjudication_code = Column(String(50), nullable=True)
    adjudication_notes = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    adjustment_reason = Column(String(255), nullable=True)

    idempotency_key = Column(String(255), nullable=True, unique=True)
    external_ref = Column(String(255), nullable=True)
    extra_metadata = Column("metadata", JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
    submitted_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_ins_claims_number", "claim_number"),
        Index("ix_ins_claims_coverage", "coverage_id"),
        Index("ix_ins_claims_patient", "patient_id"),
        Index("ix_ins_claims_status", "status"),
        {"extend_existing": True},
    )

    coverage = relationship("Coverage", backref="claims")
    items = relationship("InsuranceClaimItem", back_populates="claim", cascade="all, delete-orphan")


class InsuranceClaimItem(InsBase):
    """Individual line item on an insurance claim."""

    __tablename__ = "ins_claim_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    claim_id = Column(
        Integer, ForeignKey("ins_claims.id", ondelete="CASCADE"), nullable=False, index=True
    )

    service_code = Column(String(50), nullable=False)
    service_name = Column(String(255), nullable=True)
    service_category = Column(SAEnum(ServiceCategory), nullable=True)
    loinc_code = Column(String(20), nullable=True)
    cpt_code = Column(String(20), nullable=True)

    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(12, 2), nullable=False)
    billed_amount = Column(Numeric(12, 2), nullable=False)
    allowed_amount = Column(Numeric(12, 2), nullable=True)
    paid_amount = Column(Numeric(12, 2), nullable=True)
    copay_amount = Column(Numeric(12, 2), nullable=True)
    deductible_amount = Column(Numeric(12, 2), nullable=True)
    patient_responsibility = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(3), default="IQD")

    diagnosis_code = Column(String(20), nullable=True)
    modifier = Column(String(20), nullable=True)
    revenue_code = Column(String(50), nullable=True)
    place_of_service = Column(String(50), nullable=True)

    adjudication_status = Column(String(50), nullable=True)
    adjudication_reason = Column(String(500), nullable=True)
    adjustment_code = Column(String(50), nullable=True)
    adjustment_reason = Column(String(255), nullable=True)

    extra_metadata = Column("metadata", JSON, nullable=True)

    claim = relationship("InsuranceClaim", back_populates="items")


# =========================================================================
# Payment
# =========================================================================


class InsurancePayment(InsBase):
    """Payment received from insurance company for claims."""

    __tablename__ = "ins_payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)

    claim_id = Column(Integer, ForeignKey("ins_claims.id"), nullable=False, index=True)
    payer_id = Column(Integer, ForeignKey("ins_providers.id"), nullable=False, index=True)

    payment_number = Column(String(100), nullable=False, unique=True, index=True)
    status = Column(SAEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)

    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="IQD")
    payment_method = Column(String(50), nullable=True)
    payment_date = Column(Date, nullable=True)
    reference_number = Column(String(255), nullable=True)

    adjustment_amount = Column(Numeric(12, 2), nullable=True, default=0)
    adjustment_reason = Column(String(500), nullable=True)

    notes = Column(Text, nullable=True)
    extra_metadata = Column("metadata", JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)
    processed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_ins_payments_number", "payment_number"),
        Index("ix_ins_payments_claim", "claim_id"),
        Index("ix_ins_payments_payer", "payer_id"),
        {"extend_existing": True},
    )

    claim = relationship("InsuranceClaim", backref="payments")


# =========================================================================
# Settlement (periodic reconciliation between payer and provider)
# =========================================================================


class Settlement(InsBase):
    """Periodic settlement between payer and healthcare provider."""

    __tablename__ = "ins_settlements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)

    provider_id = Column(Integer, ForeignKey("ins_providers.id"), nullable=False, index=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    status = Column(SAEnum(SettlementStatus), nullable=False, default=SettlementStatus.PENDING)

    settlement_number = Column(String(100), nullable=False, unique=True, index=True)
    total_claims = Column(Integer, default=0)
    total_billed = Column(Numeric(14, 2), nullable=False, default=0)
    total_allowed = Column(Numeric(14, 2), nullable=True)
    total_paid = Column(Numeric(14, 2), nullable=True)
    total_adjustments = Column(Numeric(14, 2), nullable=True, default=0)
    total_deductible = Column(Numeric(14, 2), nullable=True, default=0)
    total_copay = Column(Numeric(14, 2), nullable=True, default=0)
    net_amount = Column(Numeric(14, 2), nullable=True)
    currency = Column(String(3), default="IQD")

    reconciled_at = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    extra_metadata = Column("metadata", JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_ins_settlements_number", "settlement_number"),
        Index("ix_ins_settlements_provider", "provider_id"),
        Index("ix_ins_settlements_period", "period_start", "period_end"),
        {"extend_existing": True},
    )


# =========================================================================
# Appeal
# =========================================================================


class Appeal(InsBase):
    """Appeal against a claim decision."""

    __tablename__ = "ins_appeals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)

    claim_id = Column(Integer, ForeignKey("ins_claims.id"), nullable=False, index=True)
    submitted_by = Column(Integer, nullable=False, index=True)

    appeal_number = Column(String(100), nullable=False, unique=True, index=True)
    status = Column(SAEnum(AppealStatus), nullable=False, default=AppealStatus.FILED)

    reason = Column(Text, nullable=False)
    details = Column(Text, nullable=True)
    requested_amount = Column(Numeric(12, 2), nullable=True)
    supporting_documents = Column(JSON, nullable=True)

    reviewed_by = Column(String(255), nullable=True)
    review_notes = Column(Text, nullable=True)
    decision = Column(String(50), nullable=True)
    decision_amount = Column(Numeric(12, 2), nullable=True)
    decision_date = Column(Date, nullable=True)

    escalation_level = Column(Integer, default=1)
    filed_date = Column(Date, nullable=False)
    resolved_date = Column(Date, nullable=True)

    extra_metadata = Column("metadata", JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_ins_appeals_number", "appeal_number"),
        Index("ix_ins_appeals_claim", "claim_id"),
        Index("ix_ins_appeals_status", "status"),
        {"extend_existing": True},
    )

    claim = relationship("InsuranceClaim", backref="appeals")


# =========================================================================
# Fraud Detection
# =========================================================================


class FraudAlert(InsBase):
    """Fraud detection alert generated by AI or rules engine."""

    __tablename__ = "ins_fraud_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)

    claim_id = Column(Integer, ForeignKey("ins_claims.id"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True, index=True)
    provider_id = Column(Integer, ForeignKey("ins_providers.id"), nullable=True, index=True)

    alert_type = Column(String(100), nullable=False)
    severity = Column(SAEnum(FraudSeverity), nullable=False, default=FraudSeverity.MEDIUM)
    status = Column(SAEnum(FraudStatus), nullable=False, default=FraudStatus.DETECTED)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    risk_score = Column(Float, nullable=True)
    detection_method = Column(String(100), nullable=True)
    detection_rule = Column(String(255), nullable=True)

    evidence = Column(JSON, nullable=True)
    extra_metadata = Column("metadata", JSON, nullable=True)

    assigned_to = Column(String(255), nullable=True)
    investigation_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_ins_fraud_alerts_claim", "claim_id"),
        Index("ix_ins_fraud_alerts_patient", "patient_id"),
        Index("ix_ins_fraud_alerts_severity", "severity"),
        Index("ix_ins_fraud_alerts_status", "status"),
        {"extend_existing": True},
    )


# =========================================================================
# Provider Network Contract
# =========================================================================


class ProviderContract(InsBase):
    """Contract between insurance provider and healthcare facility."""

    __tablename__ = "ins_provider_contracts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, nullable=False, index=True)

    insurance_provider_id = Column(
        Integer, ForeignKey("ins_providers.id"), nullable=False, index=True
    )
    facility_id = Column(Integer, nullable=False, index=True)
    facility_type = Column(String(50), nullable=True)

    contract_number = Column(String(100), nullable=False, unique=True, index=True)
    status = Column(
        SAEnum(ProviderContractStatus), nullable=False, default=ProviderContractStatus.DRAFT
    )

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    termination_notice_days = Column(Integer, default=90)

    contract_type = Column(String(50), nullable=True)
    network_type = Column(String(50), default="preferred")
    is_exclusive = Column(Boolean, default=False)
    fee_schedule_id = Column(String(50), nullable=True)

    discount_percentage = Column(Float, nullable=True)
    stop_loss_threshold = Column(Numeric(12, 2), nullable=True)
    risk_sharing = Column(String(50), nullable=True)

    terms_text = Column(Text, nullable=True)
    special_terms = Column(JSON, nullable=True)
    extra_metadata = Column("metadata", JSON, nullable=True)

    signed_at = Column(DateTime(timezone=True), nullable=True)
    terminated_at = Column(DateTime(timezone=True), nullable=True)
    termination_reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_ins_provider_contracts_number", "contract_number"),
        Index("ix_ins_provider_contracts_insurance", "insurance_provider_id"),
        Index("ix_ins_provider_contracts_facility", "facility_id"),
        {"extend_existing": True},
    )

    insurance_provider = relationship("InsuranceProvider", backref="contracts")
