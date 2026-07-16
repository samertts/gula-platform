
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db

from ..services.analytics_service import NationalAnalyticsService

router = APIRouter(prefix="/governance/analytics", tags=["governance_analytics"])


@router.get("/national")
def national_dashboard(db: Session = Depends(get_db)):
    svc = NationalAnalyticsService(db)
    return svc.national_dashboard()


@router.get("/governorate")
def governorate_dashboard(governorate: str, db: Session = Depends(get_db)):
    svc = NationalAnalyticsService(db)
    return svc.governorate_dashboard(governorate)


@router.get("/laboratory/{lab_id}")
def lab_dashboard(lab_id: int, db: Session = Depends(get_db)):
    svc = NationalAnalyticsService(db)
    return svc.lab_dashboard(lab_id)


@router.get("/laboratories")
def lab_statistics(lab_type: str | None = None, db: Session = Depends(get_db)):
    svc = NationalAnalyticsService(db)
    return svc.lab_statistics(lab_type)


@router.get("/workforce")
def workforce_statistics(db: Session = Depends(get_db)):
    svc = NationalAnalyticsService(db)
    return svc.workforce_statistics()


@router.get("/equipment")
def equipment_utilization(db: Session = Depends(get_db)):
    svc = NationalAnalyticsService(db)
    return svc.equipment_utilization()


@router.get("/quality")
def quality_indicators(db: Session = Depends(get_db)):
    svc = NationalAnalyticsService(db)
    return svc.quality_indicators()


@router.get("/tat")
def turnaround_time(db: Session = Depends(get_db)):
    svc = NationalAnalyticsService(db)
    return svc.turnaround_time_statistics()
