from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.database import get_db
from app.insurance.domain.enums import (
    ReferralPriority,
    ReferralStatus,
    ReferralType,
    ValidationMethod,
)
from app.insurance.domain.referral import (
    InsuranceReferral,
    ReferralHistory,
    ReferralValidation,
)
from app.models.lab_user import LabUser
from app.security.dependencies import get_current_user
from app.security.legacy_referral import block_legacy_referral_write
from app.services.audit_service import log_action

router = APIRouter(prefix="/referrals", tags=["insurance-referrals"])


class ReferralCreate(BaseModel):
    coverage_id: int | None = None
    patient_id: int
    authorization_id: int | None = None
    from_practitioner_id: int | None = None
    to_practitioner_id: int | None = None
    from_facility_id: int | None = None
    to_facility_id: int | None = None
    referral_type: ReferralType
    priority: ReferralPriority = ReferralPriority.ROUTINE
    clinical_reason: str | None = None
    diagnosis_code: str | None = None
    diagnosis_description: str | None = None
    icd10_code: str | None = None
    service_code: str | None = None
    service_description: str | None = None
    quantity: int = 1
    notes: str | None = None
    clinical_notes: str | None = None
    expiration_date: date | None = None


class ReferralUpdate(BaseModel):
    to_practitioner_id: int | None = None
    to_facility_id: int | None = None
    priority: ReferralPriority | None = None
    clinical_reason: str | None = None
    diagnosis_code: str | None = None
    diagnosis_description: str | None = None
    icd10_code: str | None = None
    service_code: str | None = None
    service_description: str | None = None
    quantity: int | None = None
    notes: str | None = None
    clinical_notes: str | None = None
    expiration_date: date | None = None


class ReferralResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lab_id: int
    coverage_id: int | None = None
    patient_id: int
    authorization_id: int | None = None
    from_practitioner_id: int | None = None
    to_practitioner_id: int | None = None
    from_facility_id: int | None = None
    to_facility_id: int | None = None
    referral_number: str
    referral_type: ReferralType
    status: ReferralStatus
    priority: ReferralPriority
    clinical_reason: str | None = None
    diagnosis_code: str | None = None
    diagnosis_description: str | None = None
    icd10_code: str | None = None
    service_code: str | None = None
    service_description: str | None = None
    quantity: int | None = None
    notes: str | None = None
    clinical_notes: str | None = None
    expiration_date: date | None = None
    qr_code: str | None = None
    digital_signature: str | None = None
    signed_by: int | None = None
    signed_at: str | None = None
    completed_at: str | None = None
    completed_notes: str | None = None
    cancelled_at: str | None = None
    cancellation_reason: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ReferralHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    referral_id: int
    from_status: str | None = None
    to_status: str
    changed_by: int | None = None
    change_reason: str | None = None
    created_at: str | None = None


def _generate_referral_number(db: Session, lab_id: int) -> str:
    count = db.query(InsuranceReferral).filter(
        InsuranceReferral.lab_id == lab_id,
    ).count()
    return f"REF-{lab_id}-{count + 1:06d}"


def _record_history(
    db: Session,
    referral_id: int,
    lab_id: int,
    to_status: ReferralStatus,
    from_status: ReferralStatus | None = None,
    changed_by: int | None = None,
    change_reason: str | None = None,
):
    history = ReferralHistory(
        lab_id=lab_id,
        referral_id=referral_id,
        from_status=from_status,
        to_status=to_status,
        changed_by=changed_by,
        change_reason=change_reason,
    )
    db.add(history)


@router.get("", response_model=list[ReferralResponse])
def list_referrals(
    status: ReferralStatus | None = Query(None),
    patient_id: int | None = Query(None),
    referral_type: ReferralType | None = Query(None),
    from_practitioner_id: int | None = Query(None),
    to_practitioner_id: int | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(InsuranceReferral).filter(InsuranceReferral.lab_id == current_user.lab_id)
    if status:
        q = q.filter(InsuranceReferral.status == status)
    if patient_id:
        q = q.filter(InsuranceReferral.patient_id == patient_id)
    if referral_type:
        q = q.filter(InsuranceReferral.referral_type == referral_type)
    if from_practitioner_id:
        q = q.filter(InsuranceReferral.from_practitioner_id == from_practitioner_id)
    if to_practitioner_id:
        q = q.filter(InsuranceReferral.to_practitioner_id == to_practitioner_id)
    return q.order_by(InsuranceReferral.created_at.desc()).offset(skip).limit(limit).all()


@router.post("", status_code=201, response_model=ReferralResponse, dependencies=[Depends(block_legacy_referral_write)])
def create_referral(
    data: ReferralCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    referral = InsuranceReferral(
        lab_id=current_user.lab_id,
        referral_number=_generate_referral_number(db, current_user.lab_id),
        status=ReferralStatus.DRAFT,
        **data.model_dump(),
    )
    db.add(referral)
    db.flush()

    _record_history(
        db=db,
        referral_id=referral.id,
        lab_id=current_user.lab_id,
        to_status=ReferralStatus.DRAFT,
        changed_by=current_user.id,
        change_reason="Referral created",
    )

    log_action(
        db=db,
        action="insurance.referral.create",
        resource_type="insurance_referral",
        resource_id=referral.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Created referral '{referral.referral_number}' for patient {referral.patient_id}",
    )
    db.commit()
    db.refresh(referral)
    return referral


@router.get("/{referral_id}", response_model=ReferralResponse)
def get_referral(
    referral_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    referral = db.query(InsuranceReferral).filter(
        InsuranceReferral.id == referral_id,
        InsuranceReferral.lab_id == current_user.lab_id,
    ).first()
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")
    return referral


@router.put("/{referral_id}", response_model=ReferralResponse, dependencies=[Depends(block_legacy_referral_write)])
def update_referral(
    referral_id: int,
    data: ReferralUpdate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    referral = db.query(InsuranceReferral).filter(
        InsuranceReferral.id == referral_id,
        InsuranceReferral.lab_id == current_user.lab_id,
    ).first()
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")
    if referral.status != ReferralStatus.DRAFT:
        raise HTTPException(status_code=400, detail=f"Only draft referrals can be updated, current status: {referral.status.value}")

    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    for field, value in update_data.items():
        setattr(referral, field, value)

    log_action(
        db=db,
        action="insurance.referral.update",
        resource_type="insurance_referral",
        resource_id=referral.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Updated referral '{referral.referral_number}'",
    )
    db.commit()
    db.refresh(referral)
    return referral


@router.post("/{referral_id}/send", response_model=ReferralResponse, dependencies=[Depends(block_legacy_referral_write)])
def send_referral(
    referral_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    referral = db.query(InsuranceReferral).filter(
        InsuranceReferral.id == referral_id,
        InsuranceReferral.lab_id == current_user.lab_id,
    ).first()
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")
    if referral.status != ReferralStatus.DRAFT:
        raise HTTPException(status_code=400, detail=f"Only draft referrals can be sent, current status: {referral.status.value}")

    old_status = referral.status
    referral.status = ReferralStatus.SENT
    _record_history(
        db=db, referral_id=referral.id, lab_id=current_user.lab_id,
        to_status=ReferralStatus.SENT, from_status=old_status,
        changed_by=current_user.id, change_reason="Referral sent",
    )

    log_action(
        db=db,
        action="insurance.referral.send",
        resource_type="insurance_referral",
        resource_id=referral.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Sent referral '{referral.referral_number}'",
    )
    db.commit()
    db.refresh(referral)
    return referral


@router.post("/{referral_id}/accept", response_model=ReferralResponse, dependencies=[Depends(block_legacy_referral_write)])
def accept_referral(
    referral_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    referral = db.query(InsuranceReferral).filter(
        InsuranceReferral.id == referral_id,
        InsuranceReferral.lab_id == current_user.lab_id,
    ).first()
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")
    if referral.status not in (ReferralStatus.SENT, ReferralStatus.RECEIVED):
        raise HTTPException(status_code=400, detail=f"Referral cannot be accepted in status: {referral.status.value}")

    old_status = referral.status
    referral.status = ReferralStatus.ACCEPTED
    _record_history(
        db=db, referral_id=referral.id, lab_id=current_user.lab_id,
        to_status=ReferralStatus.ACCEPTED, from_status=old_status,
        changed_by=current_user.id, change_reason="Referral accepted",
    )

    log_action(
        db=db,
        action="insurance.referral.accept",
        resource_type="insurance_referral",
        resource_id=referral.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Accepted referral '{referral.referral_number}'",
    )
    db.commit()
    db.refresh(referral)
    return referral


@router.post("/{referral_id}/decline", response_model=ReferralResponse, dependencies=[Depends(block_legacy_referral_write)])
def decline_referral(
    referral_id: int,
    reason: str = Query(..., min_length=1),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    referral = db.query(InsuranceReferral).filter(
        InsuranceReferral.id == referral_id,
        InsuranceReferral.lab_id == current_user.lab_id,
    ).first()
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")
    if referral.status not in (ReferralStatus.SENT, ReferralStatus.RECEIVED):
        raise HTTPException(status_code=400, detail=f"Referral cannot be declined in status: {referral.status.value}")

    old_status = referral.status
    referral.status = ReferralStatus.DECLINED
    _record_history(
        db=db, referral_id=referral.id, lab_id=current_user.lab_id,
        to_status=ReferralStatus.DECLINED, from_status=old_status,
        changed_by=current_user.id, change_reason=reason,
    )

    log_action(
        db=db,
        action="insurance.referral.decline",
        resource_type="insurance_referral",
        resource_id=referral.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Declined referral '{referral.referral_number}': {reason}",
    )
    db.commit()
    db.refresh(referral)
    return referral


@router.post("/{referral_id}/complete", response_model=ReferralResponse, dependencies=[Depends(block_legacy_referral_write)])
def complete_referral(
    referral_id: int,
    completed_notes: str | None = Query(None),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    referral = db.query(InsuranceReferral).filter(
        InsuranceReferral.id == referral_id,
        InsuranceReferral.lab_id == current_user.lab_id,
    ).first()
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")
    if referral.status != ReferralStatus.ACCEPTED:
        raise HTTPException(status_code=400, detail=f"Only accepted referrals can be completed, current status: {referral.status.value}")

    old_status = referral.status
    referral.status = ReferralStatus.COMPLETED
    referral.completed_at = datetime.utcnow()
    referral.completed_notes = completed_notes
    _record_history(
        db=db, referral_id=referral.id, lab_id=current_user.lab_id,
        to_status=ReferralStatus.COMPLETED, from_status=old_status,
        changed_by=current_user.id, change_reason=completed_notes or "Referral completed",
    )

    log_action(
        db=db,
        action="insurance.referral.complete",
        resource_type="insurance_referral",
        resource_id=referral.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Completed referral '{referral.referral_number}'",
    )
    db.commit()
    db.refresh(referral)
    return referral


@router.post("/{referral_id}/cancel", response_model=ReferralResponse, dependencies=[Depends(block_legacy_referral_write)])
def cancel_referral(
    referral_id: int,
    reason: str = Query(..., min_length=1),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    referral = db.query(InsuranceReferral).filter(
        InsuranceReferral.id == referral_id,
        InsuranceReferral.lab_id == current_user.lab_id,
    ).first()
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")
    if referral.status in (ReferralStatus.COMPLETED, ReferralStatus.CANCELLED, ReferralStatus.EXPIRED):
        raise HTTPException(status_code=400, detail=f"Referral cannot be cancelled in status: {referral.status.value}")

    old_status = referral.status
    referral.status = ReferralStatus.CANCELLED
    referral.cancelled_at = datetime.utcnow()
    referral.cancellation_reason = reason
    _record_history(
        db=db, referral_id=referral.id, lab_id=current_user.lab_id,
        to_status=ReferralStatus.CANCELLED, from_status=old_status,
        changed_by=current_user.id, change_reason=reason,
    )

    log_action(
        db=db,
        action="insurance.referral.cancel",
        resource_type="insurance_referral",
        resource_id=referral.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Cancelled referral '{referral.referral_number}': {reason}",
    )
    db.commit()
    db.refresh(referral)
    return referral


@router.post("/{referral_id}/validate", response_model=dict, dependencies=[Depends(block_legacy_referral_write)])
def validate_referral(
    referral_id: int,
    validation_method: ValidationMethod = ValidationMethod.QR_SCAN,
    identity_document: str | None = Query(None),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    referral = db.query(InsuranceReferral).filter(
        InsuranceReferral.id == referral_id,
        InsuranceReferral.lab_id == current_user.lab_id,
    ).first()
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")
    if referral.status not in (ReferralStatus.SENT, ReferralStatus.RECEIVED, ReferralStatus.ACCEPTED):
        raise HTTPException(status_code=400, detail=f"Referral cannot be validated in status: {referral.status.value}")

    validation = ReferralValidation(
        lab_id=current_user.lab_id,
        referral_id=referral_id,
        validated_by=current_user.id,
        validation_method=validation_method,
        qr_verified=validation_method == ValidationMethod.QR_SCAN,
        identity_verified=bool(identity_document),
        identity_document=identity_document,
        verified_at=datetime.utcnow(),
        is_valid=True,
    )
    db.add(validation)
    db.flush()

    log_action(
        db=db,
        action="insurance.referral.validate",
        resource_type="insurance_referral",
        resource_id=referral.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Validated referral '{referral.referral_number}' via {validation_method.value}",
    )
    db.commit()

    return {
        "valid": True,
        "referral_id": referral_id,
        "referral_number": referral.referral_number,
        "status": referral.status.value,
        "patient_id": referral.patient_id,
        "validation_method": validation_method.value,
        "verified_at": validation.verified_at.isoformat(),
    }


@router.get("/{referral_id}/history", response_model=list[ReferralHistoryResponse])
def referral_status_history(
    referral_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    referral = db.query(InsuranceReferral).filter(
        InsuranceReferral.id == referral_id,
        InsuranceReferral.lab_id == current_user.lab_id,
    ).first()
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")

    return db.query(ReferralHistory).filter(
        ReferralHistory.referral_id == referral_id,
    ).order_by(ReferralHistory.created_at.asc()).all()


@router.get("/{referral_id}/qr", response_model=dict)
def get_referral_qr(
    referral_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    referral = db.query(InsuranceReferral).filter(
        InsuranceReferral.id == referral_id,
        InsuranceReferral.lab_id == current_user.lab_id,
    ).first()
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")

    return {
        "referral_id": referral.id,
        "referral_number": referral.referral_number,
        "qr_code": referral.qr_code,
        "status": referral.status.value,
        "patient_id": referral.patient_id,
    }
