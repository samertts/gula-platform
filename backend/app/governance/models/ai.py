from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)

from app._compat import UTC

from ..base import GovernanceBaseEntity
from ..enums import AIAuditAction, AIGuardrailType, AIRiskLevel


class AIGuardrail(GovernanceBaseEntity):
    __tablename__ = "gov_ai_guardrails"

    id = Column(Integer, primary_key=True, autoincrement=True)
    guardrail_code = Column(String(50), unique=True, nullable=False, index=True)
    name_ar = Column(String(300), nullable=False)
    name_en = Column(String(300), nullable=True)
    guardrail_type = Column(Enum(AIGuardrailType), nullable=False, index=True)
    description = Column(Text, nullable=True)
    rules = Column(JSON, nullable=False)
    severity = Column(Enum(AIRiskLevel), nullable=False, default=AIRiskLevel.MEDIUM)
    is_active = Column(Boolean, default=True, index=True)
    action_on_violation = Column(String(50), nullable=False, default="block")
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class LLMGovernancePolicy(GovernanceBaseEntity):
    __tablename__ = "gov_llm_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_code = Column(String(50), unique=True, nullable=False, index=True)
    name_ar = Column(String(300), nullable=False)
    name_en = Column(String(300), nullable=True)
    llm_provider = Column(String(100), nullable=False)
    model_name = Column(String(200), nullable=False)
    allowed_use_cases = Column(JSON, nullable=True)
    prohibited_use_cases = Column(JSON, nullable=True)
    max_tokens = Column(Integer, nullable=True)
    temperature_max = Column(Float, nullable=True)
    requires_human_review = Column(Boolean, default=False)
    requires_approval = Column(Boolean, default=False)
    audit_level = Column(String(20), default="full")
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class PromptPolicy(GovernanceBaseEntity):
    __tablename__ = "gov_prompt_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_code = Column(String(50), unique=True, nullable=False, index=True)
    name_ar = Column(String(300), nullable=False)
    name_en = Column(String(300), nullable=True)
    prompt_template = Column(Text, nullable=True)
    allowed_variables = Column(JSON, nullable=True)
    prohibited_content = Column(JSON, nullable=True)
    max_length = Column(Integer, nullable=True)
    requires_sanitization = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class AIAuditEvent(GovernanceBaseEntity):
    __tablename__ = "gov_ai_audit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(Enum(AIAuditAction), nullable=False, index=True)
    model_name = Column(String(200), nullable=False)
    model_version = Column(String(50), nullable=True)
    input_hash = Column(String(64), nullable=True, index=True)
    output_hash = Column(String(64), nullable=True)
    prompt = Column(Text, nullable=True)
    response = Column(Text, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    risk_level = Column(Enum(AIRiskLevel), nullable=True)
    guardrail_triggered = Column(Boolean, default=False)
    guardrail_codes = Column(JSON, nullable=True)
    requires_human_review = Column(Boolean, default=False)
    reviewed_by = Column(String(200), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    human_approved = Column(Boolean, nullable=True)
    node_id = Column(Integer, ForeignKey("gov_hierarchy_nodes.id"), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class AIRiskClassification(GovernanceBaseEntity):
    __tablename__ = "gov_ai_risk_classifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(200), nullable=False, index=True)
    model_version = Column(String(50), nullable=True)
    risk_level = Column(Enum(AIRiskLevel), nullable=False, index=True)
    risk_factors = Column(JSON, nullable=True)
    clinical_impact = Column(String(500), nullable=True)
    safety_assessment = Column(Text, nullable=True)
    classification_date = Column(Date, nullable=False)
    classified_by = Column(String(200), nullable=True)
    review_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class AIModelValidationRecord(GovernanceBaseEntity):
    __tablename__ = "gov_ai_model_validations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(200), nullable=False, index=True)
    model_version = Column(String(50), nullable=True)
    validation_type = Column(String(100), nullable=False)
    validation_date = Column(Date, nullable=False)
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    dataset_used = Column(String(300), nullable=True)
    sample_size = Column(Integer, nullable=True)
    passed = Column(Boolean, nullable=True)
    validator = Column(String(200), nullable=True)
    report_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
