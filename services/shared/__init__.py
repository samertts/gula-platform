"""Bridge to GULA Shared Library.

This package now re-exports from the canonical ``shared/`` library.
All new code should import directly from ``shared``.
"""
import warnings
warnings.warn(
    "services/shared/ is deprecated. Import from 'shared' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from shared.audit import AuditService, create_audit_entry
from shared.circuit_breaker import CircuitBreaker, CircuitState
from shared.messaging import MessageBroker

__all__ = [
    "AuditService",
    "create_audit_entry",
    "CircuitBreaker",
    "CircuitState",
    "MessageBroker",
]
