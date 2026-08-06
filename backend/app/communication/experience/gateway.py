"""Dispatch gateway for the User Communication Experience Layer.

Every GULA application sends user communications through
:func:`send_communication` — the single, provider-agnostic entry point that:

  1. loads the recipient's preferences (locale, channels, categories,
     frequency, quiet hours, weekend/holiday rules, emergency override),
  2. decides the ordered channel plan (mandatory channels always included,
     critical categories always delivered),
  3. honors digest mode (external channels deferred; the in-app inbox row
     is always written immediately — users never lose anything),
  4. dispatches through the Communication Center with a context that
     carries ``delivery_id`` so the durable sinks link history rows.

No Communication Core or provider file is modified.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC

from .domain import (
    MANDATORY_CATEGORIES,
    UserPreferences,
    UserPriority,
)
from .preferences_service import get_preferences

logger = logging.getLogger("gula.communication.experience.gateway")

DIGEST_DEFERRED = "digest_pending"


def send_communication(
    db: Session,
    user_id: int,
    *,
    category: str = "system",
    priority: UserPriority | str = UserPriority.MEDIUM,
    title: str,
    body: str = "",
    template_id: str = "",
    variables: dict[str, Any] | None = None,
    recipient: str | None = None,
    group_key: str = "",
    action: str = "",
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Send one user communication through the configured channels.

    Returns a dict with ``delivery_id``, ``channels`` (attempted), and
    ``skipped`` (reasons) so callers can log/observe the outcome.
    """
    prefs = get_preferences(db, user_id)
    prio = UserPriority(priority)
    now = datetime.now(UTC)
    channels, skipped = prefs.decide_delivery(category=category, priority=prio, now=now)

    payload_context: dict[str, Any] = {
        "user_id": user_id,
        "category": category,
        "priority": prio.value,
        "event_name": category,
        "group_key": group_key,
        "action": action,
        "template_id": template_id,
        "title": title[:255],
        "body": body,
        "recipient": recipient or f"user:{user_id}",
        **(context if context else {}),
    }

    if (
        prefs.frequency.value == "digest"
        and prio not in (UserPriority.CRITICAL, UserPriority.HIGH)
        and category not in MANDATORY_CATEGORIES
    ):
        external = [c for c in channels if c not in ("inapp",)]
        if external:
            channels = [c for c in channels if c in ("inapp",)]
            skipped = [*skipped, *[(c, DIGEST_DEFERRED) for c in external]]

    if not channels:
        logger.info(
            "communication_gateway_suppressed user=%s category=%s priority=%s skipped=%s",
            user_id,
            category,
            prio.value,
            skipped,
        )
        return {
            "delivery_id": "",
            "user_id": user_id,
            "channels": [],
            "skipped": skipped,
            "delivered": False,
            "reason": "no_channels",
        }

    try:
        from shared.communication import Policy, new_delivery_id

        from ...communication import get_communication_center

        center = get_communication_center()
        pid = new_delivery_id()
        payload_context["delivery_id"] = pid
        core_priority = prio.to_core()
        policy = Policy(
            id=f"user.{category}.{prio.value}",
            template_id=template_id,
            priority=core_priority,
            required_channels=tuple(channels),
            optional_channels=(),
            mandatory=prio in (UserPriority.CRITICAL, UserPriority.HIGH)
            or category in MANDATORY_CATEGORIES,
        )
        receipt = center.dispatch(
            payload_context["recipient"],
            policy=policy,
            content=body,
            subject=title,
            priority=core_priority,
            context={"communication_gateway": True, **payload_context},
            template_id=template_id,
            variables=variables or {},
            severity=prio.value,
        )
        logger.info(
            "communication_gateway_dispatched user=%s category=%s channels=%s state=%s",
            user_id,
            category,
            channels,
            receipt.state,
        )
        return {
            "delivery_id": pid,
            "user_id": user_id,
            "channels": channels,
            "skipped": skipped,
            "delivered": receipt.state in ("delivered", "queued"),
            "receipt_state": receipt.state,
            "error": receipt.error,
        }
    except Exception:
        logger.exception("communication_gateway_dispatch_failed user=%s category=%s", user_id, category)
        return {
            "delivery_id": "",
            "user_id": user_id,
            "channels": [],
            "skipped": skipped,
            "delivered": False,
            "reason": "dispatch_failed",
        }


def rebuild_context(db: Session, row: Any) -> dict[str, Any]:
    """Rebuild a gateway context from a stored inbox row (for retry)."""
    stored = json.loads(row.data or "{}") or {}
    return {
        "user_id": row.user_id,
        "category": row.category,
        "priority": row.priority,
        "template_id": row.template_id or "",
        "title": row.title,
        "body": row.body,
        "recipient": stored.get("recipient") or f"user:{row.user_id}",
        "group_key": row.group_key or "",
        "action": stored.get("action") or "",
    }


def resolve_dispatchable(
    db: Session,
    prefs: UserPreferences | None = None,
    user_id: int = 0,
) -> tuple[list[str], list[tuple[str, str]]]:
    """Helper: current channel plan for the user (used by admin diagnostics)."""
    prefs = prefs or get_preferences(db, user_id)
    return prefs.decide_delivery(category="system", priority=UserPriority.MEDIUM)


__all__ = [
    "DIGEST_DEFERRED",
    "rebuild_context",
    "resolve_dispatchable",
    "send_communication",
]
