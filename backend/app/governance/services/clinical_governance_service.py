from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from ..enums import ClinicalPolicyType, PolicyStatus, WestgardRule
from ..models.clinical import (
    ApprovalPolicy,
    ClinicalPolicy,
    ConsultationPolicy,
    CriticalResultPolicy,
    DeltaCheckPolicy,
    MedicalGuideline,
    NationalProtocol,
    ReferenceRangePolicy,
    RepeatTestingPolicy,
    WestgardPolicy,
)


class ClinicalGovernanceService:
    def __init__(self, db: Session):
        self.db = db

    def create_policy(
        self,
        policy_code: str,
        title_ar: str,
        policy_type: ClinicalPolicyType,
        content_ar: str,
        title_en: str | None = None,
        content_en: str | None = None,
        scope: str | None = None,
        effective_date: date | None = None,
        review_date: date | None = None,
        approved_by: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> ClinicalPolicy:
        policy = ClinicalPolicy(
            policy_code=policy_code,
            title_ar=title_ar,
            title_en=title_en,
            policy_type=policy_type,
            status=PolicyStatus.ACTIVE,
            content_ar=content_ar,
            content_en=content_en,
            scope=scope,
            effective_date=effective_date or date.today(),
            review_date=review_date,
            approved_by=approved_by,
            metadata_json=metadata_json,
        )
        self.db.add(policy)
        return policy

    def create_guideline(
        self,
        guideline_code: str,
        title_ar: str,
        specialty: str,
        title_en: str | None = None,
        issuing_body: str | None = None,
        summary_ar: str | None = None,
        evidence_level: str | None = None,
        effective_date: date | None = None,
    ) -> MedicalGuideline:
        guideline = MedicalGuideline(
            guideline_code=guideline_code,
            title_ar=title_ar,
            title_en=title_en,
            specialty=specialty,
            issuing_body=issuing_body,
            status=PolicyStatus.ACTIVE,
            summary_ar=summary_ar,
            evidence_level=evidence_level,
            effective_date=effective_date or date.today(),
        )
        self.db.add(guideline)
        return guideline

    def create_protocol(
        self,
        protocol_code: str,
        title_ar: str,
        condition: str,
        content_ar: str,
        title_en: str | None = None,
        icd10_code: str | None = None,
        steps: list[dict[str, Any]] | None = None,
        decision_tree: dict[str, Any] | None = None,
        effective_date: date | None = None,
    ) -> NationalProtocol:
        protocol = NationalProtocol(
            protocol_code=protocol_code,
            title_ar=title_ar,
            title_en=title_en,
            condition=condition,
            icd10_code=icd10_code,
            status=PolicyStatus.ACTIVE,
            content_ar=content_ar,
            steps=steps,
            decision_tree=decision_tree,
            effective_date=effective_date or date.today(),
        )
        self.db.add(protocol)
        return protocol

    def set_critical_result_policy(
        self,
        test_code: str,
        test_name_ar: str,
        critical_low: str | None = None,
        critical_high: str | None = None,
        unit: str | None = None,
        notify_within_minutes: int = 30,
        notify_roles: list[str] | None = None,
        escalation_roles: list[str] | None = None,
    ) -> CriticalResultPolicy:
        policy = CriticalResultPolicy(
            test_code=test_code,
            test_name_ar=test_name_ar,
            critical_low=critical_low,
            critical_high=critical_high,
            unit=unit,
            notify_within_minutes=notify_within_minutes,
            notify_roles=notify_roles or ["doctor", "specialist"],
            escalation_roles=escalation_roles or ["consultant", "department_head"],
        )
        self.db.add(policy)
        return policy

    def set_repeat_testing_policy(
        self,
        test_code: str,
        condition: str,
        repeat_after_minutes: int | None = None,
        max_repeats_per_day: int | None = None,
        requires_approval: bool = False,
    ) -> RepeatTestingPolicy:
        policy = RepeatTestingPolicy(
            test_code=test_code,
            condition=condition,
            repeat_after_minutes=repeat_after_minutes,
            max_repeats_per_day=max_repeats_per_day,
            requires_approval=requires_approval,
        )
        self.db.add(policy)
        return policy

    def set_delta_check_policy(
        self,
        test_code: str,
        delta_percent: float,
        time_window_hours: int,
        action: str,
        delta_absolute: str | None = None,
    ) -> DeltaCheckPolicy:
        policy = DeltaCheckPolicy(
            test_code=test_code,
            delta_percent=delta_percent,
            delta_absolute=delta_absolute,
            time_window_hours=time_window_hours,
            action=action,
        )
        self.db.add(policy)
        return policy

    def set_westgard_policy(
        self,
        test_code: str,
        rules: list[str],
        num_control_measurements: int = 2,
        multi_rule_combinations: list[list[str]] | None = None,
    ) -> WestgardPolicy:
        policy = WestgardPolicy(
            test_code=test_code,
            rules=rules,
            multi_rule_combinations=multi_rule_combinations,
            num_control_measurements=num_control_measurements,
        )
        self.db.add(policy)
        return policy

    def set_reference_range(
        self,
        test_code: str,
        low: str | None = None,
        high: str | None = None,
        unit: str | None = None,
        gender: str | None = None,
        age_min_years: int | None = None,
        age_max_years: int | None = None,
        source: str | None = None,
    ) -> ReferenceRangePolicy:
        policy = ReferenceRangePolicy(
            test_code=test_code,
            low=low,
            high=high,
            unit=unit,
            gender=gender,
            age_min_years=age_min_years,
            age_max_years=age_max_years,
            source=source,
        )
        self.db.add(policy)
        return policy

    def create_approval_policy(
        self,
        policy_code: str,
        title_ar: str,
        context: str,
        approver_role: str | None = None,
        escalation_role: str | None = None,
        approval_timeout_hours: int | None = None,
        auto_approve: bool = False,
    ) -> ApprovalPolicy:
        policy = ApprovalPolicy(
            policy_code=policy_code,
            title_ar=title_ar,
            context=context,
            approver_role=approver_role,
            escalation_role=escalation_role,
            approval_timeout_hours=approval_timeout_hours,
            auto_approve=auto_approve,
        )
        self.db.add(policy)
        return policy

    def create_consultation_policy(
        self,
        policy_code: str,
        title_ar: str,
        context: str,
        consultant_specialty: str | None = None,
        response_timeout_hours: int | None = None,
        escalation_role: str | None = None,
    ) -> ConsultationPolicy:
        policy = ConsultationPolicy(
            policy_code=policy_code,
            title_ar=title_ar,
            context=context,
            consultant_specialty=consultant_specialty,
            response_timeout_hours=response_timeout_hours,
            escalation_role=escalation_role,
        )
        self.db.add(policy)
        return policy

    def get_active_policies(
        self, policy_type: ClinicalPolicyType | None = None
    ) -> list[ClinicalPolicy]:
        q = self.db.query(ClinicalPolicy).filter(ClinicalPolicy.status == PolicyStatus.ACTIVE)
        if policy_type:
            q = q.filter(ClinicalPolicy.policy_type == policy_type)
        return q.order_by(ClinicalPolicy.policy_code).all()

    def evaluate_critical_result(
        self, test_code: str, result_value: float
    ) -> dict[str, Any]:
        policy = (
            self.db.query(CriticalResultPolicy)
            .filter(
                CriticalResultPolicy.test_code == test_code,
                CriticalResultPolicy.is_active.is_(True),
            )
            .first()
        )
        if not policy:
            return {"is_critical": False, "reason": "no policy defined"}

        is_critical = False
        reasons: list[str] = []
        if policy.critical_low is not None and result_value <= float(policy.critical_low):
            is_critical = True
            reasons.append(f"below critical low ({policy.critical_low})")
        if policy.critical_high is not None and result_value >= float(policy.critical_high):
            is_critical = True
            reasons.append(f"above critical high ({policy.critical_high})")

        return {
            "is_critical": is_critical,
            "reason": "; ".join(reasons) if reasons else None,
            "notify_roles": policy.notify_roles if is_critical else None,
            "notify_within_minutes": policy.notify_within_minutes if is_critical else None,
        }

    def evaluate_delta_check(
        self, test_code: str, current_value: float, previous_value: float
    ) -> dict[str, Any]:
        policy = (
            self.db.query(DeltaCheckPolicy)
            .filter(
                DeltaCheckPolicy.test_code == test_code,
                DeltaCheckPolicy.is_active.is_(True),
            )
            .first()
        )
        if not policy:
            return {"delta_triggered": False, "reason": "no policy defined"}

        if previous_value == 0:
            pct_change = abs(current_value - previous_value) * 100
        else:
            pct_change = abs((current_value - previous_value) / previous_value) * 100

        triggered = pct_change > policy.delta_percent
        return {
            "delta_triggered": triggered,
            "delta_percent": round(pct_change, 2),
            "threshold_percent": policy.delta_percent,
            "action": policy.action if triggered else None,
        }
