from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user
from ..services import stats_service

router = APIRouter(prefix="/stats", tags=["statistics"])


@router.get("/trends/daily")
def daily_trends(
    days: int = Query(30, ge=1, le=365, description="Number of past days to include"),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Daily order and test counts for the past N days.

    Returns a time-series list suitable for charting. Results are cached in
    Redis for 5 minutes to avoid repeated heavy GROUP BY queries.
    """
    return stats_service.daily_trends(current_user.lab_id, days, db)


@router.get("/trends/tests")
def test_frequency(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(15, ge=1, le=50, description="Top N tests to return"),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Most frequently ordered tests in the past N days.

    Useful for understanding test mix, staffing, and reagent planning.
    """
    return stats_service.test_frequency(current_user.lab_id, days, limit, db)


@router.get("/trends/flags")
def flag_distribution(
    days: int = Query(30, ge=1, le=365),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Distribution of result flags (normal / H / L / critical) over the past N days.

    Helps track overall lab result quality and critical alert frequency.
    """
    return stats_service.flag_distribution(current_user.lab_id, days, db)


@router.get("/trends/patients")
def patient_growth(
    days: int = Query(90, ge=7, le=365),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Weekly patient registration trends over the past N days.

    Helps track lab growth and seasonal patterns.
    """
    return stats_service.patient_growth(current_user.lab_id, days, db)


@router.get("/summary")
def stats_summary(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """High-level lab statistics summary (today / this week / this month / all time).

    Cached for 2 minutes — fast enough for dashboard widgets.
    """
    return stats_service.stats_summary(current_user.lab_id, db)


@router.get("/turnaround")
def turnaround_times(
    days: int = Query(30, ge=1, le=90),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Average order turnaround time (created → completed) in minutes.

    Tracks operational efficiency. Cached for 10 minutes.
    """
    return stats_service.turnaround_times(current_user.lab_id, days, db)
