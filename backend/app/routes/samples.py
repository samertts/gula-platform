"""Sample collection and tracking endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone

from ..database import get_db
from ..models.sample import Sample
from ..models.lab_order import LabOrder
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user

router = APIRouter(prefix="/samples", tags=["samples"])


class SampleCreate(BaseModel):
    order_id: int
    sample_type: str  # blood, urine, stool, swab, serum, plasma
    collected_by: Optional[str] = None
    notes: Optional[str] = None
    storage_location: Optional[str] = None


class SampleUpdate(BaseModel):
    status: Optional[str] = None  # collected, received, processing, analyzed, rejected
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None
    storage_location: Optional[str] = None


VALID_SAMPLE_TYPES = ["blood", "urine", "stool", "swab", "serum", "plasma", "csf", "sputum", "other"]
VALID_STATUSES = ["collected", "received", "processing", "analyzed", "rejected"]


@router.post("")
def create_sample(
    data: SampleCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register a new sample for an order."""
    order = db.query(LabOrder).filter(
        LabOrder.id == data.order_id,
        LabOrder.lab_id == current_user.lab_id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if data.sample_type not in VALID_SAMPLE_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid sample type. Must be one of: {', '.join(VALID_SAMPLE_TYPES)}")

    sample = Sample(
        order_id=data.order_id,
        sample_type=data.sample_type,
        collected_by=data.collected_by or current_user.name,
        notes=data.notes,
        storage_location=data.storage_location,
    )
    db.add(sample)
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
    status: Optional[str] = None,
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
    sample = db.query(Sample).join(LabOrder).filter(
        Sample.barcode == barcode,
        LabOrder.lab_id == current_user.lab_id,
    ).first()
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    return sample_to_dict(sample)


@router.put("/{barcode}")
def update_sample(
    barcode: str,
    data: SampleUpdate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update sample status (workflow tracking)."""
    sample = db.query(Sample).join(LabOrder).filter(
        Sample.barcode == barcode,
        LabOrder.lab_id == current_user.lab_id,
    ).first()
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    if data.status:
        if data.status not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}")
        if data.status == "rejected" and not data.rejection_reason:
            raise HTTPException(status_code=400, detail="Rejection reason required when rejecting a sample")
        sample.status = data.status

    if data.rejection_reason is not None:
        sample.rejection_reason = data.rejection_reason
    if data.notes is not None:
        sample.notes = data.notes
    if data.storage_location is not None:
        sample.storage_location = data.storage_location

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
