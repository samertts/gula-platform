"""Immutable domain-event shape for synthetic Health Core development.

Events are plain, frozen, JSON-serialisable records. They are not published to
any real broker and are not written to any durable store; they exist so that
contract, auditability and ordering behaviour can be tested with synthetic data.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime

from app.health_core.common.ids import new_synthetic_id

EVENT_ID_PREFIX = "EVT"

# Explicit semantic version of the event envelope + shared vocabulary.
# "1.0.0" was the implicit pre-lifecycle vocabulary (no constant existed).
# "1.1.0" adds organization.registered, encounter.started, diagnosis.resolved
# and practitioner.deactivated, plus the legacy overload disambiguation helper.
# The bump is additive/backward-compatible; no stored event is migrated.
EVENT_SCHEMA_VERSION = "1.1.0"


@dataclass(frozen=True, slots=True)
class DomainEvent:
    """A single immutable development event."""

    event_id: str
    event_type: str
    aggregate_type: str
    aggregate_id: str
    tenant_id: str
    occurred_at: str
    version: int = 1
    payload: dict[str, object] = field(default_factory=dict)
    schema_version: str = EVENT_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        """Return a stable serialisation for contract tests and audit review."""
        return asdict(self)


def new_event(
    *,
    event_type: str,
    aggregate_type: str,
    aggregate_id: str,
    tenant_id: str,
    payload: dict[str, object] | None = None,
    occurred_at: datetime | None = None,
    schema_version: str = EVENT_SCHEMA_VERSION,
) -> DomainEvent:
    """Build an event with a fresh synthetic id and a UTC ISO-8601 timestamp.

    ``schema_version`` is optional and defaults to :data:`EVENT_SCHEMA_VERSION`;
    all pre-1.1.0 call sites keep working unchanged.
    """
    moment = occurred_at or datetime.now(UTC)
    if moment.tzinfo is None:
        raise ValueError("event timestamp must be timezone-aware")
    return DomainEvent(
        event_id=new_synthetic_id(EVENT_ID_PREFIX),
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        tenant_id=tenant_id,
        occurred_at=moment.isoformat(),
        payload=dict(payload or {}),
        schema_version=schema_version,
    )
