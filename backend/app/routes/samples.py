"""Sample collection and tracking endpoints."""

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..domain.order_state import assert_not_locked
from ..models.lab_order import LabOrder
from ..models.lab_user import LabUser
from ..models.sample import Sample
from ..security.dependencies import get_current_user
from ..security.rate_limit import get_client_ip
from ..services.audit_service import log_action

router = APIRouter(prefix="/samples", tags=["samples"])


class SampleCreate(BaseModel):
    order_id: int
    sample_type: str  # blood, urine, stool, swab, serum, plasma
    collected_by: str | None = None
    notes: str | None = None
    storage_location: str | None = None


class SampleUpdate(BaseModel):
    status: str | None = None  # collected, received, processing, analyzed, rejected
    rejection_reason: str | None = None
    notes: str | None = None
    storage_location: str | None = None


VALID_SAMPLE_TYPES = [
    "blood",
    "urine",
    "stool",
    "swab",
    "serum",
    "plasma",
    "csf",
    "sputum",
    "other",
]
VALID_STATUSES = ["collected", "received", "processing", "analyzed", "rejected"]


@router.post("", status_code=201)
def create_sample(
    data: SampleCreate,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register a new sample for an order."""
    order = (
        db.query(LabOrder)
        .filter(
            LabOrder.id == data.order_id,
            LabOrder.lab_id == current_user.lab_id,
        )
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Block sample creation on locked (validated) orders
    assert_not_locked(order)

    if data.sample_type not in VALID_SAMPLE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid sample type")

    sample = Sample(
        order_id=data.order_id,
        sample_type=data.sample_type,
        collected_by=data.collected_by or current_user.name,
        notes=data.notes,
        storage_location=data.storage_location,
    )
    db.add(sample)
    db.flush()

    log_action(
        db,
        action="create",
        resource_type="sample",
        resource_id=sample.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Sample type={data.sample_type} for order {data.order_id}",
        ip_address=get_client_ip(request),
    )

    db.commit()
    db.refresh(sample)

    return {
        "message": "Sample registered",
        "sample": sample_to_dict(sample),
    }


@router.get("")
def list_samples(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
):
    """List samples for the current lab."""
    query = db.query(Sample).join(LabOrder).filter(LabOrder.lab_id == current_user.lab_id)
    if status:
        query = query.filter(Sample.status == status)
    total = query.count()
    samples = query.order_by(Sample.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "samples": [sample_to_dict(s) for s in samples],
    }


@router.get("/{barcode}")
def get_sample(
    barcode: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get sample by barcode."""
    sample = (
        db.query(Sample)
        .join(LabOrder)
        .filter(
            Sample.barcode == barcode,
            LabOrder.lab_id == current_user.lab_id,
        )
        .first()
    )
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    return sample_to_dict(sample)


@router.put("/{barcode}")
def update_sample(
    barcode: str,
    data: SampleUpdate,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update sample status (workflow tracking)."""
    sample = (
        db.query(Sample)
        .join(LabOrder)
        .filter(
            Sample.barcode == barcode,
            LabOrder.lab_id == current_user.lab_id,
        )
        .first()
    )
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    # Block status updates on locked orders
    order = db.query(LabOrder).filter(LabOrder.id == sample.order_id).first()
    if order:
        assert_not_locked(order)

    if data.status:
        if data.status not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail="Invalid status")
        if data.status == "rejected":
            if not data.rejection_reason or not data.rejection_reason.strip():
                raise HTTPException(
                    status_code=400, detail="Rejection reason required when rejecting a sample",
                )
        sample.status = data.status

    if data.rejection_reason is not None:
        sample.rejection_reason = data.rejection_reason
    if data.notes is not None:
        sample.notes = data.notes
    if data.storage_location is not None:
        sample.storage_location = data.storage_location

    log_action(
        db,
        action="update",
        resource_type="sample",
        resource_id=sample.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Sample {barcode} status: {data.status or 'unchanged'}"
        + (f" reason: {data.rejection_reason}" if data.status == "rejected" else ""),
        ip_address=get_client_ip(request),
    )

    db.commit()
    db.refresh(sample)
    return {"message": "Sample updated", "sample": sample_to_dict(sample)}


def sample_to_dict(s: Sample) -> dict:
    return {
        "id": s.id,
        "barcode": s.barcode,
        "order_id": s.order_id,
        "sample_type": s.sample_type,
        "status": s.status,
        "collected_by": s.collected_by,
        "collection_time": s.collection_time.isoformat() if s.collection_time else None,
        "rejection_reason": s.rejection_reason,
        "notes": s.notes,
        "storage_location": s.storage_location,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


class SampleIdentityVerificationRequest(BaseModel):
    verification_method: str


@router.put("/{barcode}/verify-identity")
def verify_sample_identity(
    barcode: str,
    payload: SampleIdentityVerificationRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    if_match: str | None = Header(None, alias="If-Match"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    """Record a guarded human identity/container verification for a sample.

    This command deliberately does not create ``LabResult`` records, change an
    order, or accept/release a device measurement. It only records a versioned
    human verification prerequisite for a separately approved future workflow.
    """
    from datetime import UTC, datetime

    from ..clinical.command_guard import ClinicalCommandGuard
    from ..core.feature_flags import can_lab_access
    from ..models.sample import SAMPLE_IDENTITY_VERIFICATION_METHODS

    if payload.verification_method not in SAMPLE_IDENTITY_VERIFICATION_METHODS:
        raise HTTPException(status_code=422, detail="Unsupported verification method")
    if current_user.id is None or current_user.lab_id is None or current_user.role is None:
        raise HTTPException(status_code=403, detail="Verifier identity is incomplete")
    actor_id = current_user.id
    actor_lab_id = current_user.lab_id
    actor_role = current_user.role
    if actor_role not in frozenset({"master_admin", "admin", "lab_admin"}):
        raise HTTPException(status_code=403, detail="Senior laboratory authority is required")

    sample = (
        db.query(Sample)
        .join(LabOrder)
        .filter(Sample.barcode == barcode, LabOrder.lab_id == actor_lab_id)
        .with_for_update()
        .first()
    )
    if sample is None:
        raise HTTPException(status_code=404, detail="Sample not found")
    order = db.query(LabOrder).filter(LabOrder.id == sample.order_id).with_for_update().first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if sample.id is None or sample.version is None or sample.status is None or order.status is None:
        raise HTTPException(status_code=409, detail="Sample has incomplete verification state")
    sample_id = sample.id
    version_before = sample.version
    state_before = sample.status
    order_status = order.status

    guard = ClinicalCommandGuard(
        db,
        actor_user_id=actor_id,
        lab_id=actor_lab_id,
        actor_role=actor_role,
    )
    guard.require_expected_version(if_match, current_version=version_before, resource_name="sample")
    key = guard.require_idempotency_key(idempotency_key)

    if not can_lab_access("sample_identity_verification", actor_lab_id, db):
        guard.reject(
            operation="sample.identity.verify",
            resource_type="sample",
            resource_id=sample_id,
            state_before=state_before,
            version_before=version_before,
            reason="feature_disabled",
        )
        db.commit()
        raise HTTPException(status_code=403, detail="Sample identity verification is disabled")
    if state_before != "received" or sample.verified_at is not None:
        guard.reject(
            operation="sample.identity.verify",
            resource_type="sample",
            resource_id=sample_id,
            state_before=state_before,
            version_before=version_before,
            reason="sample_not_pending_identity_verification",
        )
        db.commit()
        raise HTTPException(status_code=409, detail="Sample is not eligible for identity verification")
    if order_status != "pending" or order.locked_at is not None:
        guard.reject(
            operation="sample.identity.verify",
            resource_type="sample",
            resource_id=sample_id,
            state_before=state_before,
            version_before=version_before,
            reason="order_not_mutable",
        )
        db.commit()
        raise HTTPException(status_code=409, detail="Order is not eligible for sample verification")

    receipt = guard.claim(
        operation="sample.identity.verify",
        resource_type="sample",
        resource_id=sample_id,
        idempotency_key=key,
        payload=payload.model_dump(),
    )
    sample.status = "verified"
    sample.verified_by = actor_id
    sample.verified_at = datetime.now(UTC)
    sample.verification_method = payload.verification_method
    version_after = version_before + 1
    sample.version = version_after
    guard.complete(
        receipt,
        resource_type="sample",
        resource_id=sample_id,
        state_before=state_before,
        state_after="verified",
        version_before=version_before,
        version_after=version_after,
        reason=payload.verification_method,
    )
    db.commit()
    return {
        "message": "Sample identity verified",
        "sample": {"id": sample_id, "status": "verified", "version": version_after},
    }
