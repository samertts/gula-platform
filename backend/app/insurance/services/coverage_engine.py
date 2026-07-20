"""Coverage Engine — determines insurance coverage for medical services.

Evaluates patient coverage against policy terms, benefit packages, fee
schedules, and clinical rules. Returns coverage determination with
patient financial responsibility breakdown.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.insurance.domain.enums import (
    CoverageDetermination, ServiceCategory,
)
from app.insurance.domain.models import (
    BenefitPackage, Coverage, FeeScheduleItem, InsurancePolicy,
)


@dataclass
class CoverageResult:
    """Result of a coverage determination for a specific service."""
    coverage_id: int
    policy_id: int
    patient_id: int
    service_code: str
    service_category: ServiceCategory | None
    determination: CoverageDetermination
    is_covered: bool
    coverage_percentage: float = 0.0
    copay_percentage: float = 0.0
    copay_amount: Decimal = Decimal("0")
    deductible_applies: bool = True
    deductible_remaining: Decimal = Decimal("0")
    deductible_amount: Decimal = Decimal("0")
    max_out_of_pocket_remaining: Decimal = Decimal("0")
    max_out_of_pocket_total: Decimal = Decimal("0")
    benefit_remaining: Decimal = Decimal("0")
    benefit_total: Decimal = Decimal("0")
    estimated_allowed: Decimal = Decimal("0")
    estimated_patient_responsibility: Decimal = Decimal("0")
    estimated_insurance_payment: Decimal = Decimal("0")
    requires_pre_auth: bool = False
    requires_referral: bool = False
    pre_existing_wait: bool = False
    network_status: str = "in_network"
    denial_reason: str | None = None
    clinical_rules: list[dict[str, Any]] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)


@dataclass
class CoverageRequest:
    """Request to check coverage for a service."""
    patient_id: int
    coverage_id: int
    service_code: str
    service_category: ServiceCategory | None = None
    quantity: int = 1
    billed_amount: Decimal | None = None
    diagnosis_code: str | None = None
    referring_provider_id: int | None = None
    ordering_provider_id: int | None = None
    facility_id: int | None = None
    service_date: date | None = None


class CoverageEngine:
    """Core coverage determination engine.

    Evaluates whether a medical service is covered under a patient's
    insurance policy and calculates financial responsibility.
    """

    def __init__(self, db_session: Any) -> None:
        self._db = db_session

    def determine_coverage(self, request: CoverageRequest) -> CoverageResult:
        """Determine coverage for a given service request.

        This is the main entry point. It evaluates all applicable
        coverage rules and returns a complete CoverageResult.
        """
        coverage = self._get_coverage(request.coverage_id)
        if not coverage:
            return self._not_covered_result(request, "Coverage record not found")

        policy = self._get_policy(coverage.policy_id)
        if not policy:
            return self._not_covered_result(request, "Insurance policy not found")

        if coverage.status != "active":
            return self._not_covered_result(request, f"Coverage status is {coverage.status}")

        if policy.status != "active":
            return self._not_covered_result(request, f"Policy status is {policy.status}")

        service_date = request.service_date or date.today()

        if coverage.end_date and service_date > coverage.end_date:
            return self._not_covered_result(request, "Coverage period has expired")

        if policy.end_date and service_date > policy.end_date:
            return self._not_covered_result(request, "Policy period has expired")

        if coverage.start_date and service_date < coverage.start_date:
            return self._not_covered_result(request, "Coverage period has not started")

        benefit = self._find_matching_benefit(policy.id, request.service_code, request.service_category)
        if not benefit:
            return self._not_covered_result(request, "Service not found in benefit package")

        if not benefit.is_active:
            return self._not_covered_result(request, "Benefit package is not active")

        fee = self._find_fee_schedule_item(policy.provider_id, request.service_code)
        if not fee:
            return self._not_covered_result(request, "Service not in fee schedule")

        if not fee.is_active:
            return self._not_covered_result(request, "Fee schedule item is not active")

        if benefit.age_min or benefit.age_max:
            age_result = self._check_age_rules(benefit, request.patient_id)
            if not age_result["passes"]:
                return self._not_covered_result(request, age_result["reason"])

        if benefit.gender_restriction:
            gender_result = self._check_gender_rules(benefit, request.patient_id)
            if not gender_result["passes"]:
                return self._not_covered_result(request, gender_result["reason"])

        clinical_result = self._check_clinical_rules(benefit, request)
        if not clinical_result["passes"]:
            return self._not_covered_result(request, clinical_result["reason"])

        billed = request.billed_amount or fee.negotiated_price
        allowed = fee.allowed_amount or billed
        quantity = max(request.quantity, 1)

        total_billed = billed * quantity
        total_allowed = allowed * quantity

        copay_pct = benefit.copay_percentage or coverage.copay_percentage or policy.copay_percentage or 0.0
        deduct_applies = benefit.deductible_applies if benefit.deductible_applies is not None else True

        deductible_remaining_val = coverage.deductible_remaining or Decimal("0")
        deductible_total_val = coverage.deductible_total or Decimal("0")
        oop_remaining_val = coverage.max_out_of_pocket_remaining or Decimal("0")
        oop_total_val = coverage.max_out_of_pocket_total or Decimal("0")
        benefit_remaining_val = coverage.benefit_remaining or Decimal("0")
        benefit_total_val = coverage.benefit_total or Decimal("0")

        deductible_amount = Decimal("0")
        if deduct_applies and deductible_remaining_val > 0:
            deductible_amount = min(total_allowed, deductible_remaining_val)
            total_allowed_after_deductible = total_allowed - deductible_amount
        else:
            total_allowed_after_deductible = total_allowed

        copay_amount = Decimal("0")
        if copay_pct > 0:
            copay_amount = (total_allowed_after_deductible * Decimal(str(copay_pct))) / Decimal("100")

        coverage_pct = benefit.coverage_percentage or 100.0
        insurance_payment = (total_allowed_after_deductible - copay_amount) * Decimal(str(coverage_pct)) / Decimal("100")
        patient_responsibility = (total_allowed_after_deductible - insurance_payment) + copay_amount + deductible_amount

        copay_amount_val = min(copay_amount, total_allowed_after_deductible)
        total_insurance_payment = min(insurance_payment, benefit_remaining_val) if benefit_remaining_val > 0 else insurance_payment

        messages = [
            f"Service {request.service_code} is covered",
            f"Coverage percentage: {coverage_pct}%",
        ]
        if copay_pct > 0:
            messages.append(f"Copay: {copay_pct}%")
        if deduct_applies and deductible_remaining_val > 0:
            messages.append(f"Deductible applies: {deductible_remaining_val} remaining")
        if benefit.requires_pre_auth:
            messages.append("Prior authorization required")

        is_covered = True
        determination = CoverageDetermination.COVERED

        if patient_responsibility >= total_allowed:
            determination = CoverageDetermination.PARTIAL

        if benefit.max_benefit_per_claim and total_allowed > benefit.max_benefit_per_claim:
            if total_allowed > benefit.max_benefit_per_claim:
                messages.append(f"Service exceeds max per-claim benefit: {benefit.max_benefit_per_claim}")
                determination = CoverageDetermination.PARTIAL

        if benefit.max_visits_per_year:
            messages.append(f"Visit limit: {benefit.max_visits_per_year} per year")

        if benefit.max_benefit_lifetime and benefit_remaining_val <= 0:
            determination = CoverageDetermination.NOT_COVERED
            is_covered = False
            messages.append("Lifetime benefit exhausted")

        limited_benefit = min(total_insurance_payment, benefit_remaining_val) if benefit_remaining_val > 0 else total_insurance_payment

        return CoverageResult(
            coverage_id=coverage.id,
            policy_id=policy.id,
            patient_id=request.patient_id,
            service_code=request.service_code,
            service_category=request.service_category or benefit.service_category,
            determination=determination,
            is_covered=is_covered,
            coverage_percentage=coverage_pct,
            copay_percentage=copay_pct,
            copay_amount=copay_amount_val,
            deductible_applies=deduct_applies,
            deductible_remaining=deductible_remaining_val,
            deductible_amount=deductible_amount,
            max_out_of_pocket_remaining=oop_remaining_val,
            max_out_of_pocket_total=oop_total_val,
            benefit_remaining=benefit_remaining_val,
            benefit_total=benefit_total_val,
            estimated_allowed=total_allowed,
            estimated_patient_responsibility=patient_responsibility,
            estimated_insurance_payment=limited_benefit,
            requires_pre_auth=benefit.requires_pre_auth,
            requires_referral=benefit.requires_referral,
            pre_existing_wait=benefit.pre_existing_wait_period if hasattr(benefit, "pre_existing_wait_period") else False,
            network_status=coverage.network_status or "in_network",
            denial_reason=None,
            clinical_rules=clinical_result.get("rules", []),
            messages=messages,
        )

    def _get_coverage(self, coverage_id: int) -> Coverage | None:
        return self._db.query(Coverage).filter(Coverage.id == coverage_id).first()

    def _get_policy(self, policy_id: int) -> InsurancePolicy | None:
        return self._db.query(InsurancePolicy).filter(InsurancePolicy.id == policy_id).first()

    def _find_matching_benefit(
        self,
        policy_id: int,
        service_code: str,
        service_category: ServiceCategory | None,
    ) -> BenefitPackage | None:
        benefit = (
            self._db.query(BenefitPackage)
            .filter(
                BenefitPackage.policy_id == policy_id,
                BenefitPackage.is_active == True,
            )
            .first()
        )
        return benefit

    def _find_fee_schedule_item(
        self,
        provider_id: int,
        service_code: str,
    ) -> FeeScheduleItem | None:
        return (
            self._db.query(FeeScheduleItem)
            .filter(
                FeeScheduleItem.provider_id == provider_id,
                FeeScheduleItem.service_code == service_code,
                FeeScheduleItem.is_active == True,
            )
            .first()
        )

    def _check_age_rules(self, benefit: BenefitPackage, patient_id: int) -> dict[str, Any]:
        patient = self._db.execute(
            "SELECT date_of_birth FROM patients WHERE id = :pid",
            {"pid": patient_id},
        ).first()
        if not patient or not patient.date_of_birth:
            return {"passes": True, "reason": ""}

        dob = patient.date_of_birth
        if isinstance(dob, datetime):
            dob = dob.date()
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        if benefit.age_min is not None and age < benefit.age_min:
            return {"passes": False, "reason": f"Patient age {age} is below minimum {benefit.age_min}"}
        if benefit.age_max is not None and age > benefit.age_max:
            return {"passes": False, "reason": f"Patient age {age} exceeds maximum {benefit.age_max}"}
        return {"passes": True, "reason": ""}

    def _check_gender_rules(self, benefit: BenefitPackage, patient_id: int) -> dict[str, Any]:
        patient = self._db.execute(
            "SELECT gender FROM patients WHERE id = :pid",
            {"pid": patient_id},
        ).first()
        if patient and patient.gender and benefit.gender_restriction:
            if patient.gender.lower() != benefit.gender_restriction.lower():
                return {"passes": False, "reason": f"Gender restriction: {benefit.gender_restriction}"}
        return {"passes": True, "reason": ""}

    def _check_clinical_rules(
        self,
        benefit: BenefitPackage,
        request: CoverageRequest,
    ) -> dict[str, Any]:
        rules: list[dict[str, Any]] = []
        passes = True
        reason = ""

        if request.diagnosis_code and benefit.exclusions:
            exclusions = benefit.exclusions if isinstance(benefit.exclusions, list) else []
            for exclusion in exclusions:
                if isinstance(exclusion.get("diagnosis_codes"), list):
                    if request.diagnosis_code in exclusion["diagnosis_codes"]:
                        passes = False
                        reason = exclusion.get("reason", "Diagnosis excluded from coverage")
                        rules.append({"rule": "diagnosis_exclusion", "detail": reason})
                        break

        return {"passes": passes, "reason": reason, "rules": rules}

    def _not_covered_result(self, request: CoverageRequest, reason: str) -> CoverageResult:
        return CoverageResult(
            coverage_id=request.coverage_id,
            policy_id=0,
            patient_id=request.patient_id,
            service_code=request.service_code,
            service_category=request.service_category,
            determination=CoverageDetermination.NOT_COVERED,
            is_covered=False,
            denial_reason=reason,
            messages=[reason],
        )


class CoverageValidator:
    """Validates patient coverage and eligibility in real-time."""

    def __init__(self, db_session: Any) -> None:
        self._db = db_session

    def validate_coverage(self, coverage_id: int, service_date: date | None = None) -> dict[str, Any]:
        svc_date = service_date or date.today()
        coverage = self._db.query(Coverage).filter(Coverage.id == coverage_id).first()
        if not coverage:
            return {"valid": False, "reason": "Coverage not found"}

        if coverage.status != "active":
            return {"valid": False, "reason": f"Coverage status: {coverage.status}"}

        if coverage.end_date and svc_date > coverage.end_date:
            return {"valid": False, "reason": "Coverage expired"}

        if svc_date < coverage.start_date:
            return {"valid": False, "reason": "Coverage not yet active"}

        policy = self._db.query(InsurancePolicy).filter(InsurancePolicy.id == coverage.policy_id).first()
        if not policy:
            return {"valid": False, "reason": "Policy not found"}

        if policy.status != "active":
            return {"valid": False, "reason": f"Policy status: {policy.status}"}

        return {
            "valid": True,
            "coverage_id": coverage.id,
            "policy_id": policy.id,
            "patient_id": coverage.patient_id,
            "status": coverage.status,
            "network_status": coverage.network_status,
            "benefit_remaining": float(coverage.benefit_remaining or 0),
            "deductible_remaining": float(coverage.deductible_remaining or 0),
            "requires_pre_auth": coverage.authorization_required,
            "requires_referral": coverage.referral_required,
        }
