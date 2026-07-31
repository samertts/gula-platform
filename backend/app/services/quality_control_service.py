from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app._compat import UTC

from ..models.quality_control import QualityControl


def evaluate_westgard(measured: float, expected: float, sd: float) -> dict:
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
    if sd is None or sd <= 0:
        return evaluate_westgard(measured, expected, sd)

    z_score = (measured - expected) / sd

    if abs(z_score) >= 3.0:
        return {"status": "fail", "violation": "1-3s"}

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

    historical_z = []
    for qc in recent:
        if qc.sd and qc.sd > 0 and qc.expected_value:
            hz = (qc.measured_value - qc.expected_value) / qc.sd
            historical_z.append(hz)

    if len(historical_z) >= 1:
        last_z = historical_z[0]
        if (z_score > 2.0 and last_z > 2.0) or (z_score < -2.0 and last_z < -2.0):
            return {"status": "fail", "violation": "2-2s"}
        if abs(z_score - last_z) >= 4.0:
            return {"status": "fail", "violation": "R-4s"}

    if abs(z_score) >= 2.0:
        return {"status": "warning", "violation": "1-2s"}

    if len(historical_z) >= 3:
        recent_four = [z_score, *historical_z[:3]]
        if all(z > 1.0 for z in recent_four) or all(z < -1.0 for z in recent_four):
            return {"status": "fail", "violation": "4-1s"}

    if len(historical_z) >= 9:
        recent_ten = [z_score, *historical_z[:9]]
        if all(z > 0 for z in recent_ten) or all(z < 0 for z in recent_ten):
            return {"status": "fail", "violation": "10-x"}

    return {"status": "pass", "violation": None}


def submit_single_qc(
    test_code: str,
    level: str,
    expected_value: float,
    measured_value: float,
    sd: float | None,
    lab_id: int,
    performed_by: str,
    db: Session,
    unit: str | None = None,
    instrument_name: str | None = None,
    lot_number: str | None = None,
    notes: str | None = None,
) -> dict:
    if level not in ("low", "normal", "high"):
        raise HTTPException(status_code=400, detail="Level must be: low, normal, high")

    eval_result = evaluate_westgard_full(
        db,
        lab_id,
        test_code,
        level,
        measured_value,
        expected_value,
        sd or 0,
        instrument_name,
        lot_number,
    )

    qc = QualityControl(
        lab_id=lab_id,
        test_code=test_code,
        level=level,
        expected_value=expected_value,
        measured_value=measured_value,
        sd=sd,
        unit=unit,
        instrument_name=instrument_name,
        lot_number=lot_number,
        status=eval_result["status"],
        violation=eval_result["violation"],
        notes=notes,
        performed_by=performed_by,
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


def submit_batch_qc(
    results: list[dict],
    lab_id: int,
    performed_by: str,
    db: Session,
) -> dict:
    items = []
    failures = 0
    for r in results:
        eval_result = evaluate_westgard_full(
            db,
            lab_id,
            r["test_code"],
            r["level"],
            r["measured_value"],
            r["expected_value"],
            r.get("sd") or 0,
            r.get("instrument_name"),
            r.get("lot_number"),
        )
        qc = QualityControl(
            lab_id=lab_id,
            test_code=r["test_code"],
            level=r["level"],
            expected_value=r["expected_value"],
            measured_value=r["measured_value"],
            sd=r.get("sd"),
            unit=r.get("unit"),
            instrument_name=r.get("instrument_name"),
            lot_number=r.get("lot_number"),
            status=eval_result["status"],
            violation=eval_result["violation"],
            notes=r.get("notes"),
            performed_by=performed_by,
        )
        db.add(qc)
        if eval_result["status"] == "fail":
            failures += 1
        items.append({"test_code": r["test_code"], "level": r["level"], **eval_result})

    db.commit()
    return {
        "message": f"Recorded {len(results)} QC results ({failures} failures)",
        "message_ar": f"تم تسجيل {len(results)} نتيجة مراقبة جودة ({failures} فشل)",
        "results": items,
        "total_failures": failures,
    }


def list_qc_records(
    lab_id: int,
    db: Session,
    test_code: str | None = None,
    status: str | None = None,
    days: int = 7,
    skip: int = 0,
    limit: int = 50,
) -> dict:
    cutoff = datetime.now(UTC) - timedelta(days=days)
    query = db.query(QualityControl).filter(
        QualityControl.lab_id == lab_id,
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


def get_qc_summary(
    lab_id: int,
    db: Session,
    days: int = 7,
) -> dict:
    cutoff = datetime.now(UTC) - timedelta(days=days)
    stats = (
        db.query(
            QualityControl.test_code,
            func.count(QualityControl.id).label("total"),
            func.count(func.nullif(QualityControl.status != "pass", False)).label("issues"),
        )
        .filter(
            QualityControl.lab_id == lab_id,
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
            }
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
