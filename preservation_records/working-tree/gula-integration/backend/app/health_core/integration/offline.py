"""In-memory offline outbox and idempotent replay contract.

Ordering is deterministic by ``(occurred_at, sequence)``: the event timestamp is
the primary replay key and the monotonic outbox sequence is the stable
tie-breaker for events sharing a timestamp. Replay is idempotent by event id,
and any version that is stale, repeated or gapped is reported as an explicit
conflict decision rather than being applied or dropped silently.

No queue, broker, database, network or filesystem is involved.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.health_core.common import DomainEvent, InvalidStateTransitionError


class ApplyStatus(StrEnum):
    """Outcome of applying one event to a replay journal."""

    APPLIED = "applied"
    DUPLICATE = "duplicate"
    CONFLICT = "conflict"


@dataclass(frozen=True, slots=True)
class OutboxEntry:
    """A single sequenced outbox record."""

    sequence: int
    event: DomainEvent

    def __post_init__(self) -> None:
        if self.sequence < 1:
            raise ValueError("outbox sequence must start at 1")


@dataclass(frozen=True, slots=True)
class ApplyDecision:
    """Structured outcome of one replay attempt."""

    status: ApplyStatus
    event_id: str
    aggregate_key: str
    reason: str
    expected_version: int
    observed_version: int


def aggregate_key(event: DomainEvent) -> str:
    """Tenant-scoped key identifying the aggregate an event mutates."""
    return f"{event.tenant_id}/{event.aggregate_type}/{event.aggregate_id}"


class OfflineOutbox:
    """Process-local outbox with idempotent enqueue and deterministic ordering."""

    def __init__(self) -> None:
        self._entries: dict[str, OutboxEntry] = {}

    def enqueue(self, event: DomainEvent) -> OutboxEntry:
        """Add an event once; re-enqueue of an identical event is a no-op."""
        existing = self._entries.get(event.event_id)
        if existing is not None:
            if existing.event != event:
                raise InvalidStateTransitionError(
                    "event_id was reused with a different event",
                    details={"event_id": event.event_id},
                )
            return existing
        entry = OutboxEntry(sequence=len(self._entries) + 1, event=event)
        self._entries[event.event_id] = entry
        return entry

    @property
    def entries(self) -> tuple[OutboxEntry, ...]:
        """All entries in enqueue order."""
        return tuple(sorted(self._entries.values(), key=lambda entry: entry.sequence))

    def ordered_entries(self) -> tuple[OutboxEntry, ...]:
        """Entries in deterministic replay order: occurred_at, then sequence."""
        return tuple(
            sorted(
                self._entries.values(),
                key=lambda entry: (entry.event.occurred_at, entry.sequence),
            )
        )

    @property
    def event_ids(self) -> frozenset[str]:
        """Set of enqueued event ids."""
        return frozenset(self._entries)

    def __len__(self) -> int:
        return len(self._entries)


class ReplayJournal:
    """Tracks applied event ids and per-aggregate versions in memory only."""

    def __init__(self) -> None:
        self._applied: set[str] = set()
        self._versions: dict[str, int] = {}

    @property
    def applied_event_ids(self) -> frozenset[str]:
        """Event ids already applied (defensive copy)."""
        return frozenset(self._applied)

    def version_of(self, key: str) -> int:
        """Current version of an aggregate key; zero means not yet seen."""
        return self._versions.get(key, 0)

    def apply(self, event: DomainEvent) -> ApplyDecision:
        """Apply one event if it is new and advances its aggregate by one version."""
        key = aggregate_key(event)
        observed = self.version_of(key)
        expected = observed + 1

        if event.event_id in self._applied:
            return ApplyDecision(
                status=ApplyStatus.DUPLICATE,
                event_id=event.event_id,
                aggregate_key=key,
                reason="event_id already applied; replay is idempotent",
                expected_version=event.version,
                observed_version=observed,
            )
        if event.version == observed:
            reason = "divergent version: another event already holds this version"
        elif event.version < observed:
            reason = "stale version: event predates current aggregate version"
        elif event.version > expected:
            reason = "version gap: event skips one or more aggregate versions"
        else:
            self._applied.add(event.event_id)
            self._versions[key] = event.version
            return ApplyDecision(
                status=ApplyStatus.APPLIED,
                event_id=event.event_id,
                aggregate_key=key,
                reason="advanced aggregate by one version",
                expected_version=expected,
                observed_version=observed,
            )
        return ApplyDecision(
            status=ApplyStatus.CONFLICT,
            event_id=event.event_id,
            aggregate_key=key,
            reason=reason,
            expected_version=expected,
            observed_version=observed,
        )


def replay(outbox: OfflineOutbox, journal: ReplayJournal | None = None) -> tuple[ApplyDecision, ...]:
    """Replay an outbox in deterministic order into the given (or a new) journal."""
    target = journal if journal is not None else ReplayJournal()
    return tuple(target.apply(entry.event) for entry in outbox.ordered_entries())
