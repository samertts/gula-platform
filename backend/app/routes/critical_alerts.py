"""Critical result alerts - immediate notification system for dangerous values."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_
from datetime import datetime, timezone, timedelta
from ..database import get_db
from ..models.lab_order import LabOrder
from ..models.lab_result import LabResult
from ..models.patient import Patient
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user

router = APIRouter(prefix="/alerts", tags=["critical-alerts"])

# Critical value thresholds (life-threatening ranges requiring immediate action)
CRITICAL_THRESHOLDS = {
    "glucose": {"critical_low": 40, "critical_high": 500, "unit": "mg/dL"},
    "potassium": {"critical_low": 2.5, "critical_high": 6.5, "unit": "mEq/L"},
    "sodium": {"critical_low": 120, "critical_high": 160, "unit": "mEq/L"},
    "hemoglobin": {"critical_low": 5.0, "critical_high": 20.0, "unit": "g/dL"},
    "wbc": {"critical_low": 1.0, "critical_high": 30.0, "unit": "×10³/µL"},
    "platelets": {"critical_low": 20, "critical_high": 1000, "unit": "×10³/µL"},
    "creatinine": {"critical_low": None, "critical_high": 10.0, "unit": "mg/dL"},
    "calcium": {"critical_low": 6.0, "critical_high": 13.0, "unit": "mg/dL"},
    "tsh": {"critical_low": 0.05, "critical_high": 50.0, "unit": "mIU/L"},
    "hba1c": {"critical_low": None, "critical_high": 14.0, "unit": "%"},
    "alt": {"critical_low": None, "critical_high": 1000, "unit": "U/L"},
    "ast": {"critical_low": None, "critical_high": 1000, "unit": "U/L"},
    "troponin": {"critical_low": None, "critical_high": 0.4, "unit": "ng/mL"},
}


def check_critical(test_name: str, value: float) -> dict | None:
    """Check if a result is critically abnormal. Returns alert details or None."""
    test_key = test_name.lower().replace(" ", "_").replace("-", "_")
    thresholds = CRITICAL_THRESHOLDS.get(test_key)
    if not thresholds:
        return None

    if thresholds["critical_low"] is not None and value <= thresholds["critical_low"]:
        return {
            "severity": "critical_low",
            "severity_ar": "منخفض بشكل خطير",
            "message": f"{test_name} is critically low ({value} {thresholds['unit']}). Immediate medical attention required.",
            "message_ar": f"{test_name} منخفض بشكل خطير ({value} {thresholds['unit']}). يتطلب عناية طبية فورية.",
            "threshold": thresholds["critical_low"],
        }

    if thresholds["critical_high"] is not None and value >= thresholds["critical_high"]:
        return {
            "severity": "critical_high",
            "severity_ar": "مرتفع بشكل خطير",
            "message": f"{test_name} is critically high ({value} {thresholds['unit']}). Immediate medical attention required.",
            "message_ar": f"{test_name} مرتفع بشكل خطير ({value} {thresholds['unit']}). يتطلب عناية طبية فورية.",
            "threshold": thresholds["critical_high"],
        }

    return None


@router.get("")
def get_critical_alerts(
    hours: int = Query(24, ge=1, le=168),
    acknowledged: bool = None,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get critical results requiring immediate attention."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    results = (
        db.query(LabResult)
        .join(LabOrder)
        .options(joinedload(LabResult.order).joinedload(LabOrder.patient))
        .filter(
            LabOrder.lab_id == current_user.lab_id,
            LabResult.flag == "critical",
            LabResult.created_at >= cutoff,
        )
        .order_by(LabResult.created_at.desc())
        .all()
    )

    alerts = []
    for r in results:
        patient = r.order.patient if r.order else None
        alert_detail = check_critical(r.test_name, r.value) if r.value else None

        alerts.append({
            "result_id": r.id,
            "patient_name": patient.full_name if patient else "Unknown",
            "patient_phone": patient.phone if patient else None,
            "patient_id": patient.id if patient else None,
            "test_name": r.test_name,
            "value": r.value,
            "unit": r.unit,
            "normal_range": f"{r.normal_range_low} - {r.normal_range_high}",
            "flag": r.flag,
            "alert": alert_detail,
            "order_id": r.order_id,
            "doctor_name": r.order.doctor_name if r.order else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })

    return {
        "total_alerts": len(alerts),
        "period_hours": hours,
        "alerts": alerts,
    }


@router.get("/stats")
def alert_statistics(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Statistics on critical results for the lab."""
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(hours=24)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    base = db.query(func.count(LabResult.id)).join(LabOrder).filter(
        LabOrder.lab_id == current_user.lab_id,
        LabResult.flag == "critical",
    )

    return {
        "last_24h": base.filter(LabResult.created_at >= day_ago).scalar() or 0,
        "last_7d": base.filter(LabResult.created_at >= week_ago).scalar() or 0,
        "last_30d": base.filter(LabResult.created_at >= month_ago).scalar() or 0,
        "top_critical_tests": _top_critical_tests(db, current_user.lab_id, week_ago),
    }


def _top_critical_tests(db: Session, lab_id: int, since: datetime) -> list:
    """Get most common critical test types."""
    results = db.query(
        LabResult.test_name,
        func.count(LabResult.id).label("count"),
    ).join(LabOrder).filter(
        LabOrder.lab_id == lab_id,
        LabResult.flag == "critical",
        LabResult.created_at >= since,
    ).group_by(LabResult.test_name).order_by(func.count(LabResult.id).desc()).limit(5).all()

    return [{"test_name": r.test_name, "count": r.count} for r in results]
