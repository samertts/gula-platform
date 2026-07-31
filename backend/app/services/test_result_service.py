import secrets
from datetime import date, datetime

import sqlalchemy as sa
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session, joinedload

from app._compat import UTC

from ..core.events import RESULT_CRITICAL, events
from ..domain.order_state import enforce_transition
from ..models.lab_order import LabOrder
from ..models.lab_result import LabResult, hash_token
from ..models.lab_user import LabUser
from ..models.patient import Patient
from ..models.sample import Sample, generate_barcode
from ..models.test_type import TestType
from ..security.rate_limit import get_client_ip
from ..services.audit_service import log_action
from ..services.critical_alerts import check_critical
from ..services.interpretation import get_flag, interpret_result


def derive_status(order: LabOrder | None) -> str:
    if order is None:
        return "pending"
    if order.status == "validated":
        return "verified"
    if order.status == "cancelled":
        return "cancelled"
    return "pending"


def result_dict(r: LabResult, patient: Patient | None = None) -> dict:
    order = r.order
    interpretation = None
    if r.value is not None:
        interpretation = interpret_result(r.test_name, r.value, r.normal_range_low, r.normal_range_high)
    flag = r.flag or "unknown"
    is_critical = flag == "critical"
    is_abnormal = flag in ("critical", "H", "L")
    tt = r.test_type
    p = patient or (order.patient if order else None)
    sample_barcode = None
    if order is not None and getattr(order, "samples", None):
        sample_barcode = order.samples[0].barcode if order.samples else None
    return {
        "id": r.id, "order_id": r.order_id,
        "health_id": p.health_id if p else None,
        "patient_name": p.full_name if p else None,
        "test_name": r.test_name,
        "test_code": tt.test_code if tt else None,
        "category": tt.category if tt else None,
        "value": r.value, "value_text": r.value_text, "unit": r.unit,
        "normal_range_low": r.normal_range_low, "normal_range_high": r.normal_range_high,
        "flag": flag, "is_critical": is_critical, "is_abnormal": is_abnormal,
        "status": derive_status(order),
        "verified_by": order.validated_by if order else None,
        "verified_at": order.validated_at.isoformat() if order and order.validated_at else None,
        "sample_barcode": sample_barcode,
        "result_token": r.token, "interpretation": interpretation,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def validate_payload(
    test_name: str, value: float | None, unit: str | None,
    normal_low: float | None, normal_high: float | None,
    test_code: str | None, db: Session,
) -> list[dict]:
    warnings: list[dict] = []
    tt: TestType | None = None
    if test_code:
        tt = db.query(TestType).filter(TestType.test_code == test_code).first()
    if tt is None:
        tt = db.query(TestType).filter(TestType.test_name.ilike(test_name)).first()

    if tt and unit and tt.unit and unit.strip() and unit.strip().lower() != tt.unit.lower():
        warnings.append({"code": "unit_mismatch", "message": f"Unit '{unit}' does not match expected '{tt.unit}' for {test_name}.", "expected": tt.unit, "provided": unit})

    if normal_low is not None and normal_high is not None and normal_low > normal_high:
        warnings.append({"code": "range_inverted", "message": "normal_range_low is greater than normal_range_high."})

    if value is not None:
        if value < 0:
            warnings.append({"code": "negative_value", "message": "Numeric lab value should not be negative."})
        ref_low = normal_low if normal_low is not None else (tt.normal_range_low if tt else None)
        ref_high = normal_high if normal_high is not None else (tt.normal_range_high if tt else None)
        if ref_high is not None and ref_high > 0 and value > ref_high * 10:
            warnings.append({"code": "implausibly_high", "message": f"Value {value} is more than 10x the upper reference limit ({ref_high})."})
        if ref_low is not None and ref_low > 0 and value < ref_low * 0.1:
            warnings.append({"code": "implausibly_low", "message": f"Value {value} is less than 10% of the lower reference limit ({ref_low})."})
        crit = check_critical(test_name, value)
        if crit:
            warnings.append({"code": "critical_range", "message": crit["message"], "severity": crit["severity"]})

    if value is None and not tt:
        warnings.append({"code": "unknown_test", "message": f"Test '{test_name}' is not in the reference catalog."})

    return warnings


def get_patient_scoped(db: Session, current_user: LabUser, health_id: str) -> Patient:
    patient = db.query(Patient).filter(Patient.health_id == health_id, Patient.lab_id == current_user.lab_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


def fill_ranges_from_catalog(
    db: Session, test_name: str, test_code: str | None,
    normal_low: float | None, normal_high: float | None, unit: str | None,
) -> tuple:
    tt: TestType | None = None
    if test_code:
        tt = db.query(TestType).filter(TestType.test_code == test_code).first()
    if tt is None:
        tt = db.query(TestType).filter(TestType.test_name.ilike(test_name)).first()
    if tt is not None:
        if normal_low is None:
            normal_low = tt.normal_range_low
        if normal_high is None:
            normal_high = tt.normal_range_high
        if not unit:
            unit = tt.unit
    return normal_low, normal_high, unit, tt


def create_result(
    health_id: str, test_name: str, test_code: str | None,
    value: float | None, value_text: str | None, unit: str | None,
    normal_range_low: float | None, normal_range_high: float | None,
    sample_type: str | None, doctor_name: str | None, order_id: int | None,
    current_user: LabUser, request: Request, db: Session,
) -> dict:
    patient = get_patient_scoped(db, current_user, health_id)

    normal_low, normal_high, resolved_unit, tt = fill_ranges_from_catalog(
        db, test_name, test_code, normal_range_low, normal_range_high, unit,
    )

    order: LabOrder | None = None
    if order_id is not None:
        order = db.query(LabOrder).filter(
            LabOrder.id == order_id, LabOrder.lab_id == current_user.lab_id,
            LabOrder.patient_id == patient.id,
        ).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if order.status in ("validated", "cancelled"):
            raise HTTPException(status_code=409, detail=f"Order is {order.status} and cannot accept new results")

    if order is None:
        order = LabOrder(
            patient_id=patient.id, lab_id=current_user.lab_id,
            doctor_name=doctor_name, status="completed",
        )
        db.add(order)
        db.flush()

    existing_sample = db.query(Sample).filter(Sample.order_id == order.id).first() if order_id is not None else None
    if existing_sample is None:
        sample = Sample(
            order_id=order.id, barcode=generate_barcode(),
            sample_type=(sample_type or "blood").strip(), collected_by=current_user.email,
        )
        db.add(sample)
    else:
        sample = existing_sample

    flag = "unknown"
    if value is not None and normal_low is not None and normal_high is not None:
        flag = get_flag(value, normal_low, normal_high, test_name=test_name)

    token = secrets.token_urlsafe(32)
    token_h = hash_token(token)
    while db.query(LabResult).filter(LabResult.token_hash == token_h).first():
        token = secrets.token_urlsafe(32)
        token_h = hash_token(token)

    result = LabResult(
        order_id=order.id, test_type_id=tt.id if tt else None,
        test_name=test_name, value=value, value_text=value_text,
        unit=resolved_unit, normal_range_low=normal_low,
        normal_range_high=normal_high, flag=flag, token=token, token_hash=token_h,
    )
    db.add(result)

    log_action(db, action="create", resource_type="lab_result", user_id=current_user.id,
               user_role=current_user.role,
               details=f"Created result '{test_name}' for patient {patient.full_name}",
               ip_address=get_client_ip(request))
    db.commit()
    db.refresh(result)
    db.refresh(order)

    if flag == "critical" and value is not None:
        events.emit(RESULT_CRITICAL, {
            "order_id": order.id, "result_id": result.id, "patient_id": patient.id,
            "patient_name": patient.full_name, "patient_phone": patient.phone,
            "test_name": test_name, "value": value, "lab_id": order.lab_id,
        })

    analysis = {
        "flag": flag, "is_critical": flag == "critical",
        "is_abnormal": flag in ("critical", "H", "L"),
        "interpretation": interpret_result(test_name, value, normal_low, normal_high) if value is not None else None,
        "warnings": validate_payload(test_name, value, resolved_unit, normal_low, normal_high, test_code, db),
    }

    return {
        "message": "Result created",
        "result": result_dict(result, patient),
        "sample_barcode": sample.barcode,
        "analysis": analysis,
    }


def validate_result_payload(
    test_name: str, value: float | None, unit: str | None,
    normal_low: float | None, normal_high: float | None,
    test_code: str | None, db: Session,
) -> dict:
    warnings = validate_payload(test_name, value, unit, normal_low, normal_high, test_code, db)
    return {
        "valid": not any(
            w["code"] in ("unit_mismatch", "range_inverted", "negative_value", "implausibly_high", "implausibly_low")
            for w in warnings
        ),
        "warnings": warnings,
    }


def get_result(result_id: int, current_user: LabUser, db: Session) -> dict:
    q = (
        db.query(LabResult)
        .join(LabOrder, LabResult.order_id == LabOrder.id)
        .options(
            joinedload(LabResult.order).joinedload(LabOrder.patient),
            joinedload(LabResult.order).joinedload(LabOrder.samples),
            joinedload(LabResult.test_type),
        )
        .filter(LabResult.id == result_id)
    )
    if current_user.role == "doctor":
        q = q.filter(LabOrder.doctor_user_id == current_user.id)
    elif current_user.role == "citizen":
        q = q.filter(sa.false())
    else:
        q = q.filter(LabOrder.lab_id == current_user.lab_id)

    result = q.first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    return result_dict(result)


def verify_result(result_id: int, current_user: LabUser, request: Request, db: Session) -> dict:
    if current_user.role not in ("admin", "master_admin", "doctor"):
        raise HTTPException(status_code=403, detail="Only admin or doctor can verify results")

    base = (
        db.query(LabResult)
        .join(LabOrder, LabResult.order_id == LabOrder.id)
        .filter(LabResult.id == result_id)
    )
    if current_user.role == "doctor":
        base = base.filter(LabOrder.doctor_user_id == current_user.id)
    else:
        base = base.filter(LabOrder.lab_id == current_user.lab_id)

    result = base.first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    order = db.query(LabOrder).filter(LabOrder.id == result.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Parent order not found")

    if order.status == "validated":
        return {"message": "Result already verified", "result": result_dict(result)}

    enforce_transition(order.status, "validated")

    now = datetime.now(UTC)
    rows = (
        db.query(LabOrder)
        .filter(LabOrder.id == order.id, LabOrder.locked_at.is_(None))
        .update({"status": "validated", "validated_by": current_user.id, "validated_at": now, "locked_at": now},
                synchronize_session="fetch")
    )
    if rows == 0:
        raise HTTPException(status_code=409, detail="Result is already verified and locked")

    log_action(db, action="verify", resource_type="lab_result", resource_id=result.id,
               user_id=current_user.id, user_role=current_user.role,
               details=f"Result verified via order {order.id} by {current_user.email}",
               ip_address=get_client_ip(request))
    db.commit()
    db.refresh(result)

    return {"message": "Result verified", "result": result_dict(result)}


def list_citizen_results(
    health_id: str, category: str | None, date_from: date | None, date_to: date | None,
    is_abnormal: bool | None, skip: int, limit: int,
    current_user: LabUser, db: Session,
) -> dict:
    patient = get_patient_scoped(db, current_user, health_id)

    q = (
        db.query(LabResult)
        .join(LabOrder, LabResult.order_id == LabOrder.id)
        .outerjoin(TestType, LabResult.test_type_id == TestType.id)
        .options(
            joinedload(LabResult.order).joinedload(LabOrder.patient),
            joinedload(LabResult.order).joinedload(LabOrder.samples),
            joinedload(LabResult.test_type),
        )
        .filter(LabOrder.patient_id == patient.id, LabOrder.lab_id == current_user.lab_id)
    )

    if category:
        q = q.filter(TestType.category == category)
    if date_from:
        q = q.filter(LabResult.created_at >= datetime.combine(date_from, datetime.min.time(), tzinfo=UTC))
    if date_to:
        q = q.filter(LabResult.created_at < datetime.combine(date_to, datetime.max.time(), tzinfo=UTC))
    if is_abnormal is True:
        q = q.filter(LabResult.flag.in_(("critical", "H", "L")))
    elif is_abnormal is False:
        q = q.filter(sa.or_(LabResult.flag == "normal", LabResult.flag.is_(None)))

    total = q.count()
    rows = q.order_by(LabResult.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "patient": {"id": patient.id, "health_id": patient.health_id, "full_name": patient.full_name},
        "total": total, "skip": skip, "limit": limit,
        "results": [result_dict(r, patient) for r in rows],
    }


def list_results(
    current_user: LabUser,
    db: Session,
    *,
    health_id: str | None = None,
    category: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    is_abnormal: bool | None = None,
    skip: int = 0,
    limit: int = 50,
) -> dict:
    """List test results scoped to the current user's laboratory.

    Mirrors ``list_citizen_results`` but the health_id filter is optional so
    the lab can browse all results (used by the frontend ResultsPage).
    """
    patient = None
    q = (
        db.query(LabResult)
        .join(LabOrder, LabResult.order_id == LabOrder.id)
        .outerjoin(TestType, LabResult.test_type_id == TestType.id)
        .options(
            joinedload(LabResult.order).joinedload(LabOrder.patient),
            joinedload(LabResult.order).joinedload(LabOrder.samples),
            joinedload(LabResult.test_type),
        )
        .filter(LabOrder.lab_id == current_user.lab_id)
    )

    if health_id:
        patient = get_patient_scoped(db, current_user, health_id)
        q = q.filter(LabOrder.patient_id == patient.id)
    if category:
        q = q.filter(TestType.category == category)
    if date_from:
        q = q.filter(LabResult.created_at >= datetime.combine(date_from, datetime.min.time(), tzinfo=UTC))
    if date_to:
        q = q.filter(LabResult.created_at < datetime.combine(date_to, datetime.max.time(), tzinfo=UTC))
    if is_abnormal is True:
        q = q.filter(LabResult.flag.in_(("critical", "H", "L")))
    elif is_abnormal is False:
        q = q.filter(sa.or_(LabResult.flag == "normal", LabResult.flag.is_(None)))

    total = q.count()
    rows = q.order_by(LabResult.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total, "skip": skip, "limit": limit,
        "results": [result_dict(r, patient or r.order.patient) for r in rows],
    }


def citizen_timeline(
    health_id: str, category: str | None,
    current_user: LabUser, db: Session,
) -> dict:
    patient = get_patient_scoped(db, current_user, health_id)

    q = (
        db.query(LabResult)
        .join(LabOrder, LabResult.order_id == LabOrder.id)
        .outerjoin(TestType, LabResult.test_type_id == TestType.id)
        .options(joinedload(LabResult.test_type))
        .filter(LabOrder.patient_id == patient.id, LabOrder.lab_id == current_user.lab_id, LabResult.value.isnot(None))
    )
    if category:
        q = q.filter(TestType.category == category)

    rows = q.order_by(LabResult.created_at.asc()).all()

    grouped: dict[str, dict] = {}
    for r in rows:
        tt = r.test_type
        key = tt.test_code if tt else r.test_name.lower().replace(" ", "_")
        if key not in grouped:
            grouped[key] = {
                "test_code": tt.test_code if tt else None,
                "test_name": r.test_name, "category": tt.category if tt else None,
                "unit": r.unit or (tt.unit if tt else None),
                "normal_range_low": r.normal_range_low if r.normal_range_low is not None else (tt.normal_range_low if tt else None),
                "normal_range_high": r.normal_range_high if r.normal_range_high is not None else (tt.normal_range_high if tt else None),
                "points": [],
            }
        grouped[key]["points"].append({
            "date": r.created_at.isoformat() if r.created_at else None,
            "value": r.value, "flag": r.flag,
        })

    return {
        "patient": {"id": patient.id, "health_id": patient.health_id, "full_name": patient.full_name},
        "series": list(grouped.values()),
    }
