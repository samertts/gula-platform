from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class IntegrationEventEnvelope(BaseModel):
    """Versioned, fail-closed envelope for cross-repository events."""

    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1, max_length=120)
    event_type: str = Field(pattern=r"^[a-z][a-z0-9_.-]{2,119}$")
    schema_version: int = Field(ge=1)
    source_service: str = Field(min_length=1, max_length=80)
    tenant_id: str = Field(min_length=1, max_length=120)
    occurred_at: datetime
    actor_id: str = Field(min_length=1, max_length=160)
    entity_id: str = Field(min_length=1, max_length=160)
    correlation_id: str = Field(min_length=1, max_length=160)
    idempotency_key: str = Field(min_length=1, max_length=200)
    payload: dict

    @field_validator("occurred_at")
    @classmethod
    def require_timezone_aware_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("occurred_at must be timezone-aware")
        return value
