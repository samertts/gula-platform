from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ..models.lab_user import LabUser
from ..security.dependencies import require_institutional_permission
from .baselines import BaselineSnapshot, build_baseline, evaluate_against_baseline
from .schemas import (
    BaselineRequest,
    BaselineResponse,
    CarePlanCreate,
    CarePlanResponse,
    CarePlanTransitionRequest,
    CarePlanUpdateGoalsRequest,
    EvaluationRequest,
    EvaluationResponse,
)

router = APIRouter(prefix="/chronic-care", tags=["chronic-care"])


def _read_actor() -> LabUser:
    return Depends(require_institutional_permission("lab:read"))  # type: ignore[return-value]


def _write_actor() -> LabUser:
    return Depends(require_institutional_permission("lab:manage"))  # type: ignore[return-value]


def _not_ready(operation: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=(
            f"{operation} is not available until persistent, tenant-scoped storage "
            "and immutable audit logging are enabled"
        ),
    )


@router.post("/baseline", response_model=BaselineResponse)
def create_baseline(
    request: BaselineRequest,
    _: LabUser = _read_actor(),
) -> BaselineResponse:
    """Build a patient-specific baseline for advisory review only."""
    try:
        snapshot = build_baseline(
            request.metric_code,
            request.values,
            min_samples=request.min_samples,
            mad_multiplier=request.mad_multiplier,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return BaselineResponse.model_validate(snapshot)


@router.post("/evaluate", response_model=EvaluationResponse)
def evaluate_baseline(
    request: EvaluationRequest,
    _: LabUser = _read_actor(),
) -> EvaluationResponse:
    """Evaluate one value against a supplied baseline without treatment automation."""
    baseline = BaselineSnapshot(**request.baseline.model_dump())
    try:
        evaluation = evaluate_against_baseline(
            baseline,
            request.value,
            alert_confidence_threshold=request.alert_confidence_threshold,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return EvaluationResponse.model_validate(evaluation)


@router.post("/care-plans", response_model=CarePlanResponse)
def create_care_plan(
    _: CarePlanCreate,
    __: LabUser = _write_actor(),
) -> CarePlanResponse:
    _not_ready("Care-plan creation")


@router.post("/care-plans/{care_plan_id}/transition", response_model=CarePlanResponse)
def transition_care_plan(
    care_plan_id: int,
    _: CarePlanTransitionRequest,
    __: LabUser = _write_actor(),
) -> CarePlanResponse:
    if care_plan_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="care_plan_id must be positive"
        )
    _not_ready("Care-plan transitions")


@router.patch("/care-plans/{care_plan_id}/goals", response_model=CarePlanResponse)
def update_care_plan_goals(
    care_plan_id: int,
    _: CarePlanUpdateGoalsRequest,
    __: LabUser = _write_actor(),
) -> CarePlanResponse:
    if care_plan_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="care_plan_id must be positive"
        )
    _not_ready("Care-plan goal updates")


@router.get("/alerts")
def list_alerts(_: LabUser = _read_actor()):
    _not_ready("Persistent chronic-care alerts")


@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str, _: LabUser = _write_actor()):
    if not alert_id.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="alert_id is required")
    _not_ready("Alert acknowledgement")
