from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from ..database import get_db
from ..models.patient import Patient
from ..models.lab_order import LabOrder
from ..models.lab_result import LabResult
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user

router = APIRouter(tags=["dashboard"])


def _arabic_greeting(utc_hour: int) -> str:
    """Return a time-appropriate Arabic greeting."""
    if 5 <= utc_hour < 12:
        return "صباح الخير"
    elif 12 <= utc_hour < 17:
        return "مساء الخير"
    elif 17 <= utc_hour < 21:
        return "مساء النور"
    else:
        return "أهلاً"


@router.get("/greeting")
def greeting(current_user: LabUser = Depends(get_current_user)):
    """Return a personalized Arabic greeting based on time of day."""
    now = datetime.now(timezone.utc)
    greet = _arabic_greeting(now.hour)
    user_name = current_user.name or "مستخدم"
    return {
        "greeting": greet,
        "message": f"{greet}، {user_name}",
        "user_name": user_name,
    }


@router.get("/dashboard")
def dashboard(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lab_id = current_user.lab_id
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())

    # Total counts
    patients_count = db.query(func.count(Patient.id)).filter(
        Patient.lab_id == lab_id
    ).scalar() or 0

    orders_count = db.query(func.count(LabOrder.id)).filter(
        LabOrder.lab_id == lab_id
    ).scalar() or 0

    results_count = db.query(func.count(LabResult.id)).join(LabOrder).filter(
        LabOrder.lab_id == lab_id
    ).scalar() or 0

    critical_count = db.query(func.count(LabResult.id)).join(LabOrder).filter(
        LabOrder.lab_id == lab_id,
        LabResult.flag == "critical",
    ).scalar() or 0

    # Today's stats
    patients_today = db.query(func.count(Patient.id)).filter(
        Patient.lab_id == lab_id,
        Patient.created_at >= today_start,
    ).scalar() or 0

    orders_today = db.query(func.count(LabOrder.id)).filter(
        LabOrder.lab_id == lab_id,
        LabOrder.created_at >= today_start,
    ).scalar() or 0

    tests_today = db.query(func.count(LabResult.id)).join(LabOrder).filter(
        LabOrder.lab_id == lab_id,
        LabResult.created_at >= today_start,
    ).scalar() or 0

    # This week's stats
    orders_week = db.query(func.count(LabOrder.id)).filter(
        LabOrder.lab_id == lab_id,
        LabOrder.created_at >= week_start,
    ).scalar() or 0

    # Abnormal results (H, L, critical) from last 7 days - eagerly load relationships
    abnormal_results = (
        db.query(LabResult)
        .join(LabOrder)
        .options(joinedload(LabResult.order).joinedload(LabOrder.patient))
        .filter(
            LabOrder.lab_id == lab_id,
            LabResult.flag.in_(["H", "L", "critical"]),
            LabResult.created_at >= week_start,
        )
        .order_by(LabResult.created_at.desc())
        .limit(10)
        .all()
    )

    abnormal = []
    for r in abnormal_results:
        patient = r.order.patient if r.order else None
        abnormal.append({
            "patient_name": patient.full_name if patient else "Unknown",
            "test_name": r.test_name,
            "value": r.value,
            "unit": r.unit,
            "flag": r.flag,
            "date": r.created_at.isoformat() if r.created_at else None,
            "token": r.token,
        })

    # Recent orders - eagerly load patient
    recent_orders = (
        db.query(LabOrder)
        .options(joinedload(LabOrder.patient))
        .filter(LabOrder.lab_id == lab_id)
        .order_by(LabOrder.created_at.desc())
        .limit(5)
        .all()
    )

    recent = []
    for o in recent_orders:
        recent.append({
            "id": o.id,
            "patient_name": o.patient.full_name if o.patient else "Unknown",
            "status": o.status,
            "date": o.created_at.isoformat() if o.created_at else None,
        })

    greet = _arabic_greeting(now.hour)
    user_name = current_user.name or "مستخدم"

    return {
        "greeting": f"{greet}، {user_name}",
        "patients": patients_count,
        "orders": orders_count,
        "tests": results_count,
        "critical": critical_count,
        "today": {
            "patients": patients_today,
            "orders": orders_today,
            "tests": tests_today,
        },
        "this_week": {
            "orders": orders_week,
        },
        "abnormal_results": abnormal,
        "recent_orders": recent,
        "lab_name": current_user.lab.name if hasattr(current_user, 'lab') else None,
    }
