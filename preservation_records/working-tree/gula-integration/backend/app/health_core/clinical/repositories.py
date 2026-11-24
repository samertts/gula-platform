"""Process-local, in-memory adapters for clinical repositories and events.

Nothing in this module touches a database, a broker, the filesystem or the
network. State lives only as long as the adapter instance: it cannot become a
durable clinical record.
"""

from __future__ import annotations

from app.health_core.clinical.errors import UnknownClinicalEntityError
from app.health_core.common import DomainEvent

__all__ = ["InMemoryEventLog", "InMemoryRepository"]


class InMemoryEventLog:
    """An append-only, process-local event log."""

    def __init__(self) -> None:
        self._events: list[DomainEvent] = []

    def append(self, event: DomainEvent) -> None:
        """Append an immutable event; earlier events are never modified."""
        self._events.append(event)

    def all(self) -> tuple[DomainEvent, ...]:
        """Return events in emission order as an immutable tuple."""
        return tuple(self._events)

    @property
    def count(self) -> int:
        """Number of events currently held in memory."""
        return len(self._events)


class InMemoryRepository[T]:
    """A keyed in-memory repository with operation fingerprints for idempotency."""

    def __init__(self) -> None:
        self._entities: dict[str, T] = {}
        self._fingerprints: dict[str, str] = {}

    def add_if_absent(self, key: str, entity: T, fingerprint: str) -> tuple[T, bool]:
        """Store a new entity or return the existing one without changing it."""
        if key in self._entities:
            return self._entities[key], False
        self._entities[key] = entity
        self._fingerprints[key] = fingerprint
        return entity, True

    def fingerprint_of(self, key: str) -> str | None:
        """Return the fingerprint recorded for ``key``, if any."""
        return self._fingerprints.get(key)

    def get(self, key: str) -> T | None:
        """Return the entity stored under ``key``, if any."""
        return self._entities.get(key)

    def save(self, key: str, entity: T) -> T:
        """Replace an existing entity; refuse to create one implicitly."""
        if key not in self._entities:
            raise UnknownClinicalEntityError(
                "cannot replace an entity that was never registered",
                details={"key": key},
            )
        self._entities[key] = entity
        return entity

    def all(self) -> tuple[T, ...]:
        """Return all entities as an immutable snapshot."""
        return tuple(self._entities.values())

    @property
    def count(self) -> int:
        """Number of entities currently held in memory."""
        return len(self._entities)
