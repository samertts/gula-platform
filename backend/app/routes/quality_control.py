"""Quality Control endpoints - Westgard rules for lab instrument validation."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app._compat import UTC

from ..database import get_db
from ..models.lab_user import LabUser
from ..models.quality_control import QualityControl
from ..security.dependencies import get_current_user

router = APIRouter(prefix="/qc", tags=["quality-control"])


class QCSubmit(BaseModel):
    test_code: str
    level: str  # low, normal, high
    expected_value: float
    measured_value: float
    sd: float | None = None
    unit: str | None = None
    instrument_name: str | None = None
    lot_number: str | None = None
    notes: str | None = None


class QCBatchSubmit(BaseModel):
    results: list[QCSubmit]


def evaluate_westgard(measured: float, expected: float, sd: float) -> dict:
    """Apply Westgard multi-rules for QC evaluation (single-rule only).
    Returns status (pass/warning/fail) and violation type.
    """
    if sd is None or sd <= 0:
        deviation_pct = abs(measured - expected) / expected * 100 if expected != 0 else 0
        if deviation_pct > 15:
            return {"status": "fail", "violation": "deviation>15%"}
        if deviation_pct > 10:
            return {"status": "warning", "violation": "deviation>10%"}
        return {"status": "pass", "violation": None}

    z_score = (measured - expected) / sd

    if abs(z_score) >= 3.0:
        return {"status": "fail", "violation": "1-3s"}

    if abs(z_score) >= 2.0:
        return {"status": "warning", "violation": "1-2s"}

    return {"status": "pass", "violation": None}


def evaluate_westgard_full(
    db: Session,
    lab_id: int,
    test_code: str,
    level: str,
    measured: float,
    expected: float,
    sd: float,
    instrument_name: str | None = None,
    lot_number: str | None = None,
) -> dict:
    """Apply ALL Westgard multi-rules using historical QC data.
    Rules: 1-3s, 1-2s, 2-2s, R-4s, 4-1s, 10-x.
    """
    if sd is None or sd <= 0:
        return evaluate_westgard(measured, expected, sd)

    z_score = (measured - expected) / sd

    # 1-3s: Single measurement >3SD → FAIL
    if abs(z_score) >= 3.0:
        return {"status": "fail", "violation": "1-3s"}

    # Query recent QC results for same test/level/instrument/lot
    cutoff = datetime.now(UTC) - timedelta(hours=48)
    filters = [
        QualityControl.lab_id == lab_id,
        QualityControl.test_code == test_code,
        QualityControl.level == level,
        QualityControl.created_at >= cutoff,
    ]
    if instrument_name:
        filters.append(QualityControl.instrument_name == instrument_name)
    if lot_number:
        filters.append(QualityControl.lot_number == lot_number)

    recent = (
        db.query(QualityControl)
        .filter(*filters)
        .order_by(QualityControl.created_at.desc())
        .limit(15)
        .all()
    )

    # Compute z-scores for historical measurements
    historical_z = []
    for qc in recent:
        if qc.sd and qc.sd > 0 and qc.expected_value:
            hz = (qc.measured_value - qc.expected_value) / qc.sd
            historical_z.append(hz)

    # 1-2s: Single measurement >2SD → WARNING (checked first before multi-rules)
    if abs(z_score) >= 2.0:
        return {"status": "warning", "violation": "1-2s"}

    # 2-2s: Two consecutive measurements >2SD on same side
    if len(historical_z) >= 1:
        last_z = historical_z[0]
        if z_score > 2.0 and last_z > 2.0:
            return {"status": "fail", "violation": "2-2s"}
        if z_score < -2.0 and last_z < -2.0:
            return {"status": "fail", "violation": "2-2s"}

    # R-4s: Two consecutive measurements differ by >4SD
    if len(historical_z) >= 1:
        last_z = historical_z[0]
        if abs(z_score - last_z) >= 4.0:
            return {"status": "fail", "violation": "R-4s"}

    # 4-1s: Four consecutive measurements >1SD on same side
    if len(historical_z) >= 3:
        recent_four = [z_score, *historical_z[:3]]
        if all(z > 1.0 for z in recent_four):
            return {"status": "fail", "violation": "4-1s"}
        if all(z < -1.0 for z in recent_four):
            return {"status": "fail", "violation": "4-1s"}

    # 10-x: Ten consecutive measurements on same side of mean
    if len(historical_z) >= 9:
        recent_ten = [z_score, *historical_z[:9]]
        if all(z > 0 for z in recent_ten):
            return {"status": "fail", "violation": "10-x"}
        if all(z < 0 for z in recent_ten):
            return {"status": "fail", "violation": "10-x"}

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

    eval_result = evaluate_westgard_full(
        db,
        lab_id=current_user.lab_id,
        test_code=data.test_code,
        level=data.level,
        measured=data.measured_value,
        expected=data.expected_value,
        sd=data.sd or 0,
        instrument_name=data.instrument_name,
        lot_number=data.lot_number,
    )

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
        eval_result = evaluate_westgard_full(
            db,
            lab_id=current_user.lab_id,
            test_code=item.test_code,
            level=item.level,
            measured=item.measured_value,
            expected=item.expected_value,
            sd=item.sd or 0,
            instrument_name=item.instrument_name,
            lot_number=item.lot_number,
        )
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
    test_code: str | None = None,
    status: str | None = None,
    days: int = Query(7, ge=1, le=90),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List QC results for the lab."""
    cutoff = datetime.now(UTC) - timedelta(days=days)
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
    cutoff = datetime.now(UTC) - timedelta(days=days)
    stats = (
        db.query(
            QualityControl.test_code,
            func.count(QualityControl.id).label("total"),
            func.count(func.nullif(QualityControl.status != "pass", False)).label("issues"),
        )
        .filter(
            QualityControl.lab_id == current_user.lab_id,
            QualityControl.created_at >= cutoff,
        )
        .group_by(QualityControl.test_code)
        .all()
    )

    summary = []
    for s in stats:
        pass_rate = ((s.total - s.issues) / s.total * 100) if s.total > 0 else 100
        summary.append(
            {
                "test_code": s.test_code,
                "total": s.total,
                "issues": s.issues,
                "pass_rate": round(pass_rate, 1),
                "status": "good"
                if pass_rate >= 95
                else "review"
                if pass_rate >= 80
                else "critical",
            },
        )

    return {
        "period_days": days,
        "tests": summary,
        "overall_pass_rate": round(sum(s["pass_rate"] for s in summary) / len(summary), 1)
        if summary
        else 100,
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
