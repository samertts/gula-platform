from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.insurance.domain.enums import CoverageStatus, ServiceCategory
from app.insurance.domain.models import Coverage, InsurancePolicy
from app.insurance.services.coverage_engine import (
    CoverageEngine,
    CoverageRequest,
    CoverageResult,
    CoverageValidator,
)
from app.models.lab_user import LabUser
from app.security.dependencies import get_current_user

router = APIRouter(prefix="/coverage", tags=["insurance-coverage-check"])


class CoverageCheckRequest(BaseModel):
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


class CoverageCheckResponse(BaseModel):
    coverage_id: int
    policy_id: int
    patient_id: int
    service_code: str
    service_category: str | None = None
    determination: str
    is_covered: bool
    coverage_percentage: float = 0.0
    copay_percentage: float = 0.0
    copay_amount: float = 0.0
    deductible_applies: bool = True
    deductible_remaining: float = 0.0
    deductible_amount: float = 0.0
    max_out_of_pocket_remaining: float = 0.0
    max_out_of_pocket_total: float = 0.0
    benefit_remaining: float = 0.0
    benefit_total: float = 0.0
    estimated_allowed: float = 0.0
    estimated_patient_responsibility: float = 0.0
    estimated_insurance_payment: float = 0.0
    requires_pre_auth: bool = False
    requires_referral: bool = False
    network_status: str = "in_network"
    denial_reason: str | None = None
    messages: list[str] = []


class EligibilityRequest(BaseModel):
    patient_id: int
    coverage_id: int
    service_date: date | None = None
    service_code: str | None = None


class EligibilityResponse(BaseModel):
    eligible: bool
    coverage_id: int
    patient_id: int
    status: str | None = None
    network_status: str | None = None
    benefit_remaining: float = 0.0
    deductible_remaining: float = 0.0
    requires_pre_auth: bool = False
    requires_referral: bool = False
    messages: list[str] = []


class EstimateRequest(BaseModel):
    patient_id: int
    coverage_id: int
    service_code: str
    service_category: ServiceCategory | None = None
    quantity: int = 1
    billed_amount: Decimal | None = None
    diagnosis_code: str | None = None


class EstimateResponse(BaseModel):
    total_billed: float
    estimated_allowed: float
    deductible_amount: float
    copay_amount: float
    insurance_payment: float
    patient_responsibility: float
    coverage_percentage: float
    is_covered: bool
    messages: list[str] = []


def _result_to_response(result: CoverageResult) -> CoverageCheckResponse:
    return CoverageCheckResponse(
        coverage_id=result.coverage_id,
        policy_id=result.policy_id,
        patient_id=result.patient_id,
        service_code=result.service_code,
        service_category=result.service_category.value if result.service_category else None,
        determination=result.determination.value,
        is_covered=result.is_covered,
        coverage_percentage=result.coverage_percentage,
        copay_percentage=result.copay_percentage,
        copay_amount=float(result.copay_amount),
        deductible_applies=result.deductible_applies,
        deductible_remaining=float(result.deductible_remaining),
        deductible_amount=float(result.deductible_amount),
        max_out_of_pocket_remaining=float(result.max_out_of_pocket_remaining),
        max_out_of_pocket_total=float(result.max_out_of_pocket_total),
        benefit_remaining=float(result.benefit_remaining),
        benefit_total=float(result.benefit_total),
        estimated_allowed=float(result.estimated_allowed),
        estimated_patient_responsibility=float(result.estimated_patient_responsibility),
        estimated_insurance_payment=float(result.estimated_insurance_payment),
        requires_pre_auth=result.requires_pre_auth,
        requires_referral=result.requires_referral,
        network_status=result.network_status,
        denial_reason=result.denial_reason,
        messages=result.messages,
    )


@router.post("/check", response_model=CoverageCheckResponse)
def check_coverage(
    data: CoverageCheckRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    coverage = (
        db.query(Coverage)
        .filter(
            Coverage.id == data.coverage_id,
            Coverage.lab_id == current_user.lab_id,
        )
        .first()
    )
    if not coverage:
        raise HTTPException(status_code=404, detail="Coverage not found")

    engine = CoverageEngine(db)
    request = CoverageRequest(**data.model_dump())
    result = engine.determine_coverage(request)
    return _result_to_response(result)


@router.post("/eligibility", response_model=EligibilityResponse)
def check_eligibility(
    data: EligibilityRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    coverage = (
        db.query(Coverage)
        .filter(
            Coverage.id == data.coverage_id,
            Coverage.lab_id == current_user.lab_id,
        )
        .first()
    )
    if not coverage:
        raise HTTPException(status_code=404, detail="Coverage not found")

    validator = CoverageValidator(db)
    result = validator.validate_coverage(data.coverage_id, data.service_date)

    messages = []
    if result.get("valid"):
        messages.append("Coverage is valid and active")
    else:
        messages.append(result.get("reason", "Coverage is not valid"))

    return EligibilityResponse(
        eligible=result.get("valid", False),
        coverage_id=data.coverage_id,
        patient_id=data.patient_id,
        status=result.get("status"),
        network_status=result.get("network_status"),
        benefit_remaining=float(result.get("benefit_remaining", 0)),
        deductible_remaining=float(result.get("deductible_remaining", 0)),
        requires_pre_auth=result.get("requires_pre_auth", False),
        requires_referral=result.get("requires_referral", False),
        messages=messages,
    )


@router.post("/verify", response_model=dict)
def verify_coverage(
    patient_id: int = Query(...),
    policy_number: str | None = Query(None),
    provider_code: str | None = Query(None),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.insurance.domain.models import InsuranceProvider

    q = db.query(Coverage).filter(
        Coverage.lab_id == current_user.lab_id,
        Coverage.patient_id == patient_id,
        Coverage.status == CoverageStatus.ACTIVE,
    )

    if policy_number:
        q = q.join(InsurancePolicy).filter(InsurancePolicy.policy_number == policy_number)

    if provider_code:
        q = (
            q.join(InsurancePolicy)
            .join(
                InsuranceProvider,
                InsurancePolicy.provider_id == InsuranceProvider.id,
            )
            .filter(InsuranceProvider.code == provider_code)
        )

    coverages = q.all()

    if not coverages:
        return {
            "verified": False,
            "patient_id": patient_id,
            "message": "No active coverage found",
            "coverages": [],
        }

    return {
        "verified": True,
        "patient_id": patient_id,
        "message": f"Found {len(coverages)} active coverage(s)",
        "coverages": [
            {
                "id": c.id,
                "policy_id": c.policy_id,
                "status": c.status.value,
                "start_date": c.start_date.isoformat(),
                "end_date": c.end_date.isoformat() if c.end_date else None,
                "network_status": c.network_status,
                "benefit_remaining": float(c.benefit_remaining or 0),
            }
            for c in coverages
        ],
    }


@router.get("/{patient_id}/active", response_model=list[dict])
def list_active_coverages(
    patient_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    coverages = (
        db.query(Coverage)
        .filter(
            Coverage.lab_id == current_user.lab_id,
            Coverage.patient_id == patient_id,
            Coverage.status == CoverageStatus.ACTIVE,
        )
        .all()
    )

    return [
        {
            "id": c.id,
            "policy_id": c.policy_id,
            "status": c.status.value,
            "start_date": c.start_date.isoformat(),
            "end_date": c.end_date.isoformat() if c.end_date else None,
            "copay_percentage": c.copay_percentage,
            "deductible_remaining": float(c.deductible_remaining or 0),
            "benefit_remaining": float(c.benefit_remaining or 0),
            "network_status": c.network_status,
        }
        for c in coverages
    ]


@router.get("/{patient_id}/benefits", response_model=dict)
def patient_benefits_summary(
    patient_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.insurance.domain.models import BenefitPackage

    coverages = (
        db.query(Coverage)
        .filter(
            Coverage.lab_id == current_user.lab_id,
            Coverage.patient_id == patient_id,
            Coverage.status == CoverageStatus.ACTIVE,
        )
        .all()
    )

    if not coverages:
        return {
            "patient_id": patient_id,
            "has_active_coverage": False,
            "coverages": [],
        }

    result_coverages = []
    for coverage in coverages:
        policy = (
            db.query(InsurancePolicy)
            .filter(
                InsurancePolicy.id == coverage.policy_id,
            )
            .first()
        )

        benefits = (
            db.query(BenefitPackage)
            .filter(
                BenefitPackage.policy_id == coverage.policy_id,
                BenefitPackage.is_active,
            )
            .all()
        )

        result_coverages.append(
            {
                "coverage_id": coverage.id,
                "policy_id": coverage.policy_id,
                "policy_number": policy.policy_number if policy else None,
                "status": coverage.status.value,
                "start_date": coverage.start_date.isoformat(),
                "end_date": coverage.end_date.isoformat() if coverage.end_date else None,
                "deductible": {
                    "remaining": float(coverage.deductible_remaining or 0),
                    "total": float(coverage.deductible_total or 0),
                },
                "benefit": {
                    "remaining": float(coverage.benefit_remaining or 0),
                    "total": float(coverage.benefit_total or 0),
                },
                "max_out_of_pocket": {
                    "remaining": float(coverage.max_out_of_pocket_remaining or 0),
                    "total": float(coverage.max_out_of_pocket_total or 0),
                },
                "benefits": [
                    {
                        "id": b.id,
                        "name": b.name,
                        "code": b.code,
                        "service_category": b.service_category.value
                        if b.service_category
                        else None,
                        "coverage_percentage": b.coverage_percentage,
                        "copay_percentage": b.copay_percentage,
                        "requires_pre_auth": b.requires_pre_auth,
                        "requires_referral": b.requires_referral,
                    }
                    for b in benefits
                ],
            }
        )

    return {
        "patient_id": patient_id,
        "has_active_coverage": True,
        "total_coverages": len(result_coverages),
        "coverages": result_coverages,
    }


@router.post("/estimate", response_model=EstimateResponse)
def estimate_patient_responsibility(
    data: EstimateRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    coverage = (
        db.query(Coverage)
        .filter(
            Coverage.id == data.coverage_id,
            Coverage.lab_id == current_user.lab_id,
        )
        .first()
    )
    if not coverage:
        raise HTTPException(status_code=404, detail="Coverage not found")

    engine = CoverageEngine(db)
    request = CoverageRequest(
        patient_id=data.patient_id,
        coverage_id=data.coverage_id,
        service_code=data.service_code,
        service_category=data.service_category,
        quantity=data.quantity,
        billed_amount=data.billed_amount,
        diagnosis_code=data.diagnosis_code,
    )
    result = engine.determine_coverage(request)

    return EstimateResponse(
        total_billed=float(data.billed_amount or 0),
        estimated_allowed=float(result.estimated_allowed),
        deductible_amount=float(result.deductible_amount),
        copay_amount=float(result.copay_amount),
        insurance_payment=float(result.estimated_insurance_payment),
        patient_responsibility=float(result.estimated_patient_responsibility),
        coverage_percentage=result.coverage_percentage,
        is_covered=result.is_covered,
        messages=result.messages,
    )
