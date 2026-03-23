"""Notification endpoints - WhatsApp and SMS result delivery."""
import urllib.parse
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models.lab_result import LabResult, hash_token
from ..models.lab_order import LabOrder
from ..models.patient import Patient
from ..models.lab import Lab
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user
from ..security.rate_limit import rate_limit_user
from ..config import BASE_URL

router = APIRouter(prefix="/notify", tags=["notifications"])


class NotifyRequest(BaseModel):
    order_id: int
    channel: str = "whatsapp"  # whatsapp, sms

    @field_validator("channel")
    @classmethod
    def validate_channel(cls, v):
        if v not in ("whatsapp", "sms"):
            raise ValueError("Channel must be 'whatsapp' or 'sms'")
        return v


@router.post("/send")
def send_result_notification(
    request: Request,
    data: NotifyRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate notification link to send results to patient."""
    rate_limit_user(request, current_user.id, max_per_minute=20)
    order = db.query(LabOrder).filter(
        LabOrder.id == data.order_id,
        LabOrder.lab_id == current_user.lab_id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    patient = db.query(Patient).filter(Patient.id == order.patient_id).first()
    if not patient or not patient.phone:
        raise HTTPException(status_code=400, detail="Patient has no phone number")

    lab = db.query(Lab).filter(Lab.id == order.lab_id).first()

    # Get first result token for the link
    result = db.query(LabResult).filter(LabResult.order_id == order.id).first()
    if not result:
        raise HTTPException(status_code=400, detail="Order has no results")

    result_url = f"{BASE_URL}/r/{result.token}"
    results_count = db.query(LabResult).filter(LabResult.order_id == order.id).count()

    # Build phone number
    phone_clean = patient.phone.replace("+", "").replace("-", "").replace(" ", "")
    if phone_clean.startswith("07"):
        phone_clean = "964" + phone_clean[1:]

    lab_name = lab.name if lab else "GULA Lab"

    if data.channel == "whatsapp":
        msg = (
            f"*{lab_name} - Lab Result*\n\n"
            f"Patient: {patient.full_name}\n"
            f"Tests: {results_count} result(s)\n\n"
            f"View results: {result_url}\n\n"
            f"_Powered by GULA Platform_"
        )
        link = f"https://wa.me/{phone_clean}?text={urllib.parse.quote(msg)}"
    else:
        msg = f"{lab_name} - Your lab results are ready. View: {result_url}"
        link = f"sms:{patient.phone}?body={urllib.parse.quote(msg)}"

    return {
        "channel": data.channel,
        "link": link,
        "patient_phone": patient.phone,
        "message_preview": msg[:200],
    }


@router.get("/history/{order_id}")
def notification_status(
    order_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check if results for an order have been viewed."""
    from ..models.audit_log import AuditLog

    order = db.query(LabOrder).filter(
        LabOrder.id == order_id,
        LabOrder.lab_id == current_user.lab_id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Get result IDs for this order
    result_ids = [r.id for r in db.query(LabResult.id).filter(LabResult.order_id == order_id).all()]

    if not result_ids:
        return {"order_id": order_id, "total_views": 0, "first_viewed": None, "last_viewed": None}

    # Query only relevant audit logs (filtered in DB, not in Python)
    relevant_views = (
        db.query(AuditLog)
        .filter(
            AuditLog.action == "view",
            AuditLog.resource_type == "lab_result",
            AuditLog.resource_id.in_(result_ids),
        )
        .order_by(AuditLog.created_at.asc())
        .all()
    )

    return {
        "order_id": order_id,
        "total_views": len(relevant_views),
        "first_viewed": relevant_views[0].created_at.isoformat() if relevant_views else None,
        "last_viewed": relevant_views[-1].created_at.isoformat() if relevant_views else None,
    }
