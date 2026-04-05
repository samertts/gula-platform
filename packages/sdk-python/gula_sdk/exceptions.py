"""GULA SDK — Exceptions."""

from __future__ import annotations


class GulaError(Exception):
    """Base exception for all GULA SDK errors."""
    def __init__(self, message: str, status_code: int | None = None, detail: str | None = None):
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)


class GulaAuthError(GulaError):
    """401 — invalid or expired API key."""


class GulaValidationError(GulaError):
    """422 — request data failed server-side validation."""
    def __init__(self, message: str, errors: list | None = None):
        self.errors = errors or []
        super().__init__(message, status_code=422)


class GulaNotFoundError(GulaError):
    """404 — resource does not exist."""


class GulaConflictError(GulaError):
    """409 — duplicate or conflicting operation (idempotency key reused)."""


class GulaRateLimitError(GulaError):
    """429 — too many requests; back off and retry."""
    def __init__(self, message: str, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(message, status_code=429)


class GulaServerError(GulaError):
    """5xx — transient server-side failure; safe to retry."""


class GulaNetworkError(GulaError):
    """Network-level failure (timeout, DNS, TLS)."""


class IncompatibleTransfusionError(GulaError):
    """Blood type compatibility violation — never retry, fix the input."""
