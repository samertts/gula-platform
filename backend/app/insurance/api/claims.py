from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.insurance.domain.enums import AppealStatus, ClaimStatus, ClaimType, PaymentStatus
from app.insurance.domain.models import (
    Appeal,
    Coverage,
    InsuranceClaim,
    InsuranceClaimItem,
    InsurancePayment,
    InsuranceProvider,
)
from app.models.lab_user import LabUser
from app.security.dependencies import get_current_user
from app.services.audit_service import log_action

router = APIRouter(prefix="/claims", tags=["insurance-claims"])


class ClaimItemSchema(BaseModel):
    service_code: str
    service_name: str | None = None
    service_category: str | None = None
    loinc_code: str | None = None
    cpt_code: str | None = None
    quantity: int = Field(default=1, ge=1)
    unit_price: Decimal = Field(..., gt=0)
    billed_amount: Decimal = Field(..., gt=0)
    diagnosis_code: str | None = None
    modifier: str | None = None
    place_of_service: str | None = None


class ClaimCreate(BaseModel):
    coverage_id: int
    patient_id: int
    provider_id: int
    order_id: int | None = None
    authorization_id: int | None = None
    referral_id: int | None = None
    claim_type: ClaimType = ClaimType.LABORATORY
    service_start_date: date | None = None
    service_end_date: date | None = None
    diagnosis_code_primary: str | None = None
    diagnosis_code_secondary: list[str] | None = None
    icd10_code: str | None = None
    idempotency_key: str | None = None
    items: list[ClaimItemSchema] = Field(..., min_length=1)


class ClaimUpdate(BaseModel):
    service_start_date: date | None = None
    service_end_date: date | None = None
    diagnosis_code_primary: str | None = None
    diagnosis_code_secondary: list[str] | None = None
    icd10_code: str | None = None
    items: list[ClaimItemSchema] | None = None


class ClaimItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    claim_id: int
    service_code: str
    service_name: str | None = None
    service_category: str | None = None
    loinc_code: str | None = None
    cpt_code: str | None = None
    quantity: int
    unit_price: Decimal
    billed_amount: Decimal
    allowed_amount: Decimal | None = None
    paid_amount: Decimal | None = None
    copay_amount: Decimal | None = None
    deductible_amount: Decimal | None = None
    patient_responsibility: Decimal | None = None
    diagnosis_code: str | None = None
    adjudication_status: str | None = None


class ClaimResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lab_id: int
    coverage_id: int
    patient_id: int
    provider_id: int
    order_id: int | None = None
    authorization_id: int | None = None
    referral_id: int | None = None
    claim_number: str
    claim_type: ClaimType
    status: ClaimStatus
    service_start_date: date | None = None
    service_end_date: date | None = None
    submitted_date: date | None = None
    adjudicated_date: date | None = None
    paid_date: date | None = None
    total_billed: Decimal
    total_allowed: Decimal | None = None
    total_paid: Decimal | None = None
    total_deductible: Decimal | None = None
    total_copay: Decimal | None = None
    total_patient_responsibility: Decimal | None = None
    currency: str
    diagnosis_code_primary: str | None = None
    icd10_code: str | None = None
    adjudication_code: str | None = None
    adjudication_notes: str | None = None
    rejection_reason: str | None = None
    external_ref: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    items: list[ClaimItemResponse] = []


class AppealCreate(BaseModel):
    reason: str
    details: str | None = None
    requested_amount: Decimal | None = None
    supporting_documents: list[dict] | None = None


class AppealResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lab_id: int
    claim_id: int
    submitted_by: int
    appeal_number: str
    status: AppealStatus
    reason: str
    details: str | None = None
    requested_amount: Decimal | None = None
    reviewed_by: str | None = None
    review_notes: str | None = None
    decision: str | None = None
    decision_amount: Decimal | None = None
    decision_date: date | None = None
    escalation_level: int
    filed_date: date
    resolved_date: date | None = None
    created_at: str | None = None
    updated_at: str | None = None


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lab_id: int
    claim_id: int
    payer_id: int
    payment_number: str
    status: PaymentStatus
    amount: Decimal
    currency: str
    payment_method: str | None = None
    payment_date: date | None = None
    reference_number: str | None = None
    adjustment_amount: Decimal | None = None
    adjustment_reason: str | None = None
    notes: str | None = None
    created_at: str | None = None


def _claim_to_response(claim: InsuranceClaim) -> ClaimResponse:
    return ClaimResponse(
        id=claim.id,
        lab_id=claim.lab_id,
        coverage_id=claim.coverage_id,
        patient_id=claim.patient_id,
        provider_id=claim.provider_id,
        order_id=claim.order_id,
        authorization_id=claim.authorization_id,
        referral_id=claim.referral_id,
        claim_number=claim.claim_number,
        claim_type=claim.claim_type,
        status=claim.status,
        service_start_date=claim.service_start_date,
        service_end_date=claim.service_end_date,
        submitted_date=claim.submitted_date,
        adjudicated_date=claim.adjudicated_date,
        paid_date=claim.paid_date,
        total_billed=claim.total_billed,
        total_allowed=claim.total_allowed,
        total_paid=claim.total_paid,
        total_deductible=claim.total_deductible,
        total_copay=claim.total_copay,
        total_patient_responsibility=claim.total_patient_responsibility,
        currency=claim.currency,
        diagnosis_code_primary=claim.diagnosis_code_primary,
        icd10_code=claim.icd10_code,
        adjudication_code=claim.adjudication_code,
        adjudication_notes=claim.adjudication_notes,
        rejection_reason=claim.rejection_reason,
        external_ref=claim.external_ref,
        created_at=claim.created_at.isoformat() if claim.created_at else None,
        updated_at=claim.updated_at.isoformat() if claim.updated_at else None,
        items=[
            ClaimItemResponse(
                id=item.id,
                claim_id=item.claim_id,
                service_code=item.service_code,
                service_name=item.service_name,
                service_category=item.service_category.value if item.service_category else None,
                loinc_code=item.loinc_code,
                cpt_code=item.cpt_code,
                quantity=item.quantity,
                unit_price=item.unit_price,
                billed_amount=item.billed_amount,
                allowed_amount=item.allowed_amount,
                paid_amount=item.paid_amount,
                copay_amount=item.copay_amount,
                deductible_amount=item.deductible_amount,
                patient_responsibility=item.patient_responsibility,
                diagnosis_code=item.diagnosis_code,
                adjudication_status=item.adjudication_status,
            )
            for item in claim.items
        ],
    )


def _generate_claim_number(db: Session, lab_id: int) -> str:
    today = date.today()
    count = db.query(InsuranceClaim).filter(
        InsuranceClaim.lab_id == lab_id,
    ).count()
    return f"CLM-{lab_id}-{today.strftime('%Y%m%d')}-{count + 1:05d}"


def _generate_appeal_number(db: Session, lab_id: int) -> str:
    count = db.query(Appeal).filter(Appeal.lab_id == lab_id).count()
    return f"APL-{lab_id}-{count + 1:06d}"


@router.get("", response_model=list[ClaimResponse])
def list_claims(
    status: ClaimStatus | None = Query(None),
    patient_id: int | None = Query(None),
    provider_id: int | None = Query(None),
    coverage_id: int | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(InsuranceClaim).filter(InsuranceClaim.lab_id == current_user.lab_id)
    if status:
        q = q.filter(InsuranceClaim.status == status)
    if patient_id:
        q = q.filter(InsuranceClaim.patient_id == patient_id)
    if provider_id:
        q = q.filter(InsuranceClaim.provider_id == provider_id)
    if coverage_id:
        q = q.filter(InsuranceClaim.coverage_id == coverage_id)
    if date_from:
        q = q.filter(InsuranceClaim.service_start_date >= date_from)
    if date_to:
        q = q.filter(InsuranceClaim.service_end_date <= date_to)

    claims = q.order_by(InsuranceClaim.created_at.desc()).offset(skip).limit(limit).all()
    return [_claim_to_response(c) for c in claims]


@router.post("", status_code=201, response_model=ClaimResponse)
def create_claim(
    data: ClaimCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.idempotency_key:
        existing = db.query(InsuranceClaim).filter(
            InsuranceClaim.idempotency_key == data.idempotency_key,
            InsuranceClaim.lab_id == current_user.lab_id,
        ).first()
        if existing:
            return _claim_to_response(existing)

    coverage = db.query(Coverage).filter(
        Coverage.id == data.coverage_id,
        Coverage.lab_id == current_user.lab_id,
    ).first()
    if not coverage:
        raise HTTPException(status_code=404, detail="Coverage not found")

    provider = db.query(InsuranceProvider).filter(
        InsuranceProvider.id == data.provider_id,
        InsuranceProvider.lab_id == current_user.lab_id,
    ).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    total_billed = sum(item.billed_amount * item.quantity for item in data.items)

    claim = InsuranceClaim(
        lab_id=current_user.lab_id,
        claim_number=_generate_claim_number(db, current_user.lab_id),
        claim_type=data.claim_type,
        status=ClaimStatus.DRAFT,
        total_billed=total_billed,
        **data.model_dump(exclude={"claim_type", "items", "idempotency_key"}),
        idempotency_key=data.idempotency_key,
    )
    db.add(claim)
    db.flush()

    for item in data.items:
        claim_item = InsuranceClaimItem(
            claim_id=claim.id,
            **item.model_dump(),
        )
        db.add(claim_item)

    db.flush()

    log_action(
        db=db,
        action="insurance.claim.create",
        resource_type="insurance_claim",
        resource_id=claim.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Created claim '{claim.claim_number}' for patient {claim.patient_id}, total={total_billed}",
    )
    db.commit()
    db.refresh(claim)
    return _claim_to_response(claim)


@router.get("/{claim_id}", response_model=ClaimResponse)
def get_claim(
    claim_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    claim = db.query(InsuranceClaim).filter(
        InsuranceClaim.id == claim_id,
        InsuranceClaim.lab_id == current_user.lab_id,
    ).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return _claim_to_response(claim)


@router.put("/{claim_id}", response_model=ClaimResponse)
def update_claim(
    claim_id: int,
    data: ClaimUpdate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    claim = db.query(InsuranceClaim).filter(
        InsuranceClaim.id == claim_id,
        InsuranceClaim.lab_id == current_user.lab_id,
    ).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    if claim.status != ClaimStatus.DRAFT:
        raise HTTPException(status_code=400, detail=f"Can only update draft claims, current status: {claim.status.value}")

    update_data = data.model_dump(exclude={"items"}, exclude_unset=True)
    for field, value in update_data.items():
        setattr(claim, field, value)

    if data.items is not None:
        db.query(InsuranceClaimItem).filter(InsuranceClaimItem.claim_id == claim.id).delete()
        for item in data.items:
            claim_item = InsuranceClaimItem(
                claim_id=claim.id,
                **item.model_dump(),
            )
            db.add(claim_item)
        claim.total_billed = sum(item.billed_amount * item.quantity for item in data.items)

    log_action(
        db=db,
        action="insurance.claim.update",
        resource_type="insurance_claim",
        resource_id=claim.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Updated claim '{claim.claim_number}'",
    )
    db.commit()
    db.refresh(claim)
    return _claim_to_response(claim)


@router.post("/{claim_id}/submit", response_model=ClaimResponse)
def submit_claim(
    claim_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    claim = db.query(InsuranceClaim).filter(
        InsuranceClaim.id == claim_id,
        InsuranceClaim.lab_id == current_user.lab_id,
    ).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    valid_transitions = {ClaimStatus.VALIDATED}
    if claim.status not in valid_transitions and claim.status != ClaimStatus.DRAFT:
        valid_transitions.add(ClaimStatus.DRAFT)
    if claim.status not in valid_transitions:
        raise HTTPException(
            status_code=400,
            detail=f"Claim must be validated before submission, current status: {claim.status.value}",
        )

    claim.status = ClaimStatus.SUBMITTED
    claim.submitted_date = date.today()

    log_action(
        db=db,
        action="insurance.claim.submit",
        resource_type="insurance_claim",
        resource_id=claim.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Submitted claim '{claim.claim_number}'",
    )
    db.commit()
    db.refresh(claim)
    return _claim_to_response(claim)


@router.post("/{claim_id}/validate", response_model=ClaimResponse)
def validate_claim(
    claim_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    claim = db.query(InsuranceClaim).filter(
        InsuranceClaim.id == claim_id,
        InsuranceClaim.lab_id == current_user.lab_id,
    ).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    if claim.status != ClaimStatus.DRAFT:
        raise HTTPException(status_code=400, detail=f"Only draft claims can be validated, current status: {claim.status.value}")

    if not claim.items:
        raise HTTPException(status_code=400, detail="Claim has no items to validate")

    claim.status = ClaimStatus.VALIDATED

    log_action(
        db=db,
        action="insurance.claim.validate",
        resource_type="insurance_claim",
        resource_id=claim.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Validated claim '{claim.claim_number}'",
    )
    db.commit()
    db.refresh(claim)
    return _claim_to_response(claim)


@router.post("/{claim_id}/adjudicate", response_model=ClaimResponse)
def adjudicate_claim(
    claim_id: int,
    allowed_amount: Decimal | None = Query(None),
    adjudication_code: str | None = Query(None),
    adjudication_notes: str | None = Query(None),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    claim = db.query(InsuranceClaim).filter(
        InsuranceClaim.id == claim_id,
        InsuranceClaim.lab_id == current_user.lab_id,
    ).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    if claim.status != ClaimStatus.SUBMITTED:
        raise HTTPException(status_code=400, detail=f"Only submitted claims can be adjudicated, current status: {claim.status.value}")

    claim.status = ClaimStatus.ADJUDICATED
    claim.adjudicated_date = date.today()
    claim.adjudication_code = adjudication_code
    claim.adjudication_notes = adjudication_notes

    if allowed_amount is not None:
        ratio = allowed_amount / claim.total_billed if claim.total_billed else Decimal("0")
        claim.total_allowed = allowed_amount
        for item in claim.items:
            item.allowed_amount = item.billed_amount * ratio
    else:
        claim.total_allowed = claim.total_billed
        for item in claim.items:
            item.allowed_amount = item.billed_amount

    log_action(
        db=db,
        action="insurance.claim.adjudicate",
        resource_type="insurance_claim",
        resource_id=claim.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Adjudicated claim '{claim.claim_number}', allowed={claim.total_allowed}",
    )
    db.commit()
    db.refresh(claim)
    return _claim_to_response(claim)


@router.post("/{claim_id}/approve", response_model=ClaimResponse)
def approve_claim(
    claim_id: int,
    paid_amount: Decimal | None = Query(None),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    claim = db.query(InsuranceClaim).filter(
        InsuranceClaim.id == claim_id,
        InsuranceClaim.lab_id == current_user.lab_id,
    ).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    if claim.status not in (ClaimStatus.ADJUDICATED, ClaimStatus.SUBMITTED):
        raise HTTPException(status_code=400, detail=f"Claim cannot be approved in status: {claim.status.value}")

    claim.status = ClaimStatus.ACCEPTED
    claim.total_paid = paid_amount or claim.total_allowed or claim.total_billed
    claim.paid_date = date.today()

    log_action(
        db=db,
        action="insurance.claim.approve",
        resource_type="insurance_claim",
        resource_id=claim.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Approved claim '{claim.claim_number}', paid={claim.total_paid}",
    )
    db.commit()
    db.refresh(claim)
    return _claim_to_response(claim)


@router.post("/{claim_id}/reject", response_model=ClaimResponse)
def reject_claim(
    claim_id: int,
    rejection_reason: str = Query(..., min_length=1),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    claim = db.query(InsuranceClaim).filter(
        InsuranceClaim.id == claim_id,
        InsuranceClaim.lab_id == current_user.lab_id,
    ).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    if claim.status in (ClaimStatus.REJECTED, ClaimStatus.DENIED, ClaimStatus.CANCELLED):
        raise HTTPException(status_code=400, detail=f"Claim is already in terminal status: {claim.status.value}")

    claim.status = ClaimStatus.REJECTED
    claim.rejection_reason = rejection_reason

    log_action(
        db=db,
        action="insurance.claim.reject",
        resource_type="insurance_claim",
        resource_id=claim.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Rejected claim '{claim.claim_number}': {rejection_reason}",
    )
    db.commit()
    db.refresh(claim)
    return _claim_to_response(claim)


@router.post("/{claim_id}/cancel", response_model=ClaimResponse)
def cancel_claim(
    claim_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    claim = db.query(InsuranceClaim).filter(
        InsuranceClaim.id == claim_id,
        InsuranceClaim.lab_id == current_user.lab_id,
    ).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    if claim.status in (ClaimStatus.CANCELLED, ClaimStatus.PAID, ClaimStatus.REVERSED):
        raise HTTPException(status_code=400, detail=f"Claim cannot be cancelled in status: {claim.status.value}")

    claim.status = ClaimStatus.CANCELLED

    log_action(
        db=db,
        action="insurance.claim.cancel",
        resource_type="insurance_claim",
        resource_id=claim.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Cancelled claim '{claim.claim_number}'",
    )
    db.commit()
    db.refresh(claim)
    return _claim_to_response(claim)


@router.get("/{claim_id}/payments", response_model=list[PaymentResponse])
def list_claim_payments(
    claim_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    claim = db.query(InsuranceClaim).filter(
        InsuranceClaim.id == claim_id,
        InsuranceClaim.lab_id == current_user.lab_id,
    ).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    return db.query(InsurancePayment).filter(
        InsurancePayment.claim_id == claim_id,
        InsurancePayment.lab_id == current_user.lab_id,
    ).order_by(InsurancePayment.created_at.desc()).all()


@router.get("/{claim_id}/appeals", response_model=list[AppealResponse])
def list_claim_appeals(
    claim_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    claim = db.query(InsuranceClaim).filter(
        InsuranceClaim.id == claim_id,
        InsuranceClaim.lab_id == current_user.lab_id,
    ).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    return db.query(Appeal).filter(
        Appeal.claim_id == claim_id,
        Appeal.lab_id == current_user.lab_id,
    ).order_by(Appeal.created_at.desc()).all()


@router.post("/{claim_id}/appeals", status_code=201, response_model=AppealResponse)
def file_appeal(
    claim_id: int,
    data: AppealCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    claim = db.query(InsuranceClaim).filter(
        InsuranceClaim.id == claim_id,
        InsuranceClaim.lab_id == current_user.lab_id,
    ).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    if claim.status not in (ClaimStatus.REJECTED, ClaimStatus.DENIED):
        raise HTTPException(status_code=400, detail=f"Appeals can only be filed for rejected/denied claims, current status: {claim.status.value}")

    appeal = Appeal(
        lab_id=current_user.lab_id,
        claim_id=claim_id,
        submitted_by=current_user.id,
        appeal_number=_generate_appeal_number(db, current_user.lab_id),
        status=AppealStatus.FILED,
        filed_date=date.today(),
        **data.model_dump(),
    )
    db.add(appeal)
    db.flush()

    log_action(
        db=db,
        action="insurance.appeal.file",
        resource_type="appeal",
        resource_id=appeal.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Filed appeal '{appeal.appeal_number}' for claim '{claim.claim_number}'",
    )
    db.commit()
    db.refresh(appeal)
    return appeal


@router.get("/{claim_id}/audit", response_model=list[dict])
def claim_audit_trail(
    claim_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models.audit_log import AuditLog

    claim = db.query(InsuranceClaim).filter(
        InsuranceClaim.id == claim_id,
        InsuranceClaim.lab_id == current_user.lab_id,
    ).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    entries = db.query(AuditLog).filter(
        AuditLog.resource_type.in_(["insurance_claim", "appeal", "insurance_payment"]),
        AuditLog.resource_id == claim_id,
    ).order_by(AuditLog.created_at.asc()).all()

    return [
        {
            "id": e.id,
            "action": e.action,
            "user_id": e.user_id,
            "user_role": e.user_role,
            "details": e.details,
            "created_at": e.created_at.isoformat() if e.created_at else None,
            "chain_hash": e.chain_hash,
        }
        for e in entries
    ]
