from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.insurance.domain.enums import PolicyStatus, ServiceCategory
from app.insurance.domain.models import BenefitPackage, InsurancePolicy, InsuranceProvider
from app.models.lab_user import LabUser
from app.security.dependencies import get_current_user
from app.services.audit_service import log_action

router = APIRouter(prefix="/policies", tags=["insurance-policies"])


class PolicyCreate(BaseModel):
    provider_id: int
    policy_number: str
    group_number: Optional[str] = None
    policy_holder_id: int
    subscriber_id: Optional[str] = None
    subscriber_name: Optional[str] = None
    subscriber_relation: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    grace_period_days: int = 30
    premium_amount: Optional[Decimal] = None
    premium_currency: str = "IQD"
    premium_frequency: str = "monthly"
    copay_percentage: Optional[float] = None
    deductible_amount: Optional[Decimal] = None
    max_out_of_pocket: Optional[Decimal] = None
    max_lifetime_benefit: Optional[Decimal] = None
    terms_text: Optional[str] = None
    exclusions_text: Optional[str] = None


class PolicyUpdate(BaseModel):
    group_number: Optional[str] = None
    end_date: Optional[date] = None
    grace_period_days: Optional[int] = None
    premium_amount: Optional[Decimal] = None
    premium_currency: Optional[str] = None
    premium_frequency: Optional[str] = None
    copay_percentage: Optional[float] = None
    deductible_amount: Optional[Decimal] = None
    max_out_of_pocket: Optional[Decimal] = None
    max_lifetime_benefit: Optional[Decimal] = None
    terms_text: Optional[str] = None
    exclusions_text: Optional[str] = None


class PolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lab_id: int
    provider_id: int
    policy_number: str
    group_number: Optional[str] = None
    status: PolicyStatus
    policy_holder_id: int
    subscriber_id: Optional[str] = None
    subscriber_name: Optional[str] = None
    subscriber_relation: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    grace_period_days: int
    premium_amount: Optional[Decimal] = None
    premium_currency: Optional[str] = None
    premium_frequency: Optional[str] = None
    copay_percentage: Optional[float] = None
    deductible_amount: Optional[Decimal] = None
    max_out_of_pocket: Optional[Decimal] = None
    max_lifetime_benefit: Optional[Decimal] = None
    terms_text: Optional[str] = None
    exclusions_text: Optional[str] = None
    signed_at: Optional[str] = None
    cancelled_at: Optional[str] = None
    cancellation_reason: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class BenefitPackageCreate(BaseModel):
    provider_id: int
    policy_id: Optional[int] = None
    name: str
    name_ar: Optional[str] = None
    code: str
    description: Optional[str] = None
    service_category: Optional[ServiceCategory] = None
    is_mandatory: bool = False
    coverage_percentage: float = 100.0
    copay_percentage: float = 0.0
    deductible_applies: bool = True
    max_benefit_per_claim: Optional[Decimal] = None
    max_benefit_per_year: Optional[Decimal] = None
    max_benefit_lifetime: Optional[Decimal] = None
    max_visits_per_year: Optional[int] = None
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    gender_restriction: Optional[str] = None
    requires_pre_auth: bool = False
    requires_referral: bool = False


class BenefitPackageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lab_id: int
    provider_id: int
    policy_id: Optional[int] = None
    name: str
    name_ar: Optional[str] = None
    code: str
    description: Optional[str] = None
    service_category: Optional[ServiceCategory] = None
    is_mandatory: bool
    is_active: bool
    coverage_percentage: Optional[float] = None
    copay_percentage: Optional[float] = None
    deductible_applies: bool
    max_benefit_per_claim: Optional[Decimal] = None
    max_benefit_per_year: Optional[Decimal] = None
    max_benefit_lifetime: Optional[Decimal] = None
    max_visits_per_year: Optional[int] = None
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    gender_restriction: Optional[str] = None
    requires_pre_auth: bool
    requires_referral: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.get("", response_model=list[PolicyResponse])
def list_policies(
    provider_id: Optional[int] = Query(None),
    status: Optional[PolicyStatus] = Query(None),
    policy_holder_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(InsurancePolicy).filter(InsurancePolicy.lab_id == current_user.lab_id)
    if provider_id:
        q = q.filter(InsurancePolicy.provider_id == provider_id)
    if status:
        q = q.filter(InsurancePolicy.status == status)
    if policy_holder_id:
        q = q.filter(InsurancePolicy.policy_holder_id == policy_holder_id)
    if search:
        like = f"%{search}%"
        q = q.filter(InsurancePolicy.policy_number.ilike(like))
    return q.order_by(InsurancePolicy.created_at.desc()).offset(skip).limit(limit).all()


@router.post("", status_code=201, response_model=PolicyResponse)
def create_policy(
    data: PolicyCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    provider = db.query(InsuranceProvider).filter(
        InsuranceProvider.id == data.provider_id,
        InsuranceProvider.lab_id == current_user.lab_id,
    ).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    existing = db.query(InsurancePolicy).filter(
        InsurancePolicy.lab_id == current_user.lab_id,
        InsurancePolicy.policy_number == data.policy_number,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Policy '{data.policy_number}' already exists")

    policy = InsurancePolicy(
        lab_id=current_user.lab_id,
        status=PolicyStatus.DRAFT,
        **data.model_dump(),
    )
    db.add(policy)
    db.flush()

    log_action(
        db=db,
        action="insurance.policy.create",
        resource_type="insurance_policy",
        resource_id=policy.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Created policy '{policy.policy_number}' for provider '{provider.name}'",
    )
    db.commit()
    db.refresh(policy)
    return policy


@router.get("/{policy_id}", response_model=PolicyResponse)
def get_policy(
    policy_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    policy = db.query(InsurancePolicy).filter(
        InsurancePolicy.id == policy_id,
        InsurancePolicy.lab_id == current_user.lab_id,
    ).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.put("/{policy_id}", response_model=PolicyResponse)
def update_policy(
    policy_id: int,
    data: PolicyUpdate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    policy = db.query(InsurancePolicy).filter(
        InsurancePolicy.id == policy_id,
        InsurancePolicy.lab_id == current_user.lab_id,
    ).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    for field, value in update_data.items():
        setattr(policy, field, value)

    log_action(
        db=db,
        action="insurance.policy.update",
        resource_type="insurance_policy",
        resource_id=policy.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Updated policy '{policy.policy_number}'",
    )
    db.commit()
    db.refresh(policy)
    return policy


@router.delete("/{policy_id}", status_code=204)
def cancel_policy(
    policy_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    policy = db.query(InsurancePolicy).filter(
        InsurancePolicy.id == policy_id,
        InsurancePolicy.lab_id == current_user.lab_id,
    ).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    if policy.status == PolicyStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Policy is already cancelled")

    policy.status = PolicyStatus.CANCELLED
    policy.cancelled_at = __import__("datetime").datetime.utcnow()

    log_action(
        db=db,
        action="insurance.policy.cancel",
        resource_type="insurance_policy",
        resource_id=policy.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Cancelled policy '{policy.policy_number}'",
    )
    db.commit()


@router.get("/{policy_id}/coverages", response_model=list)
def list_policy_coverages(
    policy_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.insurance.domain.models import Coverage

    policy = db.query(InsurancePolicy).filter(
        InsurancePolicy.id == policy_id,
        InsurancePolicy.lab_id == current_user.lab_id,
    ).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    return db.query(Coverage).filter(
        Coverage.policy_id == policy_id,
        Coverage.lab_id == current_user.lab_id,
    ).order_by(Coverage.created_at.desc()).all()


@router.post("/{policy_id}/coverages", status_code=201, response_model=dict)
def add_policy_coverage(
    policy_id: int,
    patient_id: int = Query(...),
    start_date: date = Query(...),
    end_date: Optional[date] = Query(None),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.insurance.domain.enums import CoverageStatus
    from app.insurance.domain.models import Coverage

    policy = db.query(InsurancePolicy).filter(
        InsurancePolicy.id == policy_id,
        InsurancePolicy.lab_id == current_user.lab_id,
    ).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    coverage = Coverage(
        lab_id=current_user.lab_id,
        policy_id=policy_id,
        patient_id=patient_id,
        start_date=start_date,
        end_date=end_date,
        status=CoverageStatus.ACTIVE,
    )
    db.add(coverage)
    db.flush()

    log_action(
        db=db,
        action="insurance.policy.coverage.add",
        resource_type="coverage",
        resource_id=coverage.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Added coverage for patient {patient_id} under policy '{policy.policy_number}'",
    )
    db.commit()
    db.refresh(coverage)
    return {"id": coverage.id, "patient_id": coverage.patient_id, "status": coverage.status.value}


@router.get("/{policy_id}/benefits", response_model=list[BenefitPackageResponse])
def list_policy_benefits(
    policy_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    policy = db.query(InsurancePolicy).filter(
        InsurancePolicy.id == policy_id,
        InsurancePolicy.lab_id == current_user.lab_id,
    ).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    return db.query(BenefitPackage).filter(
        BenefitPackage.policy_id == policy_id,
        BenefitPackage.lab_id == current_user.lab_id,
    ).order_by(BenefitPackage.name).all()


@router.post("/{policy_id}/benefits", status_code=201, response_model=BenefitPackageResponse)
def add_policy_benefit(
    policy_id: int,
    data: BenefitPackageCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    policy = db.query(InsurancePolicy).filter(
        InsurancePolicy.id == policy_id,
        InsurancePolicy.lab_id == current_user.lab_id,
    ).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    provider = db.query(InsuranceProvider).filter(
        InsuranceProvider.id == data.provider_id,
        InsuranceProvider.lab_id == current_user.lab_id,
    ).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    existing = db.query(BenefitPackage).filter(
        BenefitPackage.lab_id == current_user.lab_id,
        BenefitPackage.code == data.code,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Benefit package with code '{data.code}' already exists")

    benefit = BenefitPackage(
        lab_id=current_user.lab_id,
        policy_id=policy_id,
        **{k: v for k, v in data.model_dump().items() if k != "policy_id"},
    )
    db.add(benefit)
    db.flush()

    log_action(
        db=db,
        action="insurance.benefit_package.create",
        resource_type="benefit_package",
        resource_id=benefit.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Added benefit package '{benefit.name}' ({benefit.code}) to policy '{policy.policy_number}'",
    )
    db.commit()
    db.refresh(benefit)
    return benefit
