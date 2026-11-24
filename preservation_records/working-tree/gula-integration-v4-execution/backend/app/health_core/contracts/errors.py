"""Serialisable error contract built from the shared Health Core errors.

The client-facing shape reuses the canonical envelope field names from the
national service contracts (``code``, ``message``, ``details``, ``request_id``,
``timestamp``, ``detail``/``detail_ar``) while preserving the shared error's
``status_code`` and ``retryable``. Values are derived from the shared error
classes; no error code is duplicated or redefined here.
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field

from app.health_core.common import (
    DuplicateEntityError,
    ForbiddenSyntheticOperationError,
    HealthCoreError,
    InvalidStateTransitionError,
    InvalidSyntheticReferenceError,
    TenantMismatchError,
    UnknownPatientError,
)

UNKNOWN_REQUEST_ID = "unknown"


@dataclass(frozen=True, slots=True)
class ErrorBodyContract:
    """A documented wire body for an error, aligned with national contracts.

    This is documentation only: the synthetic sandbox has no HTTP layer and
    creates no FHIR resource. It records BOTH bodies a production adapter must
    be able to emit so a future integration cannot silently drop one.
    """

    name: str
    content_type: str
    shape: tuple[str, ...]
    source_contract: str
    status: str


#: The two authoritative error bodies in force on the national platform.
ERROR_RESPONSE_BODIES: tuple[ErrorBodyContract, ...] = (
    ErrorBodyContract(
        name="canonical_json",
        content_type="application/json",
        shape=("code", "message", "details", "request_id", "timestamp", "detail", "detail_ar"),
        source_contract="docs/api/GULA_ERROR_CONTRACT.md",
        status="implemented by HealthCoreErrorResponse in this module",
    ),
    ErrorBodyContract(
        name="fhir_operation_outcome",
        content_type="application/fhir+json",
        shape=("resourceType=OperationOutcome", "issue[].severity", "issue[].code", "issue[].diagnostics"),
        source_contract="FHIR R4 OperationOutcome (national ehr_fhir routes)",
        status="documented for the future adapter; no FHIR resource in this sandbox",
    ),
)

#: Documented FHIR R4 ``OperationOutcome.issue.code`` for each shared error code.
#: The canonical envelope stays authoritative; this mapping exists so a future
#: FHIR adapter cannot invent its own error semantics.
FHIR_ISSUE_CODE_BY_ERROR_CODE: dict[str, str] = {
    "HEALTH_CORE_ERROR": "processing",
    "INVALID_SYNTHETIC_REFERENCE": "invalid",
    "UNKNOWN_PATIENT": "not-found",
    "TENANT_MISMATCH": "forbidden",
    "DUPLICATE_ENTITY": "conflict",
    "INVALID_STATE_TRANSITION": "conflict",
    "FORBIDDEN_SYNTHETIC_OPERATION": "forbidden",
}


class HealthCoreErrorResponse(BaseModel):
    """Stable, client-safe error shape for every Health Core error."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str = Field(..., description="Stable machine-readable error code.")
    message: str = Field(..., description="Client-safe message (no exception text).")
    status_code: int = Field(..., ge=400, le=599, description="HTTP-equivalent status code.")
    retryable: bool = Field(..., description="Whether a bounded retry may succeed.")
    details: dict[str, object] = Field(default_factory=dict, description="Sanitised context.")
    request_id: str = Field(default=UNKNOWN_REQUEST_ID, description="Correlation id or 'unknown'.")
    timestamp: str = Field(..., description="UTC ISO-8601 time the error was mapped.")
    detail: str = Field(..., description="Legacy-compatible alias of message.")
    detail_ar: str = Field(..., description="Arabic client-safe message.")


#: Authoritative map of shared error codes to their classes.
ERROR_CATALOGUE: dict[str, type[HealthCoreError]] = {
    cls.code: cls
    for cls in (
        HealthCoreError,
        InvalidSyntheticReferenceError,
        UnknownPatientError,
        TenantMismatchError,
        DuplicateEntityError,
        InvalidStateTransitionError,
        ForbiddenSyntheticOperationError,
    )
}


def error_response_from(
    error: HealthCoreError,
    *,
    request_id: str = UNKNOWN_REQUEST_ID,
    timestamp: str,
    detail_ar: str | None = None,
) -> HealthCoreErrorResponse:
    """Map a shared ``HealthCoreError`` into the stable client error shape."""
    message = str(error.message)
    return HealthCoreErrorResponse(
        code=str(error.code),
        message=message,
        status_code=int(error.status_code),
        retryable=bool(error.retryable),
        details=dict(error.details),
        request_id=request_id or UNKNOWN_REQUEST_ID,
        timestamp=timestamp,
        detail=message,
        detail_ar=detail_ar or message,
    )
