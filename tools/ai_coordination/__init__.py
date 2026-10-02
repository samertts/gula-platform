"""Provider-neutral coordination primitives for AI agents working on GULA."""

from .coordination import (
    AgentCoordinator,
    AgentIdentity,
    ChangeIntent,
    CoordinationConflict,
    CoordinationError,
    TaskClaim,
)

__all__ = [
    "AgentCoordinator",
    "AgentIdentity",
    "ChangeIntent",
    "CoordinationConflict",
    "CoordinationError",
    "TaskClaim",
]
