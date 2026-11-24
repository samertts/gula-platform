"""Structured, boundary-safe errors for synthetic Health Core development.

These errors intentionally mirror the shape used by ``app.domain.exceptions``
(``message`` + ``status_code``) so a future, owner-authorised boundary can map
them to HTTP responses without changing domain code. They carry a stable
machine-readable ``code`` for contract tests and client error handling.
"""

from __future__ import annotations

from app.domain.exceptions import DomainError


class HealthCoreError(DomainError):
    """Base class for all Health Core development errors."""

    code: str = "HEALTH_CORE_ERROR"
    status_code: int = 400
    retryable: bool = False

    def __init__(self, message: str, *, details: dict[str, object] | None = None) -> None:
        self.message = message
        self.details: dict[str, object] = dict(details or {})
        super().__init__(message)

    def to_dict(self) -> dict[str, object]:
        """Return a stable, serialisable error contract."""
        return {
            "code": self.code,
            "message": self.message,
            "status_code": self.status_code,
            "retryable": self.retryable,
            "details": dict(self.details),
        }


class InvalidSyntheticReferenceError(HealthCoreError):
    """An identifier was not a valid synthetic reference."""

    code = "INVALID_SYNTHETIC_REFERENCE"


class UnknownPatientError(HealthCoreError):
    """The referenced synthetic patient does not exist in this registry."""

    code = "UNKNOWN_PATIENT"
    status_code = 404


class TenantMismatchError(HealthCoreError):
    """A synthetic patient was addressed from the wrong synthetic tenant."""

    code = "TENANT_MISMATCH"
    status_code = 403


class DuplicateEntityError(HealthCoreError):
    """An entity with the same synthetic key already exists (idempotency conflict)."""

    code = "DUPLICATE_ENTITY"
    status_code = 409


class InvalidStateTransitionError(HealthCoreError):
    """An illegal lifecycle transition was requested."""

    code = "INVALID_STATE_TRANSITION"
    status_code = 409


class ForbiddenSyntheticOperationError(HealthCoreError):
    """An operation would cross a tenant boundary or leave the synthetic sandbox."""

    code = "FORBIDDEN_SYNTHETIC_OPERATION"
    status_code = 403
