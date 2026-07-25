"""Sample collection and tracking endpoints."""

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user
from ..security.rate_limit import get_client_ip
from ..services import sample_service

router = APIRouter(prefix="/samples", tags=["samples"])


class SampleCreate(BaseModel):
    order_id: int
    sample_type: str
    collected_by: str | None = None
    notes: str | None = None
    storage_location: str | None = None

    @field_validator("sample_type")
    @classmethod
    def validate_sample_type(cls, v):
        if v not in sample_service.VALID_SAMPLE_TYPES:
            raise ValueError(f"Invalid sample type. Must be one of: {', '.join(sample_service.VALID_SAMPLE_TYPES)}")
        return v


class SampleUpdate(BaseModel):
    status: str | None = None
    rejection_reason: str | None = None
    notes: str | None = None
    storage_location: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v is not None and v not in sample_service.VALID_STATUSES:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(sample_service.VALID_STATUSES)}")
        return v


@router.post("", status_code=201)
def create_sample(
    data: SampleCreate,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return sample_service.create_sample(
        db, current_user.lab_id, data.order_id, data.sample_type,
        data.collected_by, data.notes, data.storage_location,
        current_user, get_client_ip(request),
    )


@router.get("")
def list_samples(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
):
    return sample_service.list_samples(db, current_user.lab_id, status, skip, limit)


@router.get("/{barcode}")
def get_sample(
    barcode: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return sample_service.get_sample(db, current_user.lab_id, barcode)


@router.put("/{barcode}")
def update_sample(
    barcode: str,
    data: SampleUpdate,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return sample_service.update_sample(
        db, current_user.lab_id, barcode,
        data.status, data.rejection_reason, data.notes,
        data.storage_location, current_user, get_client_ip(request),
    )
