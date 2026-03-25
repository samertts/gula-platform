"""Quality Control endpoints - Westgard rules for lab instrument validation."""
import math
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from ..database import get_db
from ..models.quality_control import QualityControl
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user

router = APIRouter(prefix="/qc", tags=["quality-control"])


class QCSubmit(BaseModel):
    test_code: str
    level: str  # low, normal, high
    expected_value: float
    measured_value: float
    sd: Optional[float] = None
    unit: Optional[str] = None
    instrument_name: Optional[str] = None
    lot_number: Optional[str] = None
    notes: Optional[str] = None


class QCBatchSubmit(BaseModel):
    results: List[QCSubmit]


def evaluate_westgard(measured: float, expected: float, sd: float) -> dict:
    """Apply Westgard multi-rules for QC evaluation.
    Returns status (pass/warning/fail) and violation type."""
    if sd is None or sd <= 0:
        # Without SD, use simple 10% deviation check
        deviation_pct = abs(measured - expected) / expected * 100 if expected != 0 else 0
        if deviation_pct > 15:
            return {"status": "fail", "violation": "deviation>15%"}
        if deviation_pct > 10:
            return {"status": "warning", "violation": "deviation>10%"}
        return {"status": "pass", "violation": None}

    z_score = (measured - expected) / sd

    # 1-3s rule: Single measurement exceeds mean +/- 3SD → FAIL (reject run)
    if abs(z_score) >= 3.0:
        return {"status": "fail", "violation": "1-3s"}

    # 1-2s rule: Single measurement exceeds mean +/- 2SD → WARNING (investigate)
    if abs(z_score) >= 2.0:
        return {"status": "warning", "violation": "1-2s"}

    return {"status": "pass", "violation": None}


@router.post("", status_code=201)
def submit_qc(
    data: QCSubmit,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit a single QC measurement."""
    if data.level not in ("low", "normal", "high"):
        raise HTTPException(status_code=400, detail="Level must be: low, normal, high")

    eval_result = evaluate_westgard(data.measured_value, data.expected_value, data.sd or 0)

    qc = QualityControl(
        lab_id=current_user.lab_id,
        test_code=data.test_code,
        level=data.level,
        expected_value=data.expected_value,
        measured_value=data.measured_value,
        sd=data.sd,
        unit=data.unit,
        instrument_name=data.instrument_name,
        lot_number=data.lot_number,
        status=eval_result["status"],
        violation=eval_result["violation"],
        notes=data.notes,
        performed_by=current_user.name,
    )
    db.add(qc)
    db.commit()
    db.refresh(qc)

    return {
        "message": "QC result recorded",
        "message_ar": "تم تسجيل نتيجة مراقبة الجودة",
        "qc": qc_to_dict(qc),
        "evaluation": eval_result,
    }


@router.post("/batch", status_code=201)
def submit_qc_batch(
    data: QCBatchSubmit,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit multiple QC measurements at once."""
    results = []
    failures = 0
    for item in data.results:
        eval_result = evaluate_westgard(item.measured_value, item.expected_value, item.sd or 0)
        qc = QualityControl(
            lab_id=current_user.lab_id,
            test_code=item.test_code,
            level=item.level,
            expected_value=item.expected_value,
            measured_value=item.measured_value,
            sd=item.sd,
            unit=item.unit,
            instrument_name=item.instrument_name,
            lot_number=item.lot_number,
            status=eval_result["status"],
            violation=eval_result["violation"],
            notes=item.notes,
            performed_by=current_user.name,
        )
        db.add(qc)
        if eval_result["status"] == "fail":
            failures += 1
        results.append({"test_code": item.test_code, "level": item.level, **eval_result})

    db.commit()
    return {
        "message": f"Recorded {len(results)} QC results ({failures} failures)",
        "message_ar": f"تم تسجيل {len(results)} نتيجة مراقبة جودة ({failures} فشل)",
        "results": results,
        "total_failures": failures,
    }


@router.get("")
def list_qc(
    test_code: Optional[str] = None,
    status: Optional[str] = None,
    days: int = Query(7, ge=1, le=90),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List QC results for the lab."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    query = db.query(QualityControl).filter(
        QualityControl.lab_id == current_user.lab_id,
        QualityControl.created_at >= cutoff,
    )
    if test_code:
        query = query.filter(QualityControl.test_code == test_code)
    if status:
        query = query.filter(QualityControl.status == status)

    total = query.count()
    records = query.order_by(QualityControl.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "qc_results": [qc_to_dict(q) for q in records],
    }


@router.get("/summary")
def qc_summary(
    days: int = Query(7, ge=1, le=90),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """QC dashboard summary - pass/warning/fail counts by test."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    stats = db.query(
        QualityControl.test_code,
        func.count(QualityControl.id).label("total"),
        func.count(func.nullif(QualityControl.status != "pass", False)).label("issues"),
    ).filter(
        QualityControl.lab_id == current_user.lab_id,
        QualityControl.created_at >= cutoff,
    ).group_by(QualityControl.test_code).all()

    summary = []
    for s in stats:
        pass_rate = ((s.total - s.issues) / s.total * 100) if s.total > 0 else 100
        summary.append({
            "test_code": s.test_code,
            "total": s.total,
            "issues": s.issues,
            "pass_rate": round(pass_rate, 1),
            "status": "good" if pass_rate >= 95 else "review" if pass_rate >= 80 else "critical",
        })

    return {
        "period_days": days,
        "tests": summary,
        "overall_pass_rate": round(
            sum(s["pass_rate"] for s in summary) / len(summary), 1
        ) if summary else 100,
    }


def qc_to_dict(q: QualityControl) -> dict:
    return {
        "id": q.id,
        "test_code": q.test_code,
        "level": q.level,
        "expected_value": q.expected_value,
        "measured_value": q.measured_value,
        "sd": q.sd,
        "unit": q.unit,
        "instrument_name": q.instrument_name,
        "lot_number": q.lot_number,
        "status": q.status,
        "violation": q.violation,
        "notes": q.notes,
        "performed_by": q.performed_by,
        "created_at": q.created_at.isoformat() if q.created_at else None,
    }
