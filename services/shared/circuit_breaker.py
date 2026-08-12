"""Bridge to shared CircuitBreaker."""
import warnings

warnings.warn(
    "services/shared/circuit_breaker.py is deprecated. Import from 'shared.circuit_breaker' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from shared.circuit_breaker import CircuitBreaker, CircuitState

__all__ = [
    "CircuitBreaker",
    "CircuitState",
]
