"""Test Results API (CMD-009).

Higher-level endpoints built on top of the existing LabOrder/LabResult model.
These endpoints are citizen-centric (keyed by patient.health_id) and provide
per-result operations that complement the order-centric /orders API:

    POST   /test-results/                         create a single result
    POST   /test-results/validate                 pre-save sanity check
    GET    /test-results/{result_id}              fetch a single result
    PUT    /test-results/{result_id}/verify       mark result verified (locks order)
    GET    /test-results/citizen/{health_id}      list results for a citizen
    GET    /test-results/citizen/{health_id}/timeline  values over time per test
"""
from __future__ import annotations

import secrets
from datetime import datetime, timezone, date
from typing import List, Optional

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..domain.order_state import enforce_transition
from ..core.events import events, RESULT_CRITICAL
from ..models.lab_order import LabOrder
from ..models.lab_result import LabResult, hash_token
from ..models.lab_user import LabUser
from ..models.patient import Patient
from ..models.sample import Sample, generate_barcode
from ..models.test_type import TestType
from ..routes.critical_alerts import check_critical
from ..security.dependencies import get_current_user
from ..security.rate_limit import get_client_ip, rate_limit_user
from ..services.audit_service import log_action
from ..services.interpretation import get_flag, interpret_result

router = APIRouter(prefix="/test-results", tags=["test-results"])


# ───────────────────────── schemas ─────────────────────────

class TestResultCreate(BaseModel):
    """Input for POST /test-results/."""
    health_id: str = Field(..., min_length=3, max_length=20, description="Citizen health_id")
    test_name: str = Field(..., min_length=1, max_length=200)
    test_code: Optional[str] = Field(None, max_length=50)
    value: Optional[float] = None
    value_text: Optional[str] = Field(None, max_length=200)
    unit: Optional[str] = Field(None, max_length=20)
    normal_range_low: Optional[float] = None
    normal_range_high: Optional[float] = None
    sample_type: Optional[str] = Field("blood", max_length=50)
    doctor_name: Optional[str] = Field(None, max_length=200)
    order_id: Optional[int] = Field(
        None, description="Attach to an existing order; otherwise a new one is created."
    )

    @field_validator("test_name", "doctor_name")
    @classmethod
    def _strip(cls, v):
        return v.strip() if isinstance(v, str) else v


class TestResultValidateRequest(BaseModel):
    """Input for POST /test-results/validate — reuses TestResultCreate subset."""
    test_name: str = Field(..., min_length=1, max_length=200)
    test_code: Optional[str] = Field(None, max_length=50)
    value: Optional[float] = None
    unit: Optional[str] = Field(None, max_length=20)
    normal_range_low: Optional[float] = None
    normal_range_high: Optional[float] = None


# ───────────────────────── helpers ─────────────────────────

def _derive_status(order: Optional[LabOrder]) -> str:
    """Translate order state into a result-level status string.

    pending/completed → "pending"   (entered but not yet verified)
    validated         → "verified"
    cancelled         → "cancelled"
    """
    if order is None:
        return "pending"
    if order.status == "validated":
        return "verified"
    if order.status == "cancelled":
        return "cancelled"
    return "pending"


def _result_dict(r: LabResult, patient: Optional[Patient] = None) -> dict:
    order = r.order
    interpretation = None
    if r.value is not None:
        interpretation = interpret_result(
            r.test_name, r.value, r.normal_range_low, r.normal_range_high
        )
    flag = r.flag or "unknown"
    is_critical = flag == "critical"
    is_abnormal = flag in ("critical", "H", "L")

    tt = r.test_type
    p = patient or (order.patient if order else None)

    # Sample barcode: there can be many samples per order; pick the first.
    sample_barcode = None
    if order is not None and getattr(order, "samples", None):
        sample_barcode = order.samples[0].barcode if order.samples else None

    return {
        "id": r.id,
        "order_id": r.order_id,
        "health_id": p.health_id if p else None,
        "patient_name": p.full_name if p else None,
        "test_name": r.test_name,
        "test_code": tt.test_code if tt else None,
        "category": tt.category if tt else None,
        "value": r.value,
        "value_text": r.value_text,
        "unit": r.unit,
        "normal_range_low": r.normal_range_low,
        "normal_range_high": r.normal_range_high,
        "flag": flag,
        "is_critical": is_critical,
        "is_abnormal": is_abnormal,
        "status": _derive_status(order),
        "verified_by": order.validated_by if order else None,
        "verified_at": order.validated_at.isoformat()
            if order and order.validated_at else None,
        "sample_barcode": sample_barcode,
        "result_token": r.token,
        "interpretation": interpretation,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _validate_payload(
    test_name: str,
    value: Optional[float],
    unit: Optional[str],
    normal_low: Optional[float],
    normal_high: Optional[float],
    test_code: Optional[str],
    db: Session,
) -> List[dict]:
    """Return a list of warning dicts (empty if everything looks plausible)."""
    warnings: List[dict] = []

    # Look up the canonical test definition (by code first, then by name).
    tt: Optional[TestType] = None
    if test_code:
        tt = db.query(TestType).filter(TestType.test_code == test_code).first()
    if tt is None:
        tt = db.query(TestType).filter(TestType.test_name.ilike(test_name)).first()

    # Unit mismatch
    if tt and unit and tt.unit and unit.strip() and unit.strip().lower() != tt.unit.lower():
        warnings.append({
            "code": "unit_mismatch",
            "message": f"Unit '{unit}' does not match expected '{tt.unit}' for {test_name}.",
            "expected": tt.unit,
            "provided": unit,
        })

    # Reference range inversion
    if normal_low is not None and normal_high is not None and normal_low > normal_high:
        warnings.append({
            "code": "range_inverted",
            "message": "normal_range_low is greater than normal_range_high.",
        })

    # Value sanity
    if value is not None:
        if value < 0:
            warnings.append({
                "code": "negative_value",
                "message": "Numeric lab value should not be negative.",
            })
        # If we know the canonical range, flag extreme outliers (10× high / 0.1× low)
        ref_low = normal_low if normal_low is not None else (tt.normal_range_low if tt else None)
        ref_high = normal_high if normal_high is not None else (tt.normal_range_high if tt else None)
        if ref_high is not None and ref_high > 0 and value > ref_high * 10:
            warnings.append({
                "code": "implausibly_high",
                "message": f"Value {value} is more than 10× the upper reference limit ({ref_high}).",
            })
        if ref_low is not None and ref_low > 0 and value < ref_low * 0.1:
            warnings.append({
                "code": "implausibly_low",
                "message": f"Value {value} is less than 10% of the lower reference limit ({ref_low}).",
            })
        # Critical value hint (informational — the client may want to confirm)
        crit = check_critical(test_name, value)
        if crit:
            warnings.append({
                "code": "critical_range",
                "message": crit["message"],
                "severity": crit["severity"],
            })

    # Missing numeric value AND missing text — nothing to store
    if value is None and not tt:
        warnings.append({
            "code": "unknown_test",
            "message": f"Test '{test_name}' is not in the reference catalog.",
        })

    return warnings


def _get_patient_scoped(db: Session, current_user: LabUser, health_id: str) -> Patient:
    patient = db.query(Patient).filter(
        Patient.health_id == health_id,
        Patient.lab_id == current_user.lab_id,
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


def _fill_ranges_from_catalog(
    db: Session,
    test_name: str,
    test_code: Optional[str],
    normal_low: Optional[float],
    normal_high: Optional[float],
    unit: Optional[str],
) -> tuple[Optional[float], Optional[float], Optional[str], Optional[TestType]]:
    """Populate missing range/unit from the TestType catalog when available."""
    tt: Optional[TestType] = None
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


# ───────────────────────── endpoints ─────────────────────────

@router.post("/", status_code=201)
def create_test_result(
    data: TestResultCreate,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a single test result for a citizen (identified by health_id).

    - Verifies the patient exists in the caller's lab.
    - Auto-generates a sample barcode (a fresh Sample row per order).
    - Runs smart_analysis via the interpretation + critical-value engine.
    - Emits RESULT_CRITICAL when the value is critically abnormal.
    """
    patient = _get_patient_scoped(db, current_user, data.health_id)

    # Pull any missing reference data from the catalog.
    normal_low, normal_high, unit, tt = _fill_ranges_from_catalog(
        db, data.test_name, data.test_code,
        data.normal_range_low, data.normal_range_high, data.unit,
    )

    # Reuse an existing editable order or open a new one.
    order: Optional[LabOrder] = None
    if data.order_id is not None:
        order = db.query(LabOrder).filter(
            LabOrder.id == data.order_id,
            LabOrder.lab_id == current_user.lab_id,
            LabOrder.patient_id == patient.id,
        ).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if order.status in ("validated", "cancelled"):
            raise HTTPException(
                status_code=409,
                detail=f"Order is {order.status} and cannot accept new results",
            )

    if order is None:
        order = LabOrder(
            patient_id=patient.id,
            lab_id=current_user.lab_id,
            doctor_name=data.doctor_name,
            status="completed",
        )
        db.add(order)
        db.flush()

    # Ensure at least one sample exists for this order (auto-generated barcode).
    existing_sample = (
        db.query(Sample).filter(Sample.order_id == order.id).first()
        if data.order_id is not None else None
    )
    if existing_sample is None:
        sample = Sample(
            order_id=order.id,
            barcode=generate_barcode(),
            sample_type=(data.sample_type or "blood").strip(),
            collected_by=current_user.email,
        )
        db.add(sample)
    else:
        sample = existing_sample

    # Compute clinical flag (smart_analysis via get_flag + critical_alerts)
    flag = "unknown"
    if data.value is not None and normal_low is not None and normal_high is not None:
        flag = get_flag(data.value, normal_low, normal_high, test_name=data.test_name)

    # Unique result token
    token = secrets.token_urlsafe(32)
    token_h = hash_token(token)
    while db.query(LabResult).filter(LabResult.token_hash == token_h).first():
        token = secrets.token_urlsafe(32)
        token_h = hash_token(token)

    result = LabResult(
        order_id=order.id,
        test_type_id=tt.id if tt else None,
        test_name=data.test_name,
        value=data.value,
        value_text=data.value_text,
        unit=unit,
        normal_range_low=normal_low,
        normal_range_high=normal_high,
        flag=flag,
        token=token,
        token_hash=token_h,
    )
    db.add(result)

    log_action(
        db,
        action="create",
        resource_type="lab_result",
        resource_id=None,  # id not yet assigned
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Created result '{data.test_name}' for patient {patient.full_name}",
        ip_address=get_client_ip(request),
    )
    db.commit()
    db.refresh(result)
    db.refresh(order)

    # Fire critical-value event for downstream notifications.
    if flag == "critical" and data.value is not None:
        events.emit(RESULT_CRITICAL, {
            "order_id": order.id,
            "result_id": result.id,
            "patient_id": patient.id,
            "patient_name": patient.full_name,
            "patient_phone": patient.phone,
            "test_name": data.test_name,
            "value": data.value,
            "lab_id": order.lab_id,
        })

    # Smart-analysis summary returned to the caller.
    analysis = {
        "flag": flag,
        "is_critical": flag == "critical",
        "is_abnormal": flag in ("critical", "H", "L"),
        "interpretation": interpret_result(
            data.test_name, data.value, normal_low, normal_high,
        ) if data.value is not None else None,
        "warnings": _validate_payload(
            data.test_name, data.value, unit, normal_low, normal_high,
            data.test_code, db,
        ),
    }

    return {
        "message": "Result created",
        "result": _result_dict(result, patient),
        "sample_barcode": sample.barcode,
        "analysis": analysis,
    }


@router.post("/validate")
def validate_test_result(
    data: TestResultValidateRequest,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Pre-save sanity check: returns warnings without persisting anything."""
    rate_limit_user(request, current_user.id, max_per_minute=60)
    warnings = _validate_payload(
        data.test_name, data.value, data.unit,
        data.normal_range_low, data.normal_range_high,
        data.test_code, db,
    )
    return {
        "valid": not any(w["code"] in (
            "unit_mismatch", "range_inverted", "negative_value",
            "implausibly_high", "implausibly_low",
        ) for w in warnings),
        "warnings": warnings,
    }


@router.get("/{result_id}")
def get_test_result(
    result_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch a single result — lab-scoped (and doctor-scoped for doctors)."""
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
    return _result_dict(result)


@router.put("/{result_id}/verify")
def verify_test_result(
    result_id: int,
    request: Request,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a result as verified. Triggers validation (lock) of the parent order.

    Only admin / master_admin / doctor may verify.  The verification is atomic
    (UPDATE ... WHERE locked_at IS NULL) so two concurrent callers cannot
    double-verify.
    """
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
        # Idempotent — already verified.
        return {
            "message": "Result already verified",
            "result": _result_dict(result),
        }

    enforce_transition(order.status, "validated")

    now = datetime.now(timezone.utc)
    rows = (
        db.query(LabOrder)
        .filter(LabOrder.id == order.id, LabOrder.locked_at.is_(None))
        .update(
            {
                "status": "validated",
                "validated_by": current_user.id,
                "validated_at": now,
                "locked_at": now,
            },
            synchronize_session="fetch",
        )
    )
    if rows == 0:
        raise HTTPException(status_code=409, detail="Result is already verified and locked")

    log_action(
        db,
        action="verify",
        resource_type="lab_result",
        resource_id=result.id,
        user_id=current_user.id,
        user_role=current_user.role,
        details=f"Result verified via order {order.id} by {current_user.email}",
        ip_address=get_client_ip(request),
    )
    db.commit()
    db.refresh(result)

    return {
        "message": "Result verified",
        "result": _result_dict(result),
    }


@router.get("/citizen/{health_id}")
def list_citizen_results(
    health_id: str,
    category: Optional[str] = Query(None, max_length=50),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    is_abnormal: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """All results for a citizen, filterable by category / date / abnormal flag.

    Sorted newest first, paginated.
    """
    patient = _get_patient_scoped(db, current_user, health_id)

    q = (
        db.query(LabResult)
        .join(LabOrder, LabResult.order_id == LabOrder.id)
        .outerjoin(TestType, LabResult.test_type_id == TestType.id)
        .options(
            joinedload(LabResult.order).joinedload(LabOrder.patient),
            joinedload(LabResult.order).joinedload(LabOrder.samples),
            joinedload(LabResult.test_type),
        )
        .filter(
            LabOrder.patient_id == patient.id,
            LabOrder.lab_id == current_user.lab_id,
        )
    )

    if category:
        q = q.filter(TestType.category == category)
    if date_from:
        q = q.filter(LabResult.created_at >= datetime.combine(
            date_from, datetime.min.time(), tzinfo=timezone.utc,
        ))
    if date_to:
        q = q.filter(LabResult.created_at < datetime.combine(
            date_to, datetime.max.time(), tzinfo=timezone.utc,
        ))
    if is_abnormal is True:
        q = q.filter(LabResult.flag.in_(("critical", "H", "L")))
    elif is_abnormal is False:
        q = q.filter(sa.or_(LabResult.flag == "normal", LabResult.flag.is_(None)))

    total = q.count()
    rows = (
        q.order_by(LabResult.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "patient": {
            "id": patient.id,
            "health_id": patient.health_id,
            "full_name": patient.full_name,
        },
        "total": total,
        "skip": skip,
        "limit": limit,
        "results": [_result_dict(r, patient) for r in rows],
    }


@router.get("/citizen/{health_id}/timeline")
def citizen_timeline(
    health_id: str,
    category: Optional[str] = Query(None, max_length=50),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Group values by test_code over time — suitable for line charts.

    Result shape:
        {
          "patient": {...},
          "series": [
            {
              "test_code": "glucose",
              "test_name": "Glucose (Fasting)",
              "unit": "mg/dL",
              "normal_range_low": 70, "normal_range_high": 100,
              "points": [{"date": "...", "value": 95, "flag": "normal"}, ...]
            },
            ...
          ]
        }
    """
    patient = _get_patient_scoped(db, current_user, health_id)

    q = (
        db.query(LabResult)
        .join(LabOrder, LabResult.order_id == LabOrder.id)
        .outerjoin(TestType, LabResult.test_type_id == TestType.id)
        .options(joinedload(LabResult.test_type))
        .filter(
            LabOrder.patient_id == patient.id,
            LabOrder.lab_id == current_user.lab_id,
            LabResult.value.isnot(None),
        )
    )
    if category:
        q = q.filter(TestType.category == category)

    rows = q.order_by(LabResult.created_at.asc()).all()

    grouped: dict[str, dict] = {}
    for r in rows:
        tt = r.test_type
        key = (tt.test_code if tt else r.test_name.lower().replace(" ", "_"))
        if key not in grouped:
            grouped[key] = {
                "test_code": tt.test_code if tt else None,
                "test_name": r.test_name,
                "category": tt.category if tt else None,
                "unit": r.unit or (tt.unit if tt else None),
                "normal_range_low": r.normal_range_low if r.normal_range_low is not None
                    else (tt.normal_range_low if tt else None),
                "normal_range_high": r.normal_range_high if r.normal_range_high is not None
                    else (tt.normal_range_high if tt else None),
                "points": [],
            }
        grouped[key]["points"].append({
            "date": r.created_at.isoformat() if r.created_at else None,
            "value": r.value,
            "flag": r.flag,
        })

    return {
        "patient": {
            "id": patient.id,
            "health_id": patient.health_id,
            "full_name": patient.full_name,
        },
        "series": list(grouped.values()),
    }
