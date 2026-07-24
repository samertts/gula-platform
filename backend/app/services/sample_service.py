"""Sample service — business logic layer for sample operations."""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from ..domain.exceptions import NotFoundError, ValidationError
from ..domain.order_state import assert_not_locked
from ..models.lab_order import LabOrder
from ..models.sample import Sample
from ..services.audit_service import log_action

VALID_SAMPLE_TYPES = [
    "blood", "urine", "stool", "swab", "serum", "plasma", "csf", "sputum", "other",
]
VALID_STATUSES = ["collected", "received", "processing", "analyzed", "rejected"]


@dataclass
class SampleDict:
    id: int
    barcode: str
    order_id: int
    sample_type: str
    status: str
    collected_by: str | None
    collection_time: str | None
    rejection_reason: str | None
    notes: str | None
    storage_location: str | None
    created_at: str | None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "barcode": self.barcode,
            "order_id": self.order_id,
            "sample_type": self.sample_type,
            "status": self.status,
            "collected_by": self.collected_by,
            "collection_time": self.collection_time,
            "rejection_reason": self.rejection_reason,
            "notes": self.notes,
            "storage_location": self.storage_location,
            "created_at": self.created_at,
        }


def sample_to_dict(s: Sample) -> dict:
    return SampleDict(
        id=s.id,
        barcode=s.barcode,
        order_id=s.order_id,
        sample_type=s.sample_type,
        status=s.status,
        collected_by=s.collected_by,
        collection_time=s.collection_time.isoformat() if s.collection_time else None,
        rejection_reason=s.rejection_reason,
        notes=s.notes,
        storage_location=s.storage_location,
        created_at=s.created_at.isoformat() if s.created_at else None,
    ).to_dict()


def create_sample(
    db: Session,
    lab_id: int,
    order_id: int,
    sample_type: str,
    collected_by: str | None,
    notes: str | None,
    storage_location: str | None,
    current_user,
    ip_address: str | None = None,
) -> dict:
    order = (
        db.query(LabOrder)
        .filter(LabOrder.id == order_id, LabOrder.lab_id == lab_id)
        .first()
    )
    if not order:
        raise NotFoundError("Order not found")
    assert_not_locked(order)
    if sample_type not in VALID_SAMPLE_TYPES:
        raise ValidationError("Invalid sample type")

    sample = Sample(
        order_id=order_id,
        sample_type=sample_type,
        collected_by=collected_by or current_user.name,
        notes=notes,
        storage_location=storage_location,
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
        details=f"Sample type={sample_type} for order {order_id}",
        ip_address=ip_address,
    )

    db.commit()
    db.refresh(sample)
    return {
        "message": "Sample registered",
        "sample": sample_to_dict(sample),
    }


def list_samples(
    db: Session,
    lab_id: int,
    status: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> dict:
    query = db.query(Sample).join(LabOrder).filter(LabOrder.lab_id == lab_id)
    if status:
        if status not in VALID_STATUSES:
            raise ValidationError("Invalid status filter")
        query = query.filter(Sample.status == status)
    total = query.count()
    samples = query.order_by(Sample.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "samples": [sample_to_dict(s) for s in samples]}


def get_sample(db: Session, lab_id: int, barcode: str) -> dict:
    sample = (
        db.query(Sample)
        .join(LabOrder)
        .filter(Sample.barcode == barcode, LabOrder.lab_id == lab_id)
        .first()
    )
    if not sample:
        raise NotFoundError("Sample not found")
    return sample_to_dict(sample)


def update_sample(
    db: Session,
    lab_id: int,
    barcode: str,
    status: str | None,
    rejection_reason: str | None,
    notes: str | None,
    storage_location: str | None,
    current_user,
    ip_address: str | None = None,
) -> dict:
    sample = (
        db.query(Sample)
        .join(LabOrder)
        .filter(Sample.barcode == barcode, LabOrder.lab_id == lab_id)
        .first()
    )
    if not sample:
        raise NotFoundError("Sample not found")

    order = db.query(LabOrder).filter(LabOrder.id == sample.order_id).first()
    if order:
        assert_not_locked(order)

    if status:
        if status not in VALID_STATUSES:
            raise ValidationError("Invalid status")
        if status == "rejected":
            if not rejection_reason or not rejection_reason.strip():
                raise ValidationError("Rejection reason required when rejecting a sample")
        sample.status = status

    if rejection_reason is not None:
        sample.rejection_reason = rejection_reason
    if notes is not None:
        sample.notes = notes
    if storage_location is not None:
        sample.storage_location = storage_location

    log_action(
        db,
        action="update",
        resource_type="sample",
        resource_id=sample.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Sample {barcode} status: {status or 'unchanged'}"
        + (f" reason: {rejection_reason}" if status == "rejected" else ""),
        ip_address=ip_address,
    )

    db.commit()
    db.refresh(sample)
    return {"message": "Sample updated", "sample": sample_to_dict(sample)}