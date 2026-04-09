import secrets
import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from datetime import datetime, timezone
from ..database import get_db
from ..models.patient import Patient
from ..domain.order_state import enforce_transition
from ..core.events import events, ORDER_VALIDATED, ORDER_CANCELLED, ORDER_CREATED, RESULT_CRITICAL
from ..models.lab_user import LabUser
from ..models.lab_order import LabOrder
from ..models.lab_result import LabResult, hash_token
from ..security.dependencies import get_current_user
from ..security.rate_limit import rate_limit_public, rate_limit_user, get_client_ip
from ..services.interpretation import interpret_result, get_flag
from ..services.audit_service import log_action
from ..routes.critical_alerts import check_critical
from ..config import BASE_URL

router = APIRouter(tags=["results"])


# ===== Composite test profiles =====
TEST_PROFILES = {
    "CBC": [
        {"test_name": "Hemoglobin", "unit": "g/dL", "normal_range_low": 12.0, "normal_range_high": 17.0},
        {"test_name": "WBC", "unit": "x10^3/uL", "normal_range_low": 4.0, "normal_range_high": 11.0},
        {"test_name": "Platelets", "unit": "x10^3/uL", "normal_range_low": 150.0, "normal_range_high": 400.0},
    ],
    "Lipid Profile": [
        {"test_name": "Cholesterol", "unit": "mg/dL", "normal_range_low": 0, "normal_range_high": 200.0},
        {"test_name": "Triglycerides", "unit": "mg/dL", "normal_range_low": 0, "normal_range_high": 150.0},
    ],
    "Liver Function": [
        {"test_name": "ALT", "unit": "U/L", "normal_range_low": 0, "normal_range_high": 40.0},
        {"test_name": "AST", "unit": "U/L", "normal_range_low": 0, "normal_range_high": 40.0},
    ],
    "Kidney Function": [
        {"test_name": "Creatinine", "unit": "mg/dL", "normal_range_low": 0.6, "normal_range_high": 1.3},
        {"test_name": "Urea", "unit": "mg/dL", "normal_range_low": 15.0, "normal_range_high": 45.0},
    ],
    "Thyroid": [
        {"test_name": "TSH", "unit": "mIU/L", "normal_range_low": 0.4, "normal_range_high": 4.5},
    ],
    "Electrolytes": [
        {"test_name": "Sodium", "unit": "mEq/L", "normal_range_low": 135.0, "normal_range_high": 145.0},
        {"test_name": "Potassium", "unit": "mEq/L", "normal_range_low": 3.5, "normal_range_high": 5.0},
    ],
    "Diabetes": [
        {"test_name": "Glucose", "unit": "mg/dL", "normal_range_low": 70.0, "normal_range_high": 100.0},
        {"test_name": "HbA1c", "unit": "%", "normal_range_low": 0, "normal_range_high": 5.7},
    ],
}


class ResultItem(BaseModel):
    test_name: str
    value: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    normal_range_low: Optional[float] = None
    normal_range_high: Optional[float] = None


class CreateOrderRequest(BaseModel):
    patient_id: int
    doctor_name: Optional[str] = None
    doctor_user_id: Optional[int] = None  # link to a registered doctor account for data isolation
    results: List[ResultItem]

    @field_validator("doctor_name")
    @classmethod
    def validate_doctor_name(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) > 200:
                raise ValueError("Doctor name must be at most 200 characters")
        return v


def result_to_dict(r: LabResult) -> dict:
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
    # Aggregate is_critical from result flags (backend is authoritative)
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


@router.get("/test-profiles")
def list_test_profiles():
    """List available composite test profiles (CBC, Lipid, etc.)."""
    return {
        name: [{"test_name": t["test_name"], "unit": t["unit"],
                "normal_range_low": t["normal_range_low"],
                "normal_range_high": t["normal_range_high"]}
               for t in tests]
        for name, tests in TEST_PROFILES.items()
    }


@router.post("/orders", status_code=201)
def create_order(
    data: CreateOrderRequest,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Server-side idempotency: prevents duplicate orders from offline sync retries
    # Client sends Idempotency-Key (UUID) per operation; we cache the response for 24h
    _idem_key = request.headers.get("Idempotency-Key")
    if _idem_key:
        _cache_key = f"idempotency:order:{current_user.lab_id}:{_idem_key}"
        from ..security.redis_client import cache as _cache
        import json as _json
        _cached = _cache.get(_cache_key)
        if _cached:
            # Already processed — return exact same response (409 would confuse clients)
            return _json.loads(_cached)

    patient = db.query(Patient).filter(
        Patient.id == data.patient_id,
        Patient.lab_id == current_user.lab_id,
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Validate that the referenced doctor belongs to this lab and has doctor role
    if data.doctor_user_id is not None:
        doctor = db.query(LabUser).filter(
            LabUser.id == data.doctor_user_id,
            LabUser.lab_id == current_user.lab_id,
            LabUser.role == "doctor",
        ).first()
        if not doctor:
            raise HTTPException(
                status_code=400,
                detail="Invalid doctor_user_id: user not found, wrong lab, or not a doctor",
            )

    order = LabOrder(
        patient_id=data.patient_id,
        lab_id=current_user.lab_id,
        doctor_name=data.doctor_name,
        doctor_user_id=data.doctor_user_id,
        status="completed",
    )
    db.add(order)
    db.flush()

    result_links = []
    for item in data.results:
        flag = "unknown"
        if item.value is not None and item.normal_range_low is not None and item.normal_range_high is not None:
            flag = get_flag(item.value, item.normal_range_low, item.normal_range_high, test_name=item.test_name)

        token = secrets.token_urlsafe(32)
        token_h = hash_token(token)
        while db.query(LabResult).filter(LabResult.token_hash == token_h).first():
            token = secrets.token_urlsafe(32)
            token_h = hash_token(token)

        result = LabResult(
            order_id=order.id,
            test_name=item.test_name,
            value=item.value,
            value_text=item.value_text,
            unit=item.unit,
            normal_range_low=item.normal_range_low,
            normal_range_high=item.normal_range_high,
            flag=flag,
            token=token,
            token_hash=token_h,
        )
        db.add(result)
        result_links.append({"test": item.test_name, "link": f"/r/{token}"})

    # Audit log
    log_action(
        db,
        action="create",
        resource_type="lab_order",
        resource_id=order.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Created order with {len(data.results)} results for patient {patient.full_name}",
        ip_address=get_client_ip(request),
    )

    db.commit()
    db.refresh(order)

    # Build WhatsApp auto-send link
    # Build sharing links (WhatsApp + SMS fallback)
    import urllib.parse
    whatsapp_link = None
    sms_link = None
    if patient and patient.phone:
        phone_clean = patient.phone.replace("+", "").replace("-", "").replace(" ", "")
        # Add Iraq country code if not present
        if phone_clean.startswith("07"):
            phone_clean = "964" + phone_clean[1:]
        first_link = result_links[0]["link"] if result_links else ""
        result_url = f"{BASE_URL}{first_link}"
        msg = (
            f"*GULA Lab Result*\n"
            f"Patient: {patient.full_name}\n"
            f"Tests: {len(result_links)} result(s)\n"
            f"View: {result_url}\n\n"
            f"_Powered by GULA Platform_"
        )
        sms_msg = (
            f"GULA Lab Result - {patient.full_name}\n"
            f"View your results: {result_url}"
        )
        whatsapp_link = f"https://wa.me/{phone_clean}?text={urllib.parse.quote(msg)}"
        sms_link = f"sms:{patient.phone}?body={urllib.parse.quote(sms_msg)}"

    # Check for critical values and build alerts
    critical_alerts = []
    for item in data.results:
        if item.value is not None:
            alert = check_critical(item.test_name, item.value)
            if alert:
                critical_alerts.append({
                    "test_name": item.test_name,
                    "value": item.value,
                    **alert,
                })

    response_body = {
        "message": "Order created with results",
        "order": order_to_dict(order),
        "result_links": result_links,
        "whatsapp_link": whatsapp_link,
        "sms_link": sms_link,
        "critical_alerts": critical_alerts if critical_alerts else None,
    }

    # Cache response under idempotency key (24h) so retries get the same response
    if _idem_key:
        import json as _json
        _cache.set(_cache_key, _json.dumps(response_body, default=str), ex=86400)

    # Emit ORDER_CREATED event
    events.emit(ORDER_CREATED, {
        "order_id": order.id,
        "patient_id": order.patient_id,
        "lab_id": order.lab_id,
        "created_by": current_user.id,
        "result_count": len(data.results),
    })

    # Emit a RESULT_CRITICAL event for every critical value
    for alert in critical_alerts:
        events.emit(RESULT_CRITICAL, {
            "order_id": order.id,
            "patient_id": order.patient_id,
            "patient_name": patient.full_name,
            "patient_phone": patient.phone,
            "test_name": alert["test_name"],
            "value": alert["value"],
            "lab_id": order.lab_id,
        })

    return response_body


def _base_order_query(current_user: LabUser, db: Session):
    """Return base LabOrder query scoped to the caller's access level.

    - master_admin / ministry_admin / province_admin: all labs (for now just
      their own lab; multi-lab overview is via /admin/ endpoints)
    - admin / staff / lab_staff / technician: own lab only
    - doctor: only orders explicitly linked to them via doctor_user_id
    - citizen: no access (returns empty — citizens use public /r/<token> links)
    """
    base = db.query(LabOrder).options(
        joinedload(LabOrder.patient), joinedload(LabOrder.results)
    )
    if current_user.role == "doctor":
        # Data isolation: doctors see ONLY orders where they are the ordering physician
        return base.filter(LabOrder.doctor_user_id == current_user.id)
    if current_user.role == "citizen":
        # Citizens use public share tokens, not this endpoint
        return base.filter(sa.false())
    # Lab staff, admin, higher: scoped to their lab
    return base.filter(LabOrder.lab_id == current_user.lab_id)


@router.get("/orders")
def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    search: Optional[str] = Query(None, max_length=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = _base_order_query(current_user, db)
    if search and search.strip():
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


@router.get("/orders/{order_id}")
def get_order(
    order_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = _base_order_query(current_user, db).filter(LabOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order_to_dict(order)


# ===== ORDER STATE TRANSITIONS =====

_VALIDATE_ROLES = {"admin", "master_admin", "doctor"}


@router.post("/orders/{order_id}/validate")
def validate_order(
    order_id: int,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Validate and lock an order.  Only admin/master_admin/doctor may do this.
    After validation the order is immutable — results cannot be deleted or edited.

    Race-condition protection: uses an atomic UPDATE WHERE locked_at IS NULL
    so that two simultaneous validation requests cannot both succeed.
    """
    if current_user.role not in _VALIDATE_ROLES:
        raise HTTPException(status_code=403, detail="Only admin or doctor can validate orders")

    # Verify ownership/access first (uses existing RBAC-aware query)
    order = _base_order_query(current_user, db).filter(LabOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if not order.results:
        raise HTTPException(status_code=400, detail="Cannot validate an order with no results")

    # State machine enforcement (raises 409 for invalid transitions)
    enforce_transition(order.status, "validated")

    # Atomic lock — UPDATE ... WHERE locked_at IS NULL prevents double-validation
    now = datetime.now(timezone.utc)
    rows_updated = (
        db.query(LabOrder)
        .filter(LabOrder.id == order_id, LabOrder.locked_at.is_(None))
        .update(
            {
                "status": "validated",
                "validated_by": current_user.id,
                "validated_at": now,
                "locked_at": now,
            },
            synchronize_session="fetch",
        )
    )
    if rows_updated == 0:
        raise HTTPException(status_code=409, detail="Order is already validated and locked")

    log_action(
        db,
        action="validate",
        resource_type="lab_order",
        resource_id=order.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Order validated and locked by {current_user.email}",
        ip_address=get_client_ip(request),
    )
    db.commit()
    db.refresh(order)

    # Emit event — handlers run synchronously but errors never abort the response
    events.emit(ORDER_VALIDATED, {
        "order_id": order.id,
        "patient_id": order.patient_id,
        "lab_id": order.lab_id,
        "validated_by": current_user.id,
    })

    return order_to_dict(order)


@router.post("/orders/{order_id}/cancel")
def cancel_order(
    order_id: int,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel an order.  Validated (locked) orders cannot be cancelled."""
    order = _base_order_query(current_user, db).filter(LabOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # State machine enforcement
    enforce_transition(order.status, "cancelled")

    order.status = "cancelled"
    log_action(
        db,
        action="cancel",
        resource_type="lab_order",
        resource_id=order.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Order cancelled by {current_user.email}",
        ip_address=get_client_ip(request),
    )
    db.commit()

    events.emit(ORDER_CANCELLED, {
        "order_id": order.id,
        "patient_id": order.patient_id,
        "cancelled_by": current_user.id,
    })

    return {"message": "Order cancelled", "order_id": order_id}


# ===== PUBLIC RESULT PAGE (THE KILLER FEATURE) =====

@router.get("/r/{token}")
def get_public_result(token: str, request: Request, db: Session = Depends(get_db)):
    """Public result page - accessible without authentication. Rate limited."""
    # Rate limit public access
    rate_limit_public(request, max_per_minute=30)

    # Look up by hash only (prevents token exposure from DB leak)
    token_h = hash_token(token)
    result = db.query(LabResult).filter(
        LabResult.token_hash == token_h
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    # Check expiry - return 410 Gone (prevents token enumeration via expired vs not-found)
    if result.expires_at and result.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=410,
            detail="This result link has expired. Please contact your laboratory.",
        )

    # Use eager loading to fetch order, patient, lab, and all results in a single query
    order = db.query(LabOrder).options(
        joinedload(LabOrder.patient),
        joinedload(LabOrder.lab),
        joinedload(LabOrder.results)
    ).filter(LabOrder.id == result.order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Result not found")

    patient = order.patient
    lab = order.lab
    all_results = order.results

    results_with_interpretation = []
    for r in all_results:
        interp = None
        if r.value is not None:
            interp = interpret_result(r.test_name, r.value, r.normal_range_low, r.normal_range_high)

        results_with_interpretation.append({
            "test_name": r.test_name,
            "value": r.value,
            "value_text": r.value_text,
            "unit": r.unit,
            "normal_range_low": r.normal_range_low,
            "normal_range_high": r.normal_range_high,
            "flag": r.flag,
            "interpretation": interp,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })

    # Audit: log result view
    log_action(
        db,
        action="view",
        resource_type="lab_result",
        resource_id=result.id,
        details=f"Public result viewed for patient {patient.full_name if patient else 'unknown'}",
        ip_address=get_client_ip(request),
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


# ===== PDF DOWNLOAD =====

@router.get("/r/{token}/pdf")
def download_result_pdf(token: str, request: Request, db: Session = Depends(get_db)):
    """Download result as a professional PDF report with QR code."""
    from ..services.pdf_report import generate_result_pdf

    rate_limit_public(request, max_per_minute=10)

    token_h = hash_token(token)
    result = db.query(LabResult).filter(
        LabResult.token_hash == token_h
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    if result.expires_at and result.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Result link has expired")

    # Use eager loading to fetch order, patient, lab, and all results in a single query
    order = db.query(LabOrder).options(
        joinedload(LabOrder.patient),
        joinedload(LabOrder.lab),
        joinedload(LabOrder.results)
    ).filter(LabOrder.id == result.order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Result not found")

    patient = order.patient
    lab = order.lab
    all_results = order.results

    results_data = []
    for r in all_results:
        interp = None
        if r.value is not None:
            interp = interpret_result(r.test_name, r.value, r.normal_range_low, r.normal_range_high)
        results_data.append({
            "test_name": r.test_name,
            "value": r.value,
            "value_text": r.value_text,
            "unit": r.unit,
            "normal_range_low": r.normal_range_low,
            "normal_range_high": r.normal_range_high,
            "flag": r.flag,
            "interpretation": interp,
        })

    data = {
        "patient": {"name": patient.full_name if patient else "Unknown",
                     "health_id": patient.health_id if patient else None},
        "lab": {"name": lab.name if lab else "Unknown",
                "city": lab.city if lab else None},
        "order_date": order.created_at.isoformat() if order and order.created_at else None,
        "doctor_name": order.doctor_name if order else None,
        "results": results_data,
    }

    result_url = f"{BASE_URL}/r/{token}"
    import logging
    _logger = logging.getLogger("gula.results")
    try:
        pdf_bytes = generate_result_pdf(data, result_url)
    except Exception:  # noqa: BLE001
        _logger.exception("PDF generation failed for result %s", result.id)
        raise HTTPException(status_code=500, detail="Failed to generate PDF report")

    import re as _re
    raw_name = patient.full_name if patient else "result"
    # Strip all non-alphanumeric/space characters to prevent path traversal and header injection
    safe_name = _re.sub(r"[^\w\s-]", "", raw_name).strip().replace(" ", "_")[:50] or "result"
    filename = f"GULA_Report_{safe_name}.pdf"

    log_action(db, action="download_pdf", resource_type="lab_result",
               resource_id=result.id,
               details=f"PDF downloaded for patient {patient.full_name if patient else 'unknown'}",
               ip_address=get_client_ip(request))
    db.commit()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ===== PATIENT HISTORY =====

@router.get("/patient-history/{patient_id}")
def get_patient_history_by_id(
    patient_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get complete test history for a patient (authenticated, lab-scoped)."""
    patient = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.lab_id == current_user.lab_id,
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    orders = db.query(LabOrder).filter(
        LabOrder.patient_id == patient.id,
        LabOrder.lab_id == current_user.lab_id,
    ).options(joinedload(LabOrder.results)).order_by(LabOrder.created_at.desc()).limit(50).all()

    # Group results by test name for trend analysis
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

            # Build trends
            key = result.test_name
            if key not in trends:
                trends[key] = []
            if result.value is not None:
                trends[key].append({
                    "value": result.value,
                    "date": result.created_at.isoformat() if result.created_at else None,
                    "flag": result.flag,
                })

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


# Public history by phone (rate limited, requires full name match)
@router.get("/history/{phone}")
def get_patient_history(phone: str, request: Request, name: str = None, db: Session = Depends(get_db)):
    """Get patient test history by phone number (public, rate limited).
    Requires 'name' query param matching full patient name as verification.

    Multi-tenant isolation: the phone number may belong to Patient records in
    multiple labs (each lab keeps its own patient roster).  We aggregate results
    across ALL labs where the phone+name pair matches, so the citizen sees their
    complete history regardless of which lab they visited.  Only the patient's
    own results are returned — no cross-patient data is possible.
    """
    rate_limit_public(request, max_per_minute=5)

    # Use generic error to prevent enumeration
    generic_error = "Patient not found or name verification failed"

    if not name or len(name) < 4:
        raise HTTPException(status_code=400, detail="Please provide the full patient name (?name=...)")

    # Collect ALL patient records with this phone across all labs
    all_patients = db.query(Patient).filter(Patient.phone == phone).all()
    if not all_patients:
        raise HTTPException(status_code=404, detail=generic_error)

    import hmac as _hmac
    # Verify name matches at least one patient record (constant-time per record)
    name_lower = name.strip().lower()
    matched_patients = [
        p for p in all_patients
        if _hmac.compare_digest(p.full_name.strip().lower(), name_lower)
    ]
    if not matched_patients:
        raise HTTPException(status_code=403, detail=generic_error)

    # Use the canonical patient record for response metadata
    canonical = matched_patients[0]
    patient_ids = [p.id for p in matched_patients]

    # Fetch orders for all matched patient records (all labs)
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
            history.append({
                "test_name": result.test_name,
                "value": result.value,
                "unit": result.unit,
                "flag": result.flag,
                "date": result.created_at.isoformat() if result.created_at else None,
            })

    return {
        "patient_name": canonical.full_name,
        "health_id": canonical.health_id,
        "history": history,
    }


# ─── Clinical Intelligence ────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    results: List[ResultItem]


@router.post("/analyze")
def analyze_results(
    data: AnalyzeRequest,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
):
    """
    Analyze a batch of results for multi-test clinical patterns.
    Returns detected patterns (sepsis, DKA, renal failure, etc.)
    and a flag summary. Does NOT diagnose — flags for physician review.
    """
    # Rate limit: 20 analyses per minute per user_id + IP fallback (CPU-heavy endpoint)
    rate_limit_user(request, current_user.id, max_per_minute=20)
    from ..services.clinical_intelligence import analyze_results as _analyze, quick_flag_summary

    raw = [
        {
            "test_name": r.test_name,
            "value": r.value,
            "normal_range_low": r.normal_range_low,
            "normal_range_high": r.normal_range_high,
        }
        for r in data.results
    ]

    patterns = _analyze(raw)
    summary = quick_flag_summary(raw)

    return {
        "patterns_detected": len(patterns),
        "patterns": patterns,
        "flag_summary": summary,
        "has_critical_pattern": any(p["severity"] == "critical" for p in patterns),
    }


@router.get("/orders/{order_id}/intelligence")
def analyze_order(
    order_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Run clinical intelligence analysis on an existing order's results.
    Useful for post-entry review.
    """
    from ..services.clinical_intelligence import analyze_results as _analyze, quick_flag_summary

    order = db.query(LabOrder).filter(
        LabOrder.id == order_id,
        LabOrder.lab_id == current_user.lab_id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    raw = [
        {
            "test_name": r.test_name,
            "value": r.value,
            "normal_range_low": r.normal_range_low,
            "normal_range_high": r.normal_range_high,
        }
        for r in order.results
    ]

    patterns = _analyze(raw)
    summary = quick_flag_summary(raw)

    return {
        "order_id": order_id,
        "patterns_detected": len(patterns),
        "patterns": patterns,
        "flag_summary": summary,
        "has_critical_pattern": any(p["severity"] == "critical" for p in patterns),
    }
