"""Order and Result service - business logic layer for lab orders and results."""

import json
import logging
import secrets
import urllib.parse
from dataclasses import dataclass

from sqlalchemy.orm import Session, joinedload

from ..config import BASE_URL
from ..core.events import ORDER_CANCELLED, ORDER_CREATED, ORDER_VALIDATED, RESULT_CRITICAL, events
from ..domain.order_state import enforce_transition
from ..models.lab_order import LabOrder
from ..models.lab_result import LabResult, hash_token
from ..models.patient import Patient
from ..security.redis_client import cache as _cache
from ..services.audit_service import log_action
from ..services.critical_alerts import check_critical
from ..services.interpretation import get_flag, interpret_result
from ..services.pdf_report import generate_result_pdf

logger = logging.getLogger("gula.orders")

# ===== Composite test profiles =====
TEST_PROFILES = {
    "CBC": [
        {
            "test_name": "Hemoglobin",
            "unit": "g/dL",
            "normal_range_low": 12.0,
            "normal_range_high": 17.0,
        },
        {
            "test_name": "WBC",
            "unit": "x10^3/uL",
            "normal_range_low": 4.0,
            "normal_range_high": 11.0,
        },
        {
            "test_name": "Platelets",
            "unit": "x10^3/uL",
            "normal_range_low": 150.0,
            "normal_range_high": 400.0,
        },
    ],
    "Lipid Profile": [
        {
            "test_name": "Cholesterol",
            "unit": "mg/dL",
            "normal_range_low": 0,
            "normal_range_high": 200.0,
        },
        {
            "test_name": "Triglycerides",
            "unit": "mg/dL",
            "normal_range_low": 0,
            "normal_range_high": 150.0,
        },
    ],
    "Liver Function": [
        {"test_name": "ALT", "unit": "U/L", "normal_range_low": 0, "normal_range_high": 40.0},
        {"test_name": "AST", "unit": "U/L", "normal_range_low": 0, "normal_range_high": 40.0},
    ],
    "Kidney Function": [
        {
            "test_name": "Creatinine",
            "unit": "mg/dL",
            "normal_range_low": 0.6,
            "normal_range_high": 1.3,
        },
        {"test_name": "Urea", "unit": "mg/dL", "normal_range_low": 15.0, "normal_range_high": 45.0},
    ],
    "Thyroid": [
        {"test_name": "TSH", "unit": "mIU/L", "normal_range_low": 0.4, "normal_range_high": 4.5},
    ],
    "Electrolytes": [
        {
            "test_name": "Sodium",
            "unit": "mEq/L",
            "normal_range_low": 135.0,
            "normal_range_high": 145.0,
        },
        {
            "test_name": "Potassium",
            "unit": "mEq/L",
            "normal_range_low": 3.5,
            "normal_range_high": 5.0,
        },
    ],
    "Diabetes": [
        {
            "test_name": "Glucose",
            "unit": "mg/dL",
            "normal_range_low": 70.0,
            "normal_range_high": 100.0,
        },
        {"test_name": "HbA1c", "unit": "%", "normal_range_low": 0, "normal_range_high": 5.7},
    ],
}


@dataclass
class ResultDict:
    """DTO for result serialization."""

    id: int
    test_name: str
    value: float | None
    value_text: str | None
    unit: str | None
    normal_range_low: float | None
    normal_range_high: float | None
    flag: str
    result_token: str
    result_link: str
    interpretation: dict | None
    created_at: str | None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "test_name": self.test_name,
            "value": self.value,
            "value_text": self.value_text,
            "unit": self.unit,
            "normal_range_low": self.normal_range_low,
            "normal_range_high": self.normal_range_high,
            "flag": self.flag,
            "result_token": self.result_token,
            "result_link": self.result_link,
            "interpretation": self.interpretation,
            "created_at": self.created_at,
        }


@dataclass
class OrderDict:
    """DTO for order serialization."""

    id: int
    patient_id: int
    patient_name: str | None
    patient_phone: str | None
    doctor_name: str | None
    status: str
    is_critical: bool
    locked: bool
    validated_by: int | None
    validated_at: str | None
    created_at: str | None
    results: list[dict] | None = None
    share_link: str | None = None
    whatsapp_link: str | None = None

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "patient_id": self.patient_id,
            "patient_name": self.patient_name,
            "patient_phone": self.patient_phone,
            "doctor_name": self.doctor_name,
            "status": self.status,
            "is_critical": self.is_critical,
            "locked": self.locked,
            "validated_by": self.validated_by,
            "validated_at": self.validated_at,
            "created_at": self.created_at,
        }
        if self.results is not None:
            d["results"] = self.results
            if self.results and self.share_link:
                d["share_link"] = self.share_link
                d["whatsapp_link"] = self.whatsapp_link
        return d


def result_to_dict(r: LabResult) -> dict:
    """Convert LabResult ORM to dict DTO."""
    interpretation = None
    if r.value is not None:
        interpretation = interpret_result(
            r.test_name, r.value, r.normal_range_low, r.normal_range_high
        )

    return {
        "id": r.id,
        "test_name": r.test_name,
        "value": r.value,
        "value_text": r.value_text,
        "unit": r.unit,
        "normal_range_low": r.normal_range_low,
        "normal_range_high": r.normal_range_high,
        "flag": r.flag,
        "result_token": r.token,
        "result_link": f"/r/{r.token}",
        "interpretation": interpretation,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def order_to_dict(o: LabOrder, include_results: bool = True) -> dict:
    """Convert LabOrder ORM to dict DTO."""
    is_critical = any(r.flag in ("critical", "H", "L") for r in o.results) if o.results else False
    d = {
        "id": o.id,
        "patient_id": o.patient_id,
        "patient_name": o.patient.full_name if o.patient else None,
        "patient_phone": o.patient.phone if o.patient else None,
        "doctor_name": o.doctor_name,
        "status": o.status,
        "is_critical": is_critical,
        "locked": getattr(o, "locked_at", None) is not None,
        "validated_by": getattr(o, "validated_by", None),
        "validated_at": o.validated_at.isoformat() if getattr(o, "validated_at", None) else None,
        "created_at": o.created_at.isoformat() if o.created_at else None,
    }
    if include_results:
        d["results"] = [result_to_dict(r) for r in o.results]
        if o.results:
            first_token = o.results[0].token
            d["share_link"] = f"/r/{first_token}"
            share_text = f"Lab results for {o.patient.full_name if o.patient else 'patient'}"
            d["whatsapp_link"] = f"https://wa.me/?text={share_text}%20{BASE_URL}/r/{first_token}"
    return d


def _generate_unique_token(db: Session) -> tuple[str, str]:
    """Generate a unique result token and its hash."""
    token = secrets.token_urlsafe(32)
    token_h = hash_token(token)
    while db.query(LabResult).filter(LabResult.token_hash == token_h).first():
        token = secrets.token_urlsafe(32)
        token_h = hash_token(token)
    return token, token_h


def _build_sharing_links(patient_phone: str | None, patient_name: str | None, result_links: list) -> dict:
    """Build WhatsApp and SMS sharing links."""
    whatsapp_link = None
    sms_link = None
    if patient_phone:
        phone_clean = patient_phone.replace("+", "").replace("-", "").replace(" ", "")
        if phone_clean.startswith("07"):
            phone_clean = "964" + phone_clean[1:]
        first_link = result_links[0]["link"] if result_links else ""
        result_url = f"{BASE_URL}{first_link}"
        msg = (
            f"*GULA Lab Result*\n"
            f"Patient: {patient_name}\n"
            f"Tests: {len(result_links)} result(s)\n"
            f"View: {result_url}\n\n"
            f"_Powered by GULA Platform_"
        )
        sms_msg = f"GULA Lab Result - {patient_name}\nView your results: {result_url}"
        whatsapp_link = f"https://wa.me/{phone_clean}?text={urllib.parse.quote(msg)}"
        sms_link = f"sms:{patient_phone}?body={urllib.parse.quote(sms_msg)}"

    return {"whatsapp_link": whatsapp_link, "sms_link": sms_link}


def _check_critical_alerts(results: list) -> list:
    """Check for critical values in results and return alerts."""
    critical_alerts = []
    for item in results:
        if item.get("value") is not None:
            alert = check_critical(item["test_name"], item["value"])
            if alert:
                critical_alerts.append(
                    {
                        "test_name": item["test_name"],
                        "value": item["value"],
                        **alert,
                    }
                )
    return critical_alerts


def _emit_order_events(
    order: LabOrder,
    patient_name: str,
    patient_phone: str | None,
    result_count: int,
    created_by: int,
    critical_alerts: list,
):
    """Emit order and critical result events."""
    events.emit(
        ORDER_CREATED,
        {
            "order_id": order.id,
            "patient_id": order.patient_id,
            "lab_id": order.lab_id,
            "created_by": created_by,
            "result_count": result_count,
        },
    )

    for alert in critical_alerts:
        events.emit(
            RESULT_CRITICAL,
            {
                "order_id": order.id,
                "patient_id": order.patient_id,
                "patient_name": patient_name,
                "patient_phone": patient_phone,
                "test_name": alert["test_name"],
                "value": alert["value"],
                "lab_id": order.lab_id,
            },
        )


def create_order(
    db: Session,
    lab_id: int,
    user_id: int,
    user_role: str,
    patient_id: int,
    doctor_name: str | None,
    doctor_user_id: int | None,
    results_data: list[dict],
    ip_address: str | None = None,
    idempotency_key: str | None = None,
) -> dict:
    """Create a new order with results. Returns response dict."""
    # Server-side idempotency
    if idempotency_key:
        cache_key = f"idempotency:order:{lab_id}:{idempotency_key}"
        cached = _cache.get(cache_key)
        if cached:
            return json.loads(cached)

    # Validate patient exists
    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id, Patient.lab_id == lab_id)
        .first()
    )
    if not patient:
        return {"error": "Patient not found", "status_code": 404}

    # Validate doctor if provided
    if doctor_user_id is not None:
        from ..models.lab_user import LabUser

        doctor = (
            db.query(LabUser)
            .filter(
                LabUser.id == doctor_user_id,
                LabUser.lab_id == lab_id,
                LabUser.role == "doctor",
            )
            .first()
        )
        if not doctor:
            return {"error": "Invalid doctor_user_id", "status_code": 400}

    # Create order
    order = LabOrder(
        patient_id=patient_id,
        lab_id=lab_id,
        doctor_name=doctor_name,
        doctor_user_id=doctor_user_id,
        status="completed",
    )
    db.add(order)
    db.flush()

    # Create results
    result_links = []
    for item in results_data:
        flag = "unknown"
        if (
            item.get("value") is not None
            and item.get("normal_range_low") is not None
            and item.get("normal_range_high") is not None
        ):
            flag = get_flag(
                item["value"], item["normal_range_low"], item["normal_range_high"],
                test_name=item["test_name"]
            )

        token, token_h = _generate_unique_token(db)

        result = LabResult(
            order_id=order.id,
            test_name=item["test_name"],
            value=item.get("value"),
            value_text=item.get("value_text"),
            unit=item.get("unit"),
            normal_range_low=item.get("normal_range_low"),
            normal_range_high=item.get("normal_range_high"),
            flag=flag,
            token=token,
            token_hash=token_h,
        )
        db.add(result)
        result_links.append({"test": item["test_name"], "link": f"/r/{token}"})

    # Audit log
    log_action(
        db,
        action="create",
        resource_type="lab_order",
        resource_id=order.id,
        user_id=user_id,
        user_role=user_role,
        details=f"Created order with {len(results_data)} results for patient {patient.full_name}",
        ip_address=ip_address,
    )

    db.commit()
    db.refresh(order)

    # Build sharing links
    sharing = _build_sharing_links(patient.phone, patient.full_name, result_links)

    # Check critical alerts
    critical_alerts = _check_critical_alerts(results_data)

    response_body = {
        "message": "Order created with results",
        "order": order_to_dict(order),
        "result_links": result_links,
        "whatsapp_link": sharing["whatsapp_link"],
        "sms_link": sharing["sms_link"],
        "critical_alerts": critical_alerts if critical_alerts else None,
    }

    # Cache under idempotency key
    if idempotency_key:
        cache_key = f"idempotency:order:{lab_id}:{idempotency_key}"
        _cache.set(cache_key, json.dumps(response_body, default=str), ex=86400)

    # Emit events
    _emit_order_events(
        order, patient.full_name, patient.phone,
        len(results_data), user_id, critical_alerts
    )

    return response_body


def get_order_by_id(db: Session, order_id: int, lab_id: int, user_role: str, user_id: int) -> dict | None:
    """Get a single order by ID."""
    order = _base_order_query(db, user_role, user_id, lab_id).filter(LabOrder.id == order_id).first()
    if not order:
        return None
    return order_to_dict(order)


def list_orders(
    db: Session,
    lab_id: int,
    user_role: str,
    user_id: int,
    skip: int = 0,
    limit: int = 50,
    search: str | None = None,
) -> dict:
    """List orders with optional search."""
    query = _base_order_query(db, user_role, user_id, lab_id)
    if search and search.strip():
        import sqlalchemy as sa
        term = f"%{search.strip()}%"
        query = query.join(LabOrder.patient).filter(
            sa.or_(
                Patient.full_name.ilike(term),
                Patient.phone.ilike(term),
                LabOrder.doctor_name.ilike(term),
            )
        )
    total = query.count()
    orders = query.order_by(LabOrder.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "orders": [order_to_dict(o) for o in orders],
    }


def validate_order(
    db: Session,
    order_id: int,
    lab_id: int,
    user_role: str,
    user_id: int,
    ip_address: str | None = None,
) -> dict:
    """Validate and lock an order."""
    from datetime import datetime, timezone

    if user_role not in {"admin", "master_admin", "doctor"}:
        return {"error": "Only admin or doctor can validate orders", "status_code": 403}

    order = _base_order_query(db, user_role, user_id, lab_id).filter(LabOrder.id == order_id).first()
    if not order:
        return {"error": "Order not found", "status_code": 404}

    if not order.results:
        return {"error": "Cannot validate an order with no results", "status_code": 400}

    enforce_transition(order.status, "validated")

    now = datetime.now(timezone.utc)
    rows_updated = (
        db.query(LabOrder)
        .filter(LabOrder.id == order_id, LabOrder.locked_at.is_(None))
        .update(
            {
                "status": "validated",
                "validated_by": user_id,
                "validated_at": now,
                "locked_at": now,
            },
            synchronize_session="fetch",
        )
    )
    if rows_updated == 0:
        return {"error": "Order is already validated and locked", "status_code": 409}

    log_action(
        db,
        action="validate",
        resource_type="lab_order",
        resource_id=order.id,
        user_id=user_id,
        user_role=user_role,
        details=f"Order validated and locked by {user_id}",
        ip_address=ip_address,
    )
    db.commit()
    db.refresh(order)

    events.emit(
        ORDER_VALIDATED,
        {
            "order_id": order.id,
            "patient_id": order.patient_id,
            "lab_id": order.lab_id,
            "validated_by": user_id,
        },
    )

    return order_to_dict(order)


def cancel_order(
    db: Session,
    order_id: int,
    lab_id: int,
    user_role: str,
    user_id: int,
    ip_address: str | None = None,
) -> dict:
    """Cancel an order."""
    order = _base_order_query(db, user_role, user_id, lab_id).filter(LabOrder.id == order_id).first()
    if not order:
        return {"error": "Order not found", "status_code": 404}

    enforce_transition(order.status, "cancelled")

    order.status = "cancelled"
    log_action(
        db,
        action="cancel",
        resource_type="lab_order",
        resource_id=order.id,
        user_id=user_id,
        user_role=user_role,
        details=f"Order cancelled by {user_id}",
        ip_address=ip_address,
    )
    db.commit()

    events.emit(
        ORDER_CANCELLED,
        {
            "order_id": order.id,
            "patient_id": order.patient_id,
            "cancelled_by": user_id,
        },
    )

    return {"message": "Order cancelled", "order_id": order_id}


def get_public_result(db: Session, token: str, ip_address: str | None = None) -> dict:
    """Get public result by token."""
    from datetime import datetime, timezone

    token_h = hash_token(token)
    result = db.query(LabResult).filter(LabResult.token_hash == token_h).first()
    if not result:
        return {"error": "Result not found", "status_code": 404}

    if result.expires_at and result.expires_at < datetime.now(timezone.utc):
        return {"error": "Result link has expired", "status_code": 410}

    order = (
        db.query(LabOrder)
        .options(
            joinedload(LabOrder.patient), joinedload(LabOrder.lab), joinedload(LabOrder.results)
        )
        .filter(LabOrder.id == result.order_id)
        .first()
    )

    if not order:
        return {"error": "Result not found", "status_code": 404}

    patient = order.patient
    lab = order.lab

    results_with_interpretation = []
    for r in order.results:
        interp = None
        if r.value is not None:
            interp = interpret_result(r.test_name, r.value, r.normal_range_low, r.normal_range_high)

        results_with_interpretation.append(
            {
                "test_name": r.test_name,
                "value": r.value,
                "value_text": r.value_text,
                "unit": r.unit,
                "normal_range_low": r.normal_range_low,
                "normal_range_high": r.normal_range_high,
                "flag": r.flag,
                "interpretation": interp,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
        )

    log_action(
        db,
        action="view",
        resource_type="lab_result",
        resource_id=result.id,
        details=f"Public result viewed for patient {patient.full_name if patient else 'unknown'}",
        ip_address=ip_address,
    )
    db.commit()

    share_text = "Lab results - GULA Platform"
    whatsapp_link = f"https://wa.me/?text={share_text}%20{BASE_URL}/r/{token}"

    return {
        "patient": {
            "name": patient.full_name if patient else "Unknown",
            "health_id": patient.health_id if patient else None,
        },
        "lab": {
            "name": lab.name if lab else "Unknown",
            "city": lab.city if lab else None,
        },
        "order_date": order.created_at.isoformat() if order and order.created_at else None,
        "doctor_name": order.doctor_name if order else None,
        "results": results_with_interpretation,
        "whatsapp_link": whatsapp_link,
        "disclaimer": "This interpretation is for informational purposes only. It is not a medical diagnosis. Please consult your doctor.",
        "disclaimer_ar": "هذا التفسير لأغراض إعلامية فقط. ليس تشخيصاً طبياً. يرجى مراجعة طبيبك.",
    }


def download_result_pdf(db: Session, token: str, ip_address: str | None = None) -> dict:
    """Download result as PDF."""
    import re
    from datetime import datetime, timezone

    token_h = hash_token(token)
    result = db.query(LabResult).filter(LabResult.token_hash == token_h).first()
    if not result:
        return {"error": "Result not found", "status_code": 404}

    if result.expires_at and result.expires_at < datetime.now(timezone.utc):
        return {"error": "Result link has expired", "status_code": 410}

    order = (
        db.query(LabOrder)
        .options(
            joinedload(LabOrder.patient), joinedload(LabOrder.lab), joinedload(LabOrder.results)
        )
        .filter(LabOrder.id == result.order_id)
        .first()
    )

    if not order:
        return {"error": "Result not found", "status_code": 404}

    patient = order.patient
    lab = order.lab

    results_data = []
    for r in order.results:
        interp = None
        if r.value is not None:
            interp = interpret_result(r.test_name, r.value, r.normal_range_low, r.normal_range_high)
        results_data.append(
            {
                "test_name": r.test_name,
                "value": r.value,
                "value_text": r.value_text,
                "unit": r.unit,
                "normal_range_low": r.normal_range_low,
                "normal_range_high": r.normal_range_high,
                "flag": r.flag,
                "interpretation": interp,
            }
        )

    data = {
        "patient": {
            "name": patient.full_name if patient else "Unknown",
            "health_id": patient.health_id if patient else None,
        },
        "lab": {"name": lab.name if lab else "Unknown", "city": lab.city if lab else None},
        "order_date": order.created_at.isoformat() if order and order.created_at else None,
        "doctor_name": order.doctor_name if order else None,
        "results": results_data,
    }

    result_url = f"{BASE_URL}/r/{token}"
    try:
        pdf_bytes = generate_result_pdf(data, result_url)
    except Exception:
        logger.exception("PDF generation failed for result %s", result.id)
        return {"error": "Failed to generate PDF report", "status_code": 500}

    raw_name = patient.full_name if patient else "result"
    safe_name = re.sub(r"[^\w\s-]", "", raw_name).strip().replace(" ", "_")[:50] or "result"
    filename = f"GULA_Report_{safe_name}.pdf"

    log_action(
        db,
        action="download_pdf",
        resource_type="lab_result",
        resource_id=result.id,
        details=f"PDF downloaded for patient {patient.full_name if patient else 'unknown'}",
        ip_address=ip_address,
    )
    db.commit()

    return {"pdf_bytes": pdf_bytes, "filename": filename}


def get_patient_history_by_id(
    db: Session, patient_id: int, lab_id: int
) -> dict | None:
    """Get complete test history for a patient."""
    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id, Patient.lab_id == lab_id)
        .first()
    )
    if not patient:
        return None

    orders = (
        db.query(LabOrder)
        .filter(LabOrder.patient_id == patient.id, LabOrder.lab_id == lab_id)
        .options(joinedload(LabOrder.results))
        .order_by(LabOrder.created_at.desc())
        .limit(50)
        .all()
    )

    trends = {}
    all_results = []
    for order in orders:
        for result in order.results:
            entry = {
                "test_name": result.test_name,
                "value": result.value,
                "unit": result.unit,
                "flag": result.flag,
                "normal_range_low": result.normal_range_low,
                "normal_range_high": result.normal_range_high,
                "date": result.created_at.isoformat() if result.created_at else None,
                "token": result.token,
            }
            all_results.append(entry)

            key = result.test_name
            if key not in trends:
                trends[key] = []
            if result.value is not None:
                trends[key].append(
                    {
                        "value": result.value,
                        "date": result.created_at.isoformat() if result.created_at else None,
                        "flag": result.flag,
                    }
                )

    return {
        "patient": {
            "id": patient.id,
            "full_name": patient.full_name,
            "phone": patient.phone,
            "health_id": patient.health_id,
            "gender": patient.gender,
            "birth_date": str(patient.birth_date) if patient.birth_date else None,
        },
        "total_orders": len(orders),
        "total_results": len(all_results),
        "results": all_results,
        "trends": trends,
    }


def get_patient_history_by_phone(
    db: Session, phone: str, name: str | None = None
) -> dict:
    """Get patient test history by phone number."""
    import hmac as _hmac

    generic_error = "Patient not found or name verification failed"

    if not name or len(name) < 4:
        return {"error": "Please provide the full patient name (?name=...)", "status_code": 400}

    all_patients = db.query(Patient).filter(Patient.phone == phone).all()
    if not all_patients:
        return {"error": generic_error, "status_code": 404}

    name_lower = name.strip().lower()
    matched_patients = [
        p for p in all_patients if _hmac.compare_digest(p.full_name.strip().lower(), name_lower)
    ]
    if not matched_patients:
        return {"error": generic_error, "status_code": 403}

    canonical = matched_patients[0]
    patient_ids = [p.id for p in matched_patients]

    orders = (
        db.query(LabOrder)
        .filter(LabOrder.patient_id.in_(patient_ids))
        .options(joinedload(LabOrder.results))
        .order_by(LabOrder.created_at.desc())
        .limit(20)
        .all()
    )

    history = []
    for order in orders:
        for result in order.results:
            history.append(
                {
                    "test_name": result.test_name,
                    "value": result.value,
                    "unit": result.unit,
                    "flag": result.flag,
                    "date": result.created_at.isoformat() if result.created_at else None,
                }
            )

    return {
        "patient_name": canonical.full_name,
        "health_id": canonical.health_id,
        "history": history,
    }


def _base_order_query(db: Session, user_role: str, user_id: int, lab_id: int):
    """Return base LabOrder query scoped to the caller's access level."""
    import sqlalchemy as sa

    base = db.query(LabOrder).options(joinedload(LabOrder.patient), joinedload(LabOrder.results))
    if user_role == "doctor":
        return base.filter(LabOrder.doctor_user_id == user_id)
    if user_role == "citizen":
        return base.filter(sa.false())
    return base.filter(LabOrder.lab_id == lab_id)
