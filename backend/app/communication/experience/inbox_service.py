"""Unified user inbox service (PROGRAM-COMM-003).

Query, filter, search, paginate, act on, and trace every notification a
user has ever received. All state changes are audit-able through the
append-only history table. Nothing here touches the Communication Core —
re-delivery uses the injected sender callback supplied by the routes layer.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app._compat import UTC

from ...models.communication_experience import NotificationEvent, UserNotification
from .domain import InboxState

logger = logging.getLogger("gula.communication.experience.inbox")

EVENT_MAP = {
    "read": ("state_read", "read"),
    "unread": ("state_unread", "unread"),
    "archive": ("state_archived", "archived"),
    "restore": ("state_restored", "restored"),
    "delete": ("state_deleted", "deleted"),
    "deleted_hard": ("delete", "purged"),
    "pin": ("pin", "pinned"),
    "unpin": ("pin", "unpinned"),
}

#: HTTP action verb → InboxState. Kept separate from the enum values so the
#: wire vocabulary ("archive"/"restore") stays stable while states evolve.
ACTION_TO_STATE: dict[str, InboxState] = {
    "read": InboxState.READ,
    "unread": InboxState.UNREAD,
    "archive": InboxState.ARCHIVED,
    "restore": InboxState.READ,
    "delete": InboxState.DELETED,
}


def _now() -> datetime:
    return datetime.now(UTC)


def list_inbox(
    db: Session,
    user_id: int,
    *,
    state: str | None = None,
    category: str | None = None,
    priority: str | None = None,
    group_key: str | None = None,
    search: str | None = None,
    pinned: bool | None = None,
    cursor: int | None = None,
    limit: int = 20,
    include_deleted: bool = False,
) -> dict[str, Any]:
    """Paginated, filterable inbox (cursor-based → infinite scroll).

    Returns ``{"items": [...], "next_cursor": int|None, "total": int}``.
    Deleted rows are hidden unless ``include_deleted`` is set.
    """
    limit = max(1, min(int(limit), 100))
    query = db.query(UserNotification).filter(UserNotification.user_id == user_id)
    if not include_deleted:
        query = query.filter(UserNotification.deleted_at.is_(None))
    if state:
        query = query.filter(UserNotification.state == str(state))
    if category:
        query = query.filter(UserNotification.category == str(category))
    if priority:
        query = query.filter(UserNotification.priority == str(priority))
    if group_key:
        query = query.filter(UserNotification.group_key == str(group_key))
    if pinned is not None:
        query = query.filter(UserNotification.pinned.is_(bool(pinned)))
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(UserNotification.title.ilike(term), UserNotification.body.ilike(term)),
        )
    if cursor:
        query = query.filter(UserNotification.id < int(cursor))
    query = query.order_by(UserNotification.pinned.desc(), UserNotification.id.desc())

    total = query.count()
    rows = query.limit(limit + 1).all()
    has_more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = rows[-1].id if (has_more and rows) else None
    return {
        "items": [r.to_dict() for r in rows],
        "next_cursor": next_cursor,
        "total": total,
        "limit": limit,
    }


def grouped_summary(db: Session, user_id: int) -> list[dict[str, Any]]:
    rows = (
        db.query(UserNotification.group_key, func.count(UserNotification.id))
        .filter(
            UserNotification.user_id == user_id,
            UserNotification.deleted_at.is_(None),
            UserNotification.group_key.isnot(None),
        )
        .group_by(UserNotification.group_key)
        .order_by(func.count(UserNotification.id).desc())
        .limit(50)
        .all()
    )
    return [{"group_key": g, "count": c} for g, c in rows]


def get_inbox_item(db: Session, user_id: int, notification_id: int) -> UserNotification:
    row = (
        db.query(UserNotification)
        .filter(
            UserNotification.id == notification_id,
            UserNotification.user_id == user_id,
        )
        .first()
    )
    if row is None:
        raise LookupError(f"notification not found: {notification_id}")
    return row


def unread_count(db: Session, user_id: int) -> int:
    return (
        db.query(func.count(UserNotification.id))
        .filter(
            UserNotification.user_id == user_id,
            UserNotification.state == InboxState.UNREAD.value,
            UserNotification.deleted_at.is_(None),
        )
        .scalar()
        or 0
    )


def _apply_state(
    db: Session,
    row: UserNotification,
    target: InboxState,
    *,
    event_type: str | None = None,
    detail: str | None = None,
) -> UserNotification:
    row.state = target.value
    if target == InboxState.READ:
        row.read_at = _now()
    if target == InboxState.ARCHIVED:
        row.archived_at = _now()
    if target == InboxState.DELETED:
        row.deleted_at = _now()
    db.add(row)
    db.flush()
    db.add(
        NotificationEvent(
            notification_id=row.id,
            event_type=event_type or f"state_{target.value}",
            channel="inbox",
            detail=detail,
            created_at=_now(),
        ),
    )
    db.commit()
    return row


def set_state(
    db: Session,
    user_id: int,
    notification_id: int,
    state: str,
) -> dict[str, Any]:
    """Mark read / unread / archive / restore / delete (soft)."""
    if state not in ACTION_TO_STATE:
        raise ValueError(f"unknown_state_action: {state}")
    row = get_inbox_item(db, user_id, notification_id)
    _apply_state(
        db,
        row,
        ACTION_TO_STATE[state],
        event_type=EVENT_MAP.get(state, (f"state_{state}", None))[0],
        detail=EVENT_MAP.get(state, (None, None))[1],
    )
    return row.to_dict()


def set_pinned(
    db: Session,
    user_id: int,
    notification_id: int,
    pinned: bool,
) -> dict[str, Any]:
    row = get_inbox_item(db, user_id, notification_id)
    row.pinned = bool(pinned)
    db.add(row)
    db.flush()
    db.add(
        NotificationEvent(
            notification_id=row.id,
            event_type="pinned" if pinned else "unpinned",
            channel="inbox",
            created_at=_now(),
        ),
    )
    db.commit()
    return row.to_dict()


def bulk_state(
    db: Session,
    user_id: int,
    state: str,
    ids: list[int] | None = None,
) -> dict[str, int]:
    """Bulk state transition (e.g. mark-all-read), optional subset by ids."""
    query = db.query(UserNotification).filter(
        UserNotification.user_id == user_id,
        UserNotification.deleted_at.is_(None),
    )
    if ids:
        query = query.filter(UserNotification.id.in_(ids))
    rows = query.all()
    if state not in ACTION_TO_STATE:
        raise ValueError(f"unknown_state_action: {state}")
    target = ACTION_TO_STATE[state]
    for row in rows:
        _apply_state(db, row, target, event_type=EVENT_MAP.get(state, (f"state_{state}", None))[0])
    return {"updated": len(rows)}


def purge(db: Session, user_id: int, notification_id: int) -> dict[str, Any]:
    """Permanently delete one inbox row (admin/owner only)."""
    row = get_inbox_item(db, user_id, notification_id)
    db.delete(row)
    db.commit()
    return {"id": notification_id, "deleted": True}


def history(
    db: Session,
    user_id: int,
    notification_id: int,
    limit: int = 50,
) -> list[dict[str, Any]]:
    get_inbox_item(db, user_id, notification_id)
    events = (
        db.query(NotificationEvent)
        .filter(NotificationEvent.notification_id == notification_id)
        .order_by(NotificationEvent.id.desc())
        .limit(max(1, min(limit, 200)))
        .all()
    )
    return [e.to_dict() for e in events]


def retry_delivery(
    db: Session,
    user_id: int,
    notification_id: int,
    dispatch: Callable[[dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    """Re-dispatch a delivered/read/archived notification (if permitted).

    ``dispatch(context)`` returns at least ``{"success": bool, "error": str|None}``
    and must raise nothing. The context carries the stored metadata so the
    sender can rebuild the policy + template payload.
    """
    row = get_inbox_item(db, user_id, notification_id)
    context = json.loads(row.data or "{}") or {}
    try:
        outcome = dispatch(context)
    except Exception as exc:  # defensive: callbacks must not raise
        logger.exception("inbox_retry_dispatch_failed id=%s", notification_id)
        outcome = {"success": False, "error": f"{type(exc).__name__}: {exc}"}
    db.add(
        NotificationEvent(
            notification_id=row.id,
            event_type="retried" if outcome.get("success") else "error",
            channel="retry",
            detail=(outcome.get("error") or "re-delivered")[:4000],
            created_at=_now(),
        ),
    )
    if outcome.get("success"):
        row.delivered_at = _now()
        if row.state == InboxState.DELETED.value:
            row.deleted_at = None
        db.add(row)
    db.commit()
    return {"id": row.id, "success": bool(outcome.get("success")), "error": outcome.get("error")}


def user_preference_payload(prefs: Any) -> dict[str, Any]:
    """Helper the dispatch gateway uses to publish preference context."""
    return prefs.to_dict()


__all__ = [
    "bulk_state",
    "get_inbox_item",
    "grouped_summary",
    "history",
    "list_inbox",
    "purge",
    "retry_delivery",
    "set_pinned",
    "set_state",
    "unread_count",
]
