"""Test-results API (CMD-009).

Routes:
    POST /test-results/                              Create a new result
    POST /test-results/validate                      Pre-save validation only
    GET  /test-results/{result_id}                   Read one result
    PUT  /test-results/{result_id}/verify            Move to 'verified' status
    GET  /test-results/citizen/{health_id}           List citizen results
    GET  /test-results/citizen/{health_id}/timeline  Grouped time-series

Route order matters: static segments (``/validate``) are declared before
``/{result_id}`` so FastAPI does not treat "validate" as an id.
"""
from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import and_, asc, desc
from sqlalchemy.orm import Session

from backend.app._compat import UTC

from ...core.database import get_db
from ...models.citizen import Citizen
from ...models.lab import Lab
from ...models.notification import NotificationPriority, NotificationType
from ...models.test_result import (
    ResultCategory,
    ResultStatus,
    TestResult,
    generate_sample_barcode,
)
from ...schemas.test_result import (
    CitizenTimelineResponse,
    TestResultCreate,
    TestResultListResponse,
    TestResultRead,
    TestResultValidateRequest,
    TestResultValidateResponse,
    TestResultVerifyRequest,
    TimelinePoint,
    TimelineSeries,
    ValidationWarning,
)
from ...services.audit import log_action
from ...services.notification import send_notification
from ...services.smart_analysis import (
    compare_with_history,
    validate_result,
)

router = APIRouter(prefix="/test-results", tags=["test-results"])


# ─── Helpers ────────────────────────────────────────────────────────────────

def _actor_id(request: Request) -> str | None:
    return request.headers.get("X-Actor-Id")


def _client_ip(request: Request) -> str | None:
    if request.client:
        return request.client.host
    return None


def _require_citizen(db: Session, health_id: str) -> Citizen:
    citizen = db.query(Citizen).filter(Citizen.health_id == health_id).first()
    if citizen is None:
        raise HTTPException(status_code=404, detail="citizen not found")
    return citizen


def _require_result(db: Session, result_id: UUID) -> TestResult:
    row = db.query(TestResult).filter(TestResult.id == result_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="test result not found")
    return row


def _to_warning_models(ws) -> list[ValidationWarning]:
    return [ValidationWarning(**w.__dict__) for w in ws]


def _recompute_lab_metrics(db: Session, lab: Lab, new_tat_minutes: int) -> None:
    """Increment total_tests and roll the running-average TAT.

    Running mean update: new_avg = old_avg + (x - old_avg) / n
    """
    previous_total = lab.total_tests or 0
    new_total = previous_total + 1
    previous_avg = lab.avg_tat_minutes or 0
    new_avg = previous_avg + (new_tat_minutes - previous_avg) / new_total
    lab.total_tests = new_total
    lab.avg_tat_minutes = round(new_avg)


def _fire_critical_alert(
    db: Session, row: TestResult, citizen: Citizen, request: Request
) -> None:
    """Record a critical-result alert in the audit log.

    A real alerting pipeline (SMS / ministry notification) plugs in here; for
    now we use the audit log as the durable signal so nothing is lost.
    """
    log_action(
        db,
        action="test_result.critical_alert",
        target_type="test_result",
        target_id=str(row.id),
        actor_id=_actor_id(request),
        ip_address=_client_ip(request),
        metadata={
            "health_id": citizen.health_id,
            "test_code": row.test_code,
            "value_numeric": row.value_numeric,
            "unit": row.unit,
            "direction": row.direction,
            "lab_id": str(row.lab_id),
        },
    )

    title = f"نتيجة حرجة: {row.test_name}"
    body_parts = [f"تحليل {row.test_code}"]
    if row.value_numeric is not None:
        unit = row.unit or ""
        body_parts.append(f"القيمة: {row.value_numeric} {unit}".strip())
    if row.direction:
        body_parts.append(f"الاتجاه: {row.direction}")
    send_notification(
        db,
        recipient_id=citizen.health_id,
        recipient_role="citizen",
        type=NotificationType.critical_result,
        title=title,
        body=" | ".join(body_parts),
        priority=NotificationPriority.urgent,
        related_type="test_result",
        related_id=str(row.id),
    )


# ─── POST /test-results/validate ────────────────────────────────────────────

@router.post(
    "/validate",
    response_model=TestResultValidateResponse,
    status_code=status.HTTP_200_OK,
)
def validate_payload(payload: TestResultValidateRequest) -> TestResultValidateResponse:
    vr = validate_result(
        test_code=payload.test_code,
        value=payload.value_numeric,
        unit=payload.unit,
        reference_min=payload.reference_min,
        reference_max=payload.reference_max,
    )
    return TestResultValidateResponse(
        is_valid=vr.is_valid,
        is_critical=vr.is_critical,
        is_abnormal=vr.is_abnormal,
        direction=vr.direction,
        interpretation_ar=vr.interpretation_ar,
        warnings=_to_warning_models(vr.warnings),
    )


# ─── POST /test-results/ ────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=TestResultRead,
    status_code=status.HTTP_201_CREATED,
)
def create_test_result(
    payload: TestResultCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> TestResultRead:
    citizen = _require_citizen(db, payload.health_id)

    lab = db.query(Lab).filter(Lab.id == payload.lab_id).first()
    if lab is None:
        raise HTTPException(status_code=404, detail="lab not found")
    if not lab.is_active:
        raise HTTPException(status_code=400, detail="lab is not active")

    vr = validate_result(
        test_code=payload.test_code,
        value=payload.value_numeric,
        unit=payload.unit,
        reference_min=payload.reference_min,
        reference_max=payload.reference_max,
    )
    if not vr.is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "implausible_value",
                "warnings": [w.__dict__ for w in vr.warnings],
            },
        )

    # Trend / delta warnings vs. history.
    cmp_ = compare_with_history(
        citizen_id=citizen.id,
        test_code=payload.test_code,
        new_value=payload.value_numeric,
        db=db,
    )
    warnings_payload = [w.__dict__ for w in vr.warnings] + \
                       [w.__dict__ for w in cmp_.warnings]

    performed_at = payload.performed_at or datetime.now(UTC)
    received_at = datetime.now(UTC)
    tat_minutes = max(
        0, int((received_at - performed_at).total_seconds() // 60)
    )

    row = TestResult(
        citizen_id=citizen.id,
        lab_id=lab.id,
        sample_barcode=generate_sample_barcode(),
        test_code=payload.test_code,
        test_name=payload.test_name,
        category=payload.category or ResultCategory.other,
        value_numeric=payload.value_numeric,
        value_text=payload.value_text,
        unit=payload.unit,
        reference_min=payload.reference_min,
        reference_max=payload.reference_max,
        is_abnormal=vr.is_abnormal,
        is_critical=vr.is_critical,
        direction=vr.direction,
        interpretation_ar=vr.interpretation_ar,
        warnings=warnings_payload or None,
        status=ResultStatus.final,
        performed_at=performed_at,
        received_at=received_at,
        reported_at=received_at,
    )
    db.add(row)
    db.flush()

    _recompute_lab_metrics(db, lab, tat_minutes)

    log_action(
        db,
        action="test_result.create",
        target_type="test_result",
        target_id=str(row.id),
        actor_id=_actor_id(request),
        ip_address=_client_ip(request),
        metadata={
            "health_id": citizen.health_id,
            "lab_id": str(lab.id),
            "test_code": row.test_code,
            "is_abnormal": row.is_abnormal,
            "is_critical": row.is_critical,
            "sample_barcode": row.sample_barcode,
        },
    )

    if row.is_critical:
        _fire_critical_alert(db, row, citizen, request)

    db.commit()
    db.refresh(row)
    return TestResultRead.model_validate(row)


# ─── GET /test-results/citizen/{health_id}/timeline ─────────────────────────

@router.get(
    "/citizen/{health_id}/timeline",
    response_model=CitizenTimelineResponse,
)
def citizen_timeline(
    health_id: str,
    request: Request,
    test_code: str | None = Query(default=None, max_length=60),
    db: Session = Depends(get_db),
) -> CitizenTimelineResponse:
    citizen = _require_citizen(db, health_id)

    query = (
        db.query(TestResult)
          .filter(
              TestResult.citizen_id == citizen.id,
              TestResult.value_numeric.is_not(None),
          )
          .order_by(asc(TestResult.test_code), asc(TestResult.performed_at))
    )
    if test_code:
        query = query.filter(TestResult.test_code == test_code.strip().upper())

    rows = query.all()

    by_code: dict[str, TimelineSeries] = {}
    for r in rows:
        series = by_code.get(r.test_code)
        if series is None:
            series = TimelineSeries(
                test_code=r.test_code,
                test_name=r.test_name,
                unit=r.unit,
                points=[],
            )
            by_code[r.test_code] = series
        series.points.append(TimelinePoint(
            performed_at=r.performed_at,
            value_numeric=r.value_numeric,
            value_text=r.value_text,
            unit=r.unit,
            is_abnormal=r.is_abnormal,
            is_critical=r.is_critical,
            reference_min=r.reference_min,
            reference_max=r.reference_max,
        ))

    log_action(
        db,
        action="test_result.timeline",
        target_type="citizen",
        target_id=citizen.health_id,
        actor_id=_actor_id(request),
        ip_address=_client_ip(request),
        metadata={"series": len(by_code), "test_code": test_code},
    )
    db.commit()

    return CitizenTimelineResponse(
        health_id=citizen.health_id,
        series=list(by_code.values()),
    )


# ─── GET /test-results/citizen/{health_id} ──────────────────────────────────

@router.get(
    "/citizen/{health_id}",
    response_model=TestResultListResponse,
)
def list_citizen_results(
    health_id: str,
    request: Request,
    category: ResultCategory | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    is_abnormal: bool | None = Query(default=None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> TestResultListResponse:
    citizen = _require_citizen(db, health_id)

    filters = [TestResult.citizen_id == citizen.id]
    if category is not None:
        filters.append(TestResult.category == category)
    if is_abnormal is not None:
        filters.append(TestResult.is_abnormal == is_abnormal)
    if date_from is not None:
        filters.append(TestResult.performed_at >= datetime.combine(
            date_from, datetime.min.time(), tzinfo=UTC
        ))
    if date_to is not None:
        filters.append(TestResult.performed_at <= datetime.combine(
            date_to, datetime.max.time(), tzinfo=UTC
        ))

    base_query = db.query(TestResult).filter(and_(*filters))
    total = base_query.count()
    rows = (base_query.order_by(desc(TestResult.performed_at))
                       .offset(skip).limit(limit).all())

    log_action(
        db,
        action="test_result.list",
        target_type="citizen",
        target_id=citizen.health_id,
        actor_id=_actor_id(request),
        ip_address=_client_ip(request),
        metadata={
            "total": total, "skip": skip, "limit": limit,
            "category": category.value if category else None,
            "is_abnormal": is_abnormal,
        },
    )
    db.commit()

    return TestResultListResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=[TestResultRead.model_validate(r) for r in rows],
    )


# ─── GET /test-results/{result_id} ──────────────────────────────────────────

@router.get("/{result_id}", response_model=TestResultRead)
def get_test_result(
    result_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
) -> TestResultRead:
    row = _require_result(db, result_id)

    log_action(
        db,
        action="test_result.read",
        target_type="test_result",
        target_id=str(row.id),
        actor_id=_actor_id(request),
        ip_address=_client_ip(request),
    )
    db.commit()
    return TestResultRead.model_validate(row)


# ─── PUT /test-results/{result_id}/verify ───────────────────────────────────

@router.put("/{result_id}/verify", response_model=TestResultRead)
def verify_test_result(
    result_id: UUID,
    payload: TestResultVerifyRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TestResultRead:
    row = _require_result(db, result_id)

    if row.status == ResultStatus.verified:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="test result already verified",
        )
    if row.status == ResultStatus.rejected:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="test result is rejected; cannot verify",
        )

    row.status = ResultStatus.verified
    row.verified_by = payload.verified_by
    row.verified_at = datetime.now(UTC)

    log_action(
        db,
        action="test_result.verify",
        target_type="test_result",
        target_id=str(row.id),
        actor_id=_actor_id(request),
        ip_address=_client_ip(request),
        metadata={"verified_by": payload.verified_by},
    )
    db.commit()
    db.refresh(row)
    return TestResultRead.model_validate(row)
