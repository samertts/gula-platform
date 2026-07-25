from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user
from ..services.stats_service import (
    daily_trends,
    flag_distribution,
    patient_growth,
    stats_summary,
    test_frequency,
    turnaround_times,
)

router = APIRouter(prefix="/stats", tags=["statistics"])


@router.get("/trends/daily")
def daily_trends_endpoint(
    days: int = Query(30, ge=1, le=365),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return daily_trends(current_user.lab_id, days, db)


@router.get("/trends/tests")
def test_frequency_endpoint(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(15, ge=1, le=50),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return test_frequency(current_user.lab_id, days, limit, db)


@router.get("/trends/flags")
def flag_distribution_endpoint(
    days: int = Query(30, ge=1, le=365),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return flag_distribution(current_user.lab_id, days, db)


@router.get("/trends/patients")
def patient_growth_endpoint(
    days: int = Query(90, ge=7, le=365),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return patient_growth(current_user.lab_id, days, db)


@router.get("/summary")
def stats_summary_endpoint(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return stats_summary(current_user.lab_id, db)


@router.get("/turnaround")
def turnaround_times_endpoint(
    days: int = Query(30, ge=1, le=90),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return turnaround_times(current_user.lab_id, days, db)
