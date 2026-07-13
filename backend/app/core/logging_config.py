"""Structured logging — canonical shared.logging.

Re-exports the canonical logging configuration from the shared library.
All backend code uses the same formatter and context bindings.
"""

from shared.logging import (
    JSONFormatter as _JSONFormatter,
)
from shared.logging import (
    bind_log_context,
    configure_logging,
    get_request_id,
)

JSONFormatter = _JSONFormatter

__all__ = [
    "JSONFormatter",
    "_JSONFormatter",
    "bind_log_context",
    "configure_logging",
    "get_request_id",
]
