"""Sovereign interoperability scaffolding (non-wired).

This package provides the architectural shape for Phase 16 institutional
interoperability. It is intentionally NOT imported by ``app/main.py`` and
introduces NO runtime side effects.

See ``docs/sovereign/phase16-interoperability/`` for the full design.

Public surface:
    AdapterBase, AdapterContext, AdapterResult, AdapterHealth
    TrustDomain, TenancyMode, InstitutionType, FailurePolicy
    InteropAuditEvent, InteropAuditDisposition
    InteropPrincipal, InteropRole
    CircuitBreaker, CircuitState, RetryPolicy, retry_with_backoff
    ManifestError, validate_manifest
"""

from .adapter_base import (
    AdapterBase,
    AdapterContext,
    AdapterHealth,
    AdapterResult,
)
from .audit_event import InteropAuditDisposition, InteropAuditEvent
from .failure_isolation import (
    CircuitBreaker,
    CircuitState,
    RetryPolicy,
    retry_with_backoff,
)
from .manifest import ManifestError, validate_manifest
from .principal import InteropPrincipal, InteropRole
from .trust_domain import (
    FailurePolicy,
    InstitutionType,
    TenancyMode,
    TrustDomain,
)

__all__ = [
    "AdapterBase",
    "AdapterContext",
    "AdapterHealth",
    "AdapterResult",
    "CircuitBreaker",
    "CircuitState",
    "FailurePolicy",
    "InstitutionType",
    "InteropAuditDisposition",
    "InteropAuditEvent",
    "InteropPrincipal",
    "InteropRole",
    "ManifestError",
    "RetryPolicy",
    "TenancyMode",
    "TrustDomain",
    "retry_with_backoff",
    "validate_manifest",
]
