"""Interfaces for the synthetic clinical workstream.

Interfaces are declared before any implementation: services depend on these
protocols, and the only adapters shipped here are process-local, in-memory ones.
No interface exposes a database session, a network client or an identity link.
"""

from __future__ import annotations

from typing import Protocol, TypeVar

from app.health_core.common import DomainEvent

__all__ = ["ClinicalRepository", "EventSink", "T"]

T = TypeVar("T")


class EventSink(Protocol):
    """Append-only sink for immutable synthetic domain events."""

    def append(self, event: DomainEvent) -> None:
        """Append one event to the log."""
        ...

    def all(self) -> tuple[DomainEvent, ...]:
        """Return an immutable snapshot of all events in emission order."""
        ...


class ClinicalRepository(Protocol[T]):
    """Keyed, in-memory repository contract for one aggregate type."""

    def add_if_absent(self, key: str, entity: T, fingerprint: str) -> tuple[T, bool]:
        """Store ``entity`` under ``key``; return ``(stored, was_created)``."""
        ...

    def fingerprint_of(self, key: str) -> str | None:
        """Return the operation fingerprint stored for ``key``."""
        ...

    def get(self, key: str) -> T | None:
        """Return the entity stored under ``key`` or ``None``."""
        ...

    def save(self, key: str, entity: T) -> T:
        """Replace an existing entity under ``key``."""
        ...

    def all(self) -> tuple[T, ...]:
        """Return an immutable snapshot of all stored entities."""
        ...
