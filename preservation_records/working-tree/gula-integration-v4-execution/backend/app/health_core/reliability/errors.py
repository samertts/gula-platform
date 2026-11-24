"""Structured, serialisable errors for the isolated reliability designs.

These mirror the boundary-safe shape of ``HealthCoreError`` (``code``, ``message``,
``status_code``, ``retryable``, ``details``) so a future owner-authorized boundary can
map them without changing the reliability logic. No error carries patient data.
"""

from __future__ import annotations

from app.health_core.common.errors import HealthCoreError


class ReliabilityError(HealthCoreError):
    """Base class for reliability design errors."""


class ChecksumMismatchError(ReliabilityError):
    """A snapshot, WAL or backup payload failed its checksum/schema check."""

    code = "CHECKSUM_MISMATCH"


class InvalidStoreValueError(ReliabilityError):
    """A value or code submitted to a reliability component is malformed."""

    code = "INVALID_STORE_VALUE"


class BackupIntegrityError(ReliabilityError):
    """A backup artifact failed checksum, schema or restored-data verification."""

    code = "BACKUP_INTEGRITY"


class AuditChainError(ReliabilityError):
    """An audit chain cannot be verified (used by callers that fail closed)."""

    code = "AUDIT_CHAIN_INVALID"


class IdempotencyConflictError(ReliabilityError):
    """A synthetic idempotency key was reused with a different request fingerprint."""

    code = "IDEMPOTENCY_KEY_CONFLICT"
    status_code = 409


class InvalidMetricNameError(ReliabilityError):
    """A metric name was not a safe lowercase code (possible PII or free text)."""

    code = "INVALID_METRIC_NAME"


class ConflictAccountingError(ReliabilityError):
    """A conflict resolution omitted a candidate disposition or its audit record."""

    code = "CONFLICT_ACCOUNTING_INVALID"
