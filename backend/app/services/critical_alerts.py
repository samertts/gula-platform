"""Critical result alerts service - immediate notification system for dangerous values."""

from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app._compat import UTC

from ..models.lab_order import LabOrder
from ..models.lab_result import LabResult

# Critical value thresholds (life-threatening ranges requiring immediate action)
# Sources: AACC critical value guidelines, ISLAB recommendations
CRITICAL_THRESHOLDS = {
    # --- Chemistry ---
    "glucose": {"critical_low": 40, "critical_high": 500, "unit": "mg/dL"},
    "potassium": {"critical_low": 2.5, "critical_high": 6.5, "unit": "mEq/L"},
    "sodium": {"critical_low": 120, "critical_high": 160, "unit": "mEq/L"},
    "calcium": {"critical_low": 6.0, "critical_high": 13.0, "unit": "mg/dL"},
    "creatinine": {"critical_low": None, "critical_high": 10.0, "unit": "mg/dL"},
    "urea": {"critical_low": None, "critical_high": 200, "unit": "mg/dL"},
    "phosphorus": {"critical_low": 1.0, "critical_high": 8.0, "unit": "mg/dL"},
    "magnesium": {"critical_low": 0.9, "critical_high": 4.9, "unit": "mg/dL"},
    "bicarbonate": {"critical_low": 10, "critical_high": 40, "unit": "mEq/L"},
    "ammonia": {"critical_low": None, "critical_high": 150, "unit": "µmol/L"},
    # --- Haematology ---
    "hemoglobin": {"critical_low": 5.0, "critical_high": 20.0, "unit": "g/dL"},
    "wbc": {"critical_low": 1.0, "critical_high": 30.0, "unit": "×10³/µL"},
    "platelets": {"critical_low": 20, "critical_high": 1000, "unit": "×10³/µL"},
    # --- Coagulation ---
    "pt": {"critical_low": None, "critical_high": 30.0, "unit": "seconds"},
    "inr": {"critical_low": None, "critical_high": 4.0, "unit": ""},
    "aptt": {"critical_low": None, "critical_high": 70.0, "unit": "seconds"},
    "fibrinogen": {"critical_low": 80, "critical_high": None, "unit": "mg/dL"},
    # --- Cardiac ---
    "troponin": {"critical_low": None, "critical_high": 0.4, "unit": "ng/mL"},
    "troponin_i": {"critical_low": None, "critical_high": 0.4, "unit": "ng/mL"},
    "ck": {"critical_low": None, "critical_high": 1000, "unit": "U/L"},
    "ldh": {"critical_low": None, "critical_high": 1000, "unit": "U/L"},
    # --- Endocrine ---
    "tsh": {"critical_low": 0.05, "critical_high": 50.0, "unit": "mIU/L"},
    "hba1c": {"critical_low": None, "critical_high": 14.0, "unit": "%"},
    "cortisol": {"critical_low": 2.0, "critical_high": 50.0, "unit": "µg/dL"},
    # --- Liver ---
    "alt": {"critical_low": None, "critical_high": 1000, "unit": "U/L"},
    "ast": {"critical_low": None, "critical_high": 1000, "unit": "U/L"},
    "bilirubin_total": {"critical_low": None, "critical_high": 15.0, "unit": "mg/dL"},
    "ggt": {"critical_low": None, "critical_high": 500, "unit": "U/L"},
    "alp": {"critical_low": None, "critical_high": 1000, "unit": "U/L"},
    # --- Inflammation ---
    "crp": {"critical_low": None, "critical_high": 200, "unit": "mg/L"},
    "c_reactive_protein": {"critical_low": None, "critical_high": 200, "unit": "mg/L"},
    "procalcitonin": {"critical_low": None, "critical_high": 10.0, "unit": "ng/mL"},
    # --- Pancreas ---
    "amylase": {"critical_low": None, "critical_high": 600, "unit": "U/L"},
    "lipase": {"critical_low": None, "critical_high": 600, "unit": "U/L"},
    # --- Iron Studies ---
    "iron": {"critical_low": None, "critical_high": 500, "unit": "µg/dL"},
    "ferritin": {"critical_low": None, "critical_high": 2000, "unit": "ng/mL"},
    # --- Metabolic ---
    "uric_acid": {"critical_low": None, "critical_high": 13.0, "unit": "mg/dL"},
}


def check_critical(test_name: str, value: float) -> dict | None:
    """Check if a result is critically abnormal. Returns alert details or None."""
    test_key = test_name.lower().replace(" ", "_").replace("-", "_")
    thresholds: dict = CRITICAL_THRESHOLDS.get(test_key) or {}  # type: ignore[arg-type]
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


def get_critical_alerts(
    db: Session,
    lab_id: int,
    hours: int = 24,
) -> dict:
    """Get critical results requiring immediate attention."""
    cutoff = datetime.now(UTC) - timedelta(hours=hours)

    results = (
        db.query(LabResult)
        .join(LabOrder)
        .options(joinedload(LabResult.order).joinedload(LabOrder.patient))
        .filter(
            LabOrder.lab_id == lab_id,
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

        alerts.append(
            {
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
            },
        )

    return {
        "total_alerts": len(alerts),
        "period_hours": hours,
        "alerts": alerts,
    }


def alert_statistics(db: Session, lab_id: int) -> dict:
    """Statistics on critical results for the lab."""
    now = datetime.now(UTC)
    day_ago = now - timedelta(hours=24)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    base = (
        db.query(func.count(LabResult.id))
        .join(LabOrder)
        .filter(
            LabOrder.lab_id == lab_id,
            LabResult.flag == "critical",
        )
    )

    return {
        "last_24h": base.filter(LabResult.created_at >= day_ago).scalar() or 0,
        "last_7d": base.filter(LabResult.created_at >= week_ago).scalar() or 0,
        "last_30d": base.filter(LabResult.created_at >= month_ago).scalar() or 0,
        "top_critical_tests": _top_critical_tests(db, lab_id, week_ago),
    }


def _top_critical_tests(db: Session, lab_id: int, since: datetime) -> list:
    """Get most common critical test types."""
    results = (
        db.query(
            LabResult.test_name,
            func.count(LabResult.id).label("count"),
        )
        .join(LabOrder)
        .filter(
            LabOrder.lab_id == lab_id,
            LabResult.flag == "critical",
            LabResult.created_at >= since,
        )
        .group_by(LabResult.test_name)
        .order_by(func.count(LabResult.id).desc())
        .limit(5)
        .all()
    )

    return [{"test_name": r.test_name, "count": r.count} for r in results]
