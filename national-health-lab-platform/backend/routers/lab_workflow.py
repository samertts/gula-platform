"""
Lab Workflow Router for NHOP Python Backend
Covers: test catalog, lab orders, samples, results, reports
"""

import secrets
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import get_db, get_current_user, require_roles
from models.test_catalog import TestCatalog
from models.lab_order import LabOrder, LabOrderItem
from models.sample import Sample
from models.test_result import TestResult
from models.patient import Patient
from models.user import User

router = APIRouter(prefix="/lab", tags=["Lab Workflow"])


# -------------------------------------------------------
# Helpers
# -------------------------------------------------------

def generate_barcode() -> str:
    return f"NHLP-{secrets.token_hex(4).upper()}-{secrets.token_hex(2).upper()}"


def get_abnormal_flag(value: float, min_val, max_val) -> Optional[str]:
    if value is None:
        return None
    if min_val is not None and value < min_val:
        return "L"
    if max_val is not None and value > max_val:
        return "H"
    return None


# -------------------------------------------------------
# Schemas
# -------------------------------------------------------

class OrderCreate(BaseModel):
    patient_id:     int
    test_ids:       List[int]
    clinical_notes: Optional[str] = None
    priority:       Optional[str] = "normal"


class ResultEntry(BaseModel):
    test_catalog_id: int
    value:           str
    notes:           Optional[str] = None


class ResultsSubmit(BaseModel):
    sample_id: int
    results:   List[ResultEntry]


class RejectSample(BaseModel):
    reason: Optional[str] = "No reason given"


# -------------------------------------------------------
# TEST CATALOG
# -------------------------------------------------------

@router.get("/catalog")
def list_catalog(category: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(TestCatalog).filter(TestCatalog.is_active == True)
    if category:
        q = q.filter(TestCatalog.category == category)
    tests = q.order_by(TestCatalog.category, TestCatalog.name_ar).all()
    return {"ok": True, "tests": [
        {"id": t.id, "code": t.code, "name_ar": t.name_ar, "name_en": t.name_en,
         "category": t.category, "sample_type": t.sample_type, "unit": t.unit,
         "normal_range_min": t.normal_range_min, "normal_range_max": t.normal_range_max,
         "normal_range_text": t.normal_range_text, "price": t.price,
         "turnaround_hours": t.turnaround_hours}
        for t in tests
    ]}


@router.get("/catalog/categories")
def list_categories(db: Session = Depends(get_db)):
    rows = db.query(TestCatalog.category).filter(TestCatalog.is_active == True).distinct().all()
    return {"ok": True, "categories": [r[0] for r in rows]}


# -------------------------------------------------------
# LAB ORDERS
# -------------------------------------------------------

@router.post("/orders")
def create_order(body: OrderCreate, db: Session = Depends(get_db),
                 user: User = Depends(require_roles("doctor", "lab_staff", "admin"))):
    patient = db.query(Patient).filter(Patient.id == body.patient_id).first()
    if not patient:
        raise HTTPException(404, "patient_not_found")

    order = LabOrder(
        patient_id     = body.patient_id,
        doctor_id      = user.id,
        clinical_notes = body.clinical_notes,
        priority       = body.priority,
        status         = "pending"
    )
    db.add(order)
    db.flush()

    tests = db.query(TestCatalog).filter(
        TestCatalog.id.in_(body.test_ids),
        TestCatalog.is_active == True
    ).all()

    if not tests:
        raise HTTPException(404, "no_valid_tests_found")

    sample_types = set()
    for test in tests:
        item = LabOrderItem(order_id=order.id, test_catalog_id=test.id)
        db.add(item)
        sample_types.add(test.sample_type)

    for stype in sample_types:
        sample = Sample(
            order_id    = order.id,
            patient_id  = body.patient_id,
            sample_type = stype,
            barcode     = generate_barcode(),
            status      = "ordered"
        )
        db.add(sample)

    db.commit()
    db.refresh(order)

    return {"ok": True, "order": {"id": order.id, "status": order.status, "priority": order.priority}}


@router.get("/orders")
def list_orders(status: Optional[str] = None, patient_id: Optional[int] = None,
                page: int = 1, limit: int = 30, db: Session = Depends(get_db),
                user: User = Depends(require_roles("admin", "lab_staff", "doctor"))):
    q = db.query(LabOrder)
    if status:
        q = q.filter(LabOrder.status == status)
    if patient_id:
        q = q.filter(LabOrder.patient_id == patient_id)
    if user.role == "doctor":
        q = q.filter(LabOrder.doctor_id == user.id)

    orders = q.order_by(LabOrder.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    result = []
    for o in orders:
        patient = db.query(Patient).filter(Patient.id == o.patient_id).first()
        result.append({
            "id":           o.id,
            "status":       o.status,
            "priority":     o.priority,
            "created_at":   o.created_at,
            "patient_name": patient.full_name if patient else None,
            "national_id":  patient.national_id if patient else None,
        })
    return {"ok": True, "orders": result}


@router.get("/orders/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db),
              user: User = Depends(get_current_user)):
    order = db.query(LabOrder).filter(LabOrder.id == order_id).first()
    if not order:
        raise HTTPException(404, "order_not_found")

    patient = db.query(Patient).filter(Patient.id == order.patient_id).first()

    items = db.query(LabOrderItem, TestCatalog).join(
        TestCatalog, LabOrderItem.test_catalog_id == TestCatalog.id
    ).filter(LabOrderItem.order_id == order_id).all()

    samples = db.query(Sample).filter(Sample.order_id == order_id).all()

    return {
        "ok": True,
        "order": {
            "id": order.id, "status": order.status, "priority": order.priority,
            "clinical_notes": order.clinical_notes, "created_at": order.created_at
        },
        "patient": {"name": patient.full_name, "national_id": patient.national_id} if patient else None,
        "items": [
            {"id": i.id, "status": i.status, "test_code": t.code,
             "name_ar": t.name_ar, "name_en": t.name_en}
            for i, t in items
        ],
        "samples": [
            {"id": s.id, "barcode": s.barcode, "sample_type": s.sample_type, "status": s.status}
            for s in samples
        ]
    }


# -------------------------------------------------------
# SAMPLES
# -------------------------------------------------------

@router.get("/samples")
def list_samples(status: Optional[str] = None, page: int = 1, limit: int = 30,
                 db: Session = Depends(get_db),
                 _=Depends(require_roles("admin", "lab_staff"))):
    q = db.query(Sample)
    if status:
        q = q.filter(Sample.status == status)
    samples = q.order_by(Sample.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    result = []
    for s in samples:
        patient = db.query(Patient).filter(Patient.id == s.patient_id).first()
        result.append({
            "id":           s.id,
            "barcode":      s.barcode,
            "sample_type":  s.sample_type,
            "status":       s.status,
            "collected_at": s.collected_at,
            "received_at":  s.received_at,
            "patient_name": patient.full_name if patient else None,
        })
    return {"ok": True, "samples": result}


@router.patch("/samples/{sample_id}/collect")
def collect_sample(sample_id: int, db: Session = Depends(get_db),
                   user: User = Depends(require_roles("lab_staff", "admin"))):
    sample = db.query(Sample).filter(Sample.id == sample_id, Sample.status == "ordered").first()
    if not sample:
        raise HTTPException(404, "sample_not_found_or_already_collected")

    sample.status       = "collected"
    sample.collected_at = datetime.utcnow()
    sample.collector_id = user.id

    order = db.query(LabOrder).filter(LabOrder.id == sample.order_id).first()
    if order and order.status == "pending":
        order.status = "received"

    db.commit()
    return {"ok": True, "sample": {"id": sample.id, "status": sample.status}}


@router.patch("/samples/{sample_id}/receive")
def receive_sample(sample_id: int, db: Session = Depends(get_db),
                   _=Depends(require_roles("lab_staff", "admin"))):
    sample = db.query(Sample).filter(Sample.id == sample_id, Sample.status == "collected").first()
    if not sample:
        raise HTTPException(404, "sample_not_collected_yet")

    sample.status      = "received"
    sample.received_at = datetime.utcnow()

    order = db.query(LabOrder).filter(LabOrder.id == sample.order_id).first()
    if order:
        order.status = "processing"

    db.commit()
    return {"ok": True, "sample": {"id": sample.id, "status": sample.status}}


@router.patch("/samples/{sample_id}/reject")
def reject_sample(sample_id: int, body: RejectSample, db: Session = Depends(get_db),
                  _=Depends(require_roles("lab_staff", "admin"))):
    sample = db.query(Sample).filter(Sample.id == sample_id).first()
    if not sample:
        raise HTTPException(404, "sample_not_found")

    sample.status           = "rejected"
    sample.rejection_reason = body.reason
    db.commit()
    return {"ok": True, "sample": {"id": sample.id, "status": sample.status}}


# -------------------------------------------------------
# RESULTS
# -------------------------------------------------------

@router.post("/results")
def enter_results(body: ResultsSubmit, db: Session = Depends(get_db),
                  user: User = Depends(require_roles("lab_staff", "admin"))):
    sample = db.query(Sample).filter(Sample.id == body.sample_id).first()
    if not sample:
        raise HTTPException(404, "sample_not_found")

    inserted = []
    for r in body.results:
        catalog = db.query(TestCatalog).filter(TestCatalog.id == r.test_catalog_id).first()
        if not catalog:
            continue

        try:
            num_val = float(r.value)
        except (ValueError, TypeError):
            num_val = None

        flag       = get_abnormal_flag(num_val, catalog.normal_range_min, catalog.normal_range_max)
        is_abnormal = flag is not None

        order_item = db.query(LabOrderItem).filter(
            LabOrderItem.order_id == sample.order_id,
            LabOrderItem.test_catalog_id == r.test_catalog_id
        ).first()

        result = TestResult(
            sample_id       = sample.id,
            order_item_id   = order_item.id if order_item else None,
            test_catalog_id = r.test_catalog_id,
            patient_id      = sample.patient_id,
            value           = r.value,
            value_numeric   = num_val,
            unit            = catalog.unit,
            status          = "resulted",
            is_abnormal     = is_abnormal,
            abnormal_flag   = flag,
            tech_id         = user.id,
            notes           = r.notes
        )
        db.add(result)

        if order_item:
            order_item.status = "resulted"

        inserted.append({"test": catalog.code, "value": r.value, "flag": flag})

    sample.status = "processing"
    db.commit()

    return {"ok": True, "count": len(inserted), "results": inserted}


@router.patch("/results/{result_id}/approve")
def approve_result(result_id: int, db: Session = Depends(get_db),
                   user: User = Depends(require_roles("lab_staff", "admin"))):
    result = db.query(TestResult).filter(
        TestResult.id == result_id,
        TestResult.status == "resulted"
    ).first()
    if not result:
        raise HTTPException(404, "result_not_found_or_not_resulted")

    result.status      = "approved"
    result.approved_by = user.id
    result.approved_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "result_id": result_id}


@router.post("/orders/{order_id}/release")
def release_order(order_id: int, db: Session = Depends(get_db),
                  _=Depends(require_roles("lab_staff", "admin"))):
    results = db.query(TestResult).join(
        Sample, TestResult.sample_id == Sample.id
    ).filter(
        Sample.order_id == order_id,
        TestResult.status == "approved"
    ).all()

    for r in results:
        r.status = "released"

    order = db.query(LabOrder).filter(LabOrder.id == order_id).first()
    if order:
        order.status = "completed"

    db.commit()
    return {"ok": True, "released": len(results)}


# -------------------------------------------------------
# REPORTS
# -------------------------------------------------------

@router.get("/reports/{order_id}")
def get_report(order_id: int, db: Session = Depends(get_db),
               user: User = Depends(get_current_user)):
    order = db.query(LabOrder).filter(LabOrder.id == order_id).first()
    if not order:
        raise HTTPException(404, "order_not_found")

    patient = db.query(Patient).filter(Patient.id == order.patient_id).first()

    results = db.query(TestResult, TestCatalog).join(
        TestCatalog, TestResult.test_catalog_id == TestCatalog.id
    ).join(
        Sample, TestResult.sample_id == Sample.id
    ).filter(Sample.order_id == order_id).all()

    grouped = {}
    for res, cat in results:
        cat_key = cat.category
        if cat_key not in grouped:
            grouped[cat_key] = []
        grouped[cat_key].append({
            "name_ar":          cat.name_ar,
            "name_en":          cat.name_en,
            "code":             cat.code,
            "value":            res.value,
            "unit":             res.unit,
            "is_abnormal":      res.is_abnormal,
            "abnormal_flag":    res.abnormal_flag,
            "normal_range_min": cat.normal_range_min,
            "normal_range_max": cat.normal_range_max,
            "normal_range_text": cat.normal_range_text,
            "status":           res.status
        })

    return {
        "ok": True,
        "report": {
            "report_id":    f"RPT-{order_id:08d}",
            "generated_at": datetime.utcnow().isoformat(),
            "patient":      {"name": patient.full_name, "national_id": patient.national_id,
                             "birth_date": str(patient.birth_date) if patient.birth_date else None,
                             "gender": patient.gender} if patient else None,
            "order":        {"id": order.id, "status": order.status, "created_at": str(order.created_at)},
            "results":      grouped,
            "abnormal_count": sum(1 for r, _ in results if r.is_abnormal),
            "total_tests":    len(results)
        }
    }


# -------------------------------------------------------
# STATS
# -------------------------------------------------------

@router.get("/stats")
def lab_stats(db: Session = Depends(get_db),
              _=Depends(require_roles("admin", "lab_staff"))):
    from sqlalchemy import func

    order_stats  = dict(db.query(LabOrder.status, func.count()).group_by(LabOrder.status).all())
    sample_stats = dict(db.query(Sample.status, func.count()).group_by(Sample.status).all())

    total_results   = db.query(TestResult).count()
    abnormal_results = db.query(TestResult).filter(TestResult.is_abnormal == True).count()

    return {
        "ok":     True,
        "orders": order_stats,
        "samples": sample_stats,
        "results": {"total": total_results, "abnormal": abnormal_results}
    }
