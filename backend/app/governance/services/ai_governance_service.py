from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC

from ..enums import AIAuditAction, AIGuardrailType, AIRiskLevel
from ..models.ai import (
    AIAuditEvent,
    AIGuardrail,
    AIModelValidationRecord,
    AIRiskClassification,
    LLMGovernancePolicy,
    PromptPolicy,
)


class AIGovernanceService:
    def __init__(self, db: Session):
        self.db = db

    def create_guardrail(
        self,
        guardrail_code: str,
        name_ar: str,
        guardrail_type: AIGuardrailType,
        rules: dict[str, Any],
        name_en: str | None = None,
        description: str | None = None,
        severity: AIRiskLevel = AIRiskLevel.MEDIUM,
        action_on_violation: str = "block",
    ) -> AIGuardrail:
        guardrail = AIGuardrail(
            guardrail_code=guardrail_code,
            name_ar=name_ar,
            name_en=name_en,
            guardrail_type=guardrail_type,
            description=description,
            rules=rules,
            severity=severity,
            action_on_violation=action_on_violation,
        )
        self.db.add(guardrail)
        return guardrail

    def create_llm_policy(
        self,
        policy_code: str,
        name_ar: str,
        llm_provider: str,
        model_name: str,
        name_en: str | None = None,
        allowed_use_cases: list[str] | None = None,
        prohibited_use_cases: list[str] | None = None,
        max_tokens: int | None = None,
        temperature_max: float | None = None,
        requires_human_review: bool = False,
        requires_approval: bool = False,
        audit_level: str = "full",
    ) -> LLMGovernancePolicy:
        policy = LLMGovernancePolicy(
            policy_code=policy_code,
            name_ar=name_ar,
            name_en=name_en,
            llm_provider=llm_provider,
            model_name=model_name,
            allowed_use_cases=allowed_use_cases or [],
            prohibited_use_cases=prohibited_use_cases or [],
            max_tokens=max_tokens,
            temperature_max=temperature_max,
            requires_human_review=requires_human_review,
            requires_approval=requires_approval,
            audit_level=audit_level,
        )
        self.db.add(policy)
        return policy

    def create_prompt_policy(
        self,
        policy_code: str,
        name_ar: str,
        name_en: str | None = None,
        prompt_template: str | None = None,
        allowed_variables: list[str] | None = None,
        prohibited_content: list[str] | None = None,
        max_length: int | None = None,
        requires_sanitization: bool = True,
    ) -> PromptPolicy:
        policy = PromptPolicy(
            policy_code=policy_code,
            name_ar=name_ar,
            name_en=name_en,
            prompt_template=prompt_template,
            allowed_variables=allowed_variables,
            prohibited_content=prohibited_content,
            max_length=max_length,
            requires_sanitization=requires_sanitization,
        )
        self.db.add(policy)
        return policy

    def log_ai_audit(
        self,
        action: AIAuditAction,
        model_name: str,
        model_version: str | None = None,
        prompt: str | None = None,
        response: str | None = None,
        latency_ms: int | None = None,
        risk_level: AIRiskLevel | None = None,
        guardrail_triggered: bool = False,
        guardrail_codes: list[str] | None = None,
        requires_human_review: bool = False,
        node_id: int | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> AIAuditEvent:
        import hashlib

        input_hash = hashlib.sha256((prompt or "").encode()).hexdigest() if prompt else None
        output_hash = hashlib.sha256((response or "").encode()).hexdigest() if response else None

        event = AIAuditEvent(
            action=action,
            model_name=model_name,
            model_version=model_version,
            input_hash=input_hash,
            output_hash=output_hash,
            prompt=prompt,
            response=response,
            latency_ms=latency_ms,
            risk_level=risk_level,
            guardrail_triggered=guardrail_triggered,
            guardrail_codes=guardrail_codes,
            requires_human_review=requires_human_review,
            node_id=node_id,
            metadata_json=metadata_json,
        )
        self.db.add(event)
        return event

    def approve_ai_output(
        self,
        audit_event_id: int,
        reviewed_by: str,
        approved: bool,
    ) -> AIAuditEvent | None:
        event = self.db.query(AIAuditEvent).filter(AIAuditEvent.id == audit_event_id).first()
        if not event:
            return None
        event.reviewed_by = reviewed_by
        event.reviewed_at = datetime.now(UTC)
        event.human_approved = approved
        return event

    def classify_ai_risk(
        self,
        model_name: str,
        risk_level: AIRiskLevel,
        model_version: str | None = None,
        risk_factors: list[str] | None = None,
        clinical_impact: str | None = None,
        safety_assessment: str | None = None,
        classified_by: str | None = None,
    ) -> AIRiskClassification:
        classification = AIRiskClassification(
            model_name=model_name,
            model_version=model_version,
            risk_level=risk_level,
            risk_factors=risk_factors or [],
            clinical_impact=clinical_impact,
            safety_assessment=safety_assessment,
            classification_date=date.today(),
            classified_by=classified_by,
        )
        self.db.add(classification)
        return classification

    def validate_model(
        self,
        model_name: str,
        validation_type: str,
        accuracy: float | None = None,
        precision: float | None = None,
        recall: float | None = None,
        f1_score: float | None = None,
        dataset_used: str | None = None,
        sample_size: int | None = None,
        passed: bool | None = None,
        validator: str | None = None,
        model_version: str | None = None,
        notes: str | None = None,
    ) -> AIModelValidationRecord:
        record = AIModelValidationRecord(
            model_name=model_name,
            model_version=model_version,
            validation_type=validation_type,
            validation_date=date.today(),
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            dataset_used=dataset_used,
            sample_size=sample_size,
            passed=passed,
            validator=validator,
            notes=notes,
        )
        self.db.add(record)
        return record

    def get_model_risk(self, model_name: str) -> AIRiskClassification | None:
        return (
            self.db.query(AIRiskClassification)
            .filter(
                AIRiskClassification.model_name == model_name,
                AIRiskClassification.is_active.is_(True),
            )
            .order_by(AIRiskClassification.classification_date.desc())
            .first()
        )

    def evaluate_guardrails(
        self,
        prompt: str,
        guardrail_type: AIGuardrailType | None = None,
    ) -> list[dict[str, Any]]:
        q = self.db.query(AIGuardrail).filter(AIGuardrail.is_active.is_(True))
        if guardrail_type:
            q = q.filter(AIGuardrail.guardrail_type == guardrail_type)
        guardrails = q.all()

        violations: list[dict[str, Any]] = []
        for guardrail in guardrails:
            if guardrail.guardrail_type == AIGuardrailType.PROMPT_INJECTION:
                injection_patterns = guardrail.rules.get("patterns", [])
                for pattern in injection_patterns:
                    if pattern.lower() in prompt.lower():
                        violations.append(
                            {
                                "guardrail_code": guardrail.guardrail_code,
                                "type": guardrail.guardrail_type.value,
                                "violation": f"Pattern detected: {pattern}",
                                "severity": guardrail.severity.value,
                                "action": guardrail.action_on_violation,
                            }
                        )

            elif guardrail.guardrail_type == AIGuardrailType.PRIVACY:
                pii_patterns = guardrail.rules.get("pii_patterns", [])
                for pattern in pii_patterns:
                    if pattern.lower() in prompt.lower():
                        violations.append(
                            {
                                "guardrail_code": guardrail.guardrail_code,
                                "type": guardrail.guardrail_type.value,
                                "violation": f"PII pattern detected: {pattern}",
                                "severity": guardrail.severity.value,
                                "action": guardrail.action_on_violation,
                            }
                        )

        return violations
