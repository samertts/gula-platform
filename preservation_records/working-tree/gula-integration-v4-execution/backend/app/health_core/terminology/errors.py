"""Errors raised by the terminology registry (not by code validation)."""

from __future__ import annotations

from app.health_core.common.errors import HealthCoreError


class TerminologyError(HealthCoreError):
    """Base class for terminology configuration and registry errors."""

    code = "TERMINOLOGY_ERROR"


class UnknownTerminologySystemError(TerminologyError):
    """A validator was requested for a code system with no curated adapter."""

    code = "UNKNOWN_TERMINOLOGY_SYSTEM"


__all__ = ["TerminologyError", "UnknownTerminologySystemError"]
