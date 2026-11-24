"""Audit integration for the GULA Communication Platform Core.

Every communication operation (dispatch, policy decision, provider attempt,
state transition, escalation, template render, plugin lifecycle) is emitted
as a structured :class:`AuditEvent` to an :class:`AuditSink`. The sink is an
interface — the tamper-evident audit trail is provided by the platform (see
``audit_service.log_action``) and bound at the composition root.
"""

from __future__ import annotations

import enum
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol

logger = logging.getLogger("gula.communication.audit")


class AuditAction(enum.StrEnum):
    DISPATCH_CREATED = "communication.dispatch.created"
    POLICY_DECISION = "communication.policy.decision"
    RENDER = "communication.template.render"
    PROVIDER_ATTEMPT = "communication.provider.attempt"
    STATE_TRANSITION = "communication.state.transition"
    ESCALATION = "communication.escalation"
    PLUGIN_ACTIVATED = "communication.plugin.activated"
    PLUGIN_DEACTIVATED = "communication.plugin.deactivated"
    FAILED = "communication.failed"

    @classmethod
    def _missing_(cls, value: object) -> AuditAction:
        return cls.FAILED


@dataclass(frozen=True)
class AuditEvent:
    """Structured, serialisable audit record for one communication operation."""

    action: AuditAction
    delivery_id: str
    context: dict[str, Any] = field(default_factory=dict)
    outcome: str = ""
    entity_type: str = "communication.delivery"
    actor: str = "system"
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        object.__setattr__(self, "action", AuditAction(self.action))

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action.value,
            "delivery_id": self.delivery_id,
            "context": dict(self.context),
            "outcome": self.outcome,
            "entity_type": self.entity_type,
            "actor": self.actor,
            "occurred_at": self.occurred_at.isoformat(),
        }


class AuditSink(Protocol):
    """Receives audit events. Implemented outside the Core."""

    def record(self, event: AuditEvent) -> None: ...


class LoggingAuditSink:
    """Structured-logging sink used when no durable sink is bound."""

    def record(self, event: AuditEvent) -> None:
        logger.info(
            "communication_audit action=%s delivery=%s outcome=%s",
            event.action.value,
            event.delivery_id,
            event.outcome or "-",
        )


class CompositeAuditSink:
    """Fan-out sink so multiple auditors (log + durable trail) can coexist."""

    def __init__(self) -> None:
        self._sinks: list[AuditSink] = []

    def add(self, sink: AuditSink) -> None:
        self._sinks.append(sink)

    def clear(self) -> None:
        self._sinks.clear()

    def record(self, event: AuditEvent) -> None:
        for sink in self._sinks:
            try:
                sink.record(event)
            except Exception:
                logger.exception(
                    "communication_audit_sink_failed action=%s delivery=%s",
                    event.action.value,
                    event.delivery_id,
                )


class NullAuditSink:
    """Discards all events (explicit opt-out)."""

    def record(self, event: AuditEvent) -> None:
        pass


__all__ = [
    "AuditAction",
    "AuditEvent",
    "AuditSink",
    "CompositeAuditSink",
    "LoggingAuditSink",
    "NullAuditSink",
]