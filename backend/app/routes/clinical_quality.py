from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.lab_user import LabUser
from app.security.dependencies import get_current_user
from app.services.clinical_service import QualityService

logger = logging.getLogger("gula.routes.clinical_quality")

router = APIRouter(prefix="/clinical/quality", tags=["clinical quality"])


# ==============================================================================
# Clinical KPIs
# ==============================================================================


@router.get("/kpis")
def get_clinical_kpis(
    department: str | None = None,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return QualityService.get_kpi_summary(db, department=department)


# ==============================================================================
# Quality Indicator Measurements
# ==============================================================================


class MeasurementRecord(BaseModel):
    indicator_id: str
    measurement_date: str
    period_start: str | None = None
    period_end: str | None = None
    numerator_value: float
    denominator_value: float | None = None
    result_value: float | None = None
    notes: str | None = None
    measured_by: str | None = None


@router.post("/measurements", status_code=201)
def record_quality_measurement(
    data: MeasurementRecord,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    obj = QualityService.record_measurement(db, data.model_dump(exclude_none=True))
    return obj.to_dict()


# ==============================================================================
# Compliance Dashboard
# ==============================================================================


@router.get("/compliance-dashboard")
def get_compliance_dashboard(
    department: str | None = None,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return QualityService.get_compliance_dashboard(db, department=department)


# ==============================================================================
# Clinical Benchmarks
# ==============================================================================


@router.get("/benchmarks")
def get_clinical_benchmarks(
    indicator_id: str | None = None,
    year: int | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = QualityService.get_benchmarks(
        db, indicator_id=indicator_id, year=year, skip=skip, limit=limit,
    )
    return {"items": [b.to_dict() for b in items], "total": total, "skip": skip, "limit": limit}
