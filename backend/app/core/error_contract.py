from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any


_STATUS_CODES: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "AUTHENTICATION_REQUIRED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    412: "PRECONDITION_FAILED",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    503: "SERVICE_UNAVAILABLE",
}


def code_for_status(status_code: int, explicit: str | None = None) -> str:
    """Return a stable, client-safe code for an HTTP response."""

    if explicit:
        return explicit
    if status_code >= 500:
        return "INTERNAL_ERROR"
    return _STATUS_CODES.get(status_code, "HTTP_ERROR")


def _safe_validation_details(errors: Sequence[Any]) -> list[dict[str, Any]]:
    """Keep validation locations/types/messages without echoing submitted input."""

    safe: list[dict[str, Any]] = []
    for error in errors:
        if not isinstance(error, Mapping):
            continue
        location = error.get("loc", ())
        safe.append(
            {
                "loc": [str(item) for item in location] if isinstance(location, Sequence) else [],
                "type": str(error.get("type", "validation_error")),
                "message": str(error.get("msg", "Invalid value")),
            }
        )
    return safe


def validation_details(errors: Sequence[Any]) -> dict[str, list[dict[str, Any]]]:
    """Build non-sensitive details for a RequestValidationError."""

    return {"errors": _safe_validation_details(errors)}


def build_error_payload(
    *,
    status_code: int,
    message: str,
    detail_ar: str | None = None,
    details: Mapping[str, Any] | None = None,
    request_id: str = "unknown",
    explicit_code: str | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Build the canonical error shape while retaining legacy compatibility fields.

    The compatibility ``detail`` and ``detail_ar`` fields remain because existing
    clients use them. ``details`` is intentionally caller-supplied and should only
    contain sanitized values such as validation locations and error types.
    """

    safe_message = str(message)
    safe_detail_ar = str(detail_ar or safe_message)
    return {
        "code": code_for_status(status_code, explicit_code),
        "message": safe_message,
        "details": dict(details or {}),
        "request_id": request_id,
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
        "detail": safe_message,
        "detail_ar": safe_detail_ar,
    }


def public_http_detail(detail: Any, *, status_code: int) -> tuple[str, dict[str, Any]]:
    """Normalize an HTTPException detail without exposing arbitrary structures."""

    if status_code >= 500:
        return "An unexpected error occurred. Please try again later.", {}
    if isinstance(detail, str) and detail.strip():
        return detail, {}
    if isinstance(detail, Mapping):
        return "Request failed.", {}
    if isinstance(detail, Sequence) and not isinstance(detail, (str, bytes, bytearray)):
        return "Request failed.", {}
    return "Request failed.", {}
