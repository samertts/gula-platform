"""Notifications API (CMD-024).

Routes:
    GET  /notifications/                  List caller's notifications
    GET  /notifications/unread-count      Unread count for caller
    PUT  /notifications/{id}/read         Mark a single notification read

Caller identity comes from the server-established trusted context, the same
single source the rest of the v1 surface reads (see core/trusted_context.py).
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.trusted_context import current_context
from ...schemas.notification import (
    NotificationListResponse,
    NotificationRead,
    NotificationUnreadCount,
)
from ...services.audit import log_action
from ...services.notification import (
    list_for_user,
    mark_read,
    unread_count,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _require_user_id(request: Request) -> str:
    # NR-127. This read the actor off the wire. Identity now comes from
    # the server-established context; see app/core/trusted_context.py.
    user_id = current_context(request).actor_id
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="a trusted caller identity is required",
        )
    return user_id


def _client_ip(request: Request) -> str | None:
    if request.client:
        return request.client.host
    return None


# ─── GET /notifications/ ────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=NotificationListResponse,
)
def list_notifications(
    request: Request,
    unread_only: bool = Query(default=False),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> NotificationListResponse:
    user_id = _require_user_id(request)

    total, rows = list_for_user(
        db,
        user_id=user_id,
        skip=skip,
        limit=limit,
        unread_only=unread_only,
    )
    return NotificationListResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=[NotificationRead.model_validate(r) for r in rows],
    )


# ─── GET /notifications/unread-count ────────────────────────────────────────

@router.get(
    "/unread-count",
    response_model=NotificationUnreadCount,
)
def get_unread_count(
    request: Request,
    db: Session = Depends(get_db),
) -> NotificationUnreadCount:
    user_id = _require_user_id(request)
    return NotificationUnreadCount(unread=unread_count(db, user_id=user_id))


# ─── PUT /notifications/{notification_id}/read ──────────────────────────────

@router.put(
    "/{notification_id}/read",
    response_model=NotificationRead,
)
def mark_notification_read(
    notification_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
) -> NotificationRead:
    user_id = _require_user_id(request)

    row = mark_read(db, notification_id=notification_id, user_id=user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="notification not found")

    log_action(
        db,
        action="notification.read",
        target_type="notification",
        target_id=str(row.id),
        actor_id=user_id,
        ip_address=_client_ip(request),
    )
    db.commit()
    db.refresh(row)
    return NotificationRead.model_validate(row)
