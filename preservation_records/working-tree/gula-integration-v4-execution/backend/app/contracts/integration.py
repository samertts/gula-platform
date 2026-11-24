from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator

# C12/C14 propagation contract. These names are shared by HTTP middleware,
# outbox workers and offline bridge adapters; do not duplicate them elsewhere.
REQUEST_ID_HEADER = "X-Request-ID"
CORRELATION_ID_HEADER = "X-Correlation-ID"
TRACEPARENT_HEADER = "traceparent"

# Log-safe, bounded identifiers. Reject control characters, whitespace and
# other injection surfaces before the value reaches headers, logs or events.
_CORRELATION_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


def normalize_correlation_id(value: str | None, fallback: str | None = None) -> str:
    """Return a bounded correlation ID, falling back safely when invalid.

    Caller-supplied values are accepted only when they match the log-safe
    pattern. Invalid or absent values use ``fallback`` when that is itself
    valid, otherwise a fresh UUID is generated. No PHI or free text is copied.
    """
    candidate = (value or "").strip()
    if _CORRELATION_ID_RE.fullmatch(candidate):
        return candidate
    fallback_candidate = (fallback or "").strip()
    if _CORRELATION_ID_RE.fullmatch(fallback_candidate):
        return fallback_candidate
    return str(uuid.uuid4())


def correlation_id_from_headers(
    headers: Mapping[str, str],
    fallback: str | None = None,
) -> str:
    """Resolve the end-to-end correlation ID from inbound HTTP headers."""
    return normalize_correlation_id(
        headers.get(CORRELATION_ID_HEADER) or headers.get(TRACEPARENT_HEADER),
        fallback=headers.get(REQUEST_ID_HEADER) or fallback,
    )


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
