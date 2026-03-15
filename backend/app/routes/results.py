import secrets
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from datetime import datetime, timezone
from ..database import get_db
from ..models.patient import Patient
from ..models.lab import Lab
from ..models.lab_user import LabUser
from ..models.lab_order import LabOrder
from ..models.lab_result import LabResult, hash_token
from ..models.test_type import TestType
from ..security.dependencies import get_current_user
from ..security.rate_limit import rate_limit_public
from ..services.interpretation import interpret_result, get_flag
from ..services.audit_service import log_action
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
    results: List[ResultItem]


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
        "token": r.token,
        "result_link": f"/r/{r.token}",
        "interpretation": interpretation,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def order_to_dict(o: LabOrder, include_results: bool = True) -> dict:
    d = {
        "id": o.id,
        "patient_id": o.patient_id,
        "patient_name": o.patient.full_name if o.patient else None,
        "patient_phone": o.patient.phone if o.patient else None,
        "doctor_name": o.doctor_name,
        "status": o.status,
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


@router.post("/orders")
def create_order(
    data: CreateOrderRequest,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    patient = db.query(Patient).filter(
        Patient.id == data.patient_id,
        Patient.lab_id == current_user.lab_id,
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    order = LabOrder(
        patient_id=data.patient_id,
        lab_id=current_user.lab_id,
        doctor_name=data.doctor_name,
        status="completed",
    )
    db.add(order)
    db.flush()

    result_links = []
    for item in data.results:
        flag = "unknown"
        if item.value is not None and item.normal_range_low is not None and item.normal_range_high is not None:
            flag = get_flag(item.value, item.normal_range_low, item.normal_range_high)

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
        ip_address=request.client.host if request.client else None,
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

    return {
        "message": "Order created with results",
        "order": order_to_dict(order),
        "result_links": result_links,
        "whatsapp_link": whatsapp_link,
        "sms_link": sms_link,
    }


@router.get("/orders")
def list_orders(
    skip: int = 0,
    limit: int = 50,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(LabOrder).filter(
        LabOrder.lab_id == current_user.lab_id,
    ).options(joinedload(LabOrder.patient), joinedload(LabOrder.results))

    total = db.query(LabOrder).filter(LabOrder.lab_id == current_user.lab_id).count()
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
    order = db.query(LabOrder).filter(
        LabOrder.id == order_id,
        LabOrder.lab_id == current_user.lab_id,
    ).options(joinedload(LabOrder.patient), joinedload(LabOrder.results)).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order_to_dict(order)


# ===== PUBLIC RESULT PAGE (THE KILLER FEATURE) =====

@router.get("/api/r/{token}")
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

    # Check expiry - return friendly JSON instead of raw error
    if result.expires_at and result.expires_at < datetime.now(timezone.utc):
        return {
            "expired": True,
            "message": "This result link has expired.",
            "message_ar": "انتهت صلاحية رابط النتيجة.",
            "expired_at": result.expires_at.isoformat(),
            "advice": "Please contact your laboratory for a new link.",
            "advice_ar": "يرجى التواصل مع المختبر للحصول على رابط جديد.",
        }

    order = db.query(LabOrder).filter(LabOrder.id == result.order_id).first()
    patient = db.query(Patient).filter(Patient.id == order.patient_id).first() if order else None
    lab = db.query(Lab).filter(Lab.id == order.lab_id).first() if order else None

    # Get all results for this order
    all_results = db.query(LabResult).filter(LabResult.order_id == result.order_id).all()

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
        ip_address=request.client.host if request.client else None,
    )
    db.commit()

    share_text = f"Lab results - GULA Platform"
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

@router.get("/api/r/{token}/pdf")
def download_result_pdf(token: str, request: Request, db: Session = Depends(get_db)):
    """Download result as a professional PDF report with QR code."""
    from ..services.pdf_report import generate_result_pdf

    rate_limit_public(request, max_per_minute=10)

    token_h = hash_token(token)
    result = db.query(LabResult).filter(
        (LabResult.token_hash == token_h) | (LabResult.token == token)
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    if result.expires_at and result.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Result link has expired")

    order = db.query(LabOrder).filter(LabOrder.id == result.order_id).first()
    patient = db.query(Patient).filter(Patient.id == order.patient_id).first() if order else None
    lab = db.query(Lab).filter(Lab.id == order.lab_id).first() if order else None
    all_results = db.query(LabResult).filter(LabResult.order_id == result.order_id).all()

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
    pdf_bytes = generate_result_pdf(data, result_url)

    patient_name = (patient.full_name if patient else "result").replace(" ", "_")
    filename = f"GULA_Report_{patient_name}.pdf"

    log_action(db, action="download_pdf", resource_type="lab_result",
               resource_id=result.id,
               details=f"PDF downloaded for patient {patient.full_name if patient else 'unknown'}",
               ip_address=request.client.host if request.client else None)
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
    Requires 'name' query param matching full patient name as verification."""
    rate_limit_public(request, max_per_minute=5)

    # Use generic error to prevent enumeration
    generic_error = "Patient not found or name verification failed"

    patient = db.query(Patient).filter(Patient.phone == phone).first()
    if not patient:
        raise HTTPException(status_code=404, detail=generic_error)

    # Full name verification (case-insensitive, stripped)
    if not name or len(name) < 4:
        raise HTTPException(status_code=400, detail="Please provide the full patient name (?name=...)")
    if patient.full_name.strip().lower() != name.strip().lower():
        raise HTTPException(status_code=403, detail=generic_error)

    orders = db.query(LabOrder).filter(
        LabOrder.patient_id == patient.id,
    ).options(joinedload(LabOrder.results)).order_by(LabOrder.created_at.desc()).limit(20).all()

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
        "patient_name": patient.full_name,
        "health_id": patient.health_id,
        "history": history,
    }
