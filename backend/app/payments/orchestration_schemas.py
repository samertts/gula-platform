"""Contracts for provider-agnostic, advisory-only payment orchestration."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app._compat import UTC


class PaymentEntityCreate(BaseModel):
    code: str = Field(min_length=3, max_length=64)
    legal_name: str = Field(min_length=2, max_length=256)
    jurisdiction_code: str = Field(min_length=2, max_length=16)
    entity_type: Literal["DOMESTIC", "INTERNATIONAL", "SANDBOX"]
    ledger_namespace: str = Field(min_length=3, max_length=96)

    @field_validator("code", "jurisdiction_code")
    @classmethod
    def normalize_codes(cls, value: str) -> str:
        return value.upper().replace(" ", "_")


class PaymentRailCreate(BaseModel):
    payment_entity_id: str = Field(min_length=36, max_length=36)
    code: str = Field(min_length=3, max_length=64)
    rail_type: Literal["IRAQ_DOMESTIC", "INTERNATIONAL", "CASH", "SANDBOX"]
    jurisdiction_code: str = Field(min_length=2, max_length=16)
    supported_currencies: list[str] = Field(min_length=1, max_length=32)

    @field_validator("code", "jurisdiction_code")
    @classmethod
    def normalize_codes(cls, value: str) -> str:
        return value.upper().replace(" ", "_")

    @field_validator("supported_currencies")
    @classmethod
    def normalize_currencies(cls, values: list[str]) -> list[str]:
        normalized = sorted(set(value.upper() for value in values))
        if any(len(value) != 3 or not value.isalpha() for value in normalized):
            raise ValueError("Supported currencies must be ISO-style three-letter codes")
        return normalized


class PaymentProviderCreate(BaseModel):
    code: str = Field(min_length=3, max_length=64)
    display_name: str = Field(min_length=2, max_length=128)
    provider_type: Literal["bank", "psp", "wallet", "qr", "card", "cash", "aggregator"]
    payment_entity_id: str = Field(min_length=36, max_length=36)
    rail_code: str = Field(min_length=3, max_length=64)
    jurisdiction_code: str = Field(min_length=2, max_length=16)
    supports_refund: bool = False
    supports_reconciliation: bool = True

    @field_validator("code", "rail_code", "jurisdiction_code")
    @classmethod
    def normalize_codes(cls, value: str) -> str:
        return value.upper().replace(" ", "_")


class RoutingRuleCreate(BaseModel):
    payment_entity_id: str = Field(min_length=36, max_length=36)
    rail_code: str = Field(min_length=3, max_length=64)
    provider_code: str = Field(min_length=3, max_length=64)
    rule_version: str = Field(min_length=3, max_length=96)
    priority: int = Field(default=100, ge=0, le=10_000)
    minimum_amount: Decimal | None = Field(default=None, ge=0, max_digits=24, decimal_places=6)
    maximum_amount: Decimal | None = Field(default=None, ge=0, max_digits=24, decimal_places=6)
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    required_risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] | None = None
    service_reference: str | None = Field(default=None, max_length=128)
    estimated_fee_bps: int = Field(default=0, ge=0, le=10_000)
    success_rate_bps: int = Field(default=0, ge=0, le=10_000)
    latency_ms: int | None = Field(default=None, ge=0, le=60_000)
    effective_from: datetime
    effective_until: datetime | None = None

    @field_validator("rail_code", "provider_code", "currency_code")
    @classmethod
    def normalize_optional_codes(cls, value: str | None) -> str | None:
        return value.upper().replace(" ", "_") if value is not None else None

    @field_validator("effective_from", "effective_until")
    @classmethod
    def validate_times(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("Routing rule timestamps must include a timezone")
        return value.astimezone(UTC) if value is not None else None


class RoutingDecisionCreate(BaseModel):
    payment_entity_id: str = Field(min_length=36, max_length=36)
    correlation_id: str = Field(min_length=8, max_length=128)
    service_reference: str | None = Field(default=None, max_length=128)


class RoutingDecisionResponse(BaseModel):
    id: str
    payment_intent_id: str
    payment_entity_id: str
    rail_code: str | None
    provider_code: str | None
    decision: str
    score: Decimal | None
    reason_codes: list[str]
    evaluated_candidates: list[dict]
    rule_version: str | None
    correlation_id: str
