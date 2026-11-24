"""Quality Control endpoints - Westgard rules for lab instrument validation.

Business logic lives in `app.services.quality_control_service`; this thin route
only exposes HTTP endpoints and re-exports the service functions so existing
test imports (`from app.routes.quality_control import evaluate_westgard`) keep
working.
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user
from ..services.quality_control_service import (
    evaluate_westgard,  # noqa: F401 — re-exported for tests that import it from here
    get_qc_summary,
    list_qc_records,
    submit_batch_qc,
    submit_single_qc,
)

router = APIRouter(prefix="/qc", tags=["quality-control"])


class QCSubmit(BaseModel):
    """QC measurement request body (kept inline to preserve OpenAPI schema).

    Delegates business logic to `app.services.quality_control_service`.
    """

    test_code: str
    level: str  # low, normal, high
    expected_value: float
    measured_value: float
    sd: float | None = None
    unit: str | None = None
    instrument_name: str | None = None
    lot_number: str | None = None
    notes: str | None = None


class QCBatchSubmit(BaseModel):
    """Batch QC measurement request body."""

    results: list[QCSubmit]


@router.post("", status_code=201)
def submit_qc(
    data: QCSubmit,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit a single QC measurement (Westgard evaluation + persistence)."""
    return submit_single_qc(
        lab_id=current_user.lab_id,
        test_code=data.test_code,
        level=data.level,
        expected_value=data.expected_value,
        measured_value=data.measured_value,
        sd=data.sd,
        unit=data.unit,
        instrument_name=data.instrument_name,
        lot_number=data.lot_number,
        notes=data.notes,
        performed_by=current_user.name,
        db=db,
    )


@router.post("/batch", status_code=201)
def submit_qc_batch(
    data: QCBatchSubmit,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit multiple QC measurements at once (batch Westgard evaluation)."""
    return submit_batch_qc(
        lab_id=current_user.lab_id,
        performed_by=current_user.name,
        db=db,
        results=[
            {
                "test_code": r.test_code,
                "level": r.level,
                "expected_value": r.expected_value,
                "measured_value": r.measured_value,
                "sd": r.sd,
                "unit": r.unit,
                "instrument_name": r.instrument_name,
                "lot_number": r.lot_number,
                "notes": r.notes,
            }
            for r in data.results
        ],
    )


@router.get("")
def list_qc(
    test_code: str | None = None,
    status: str | None = None,
    days: int = Query(7, ge=1, le=90),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List QC results for the lab."""
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
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """QC dashboard summary - pass/warning/fail counts by test."""
    return get_qc_summary(lab_id=current_user.lab_id, db=db, days=days)
