"""Electronic Health Record endpoints - patient's unified health view."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from collections import defaultdict

from ..database import get_db
from ..models.patient import Patient
from ..models.lab_order import LabOrder
from ..models.lab_result import LabResult
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user

router = APIRouter(prefix="/ehr", tags=["ehr"])


@router.get("/patient/{patient_id}")
def get_patient_ehr(
    patient_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get complete electronic health record for a patient.

    Returns all lab results organized by test type with trend data.
    """
    patient = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.lab_id == current_user.lab_id,
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Get all orders with results - scoped to current lab to prevent cross-lab data leak
    orders = db.query(LabOrder).filter(
        LabOrder.patient_id == patient_id,
        LabOrder.lab_id == current_user.lab_id,
    ).options(
        joinedload(LabOrder.results),
        joinedload(LabOrder.lab),
    ).order_by(LabOrder.created_at.desc()).all()

    # Organize results by test type for trends
    test_history = defaultdict(list)
    all_records = []

    for order in orders:
        lab = order.lab
        for result in order.results:
            record = {
                "test_name": result.test_name,
                "value": result.value,
                "value_text": result.value_text,
                "unit": result.unit,
                "flag": result.flag,
                "normal_range_low": result.normal_range_low,
                "normal_range_high": result.normal_range_high,
                "date": result.created_at.isoformat() if result.created_at else None,
                "lab_name": lab.name if lab else None,
                "doctor": order.doctor_name,
                "token": result.token,
            }
            all_records.append(record)

            if result.value is not None:
                test_history[result.test_name].append({
                    "value": result.value,
                    "date": result.created_at.isoformat() if result.created_at else None,
                    "flag": result.flag,
                })

    # Summary stats
    total_tests = len(all_records)
    abnormal_count = sum(1 for r in all_records if r["flag"] in ("H", "L", "critical"))

    return {
        "patient": {
            "id": patient.id,
            "full_name": patient.full_name,
            "health_id": patient.health_id,
            "phone": patient.phone,
            "gender": patient.gender,
            "birth_date": str(patient.birth_date) if patient.birth_date else None,
        },
        "summary": {
            "total_orders": len(orders),
            "total_tests": total_tests,
            "abnormal_count": abnormal_count,
            "test_types": len(test_history),
        },
        "records": all_records,
        "trends": dict(test_history),
    }


@router.get("/patient/{patient_id}/summary")
def get_patient_summary(
    patient_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Quick health summary - latest value for each test type."""
    patient = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.lab_id == current_user.lab_id,
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Get latest result for each unique test - scoped to current lab
    results = db.query(LabResult).join(LabOrder).filter(
        LabOrder.patient_id == patient_id,
        LabOrder.lab_id == current_user.lab_id,
    ).order_by(LabResult.created_at.desc()).all()

    seen_tests = set()
    latest = []
    for r in results:
        if r.test_name not in seen_tests:
            seen_tests.add(r.test_name)
            latest.append({
                "test_name": r.test_name,
                "value": r.value,
                "unit": r.unit,
                "flag": r.flag,
                "date": r.created_at.isoformat() if r.created_at else None,
            })

    return {
        "patient_name": patient.full_name,
        "health_id": patient.health_id,
        "latest_results": latest,
    }
