"""API contracts for the non-production currency and FX quote engine."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app._compat import UTC


class CurrencyDefinitionCreate(BaseModel):
    code: str = Field(min_length=3, max_length=3)
    display_name: str = Field(min_length=1, max_length=96)
    minor_unit: int = Field(ge=0, le=6)
    rounding_mode: Literal["HALF_UP", "HALF_EVEN", "DOWN", "UP"] = "HALF_UP"
    fx_quote_enabled: bool = False

    @field_validator("code")
    @classmethod
    def code_must_be_iso_uppercase(cls, value: str) -> str:
        normalized = value.upper()
        if not normalized.isalpha():
            raise ValueError("Currency code must contain three alphabetic ISO characters")
        return normalized


class FxRateSnapshotCreate(BaseModel):
    source_code: Literal["CBI_PUBLISHED_RATE", "SANDBOX", "MANUAL_EXCEPTION"]
    source_reference: str = Field(min_length=5, max_length=512)
    source_digest: str | None = Field(default=None, max_length=128)
    rate_version: str = Field(min_length=1, max_length=96)
    base_currency: str = Field(min_length=3, max_length=3)
    quote_currency: str = Field(min_length=3, max_length=3)
    reference_rate: Decimal = Field(gt=0, max_digits=24, decimal_places=10)
    published_at: datetime

    @field_validator("base_currency", "quote_currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()

    @field_validator("published_at")
    @classmethod
    def published_at_must_be_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("published_at must include a timezone")
        return value.astimezone(UTC)


class FxFeePolicyCreate(BaseModel):
    policy_version: str = Field(min_length=1, max_length=96)
    institution_id: int | None = Field(default=None, gt=0)
    base_currency: str | None = Field(default=None, min_length=3, max_length=3)
    quote_currency: str | None = Field(default=None, min_length=3, max_length=3)
    service_reference: str | None = Field(default=None, max_length=128)
    provider_code: str | None = Field(default=None, max_length=64)
    fee_bps: int = Field(default=200, ge=0, le=10_000)
    minimum_fee: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=18, decimal_places=2)
    maximum_fee: Decimal | None = Field(default=None, ge=0, max_digits=18, decimal_places=2)
    currency: str = Field(default="IQD", min_length=3, max_length=3)
    effective_from: datetime
    effective_until: datetime | None = None
    active: bool = False

    @field_validator("base_currency", "quote_currency", "currency")
    @classmethod
    def normalize_optional_currency(cls, value: str | None) -> str | None:
        return value.upper() if value is not None else None

    @field_validator("effective_from", "effective_until")
    @classmethod
    def effective_date_must_be_aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("Policy timestamps must include a timezone")
        return value.astimezone(UTC) if value is not None else None


class FxQuoteCreate(BaseModel):
    invoice_id: str | None = Field(default=None, min_length=36, max_length=36)
    base_currency: str = Field(min_length=3, max_length=3)
    quote_currency: str = Field(min_length=3, max_length=3)
    base_amount: Decimal = Field(gt=0, max_digits=18, decimal_places=6)
    service_reference: str | None = Field(default=None, max_length=128)
    provider_code: str | None = Field(default=None, max_length=64)
    quote_ttl_seconds: int = Field(default=600, ge=60, le=3600)

    @field_validator("base_currency", "quote_currency")
    @classmethod
    def normalize_quote_currency(cls, value: str) -> str:
        return value.upper()


class FxQuoteResponse(BaseModel):
    id: str
    status: str
    base_currency: str
    base_amount: Decimal
    quote_currency: str
    reference_rate: Decimal
    base_converted_amount: Decimal
    administrative_fee_amount: Decimal
    provider_fee_amount: Decimal
    total_quote_amount: Decimal
    rate_version: str
    source_code: str
    expires_at: datetime


class RiskAssessmentResponse(BaseModel):
    id: str
    risk_score: Decimal
    risk_level: str
    recommended_action: str
    reason_codes: list[str]
