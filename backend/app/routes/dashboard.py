from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models.patient import Patient
from ..models.lab_order import LabOrder
from ..models.lab_result import LabResult
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def dashboard(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lab_id = current_user.lab_id

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

    # Recent orders
    recent_orders = db.query(LabOrder).filter(
        LabOrder.lab_id == lab_id,
    ).order_by(LabOrder.created_at.desc()).limit(5).all()

    recent = []
    for o in recent_orders:
        patient = db.query(Patient).filter(Patient.id == o.patient_id).first()
        recent.append({
            "id": o.id,
            "patient_name": patient.full_name if patient else "Unknown",
            "status": o.status,
            "date": o.created_at.isoformat() if o.created_at else None,
        })

    return {
        "patients": patients_count,
        "orders": orders_count,
        "tests": results_count,
        "critical": critical_count,
        "recent_orders": recent,
        "lab_name": current_user.lab.name if hasattr(current_user, 'lab') else None,
    }
