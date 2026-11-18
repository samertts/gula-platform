"""Structured FHIR R4 ``OperationOutcome`` responses for the T6 HTTP surface.

This module is a **local, non-activated** HTTP helper. It never registers a
route on the application and never performs I/O. It builds a real FHIR R4
``OperationOutcome`` for local ``TestClient`` evidence.

Diagnostics follow the I-2 hardening pattern already established in
``app.health_core.fhir.errors``: only a closed allow-list of non-sensitive
detail keys is emitted, every emitted value is HTML-escaped with
``html.escape(..., quote=True)``, and identifier-bearing keys (tokens, NIDs,
patient/tenant references, raw payload fragments) are dropped entirely.
Diagnostics are untrusted text: an HTML consumer MUST render them escaped.

Where a failure originates in the existing Health Core adapter, the adapter's
own ``operation_outcome_from_error`` is reused verbatim instead of forking the
mapping.
"""

from __future__ import annotations

import html
import json
from dataclasses import dataclass, field
from typing import Final

from fastapi.responses import JSONResponse

from app.health_core.common import HealthCoreError
from app.health_core.fhir.errors import (
    FHIR_R4_ISSUE_TYPES,
    operation_outcome_from_error,
)

__all__ = [
    "FHIR_JSON_MEDIA_TYPE",
    "ErrorBody",
    "bad_request",
    "conflict",
    "error_response",
    "error_response_for_health_core_error",
    "forbidden",
    "health_core_error_body",
    "not_found",
    "precondition_required",
    "unauthenticated",
]

FHIR_JSON_MEDIA_TYPE: Final[str] = "application/fhir+json"

# The same closed set used by the canonical Health Core adapter. Unknown future
# keys are dropped by default, so a new identifier-bearing field cannot leak.
_DIAGNOSTICS_ALLOWED_DETAIL_KEYS: Final[frozenset[str]] = frozenset(
    {"field", "key", "reason", "expected", "actual", "status"}
)


@dataclass(frozen=True, slots=True)
class ErrorBody:
    """A structured, client-safe error carried from a dependency to a route."""

    status_code: int
    issue_code: str
    message: str
    details: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.issue_code not in FHIR_R4_ISSUE_TYPES:
            msg = f"non-R4 issue code: {self.issue_code}"
            raise ValueError(msg)


def _diagnostics(body: ErrorBody) -> str:
    """Render allow-listed, HTML-escaped details into a single R4 string."""
    safe = {
        key: html.escape(str(value), quote=True)
        for key, value in body.details.items()
        if key in _DIAGNOSTICS_ALLOWED_DETAIL_KEYS
    }
    text = f"{body.issue_code.upper()}: {body.message}"
    if safe:
        text += " | " + json.dumps(safe, sort_keys=True, separators=(",", ":"))
    return text


def error_response(body: ErrorBody) -> JSONResponse:
    """Return a bare FHIR ``OperationOutcome`` body with the correct status."""
    severity = "fatal" if body.status_code >= 500 else "error"
    outcome: dict[str, object] = {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": severity,
                "code": body.issue_code,
                "diagnostics": _diagnostics(body),
            }
        ],
    }
    return JSONResponse(
        status_code=body.status_code,
        content=outcome,
        media_type=FHIR_JSON_MEDIA_TYPE,
    )


def error_response_for_health_core_error(error: HealthCoreError) -> JSONResponse:
    """Reuse the canonical adapter mapping for adapter-originated failures."""
    return JSONResponse(
        status_code=int(error.status_code),
        content=operation_outcome_from_error(error),
        media_type=FHIR_JSON_MEDIA_TYPE,
    )


def health_core_error_body(error: HealthCoreError) -> ErrorBody:
    """Project a Health Core error into the shared ErrorBody envelope.

    Used where a dependency must carry the failure without raising (the router
    is mounted with ``include_router`` only and has no app-level handler).
    """
    code = str(error.code)
    mapped = operation_outcome_from_error(error)["issue"]
    issue = mapped[0] if isinstance(mapped, list) and mapped else None
    issue_code = issue["code"] if isinstance(issue, dict) else "processing"
    if not isinstance(issue_code, str) or issue_code not in FHIR_R4_ISSUE_TYPES:
        issue_code = "processing"
    return ErrorBody(
        status_code=int(error.status_code),
        issue_code=issue_code,
        message=code,
        details={"field": "resource"},
    )


def unauthenticated() -> ErrorBody:
    """No synthetic principal was supplied (fail closed)."""
    return ErrorBody(401, "login", "FHIR authentication is required")


def forbidden(reason: str) -> ErrorBody:
    """Authenticated but not authorised for this scope, claim or resource."""
    return ErrorBody(403, "denied", reason)


def not_found() -> ErrorBody:
    """A resource or version does not exist in the synthetic repository."""
    return ErrorBody(404, "not-found", "Requested FHIR resource was not found")


def bad_request(reason: str, *, field: str) -> ErrorBody:
    """A client payload or query parameter failed validation."""
    return ErrorBody(400, "invalid", reason, details={"field": field})


def precondition_required() -> ErrorBody:
    """A conditional write omitted its ``If-Match`` precondition."""
    return ErrorBody(428, "invariant", "If-Match precondition is required for update")


def conflict() -> ErrorBody:
    """The supplied ``If-Match`` ETag does not match the current version."""
    return ErrorBody(409, "invariant", "If-Match ETag does not match the current version")
