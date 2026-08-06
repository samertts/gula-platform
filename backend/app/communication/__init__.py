"""GULA Platform — Communication Platform Core composition root.

Wires the provider-independent Core (``shared.communication``) to platform
infrastructure:

  - Event bus: binds registered event policies to the canonical in-process
    bus (``app.core.events.events``) so the Platform *consumes* events.
  - Audit: every communication operation is recorded on the tamper-evident
    audit trail (``audit_service.log_action``).
  - State store / queue registry: left unbound on purpose — PROGRAM-COMM-002
    plugs queue providers and provider plugins without touching the Core.

No provider implementation lives here. The Center never imports a provider.
"""

from __future__ import annotations

import logging
from typing import Any

from shared.communication import (
    CommunicationCenter,
    CommunicationConfig,
    EventBridge,
    Policy,
    Priority,
    Template,
    build_communication_center,
)
from shared.communication.audit import AuditEvent

logger = logging.getLogger("gula.platform.communication")

_center: CommunicationCenter | None = None
_center_built = False


# ── Provider plugin wiring (PROGRAM-COMM-002) ───────────────────────────────


def _register_provider_plugins(center: CommunicationCenter) -> None:
    """Discover + register provider plugins without touching the Core.

    Providers self-register through the plugin catalog / entry points; the
    Center publishes them into its registry. Providers without credentials
    report ``DOWN`` health and are skipped by routing — configuration is
    purely env / docker / k8s / cloud secrets.
    """
    try:
        from shared.communication_providers import load_provider_plugins

        manager = load_provider_plugins(center.providers)
        logger.info(
            "communication_providers_registered count=%d channels=%s",
            len(manager.states()),
            ",".join(center.providers.channels()),
        )
    except Exception:
        logger.exception("communication_provider_registration_failed")


def _install_experience_sinks(center: CommunicationCenter) -> None:
    """Bind the durable user-experience sinks (PROGRAM-COMM-003).

    The unified user inbox is written by the durable in-app sink installed
    on the ``inapp`` provider, and the audit-history sink appends
    channel/provider outcomes to per-notification history. Both are
    best-effort: failures never block delivery.
    """
    try:
        from .experience.sinks import DurableInAppSink, InboxAuditSink

        provider = center.providers.get("inapp")
        if provider is not None:
            provider._sink = DurableInAppSink()
            logger.info("communication_durable_inbox_sink_installed")
    except Exception:
        logger.exception("communication_durable_inbox_sink_failed")
    try:
        from shared.communication.audit import CompositeAuditSink

        composite = center.audit_sink
        if isinstance(composite, CompositeAuditSink):
            composite.add(InboxAuditSink())
            logger.info("communication_inbox_audit_sink_installed")
    except Exception:
        logger.exception("communication_inbox_audit_sink_install_failed")


# ── Platform audit sink ───────────────────────────────────────────────────────


class _AuditServiceSink:
    """Durable audit sink backed by the tamper-evident audit trail.

    Each communication operation is appended via ``audit_service.log_action``
    (immutable table + chain hashes + disk anchors). Opens a short session
    per event — writes are small and infrequent.
    """

    def __init__(self) -> None:
        self._session_factory: Any | None = None

    def _ensure_dependencies(self) -> bool:
        if self._session_factory is not None:
            return True
        try:
            from ..database import SessionLocal
            from ..services import audit_service

            self._session_factory = SessionLocal
            self._log_action = audit_service.log_action
            return True
        except Exception:
            logger.warning("communication_audit_sink_unavailable falling_back_to_logging")
            return False

    def record(self, event: AuditEvent) -> None:
        if not self._ensure_dependencies():
            return
        try:
            db = self._session_factory()
            try:
                self._log_action(
                    db=db,
                    action=event.action.value,
                    resource_type=event.entity_type,
                    resource_id=None,
                    user_id=None,
                    user_role=None,
                    details=_redact_details(event.to_dict()),
                    ip_address=None,
                )
                db.commit()
            except Exception:
                db.rollback()
                logger.exception(
                    "communication_audit_trail_write_failed action=%s delivery=%s",
                    event.action.value,
                    event.delivery_id,
                )
            finally:
                db.close()
        except Exception:
            logger.exception("communication_audit_session_failed")


def _redact_details(entry: dict[str, Any]) -> str:
    """Structured, safe audit details (never contains secrets by design)."""
    import json

    return json.dumps(entry, ensure_ascii=False, default=str)[:1000]


# ── Starter platform policies + templates ────────────────────────────────────


def _register_starter_content(center: CommunicationCenter) -> None:
    """Declarative event→policy→template bindings for platform events.

    Channels are intentionally EMPTY until PROGRAM-COMM-002 plugs providers —
    binding an event now means the mapping exists; delivery starts as soon
    as a provider registers for the channel.
    """
    center.policies.register(
        Policy(
            id="platform.result.critical",
            template_id="alert.critical_result",
            priority=Priority.URGENT,
            required_channels=("telegram",),
            fallback_channels=("email",),
            escalation_channels=("sms",),
            escalation_after_seconds=300,
            mandatory=True,
        ),
    )
    center.policies.register(
        Policy(
            id="platform.order.validated",
            template_id="inform.order_validated",
            priority=Priority.NORMAL,
            optional_channels=("email",),
        ),
    )
    center.policies.register(
        Policy(
            id="platform.backup.failed",
            template_id="alert.backup_failed",
            priority=Priority.HIGH,
            optional_channels=("telegram", "email"),
            mandatory=True,
        ),
    )

    engine = center.templates
    engine.register(
        Template(
            id="alert.critical_result",
            locale="",
            subject="CRITICAL RESULT: {patient_name}",
            bodies={
                "plain": "CRITICAL ALERT\nPatient: {patient_name}\nTest: {test_name}\nValue: {value}",
                "html": "<b>CRITICAL ALERT</b><br/>Patient: {patient_name}<br/>Test: {test_name}<br/>Value: {value}",
            },
        ),
    )
    engine.register(
        Template(
            id="inform.order_validated",
            locale="",
            subject="Order validated: {order_id}",
            bodies={
                "plain": "Order {order_id} was validated.",
                "html": "Order <b>{order_id}</b> was validated.",
            },
        ),
    )
    engine.register(
        Template(
            id="alert.backup_failed",
            locale="",
            subject="BACKUP FAILED",
            bodies={
                "plain": "Backup failed for {target}.",
                "html": "<b>BACKUP FAILED</b><br/>Backup failed for {target}.",
            },
        ),
    )

    center.event_policies.bind("result.critical", "platform.result.critical", recipient_key="recipient")
    center.event_policies.bind("order.validated", "platform.order.validated", recipient_key="recipient")
    center.event_policies.bind("backup.failed", "platform.backup.failed", recipient_key="recipient")


# ── Singleton + wiring ────────────────────────────────────────────────────────


def get_communication_center() -> CommunicationCenter:
    """Lazy singleton: build once, wire the event bus exactly once."""
    global _center, _center_built
    if _center is not None:
        return _center
    config = CommunicationConfig.from_env()
    _center = build_communication_center(config=config)
    _register_provider_plugins(_center)
    _register_starter_content(_center)
    _install_experience_sinks(_center)

    if config.audit_enabled:
        composite = _center.audit_sink
        from shared.communication.audit import CompositeAuditSink

        if isinstance(composite, CompositeAuditSink):
            composite.add(_AuditServiceSink())
        else:
            logger.warning("communication_durable_audit_not_bound")

    if not _center_built:
        _bind_events(_center)
        _center_built = True
    return _center


def _bind_events(center: CommunicationCenter) -> None:
    """Subscribe the Center to the canonical platform event bus."""
    try:
        from app.core.events import events

        bridge = EventBridge(center, center.event_policies)
        bridge.bind(events)
        bound = bridge.bound_event_names()
        logger.info("communication_event_bridge_bound events=%s", bound)
    except Exception:
        logger.exception("communication_event_bridge_bind_failed")


def reset_center() -> None:
    """Test helper: drop the singleton (never called in production)."""
    global _center, _center_built
    _center = None
    _center_built = False


__all__ = ["get_communication_center", "reset_center"]
