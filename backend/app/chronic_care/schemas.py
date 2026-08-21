from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .care_plans import CarePlanState


class BaselineRequest(BaseModel):
    metric_code: str = Field(..., min_length=1)
    values: list[float] = Field(..., min_length=3)
    min_samples: int = 7
    mad_multiplier: float = 3.5


class BaselineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    metric_code: str
    sample_count: int
    median: float | None
    mad: float | None
    lower_bound: float | None
    upper_bound: float | None
    confidence: float
    status: str
    reason: str
    generated_at: datetime


class EvaluationRequest(BaseModel):
    baseline: BaselineResponse
    value: float
    alert_confidence_threshold: float = 0.75


class EvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    metric_code: str
    value: float
    is_anomaly: bool
    severity: str
    deviation_score: float | None
    confidence: float
    explanation: str
    requires_clinician_review: bool


class AlertAcknowledgeRequest(BaseModel):
    actor_id: int = Field(..., gt=0)


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    alert_id: str
    patient_id: int
    metric_code: str
    severity: str
    status: str
    escalation_level: str
    title: str
    explanation: str
    created_at: datetime
    dedupe_key: str
    requires_clinician_review: bool


class CarePlanGoal(BaseModel):
    description: str
    target_value: float | None = None
    unit: str | None = None
    deadline: datetime | None = None


class CarePlanCreate(BaseModel):
    patient_id: int = Field(..., gt=0)
    condition_code: str = Field(..., min_length=1)
    goals: list[CarePlanGoal]


class CarePlanTransitionRequest(BaseModel):
    target: CarePlanState
    actor_id: int = Field(..., gt=0)
    clinician_approved: bool = False


class CarePlanUpdateGoalsRequest(BaseModel):
    goals: list[CarePlanGoal]
    expected_version: int = Field(..., gt=0)


class CarePlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    patient_id: int
    condition_code: str
    goals: list[Any]
    state: CarePlanState
    version: int
    updated_at: datetime
    approved_by: int | None
