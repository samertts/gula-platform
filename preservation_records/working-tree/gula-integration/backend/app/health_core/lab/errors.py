"""Lab-workflow-specific errors for synthetic Health Core development.

All errors derive from the shared :class:`HealthCoreError` so a future,
owner-authorised boundary could map them without any change to domain code.
Nothing here performs I/O or refers to a real patient system.
"""

from __future__ import annotations

from app.health_core.common.errors import HealthCoreError


class LabWorkflowError(HealthCoreError):
    """Base class for domain-rule violations inside the synthetic lab workflow."""

    code = "LAB_WORKFLOW_ERROR"


class UnknownLabEntityError(LabWorkflowError):
    """A referenced lab entity does not exist in the in-memory repository."""

    code = "UNKNOWN_LAB_ENTITY"
    status_code = 404


class UnknownTestCodeError(LabWorkflowError):
    """A test code is not present in the synthetic test catalogue."""

    code = "UNKNOWN_TEST_CODE"


class InvalidResultError(LabWorkflowError):
    """A result value, unit or reference range failed validation."""

    code = "INVALID_RESULT"


class InvalidActorError(LabWorkflowError):
    """An actor/reviewer identifier was not a synthetic reference."""

    code = "INVALID_ACTOR"
