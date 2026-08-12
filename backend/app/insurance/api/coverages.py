from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.database import get_db
from app.insurance.domain.enums import CoverageStatus
from app.insurance.domain.models import (
    BenefitPackage,
    BenefitUtilization,
    Coverage,
    DeductibleTracking,
    InsurancePolicy,
)
from app.insurance.services.coverage_engine import CoverageValidator
from app.models.lab_user import LabUser
from app.security.dependencies import get_current_user
from app.services.audit_service import log_action

router = APIRouter(prefix="/coverages", tags=["insurance-coverages"])


class CoverageCreate(BaseModel):
    policy_id: int
    patient_id: int
    dependent_id: int | None = None
    subscriber_relation: str | None = None
    start_date: date
    end_date: date | None = None
    copay_percentage: float | None = None
    deductible_amount: Decimal | None = None
    deductible_total: Decimal | None = None
    max_out_of_pocket: Decimal | None = None
    benefit_total: Decimal | None = None
    network_status: str = "in_network"
    authorization_required: bool = False
    referral_required: bool = False
    pre_existing_wait_period: bool = False
    notes: str | None = None


class CoverageUpdate(BaseModel):
    end_date: date | None = None
    copay_percentage: float | None = None
    deductible_remaining: Decimal | None = None
    deductible_total: Decimal | None = None
    max_out_of_pocket_remaining: Decimal | None = None
    max_out_of_pocket_total: Decimal | None = None
    benefit_remaining: Decimal | None = None
    benefit_total: Decimal | None = None
    network_status: str | None = None
    authorization_required: bool | None = None
    referral_required: bool | None = None
    notes: str | None = None


class CoverageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lab_id: int
    policy_id: int
    patient_id: int
    dependent_id: int | None = None
    status: CoverageStatus
    subscriber_relation: str | None = None
    start_date: date
    end_date: date | None = None
    verification_date: date | None = None
    copay_percentage: float | None = None
    deductible_remaining: Decimal | None = None
    deductible_total: Decimal | None = None
    max_out_of_pocket_remaining: Decimal | None = None
    max_out_of_pocket_total: Decimal | None = None
    benefit_remaining: Decimal | None = None
    benefit_total: Decimal | None = None
    network_status: str | None = None
    authorization_required: bool
    referral_required: bool
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@router.get("", response_model=list[CoverageResponse])
def list_coverages(
    patient_id: int | None = Query(None),
    policy_id: int | None = Query(None),
    status: CoverageStatus | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Coverage).filter(Coverage.lab_id == current_user.lab_id)
    if patient_id:
        q = q.filter(Coverage.patient_id == patient_id)
    if policy_id:
        q = q.filter(Coverage.policy_id == policy_id)
    if status:
        q = q.filter(Coverage.status == status)
    if date_from:
        q = q.filter(Coverage.start_date >= date_from)
    if date_to:
        q = q.filter(Coverage.end_date <= date_to)
    return q.order_by(Coverage.created_at.desc()).offset(skip).limit(limit).all()


@router.post("", status_code=201, response_model=CoverageResponse)
def create_coverage(
    data: CoverageCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    policy = db.query(InsurancePolicy).filter(
        InsurancePolicy.id == data.policy_id,
        InsurancePolicy.lab_id == current_user.lab_id,
    ).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    if policy.status.value != "active":
        raise HTTPException(status_code=400, detail=f"Policy status is '{policy.status.value}', must be active")

    coverage = Coverage(
        lab_id=current_user.lab_id,
        status=CoverageStatus.ACTIVE,
        deductible_remaining=data.deductible_amount or data.deductible_total or Decimal(0),
        deductible_total=data.deductible_total or data.deductible_amount or Decimal(0),
        max_out_of_pocket_total=data.max_out_of_pocket or Decimal(0),
        max_out_of_pocket_remaining=data.max_out_of_pocket or Decimal(0),
        benefit_total=data.benefit_total or Decimal(0),
        benefit_remaining=data.benefit_total or Decimal(0),
        **data.model_dump(exclude={"deductible_amount", "max_out_of_pocket", "benefit_total"}),
    )
    db.add(coverage)
    db.flush()

    log_action(
        db=db,
        action="insurance.coverage.create",
        resource_type="coverage",
        resource_id=coverage.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Created coverage for patient {coverage.patient_id} under policy '{policy.policy_number}'",
    )
    db.commit()
    db.refresh(coverage)
    return coverage


@router.get("/{coverage_id}", response_model=CoverageResponse)
def get_coverage(
    coverage_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    coverage = db.query(Coverage).filter(
        Coverage.id == coverage_id,
        Coverage.lab_id == current_user.lab_id,
    ).first()
    if not coverage:
        raise HTTPException(status_code=404, detail="Coverage not found")
    return coverage


@router.put("/{coverage_id}", response_model=CoverageResponse)
def update_coverage(
    coverage_id: int,
    data: CoverageUpdate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    coverage = db.query(Coverage).filter(
        Coverage.id == coverage_id,
        Coverage.lab_id == current_user.lab_id,
    ).first()
    if not coverage:
        raise HTTPException(status_code=404, detail="Coverage not found")

    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    for field, value in update_data.items():
        setattr(coverage, field, value)

    log_action(
        db=db,
        action="insurance.coverage.update",
        resource_type="coverage",
        resource_id=coverage.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Updated coverage {coverage.id} for patient {coverage.patient_id}",
    )
    db.commit()
    db.refresh(coverage)
    return coverage


@router.delete("/{coverage_id}", status_code=204)
def terminate_coverage(
    coverage_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    coverage = db.query(Coverage).filter(
        Coverage.id == coverage_id,
        Coverage.lab_id == current_user.lab_id,
    ).first()
    if not coverage:
        raise HTTPException(status_code=404, detail="Coverage not found")
    if coverage.status in (CoverageStatus.TERMINATED, CoverageStatus.CANCELLED, CoverageStatus.EXPIRED):
        raise HTTPException(status_code=400, detail=f"Coverage is already {coverage.status.value}")

    coverage.status = CoverageStatus.TERMINATED
    coverage.end_date = date.today()

    log_action(
        db=db,
        action="insurance.coverage.terminate",
        resource_type="coverage",
        resource_id=coverage.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Terminated coverage {coverage.id} for patient {coverage.patient_id}",
    )
    db.commit()


@router.post("/{coverage_id}/verify", response_model=dict)
def verify_coverage(
    coverage_id: int,
    service_date: date | None = None,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    coverage = db.query(Coverage).filter(
        Coverage.id == coverage_id,
        Coverage.lab_id == current_user.lab_id,
    ).first()
    if not coverage:
        raise HTTPException(status_code=404, detail="Coverage not found")

    validator = CoverageValidator(db)
    result = validator.validate_coverage(coverage_id, service_date)

    if result.get("valid"):
        coverage.verification_date = date.today()
        db.commit()

    return result


@router.get("/{coverage_id}/benefits", response_model=dict)
def list_coverage_benefits(
    coverage_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    coverage = db.query(Coverage).filter(
        Coverage.id == coverage_id,
        Coverage.lab_id == current_user.lab_id,
    ).first()
    if not coverage:
        raise HTTPException(status_code=404, detail="Coverage not found")

    db.query(InsurancePolicy).filter(
        InsurancePolicy.id == coverage.policy_id,
    ).first()

    benefits = db.query(BenefitPackage).filter(
        BenefitPackage.policy_id == coverage.policy_id,
        BenefitPackage.is_active,
    ).all()

    utilization = db.query(BenefitUtilization).filter(
        BenefitUtilization.coverage_id == coverage_id,
    ).all()

    util_by_service = {u.service_code: u for u in utilization if u.service_code}

    return {
        "coverage_id": coverage_id,
        "patient_id": coverage.patient_id,
        "policy_id": coverage.policy_id,
        "deductible_remaining": float(coverage.deductible_remaining or 0),
        "deductible_total": float(coverage.deductible_total or 0),
        "max_out_of_pocket_remaining": float(coverage.max_out_of_pocket_remaining or 0),
        "benefit_remaining": float(coverage.benefit_remaining or 0),
        "benefit_total": float(coverage.benefit_total or 0),
        "benefits": [
            {
                "id": b.id,
                "name": b.name,
                "code": b.code,
                "service_category": b.service_category.value if b.service_category else None,
                "coverage_percentage": b.coverage_percentage,
                "copay_percentage": b.copay_percentage,
                "max_benefit_per_claim": float(b.max_benefit_per_claim) if b.max_benefit_per_claim else None,
                "max_benefit_per_year": float(b.max_benefit_per_year) if b.max_benefit_per_year else None,
                "max_visits_per_year": b.max_visits_per_year,
                "requires_pre_auth": b.requires_pre_auth,
                "remaining": float(util_by_service.get(b.code, BenefitUtilization()).total_remaining) if b.code in util_by_service else None,
            }
            for b in benefits
        ],
    }


@router.get("/{coverage_id}/utilization", response_model=dict)
def coverage_utilization_report(
    coverage_id: int,
    year: int | None = Query(None),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    coverage = db.query(Coverage).filter(
        Coverage.id == coverage_id,
        Coverage.lab_id == current_user.lab_id,
    ).first()
    if not coverage:
        raise HTTPException(status_code=404, detail="Coverage not found")

    cal_year = year or date.today().year

    deductible = db.query(DeductibleTracking).filter(
        DeductibleTracking.coverage_id == coverage_id,
        DeductibleTracking.calendar_year == cal_year,
    ).first()

    utilization = db.query(BenefitUtilization).filter(
        BenefitUtilization.coverage_id == coverage_id,
    ).all()

    return {
        "coverage_id": coverage_id,
        "patient_id": coverage.patient_id,
        "year": cal_year,
        "deductible": {
            "total": float(deductible.total_deductible) if deductible else float(coverage.deductible_total or 0),
            "applied": float(deductible.applied_deductible) if deductible else 0,
            "remaining": float(deductible.remaining_deductible) if deductible else float(coverage.deductible_remaining or 0),
            "is_met": deductible.is_met if deductible else False,
        } if deductible or coverage.deductible_total else None,
        "utilization": [
            {
                "service_code": u.service_code,
                "benefit_type": u.benefit_type,
                "total_used": float(u.total_used),
                "total_remaining": float(u.total_remaining),
                "max_limit": float(u.max_limit),
                "utilization_percentage": u.utilization_percentage,
                "is_exhausted": u.is_exhausted,
                "visit_count": u.visit_count,
                "max_visits": u.max_visits,
            }
            for u in utilization
        ],
        "total_benefit_remaining": float(coverage.benefit_remaining or 0),
        "total_benefit_total": float(coverage.benefit_total or 0),
    }
