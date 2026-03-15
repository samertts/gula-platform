import secrets
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from datetime import datetime, timezone
from ..database import get_db
from ..models.patient import Patient
from ..models.lab import Lab
from ..models.lab_user import LabUser
from ..models.lab_order import LabOrder
from ..models.lab_result import LabResult
from ..models.test_type import TestType
from ..security.dependencies import get_current_user
from ..services.interpretation import interpret_result, get_flag
from ..config import BASE_URL

router = APIRouter(tags=["results"])


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
        # Generate share links for all results
        if o.results:
            first_token = o.results[0].token
            d["share_link"] = f"/r/{first_token}"
            share_text = f"Lab results for {o.patient.full_name if o.patient else 'patient'}"
            d["whatsapp_link"] = f"https://wa.me/?text={share_text}%20{BASE_URL}/r/{first_token}"
    return d


@router.post("/orders")
def create_order(
    data: CreateOrderRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify patient belongs to this lab
    patient = db.query(Patient).filter(
        Patient.id == data.patient_id,
        Patient.lab_id == current_user.lab_id,
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Create order
    order = LabOrder(
        patient_id=data.patient_id,
        lab_id=current_user.lab_id,
        doctor_name=data.doctor_name,
        status="completed",
    )
    db.add(order)
    db.flush()

    # Create results
    result_links = []
    for item in data.results:
        flag = "unknown"
        if item.value is not None and item.normal_range_low is not None and item.normal_range_high is not None:
            flag = get_flag(item.value, item.normal_range_low, item.normal_range_high)

        token = secrets.token_urlsafe(32)
        # Ensure unique token
        while db.query(LabResult).filter(LabResult.token == token).first():
            token = secrets.token_urlsafe(32)

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
        )
        db.add(result)
        result_links.append({"test": item.test_name, "link": f"/r/{token}"})

    db.commit()
    db.refresh(order)

    return {
        "message": "Order created with results",
        "order": order_to_dict(order),
        "result_links": result_links,
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

@router.get("/r/{token}")
def get_public_result(token: str, db: Session = Depends(get_db)):
    """Public result page - accessible without authentication."""
    result = db.query(LabResult).filter(LabResult.token == token).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    # Check expiry
    if result.expires_at and result.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Result link has expired")

    # Get order, patient, and lab info
    order = db.query(LabOrder).filter(LabOrder.id == result.order_id).first()
    patient = db.query(Patient).filter(Patient.id == order.patient_id).first() if order else None
    lab = db.query(Lab).filter(Lab.id == order.lab_id).first() if order else None

    # Get all results for this order
    all_results = db.query(LabResult).filter(LabResult.order_id == result.order_id).all()

    # Build interpretation
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


# Patient history - get all results for a patient by phone
@router.get("/history/{phone}")
def get_patient_history(phone: str, db: Session = Depends(get_db)):
    """Get patient test history by phone number (simplified public access)."""
    patient = db.query(Patient).filter(Patient.phone == phone).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

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
