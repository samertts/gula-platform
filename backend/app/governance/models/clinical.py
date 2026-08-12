from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Enum, Float, Integer, String, Text

from app._compat import UTC

from ..base import GovernanceBaseEntity
from ..enums import ClinicalPolicyType, PolicyStatus


class ClinicalPolicy(GovernanceBaseEntity):
    __tablename__ = "gov_clinical_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_code = Column(String(50), unique=True, nullable=False, index=True)
    title_ar = Column(String(300), nullable=False)
    title_en = Column(String(300), nullable=True)
    policy_type = Column(Enum(ClinicalPolicyType), nullable=False, index=True)
    status = Column(Enum(PolicyStatus), nullable=False, default=PolicyStatus.DRAFT, index=True)
    version = Column(String(20), nullable=False, default="1.0")
    content_ar = Column(Text, nullable=False)
    content_en = Column(Text, nullable=True)
    scope = Column(String(500), nullable=True)
    effective_date = Column(Date, nullable=True)
    review_date = Column(Date, nullable=True)
    approved_by = Column(String(200), nullable=True)
    supersedes_policy_code = Column(String(50), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class MedicalGuideline(GovernanceBaseEntity):
    __tablename__ = "gov_medical_guidelines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    guideline_code = Column(String(50), unique=True, nullable=False, index=True)
    title_ar = Column(String(300), nullable=False)
    title_en = Column(String(300), nullable=True)
    specialty = Column(String(200), nullable=False, index=True)
    issuing_body = Column(String(200), nullable=True)
    status = Column(Enum(PolicyStatus), nullable=False, default=PolicyStatus.DRAFT, index=True)
    version = Column(String(20), nullable=False, default="1.0")
    summary_ar = Column(Text, nullable=True)
    summary_en = Column(Text, nullable=True)
    content_url = Column(String(500), nullable=True)
    evidence_level = Column(String(50), nullable=True)
    effective_date = Column(Date, nullable=True)
    review_date = Column(Date, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class NationalProtocol(GovernanceBaseEntity):
    __tablename__ = "gov_national_protocols"

    id = Column(Integer, primary_key=True, autoincrement=True)
    protocol_code = Column(String(50), unique=True, nullable=False, index=True)
    title_ar = Column(String(300), nullable=False)
    title_en = Column(String(300), nullable=True)
    condition = Column(String(200), nullable=False, index=True)
    icd10_code = Column(String(20), nullable=True, index=True)
    status = Column(Enum(PolicyStatus), nullable=False, default=PolicyStatus.DRAFT, index=True)
    version = Column(String(20), nullable=False, default="1.0")
    content_ar = Column(Text, nullable=False)
    content_en = Column(Text, nullable=True)
    steps = Column(JSON, nullable=True)
    decision_tree = Column(JSON, nullable=True)
    effective_date = Column(Date, nullable=True)
    review_date = Column(Date, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class CriticalResultPolicy(GovernanceBaseEntity):
    __tablename__ = "gov_critical_result_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    test_code = Column(String(50), nullable=False, index=True)
    test_name_ar = Column(String(300), nullable=False)
    test_name_en = Column(String(300), nullable=True)
    critical_low = Column(String(50), nullable=True)
    critical_high = Column(String(50), nullable=True)
    unit = Column(String(50), nullable=True)
    notify_within_minutes = Column(Integer, nullable=False, default=30)
    notify_roles = Column(JSON, nullable=True)
    escalation_roles = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class RepeatTestingPolicy(GovernanceBaseEntity):
    __tablename__ = "gov_repeat_testing_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    test_code = Column(String(50), nullable=False, index=True)
    condition = Column(String(200), nullable=False)
    repeat_after_minutes = Column(Integer, nullable=True)
    max_repeats_per_day = Column(Integer, nullable=True)
    requires_approval = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class DeltaCheckPolicy(GovernanceBaseEntity):
    __tablename__ = "gov_delta_check_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    test_code = Column(String(50), nullable=False, index=True)
    delta_percent = Column(Float, nullable=False)
    delta_absolute = Column(String(50), nullable=True)
    time_window_hours = Column(Integer, nullable=False)
    action = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class WestgardPolicy(GovernanceBaseEntity):
    __tablename__ = "gov_westgard_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    test_code = Column(String(50), nullable=False, index=True)
    rules = Column(JSON, nullable=False)
    multi_rule_combinations = Column(JSON, nullable=True)
    num_control_measurements = Column(Integer, nullable=False, default=2)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class ReferenceRangePolicy(GovernanceBaseEntity):
    __tablename__ = "gov_reference_range_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    test_code = Column(String(50), nullable=False, index=True)
    gender = Column(String(10), nullable=True, index=True)
    age_min_years = Column(Integer, nullable=True)
    age_max_years = Column(Integer, nullable=True)
    low = Column(String(50), nullable=True)
    high = Column(String(50), nullable=True)
    unit = Column(String(50), nullable=True)
    source = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class ApprovalPolicy(GovernanceBaseEntity):
    __tablename__ = "gov_approval_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_code = Column(String(50), unique=True, nullable=False, index=True)
    title_ar = Column(String(300), nullable=False)
    title_en = Column(String(300), nullable=True)
    context = Column(String(100), nullable=False, index=True)
    requires_approval = Column(Boolean, default=True)
    approver_role = Column(String(100), nullable=True)
    escalation_role = Column(String(100), nullable=True)
    approval_timeout_hours = Column(Integer, nullable=True)
    auto_approve = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class ConsultationPolicy(GovernanceBaseEntity):
    __tablename__ = "gov_consultation_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_code = Column(String(50), unique=True, nullable=False, index=True)
    title_ar = Column(String(300), nullable=False)
    title_en = Column(String(300), nullable=True)
    context = Column(String(100), nullable=False, index=True)
    requires_consultation = Column(Boolean, default=True)
    consultant_specialty = Column(String(200), nullable=True)
    response_timeout_hours = Column(Integer, nullable=True)
    escalation_role = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
