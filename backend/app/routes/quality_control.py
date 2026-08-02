from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab_user import LabUser
from ..security.dependencies import require_permission
from ..services.quality_control_service import (
    get_qc_summary,
    list_qc_records,
    submit_batch_qc,
    submit_single_qc,
)

router = APIRouter(prefix="/qc", tags=["quality-control"])


class QCSubmit(BaseModel):
    test_code: str
    level: str
    expected_value: float
    measured_value: float
    sd: float | None = None
    unit: str | None = None
    instrument_name: str | None = None
    lot_number: str | None = None
    notes: str | None = None


class QCBatchSubmit(BaseModel):
    results: list[QCSubmit]


@router.post("", status_code=201)
def submit_qc(
    data: QCSubmit,
    current_user: LabUser = Depends(require_permission("results:write")),
    db: Session = Depends(get_db),
):
    return submit_single_qc(
        test_code=data.test_code,
        level=data.level,
        expected_value=data.expected_value,
        measured_value=data.measured_value,
        sd=data.sd,
        lab_id=current_user.lab_id,
        performed_by=current_user.name,
        db=db,
        unit=data.unit,
        instrument_name=data.instrument_name,
        lot_number=data.lot_number,
        notes=data.notes,
    )


@router.post("/batch", status_code=201)
def submit_qc_batch(
    data: QCBatchSubmit,
    current_user: LabUser = Depends(require_permission("results:write")),
    db: Session = Depends(get_db),
):
    return submit_batch_qc(
        results=[r.model_dump() for r in data.results],
        lab_id=current_user.lab_id,
        performed_by=current_user.name,
        db=db,
    )


@router.get("")
def list_qc(
    test_code: str | None = None,
    status: str | None = None,
    days: int = Query(7, ge=1, le=90),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(require_permission("results:read")),
    db: Session = Depends(get_db),
):
    return list_qc_records(
        lab_id=current_user.lab_id,
        db=db,
        test_code=test_code,
        status=status,
        days=days,
        skip=skip,
        limit=limit,
    )


@router.get("/summary")
def qc_summary(
    days: int = Query(7, ge=1, le=90),
    current_user: LabUser = Depends(require_permission("results:read")),
    db: Session = Depends(get_db),
):
    return get_qc_summary(lab_id=current_user.lab_id, db=db, days=days)
