"""Doctor-portal API (CMD-017).

Routes:
    POST /doctor/order-tests                           Physician test order
    GET  /doctor/patient/{health_id}/overview          Patient snapshot
    GET  /doctor/patient/{health_id}/timeline/{code}   Value-over-time series
    POST /doctor/refer                                 Refer to another doctor

Authorization (pending the central RBAC layer):
    * The trusted context's role must be ``DOCTOR`` (case-insensitive).
    * The trusted context's actor id identifies the physician and is persisted
      on the order / referral.

Route ordering matters: the ``/patient/{health_id}/timeline/{test_code}``
static prefix is declared before the looser overview route, and both are
declared before any free ``/{something}`` dynamic route would be, so FastAPI
does not accidentally match ``overview`` or ``timeline`` as a path variable.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.trusted_context import current_context
from ...models.citizen import Citizen
from ...models.lab import Lab
from ...models.test_order import TestOrder, TestOrderStatus
from ...models.test_result import TestResult
from ...schemas.doctor import (
    DoctorTimelineResponse,
    DuplicateTestNotice,
    OrderTestsRequest,
    OrderTestsResponse,
    OverviewAlert,
    OverviewCitizen,
    OverviewResultRow,
    PatientOverviewResponse,
    ReferralRequest,
    ReferralResponse,
    TimelineDoctorPoint,
)
from ...services.audit import log_action
from ...services.test_suggestions import suggest_additional_tests

router = APIRouter(prefix="/doctor", tags=["doctor"])


# ─── Request context helpers ────────────────────────────────────────────────

_DOCTOR_ROLE = "DOCTOR"


def _actor_id(request: Request) -> str | None:
    # NR-127. This read the actor off the wire. Identity now comes from
    # the server-established context; see app/core/trusted_context.py.
    return current_context(request).actor_id


def _client_ip(request: Request) -> str | None:
    if request.client:
        return request.client.host
    return None


def _require_doctor(request: Request) -> str:
    """Enforce the DOCTOR role + presence of an actor id.

    Returns the doctor id so endpoint code does not have to re-read headers.
    Raises 403 on missing / wrong role, 401 on missing actor id, matching
    the minimal auth contract used elsewhere in the service.
    """
    # NR-127. This read the actor off the wire. Identity now comes from
    # the server-established context; see app/core/trusted_context.py.
    role = (current_context(request).role or "").strip().upper()
    if role != _DOCTOR_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="DOCTOR role required",
        )
    doctor_id = _actor_id(request)
    if not doctor_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="a trusted caller identity is required",
        )
    return doctor_id


def _require_citizen(db: Session, health_id: str) -> Citizen:
    row = db.query(Citizen).filter(Citizen.health_id == health_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="citizen not found")
    return row


# ─── POST /doctor/order-tests ───────────────────────────────────────────────

@router.post(
    "/order-tests",
    response_model=OrderTestsResponse,
    status_code=status.HTTP_201_CREATED,
)
def order_tests(
    payload: OrderTestsRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> OrderTestsResponse:
    doctor_id = _require_doctor(request)
    citizen = _require_citizen(db, payload.citizen_health_id)

    # 1. Smart suggestions keyed by clinical indication.
    additions, rationales = suggest_additional_tests(
        payload.clinical_indication, payload.tests
    )
    combined = list(payload.tests) + additions

    # 2. Dedup against the last 7 days of results for this citizen.
    cutoff = datetime.now(UTC) - timedelta(days=7)
    recent_rows = (
        db.query(TestResult)
          .filter(
              TestResult.citizen_id == citizen.id,
              TestResult.test_code.in_(combined),
              TestResult.performed_at >= cutoff,
          )
          .order_by(desc(TestResult.performed_at))
          .all()
    )
    latest_by_code: dict[str, TestResult] = {}
    for r in recent_rows:
        latest_by_code.setdefault(r.test_code, r)

    duplicates: list[DuplicateTestNotice] = []
    kept: list[str] = []
    kept_additions: list[str] = []
    for code in combined:
        prev = latest_by_code.get(code)
        if prev is not None:
            duplicates.append(DuplicateTestNotice(
                test_code=code,
                last_performed_at=prev.performed_at,
                last_result_id=prev.id,
            ))
            continue
        kept.append(code)
        if code in additions:
            kept_additions.append(code)

    if not kept:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "all_tests_duplicate_within_7_days",
                "duplicates": [d.model_dump(mode="json") for d in duplicates],
            },
        )

    # 3. Resolve the preferred lab (must be active if supplied).
    lab_id: UUID | None = None
    if payload.preferred_lab_id is not None:
        lab = db.query(Lab).filter(Lab.id == payload.preferred_lab_id).first()
        if lab is None:
            raise HTTPException(status_code=404, detail="preferred lab not found")
        if not lab.is_active:
            raise HTTPException(status_code=400, detail="preferred lab is not active")
        lab_id = lab.id

    # 4. Persist the order. Dispatched if bound to a lab, else pending.
    order = TestOrder(
        citizen_id=citizen.id,
        doctor_id=doctor_id,
        lab_id=lab_id,
        tests=kept,
        suggested_additions=kept_additions or None,
        clinical_indication=payload.clinical_indication,
        urgent=payload.urgent,
        status=TestOrderStatus.dispatched if lab_id else TestOrderStatus.pending,
    )
    db.add(order)
    db.flush()

    log_action(
        db,
        action="doctor.order_tests",
        target_type="test_order",
        target_id=str(order.id),
        actor_id=doctor_id,
        ip_address=_client_ip(request),
        metadata={
            "health_id": citizen.health_id,
            "lab_id": str(lab_id) if lab_id else None,
            "tests": kept,
            "suggested_additions": kept_additions,
            "suggestion_rationales": rationales,
            "duplicates_skipped": [d.test_code for d in duplicates],
            "urgent": payload.urgent,
        },
    )
    db.commit()
    db.refresh(order)

    return OrderTestsResponse(
        id=order.id,
        citizen_id=order.citizen_id,
        doctor_id=order.doctor_id,
        lab_id=order.lab_id,
        tests=list(order.tests or []),
        suggested_additions=list(order.suggested_additions or []),
        duplicates_skipped=duplicates,
        clinical_indication=order.clinical_indication,
        urgent=order.urgent,
        status=order.status,
        created_at=order.created_at,
    )


# ─── GET /doctor/patient/{health_id}/timeline/{test_code} ───────────────────
#
# Declared before the broader ``/patient/{health_id}/overview`` handler so
# FastAPI's longest-match routing picks this up first when both static
# prefixes are present.

@router.get(
    "/patient/{health_id}/timeline/{test_code}",
    response_model=DoctorTimelineResponse,
)
def patient_timeline(
    health_id: str,
    test_code: str,
    request: Request,
    db: Session = Depends(get_db),
) -> DoctorTimelineResponse:
    doctor_id = _require_doctor(request)
    citizen = _require_citizen(db, health_id)

    code = (test_code or "").strip().upper()
    rows = (
        db.query(TestResult)
          .filter(
              TestResult.citizen_id == citizen.id,
              TestResult.test_code == code,
          )
          .order_by(TestResult.performed_at.asc())
          .all()
    )

    log_action(
        db,
        action="doctor.patient_timeline",
        target_type="citizen",
        target_id=citizen.health_id,
        actor_id=doctor_id,
        ip_address=_client_ip(request),
        metadata={"test_code": code, "points": len(rows)},
    )
    db.commit()

    first = rows[0] if rows else None
    return DoctorTimelineResponse(
        health_id=citizen.health_id,
        test_code=code,
        test_name=first.test_name if first else None,
        unit=first.unit if first else None,
        points=[
            TimelineDoctorPoint(
                performed_at=r.performed_at,
                value_numeric=r.value_numeric,
                value_text=r.value_text,
                unit=r.unit,
                is_abnormal=r.is_abnormal,
                is_critical=r.is_critical,
                direction=r.direction,
                reference_min=r.reference_min,
                reference_max=r.reference_max,
            )
            for r in rows
        ],
    )


# ─── GET /doctor/patient/{health_id}/overview ───────────────────────────────

_RECENT_RESULTS_LIMIT = 10
_HEALTH_SCORE_WINDOW_DAYS = 180
_CRITICAL_PENALTY = 12
_ABNORMAL_PENALTY = 4
_CHRONIC_PENALTY = 3


def _compute_health_score(
    citizen: Citizen, recent_window: list[TestResult]
) -> int:
    """Heuristic 0–100 score for patient dashboard ribboning.

    Starts at 100, subtracts fixed penalties per critical/abnormal result in
    the 6-month window and per declared chronic disease, and clamps into
    [0, 100]. Intentionally coarse: this is a glanceable indicator, not a
    clinical grade.
    """
    score = 100
    for r in recent_window:
        if r.is_critical:
            score -= _CRITICAL_PENALTY
        elif r.is_abnormal:
            score -= _ABNORMAL_PENALTY
    score -= _CHRONIC_PENALTY * len(citizen.chronic_diseases or [])
    return max(0, min(100, score))


@router.get(
    "/patient/{health_id}/overview",
    response_model=PatientOverviewResponse,
)
def patient_overview(
    health_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> PatientOverviewResponse:
    doctor_id = _require_doctor(request)
    citizen = _require_citizen(db, health_id)

    recent = (
        db.query(TestResult)
          .filter(TestResult.citizen_id == citizen.id)
          .order_by(desc(TestResult.performed_at))
          .limit(_RECENT_RESULTS_LIMIT)
          .all()
    )

    window_cutoff = datetime.now(UTC) - timedelta(
        days=_HEALTH_SCORE_WINDOW_DAYS
    )
    window_rows = (
        db.query(TestResult)
          .filter(and_(
              TestResult.citizen_id == citizen.id,
              TestResult.performed_at >= window_cutoff,
          ))
          .all()
    )

    alerts: list[OverviewAlert] = []
    for r in recent:
        if r.is_critical:
            alerts.append(OverviewAlert(
                code="critical_result",
                message=(
                    r.interpretation_ar
                    or f"قيمة حرجة للتحليل {r.test_code}: {r.value_numeric} {r.unit or ''}".strip()
                ),
                severity="critical",
            ))
        elif r.is_abnormal:
            alerts.append(OverviewAlert(
                code="abnormal_result",
                message=(
                    r.interpretation_ar
                    or f"قيمة غير طبيعية للتحليل {r.test_code}."
                ),
                severity="warning",
            ))

    score = _compute_health_score(citizen, window_rows)

    log_action(
        db,
        action="doctor.patient_overview",
        target_type="citizen",
        target_id=citizen.health_id,
        actor_id=doctor_id,
        ip_address=_client_ip(request),
        metadata={"results_returned": len(recent), "health_score": score},
    )
    db.commit()

    return PatientOverviewResponse(
        citizen=OverviewCitizen(
            health_id=citizen.health_id,
            full_name=citizen.full_name,
            gender=citizen.gender,
            birth_date=(
                datetime.combine(citizen.birth_date, datetime.min.time())
                if citizen.birth_date else None
            ),
            blood_type=citizen.blood_type,
            province=citizen.province,
            chronic_diseases=list(citizen.chronic_diseases or []),
            allergies=list(citizen.allergies or []),
        ),
        recent_results=[
            OverviewResultRow(
                id=r.id,
                test_code=r.test_code,
                test_name=r.test_name,
                value_numeric=r.value_numeric,
                value_text=r.value_text,
                unit=r.unit,
                is_abnormal=r.is_abnormal,
                is_critical=r.is_critical,
                direction=r.direction,
                performed_at=r.performed_at,
            )
            for r in recent
        ],
        medications=[],  # NHOP does not yet track prescriptions
        active_alerts=alerts,
        health_score=score,
    )


# ─── POST /doctor/refer ─────────────────────────────────────────────────────

@router.post(
    "/refer",
    response_model=ReferralResponse,
    status_code=status.HTTP_201_CREATED,
)
def refer_patient(
    payload: ReferralRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> ReferralResponse:
    doctor_id = _require_doctor(request)
    citizen = _require_citizen(db, payload.citizen_health_id)

    if payload.to_doctor_id == doctor_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="cannot refer a patient to yourself",
        )

    recent: list[TestResult] = []
    if payload.include_recent_results > 0:
        recent = (
            db.query(TestResult)
              .filter(TestResult.citizen_id == citizen.id)
              .order_by(desc(TestResult.performed_at))
              .limit(payload.include_recent_results)
              .all()
        )

    summary = {
        "citizen": {
            "health_id": citizen.health_id,
            "full_name": citizen.full_name,
            "gender": citizen.gender,
            "birth_date": (
                citizen.birth_date.isoformat() if citizen.birth_date else None
            ),
            "blood_type": citizen.blood_type,
            "chronic_diseases": list(citizen.chronic_diseases or []),
            "allergies": list(citizen.allergies or []),
        },
        "recent_results": [
            {
                "id": str(r.id),
                "test_code": r.test_code,
                "test_name": r.test_name,
                "value_numeric": r.value_numeric,
                "value_text": r.value_text,
                "unit": r.unit,
                "is_abnormal": r.is_abnormal,
                "is_critical": r.is_critical,
                "performed_at": r.performed_at.isoformat(),
            }
            for r in recent
        ],
    }

    referral_id = uuid4()
    created_at = datetime.now(UTC)

    # Referrals do not have their own table yet; durability comes via the
    # audit log, matching how critical alerts are persisted elsewhere.
    log_action(
        db,
        action="doctor.refer",
        target_type="citizen",
        target_id=citizen.health_id,
        actor_id=doctor_id,
        ip_address=_client_ip(request),
        metadata={
            "referral_id": str(referral_id),
            "to_doctor_id": payload.to_doctor_id,
            "reason": payload.reason,
            "recent_results_count": len(recent),
            "created_at": created_at.isoformat(),
        },
    )
    db.commit()

    return ReferralResponse(
        id=referral_id,
        citizen_health_id=citizen.health_id,
        from_doctor_id=doctor_id,
        to_doctor_id=payload.to_doctor_id,
        reason=payload.reason,
        summary=summary,
        created_at=created_at,
    )
