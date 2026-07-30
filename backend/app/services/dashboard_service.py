import logging
from datetime import datetime, timedelta

from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session, joinedload

from app._compat import UTC

from ..models.lab_order import LabOrder
from ..models.lab_result import LabResult
from ..models.lab_user import LabUser
from ..models.patient import Patient

logger = logging.getLogger("gula.dashboard")

IRAQ_UTC_OFFSET = timedelta(hours=3)


def _iraq_hour() -> int:
    return (datetime.now(UTC) + IRAQ_UTC_OFFSET).hour


def arabic_greeting(iraq_hour: int | None = None) -> str:
    if iraq_hour is None:
        iraq_hour = _iraq_hour()
    if 5 <= iraq_hour < 12:
        return "صباح الخير"
    if 12 <= iraq_hour < 17:
        return "مساء الخير"
    if 17 <= iraq_hour < 21:
        return "مساء النور"
    return "أهلاً"


def get_greeting(current_user: LabUser | None = None) -> dict:
    greet = arabic_greeting()
    user_name = current_user.name if current_user and current_user.name else "مستخدم"
    return {"greeting": greet, "message": f"{greet}، {user_name}", "user_name": user_name}


def get_dashboard(
    db: Session,
    current_user: LabUser,
) -> dict:
    lab_id = current_user.lab_id
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())

    stats = (
        db.query(
            func.count(Patient.id).label("total_patients"),
            func.count(case((Patient.created_at >= today_start, Patient.id))).label("patients_today"),
            func.count(case((Patient.created_at >= week_start, Patient.id))).label("patients_week"),
        )
        .filter(Patient.lab_id == lab_id)
        .first()
    )

    order_stats = (
        db.query(
            func.count(LabOrder.id).label("total_orders"),
            func.count(case((LabOrder.created_at >= today_start, LabOrder.id))).label("orders_today"),
            func.count(case((LabOrder.created_at >= week_start, LabOrder.id))).label("orders_week"),
        )
        .filter(LabOrder.lab_id == lab_id)
        .first()
    )

    result_stats = (
        db.query(
            func.count(LabResult.id).label("total_results"),
            func.count(case((LabResult.flag == "critical", LabResult.id))).label("critical_count"),
            func.count(case((LabResult.created_at >= today_start, LabResult.id))).label("tests_today"),
            func.count(case((LabResult.created_at >= week_start, LabResult.id))).label("tests_week"),
            func.count(
                case(
                    (
                        and_(
                            LabResult.flag.in_(["H", "L", "critical"]),
                            LabResult.created_at >= week_start,
                        ),
                        LabResult.id,
                    ),
                ),
            ).label("abnormal_week"),
        )
        .join(LabOrder)
        .filter(LabOrder.lab_id == lab_id)
        .first()
    )

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
        abnormal.append(
            {
                "patient_name": patient.full_name if patient else "Unknown",
                "test_name": r.test_name,
                "value": r.value,
                "unit": r.unit,
                "normal_range_low": r.normal_range_low,
                "normal_range_high": r.normal_range_high,
                "flag": r.flag,
                "date": r.created_at.isoformat() if r.created_at else None,
                "token": r.token,
            },
        )

    recent_orders = (
        db.query(LabOrder)
        .options(joinedload(LabOrder.patient), joinedload(LabOrder.results))
        .filter(LabOrder.lab_id == lab_id)
        .order_by(LabOrder.created_at.desc())
        .limit(6)
        .all()
    )

    recent = []
    for o in recent_orders:
        recent.append(
            {
                "id": o.id,
                "patient_name": o.patient.full_name if o.patient else "Unknown",
                "status": o.status,
                "test_count": len(o.results) if o.results else 0,
                "date": o.created_at.isoformat() if o.created_at else None,
            },
        )

    greet = arabic_greeting()
    user_name = current_user.name or "مستخدم"

    return {
        "greeting": f"{greet}، {user_name}",
        "patients": stats.total_patients or 0,
        "orders": order_stats.total_orders or 0,
        "tests": result_stats.total_results or 0,
        "critical": result_stats.critical_count or 0,
        "today": {
            "patients": stats.patients_today or 0,
            "orders": order_stats.orders_today or 0,
            "tests": result_stats.tests_today or 0,
        },
        "this_week": {
            "patients": stats.patients_week or 0,
            "orders": order_stats.orders_week or 0,
            "tests": result_stats.tests_week or 0,
        },
        "abnormal_results": abnormal,
        "recent_orders": recent,
        "lab_name": current_user.lab.name if hasattr(current_user, "lab") else None,
    }
