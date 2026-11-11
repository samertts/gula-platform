"""Pydantic contracts for institutional subscription billing and entitlements."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app._compat import UTC


class SubscriptionPlanCreate(BaseModel):
    plan_code: str = Field(min_length=3, max_length=64)
    version: str = Field(min_length=1, max_length=64)
    display_name: str = Field(min_length=2, max_length=128)
    currency: str = Field(default="IQD", min_length=3, max_length=3)
    monthly_price: Decimal = Field(ge=0, max_digits=24, decimal_places=6)
    yearly_price: Decimal = Field(ge=0, max_digits=24, decimal_places=6)
    grace_period_days: int = Field(default=0, ge=0, le=365)
    usage_limits: dict[str, int] = Field(default_factory=dict)
    feature_entitlements: dict[str, bool] = Field(default_factory=dict)

    @field_validator("plan_code", "currency")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.upper().replace(" ", "_")

    @field_validator("usage_limits")
    @classmethod
    def validate_limits(cls, values: dict[str, int]) -> dict[str, int]:
        if any(not key or quantity < 0 for key, quantity in values.items()):
            raise ValueError("Usage limits must have non-empty metric keys and non-negative quantities")
        return {key.upper(): quantity for key, quantity in values.items()}


class PlatformSubscriptionCreate(BaseModel):
    lab_id: int = Field(gt=0)
    plan_id: str = Field(min_length=36, max_length=36)
    billing_cycle: Literal["MONTHLY", "YEARLY"]
    starts_at: datetime
    auto_renew: bool = False

    @field_validator("starts_at")
    @classmethod
    def ensure_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Subscription start time must include a timezone")
        return value.astimezone(UTC)


class SubscriptionUsageRecord(BaseModel):
    metric_code: str = Field(min_length=1, max_length=64)
    quantity: int = Field(gt=0, le=1_000_000)
    idempotency_key: str = Field(min_length=8, max_length=128)
    reference_type: str | None = Field(default=None, max_length=64)
    reference_id: str | None = Field(default=None, max_length=128)
    hard_limit: bool = True

    @field_validator("metric_code")
    @classmethod
    def normalize_metric(cls, value: str) -> str:
        return value.upper().replace(" ", "_")


class SubscriptionCycleGenerate(BaseModel):
    as_of: datetime

    @field_validator("as_of")
    @classmethod
    def ensure_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Cycle generation time must include a timezone")
        return value.astimezone(UTC)


class UsageDecisionResponse(BaseModel):
    subscription_id: str
    metric_code: str
    period_start: datetime
    used_quantity: int
    limit_quantity: int
    decision: Literal["ALLOWED", "WARNING", "REJECTED"]
    idempotent_replay: bool


class SubscriptionCycleResponse(BaseModel):
    id: str
    subscription_id: str
    cycle_key: str
    period_start: datetime
    period_end: datetime
    due_at: datetime
    amount: Decimal
    currency: str
    status: str
