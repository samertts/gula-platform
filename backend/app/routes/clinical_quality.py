from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.lab_user import LabUser
from app.security.dependencies import get_current_user
from app.services.clinical_service import QualityService

logger = logging.getLogger("gula.routes.clinical_quality")

router = APIRouter(prefix="/clinical/quality", tags=["clinical quality"])


@router.get("/kpis")
def get_clinical_kpis(
    department: str | None = None,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return QualityService.get_kpi_summary(db, department=department)


@router.get("/compliance-dashboard")
def get_compliance_dashboard(
    department: str | None = None,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return QualityService.get_compliance_dashboard(db, department=department)
