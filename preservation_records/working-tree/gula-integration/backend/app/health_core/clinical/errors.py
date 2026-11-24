"""Errors raised by the synthetic clinical workstream.

These extend the shared Health Core error contract with two clinical-specific
machine-readable codes. They never carry patient data and are safe to serialise
at a future, owner-authorised boundary.
"""

from __future__ import annotations

from app.health_core.common import HealthCoreError

__all__ = ["ClinicalValidationError", "UnknownClinicalEntityError"]


class ClinicalValidationError(HealthCoreError):
    """A clinical input failed domain validation."""

    code = "CLINICAL_VALIDATION_ERROR"


class UnknownClinicalEntityError(HealthCoreError):
    """A referenced synthetic clinical entity does not exist in this context."""

    code = "UNKNOWN_CLINICAL_ENTITY"
    status_code = 404
