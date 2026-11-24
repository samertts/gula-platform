"""Durable sinks for the User Communication Experience Layer.

Bound at the platform composition root (never in the Core):

  - :class:`DurableInAppSink` implements the provider-layer ``InAppSink``
    protocol: every in-app delivery is persisted as an inbox row, so every
    communication appears inside GULA even when external delivery fails.
  - :class:`InboxAuditSink` implements the Core ``AuditSink`` protocol and
    records channel/provider attempts + failures into the notification
    history for inbox rows it can link (by ``delivery_id`` — the gateway
    passes its own delivery id in ``context.delivery_id``).

Both are best-effort: sink failures never break communication delivery.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from app._compat import UTC
from shared.communication.audit import AuditEvent

logger = logging.getLogger("gula.communication.experience.sinks")


def _now() -> datetime:
    return datetime.now(UTC)


class DurableInAppSink:
    """DB-backed ``InAppSink`` — the unified user inbox writer."""

    def __init__(self, session_factory: Any | None = None) -> None:
        self._session_factory = session_factory
        self._inbox = None
        self._models = None

    def _ensure(self) -> bool:
        if self._models is not None:
            return True
        try:
            from ...database import SessionLocal
            from ...models.communication_experience import (
                NotificationEvent,
                UserNotification,
            )

            self._models = (NotificationEvent, UserNotification)
            self._session_factory = self._session_factory or SessionLocal
            return True
        except Exception:
            logger.warning("durable_inapp_sink_unavailable")
            return False

    def record(self, delivery_ref: str, recipient: str, message: Any) -> None:
        """Persist one in-app delivery into the user inbox."""
        if not self._ensure():
            return
        notification_event, user_notification = self._models
        metadata = dict(getattr(message, "metadata", {}) or {})
        context = metadata.get("context") or {}
        user_id = context.get("user_id")
        if user_id is None:
            user_id = _user_id_for_recipient(recipient, user_notification)
        if user_id is None:
            return  # no user to attach to; audit trail still records the delivery
        category = str(context.get("category") or context.get("event_name") or "system")
        priority = str(context.get("priority") or "medium")
        try:
            db = self._session_factory()
            try:
                row = user_notification(
                    user_id=int(user_id),
                    category=category,
                    priority=priority,
                    title=(getattr(message, "subject", "") or "")[:255],
                    body=getattr(message, "content", "") or "",
                    data=json.dumps(metadata, ensure_ascii=False)[:8000] or None,
                    state="unread",
                    group_key=(context.get("group_key") or None),
                    delivery_id=(context.get("delivery_id") or delivery_ref)[:64],
                    template_id=(getattr(message, "template_id", "") or "")[:100] or None,
                    locale=(getattr(message, "locale", "") or "ar")[:10],
                    created_at=_now(),
                    delivered_at=_now(),
                )
                db.add(row)
                db.flush()
                db.add(
                    notification_event(
                        notification_id=row.id,
                        event_type="delivered",
                        channel="inapp",
                        provider="inapp",
                        detail=json.dumps({"delivery_ref": delivery_ref}, ensure_ascii=False),
                        created_at=_now(),
                    ),
                )
                db.commit()
            except Exception:
                db.rollback()
                logger.exception("durable_inapp_sink_write_failed")
            finally:
                db.close()
        except Exception:
            logger.exception("durable_inapp_sink_session_failed")


class InboxAuditSink:
    """Audit-stream adapter: channel/provider history + delivery outcomes."""

    def __init__(self, session_factory: Any | None = None) -> None:
        self._session_factory = session_factory
        self._models = None

    def _ensure(self) -> bool:
        if self._models is not None:
            return True
        try:
            from ...database import SessionLocal
            from ...models.communication_experience import (
                NotificationEvent,
                UserNotification,
            )

            self._models = (NotificationEvent, UserNotification)
            self._session_factory = self._session_factory or SessionLocal
            return True
        except Exception:
            logger.warning("inbox_audit_sink_unavailable")
            return False

    def record(self, event: AuditEvent) -> None:
        """Map Core audit events onto per-notification history rows."""
        if event.action.value not in ("provider_attempt", "failed", "state_transition"):
            return
        if not self._ensure():
            return
        notification_event, user_notification = self._models
        if event.action.value == "state_transition":
            target = event.context.get("to")
            if target not in ("delivered", "failed"):
                return
            event_type = "delivered" if target == "delivered" else "error"
        elif event.action.value == "failed":
            event_type = "error"
        else:
            event_type = "delivered"
            if not event.context.get("success", True):
                event_type = "error"
        channel = str(event.context.get("channel") or "")
        provider = str(event.context.get("provider") or "")
        try:
            db = self._session_factory()
            try:
                row = (
                    db.query(user_notification)
                    .filter(
                        user_notification.delivery_id == event.delivery_id,
                        user_notification.deleted_at.is_(None),
                    )
                    .order_by(user_notification.id.desc())
                    .first()
                )
                if row is None:
                    return  # no inbox row to attach history to (audit trail has it)
                db.add(
                    notification_event(
                        notification_id=row.id,
                        event_type=event_type,
                        channel=channel[:40] or None,
                        provider=provider[:40] or None,
                        detail=json.dumps(
                            {
                                "outcome": event.outcome,
                                "context": {k: v for k, v in event.context.items() if k in ("error", "success", "attempt", "escalated", "from", "to")},
                            },
                            ensure_ascii=False,
                            default=str,
                        )[:4000],
                        created_at=_now(),
                    ),
                )
                db.commit()
            except Exception:
                db.rollback()
                logger.exception("inbox_audit_sink_write_failed")
            finally:
                db.close()
        except Exception:
            logger.exception("inbox_audit_sink_session_failed")


def _user_id_for_recipient(recipient: str, model: Any) -> int | None:
    """Best-effort address → user_id resolution (email / phone / id string)."""
    if recipient.isdigit():
        return int(recipient)
    return None


__all__ = ["DurableInAppSink", "InboxAuditSink"]
