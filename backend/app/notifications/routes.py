from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_niam_db as get_db
from app.identity.security import get_current_identity

from .services import NotificationQueueService

router = APIRouter(
    prefix="/notifications",
    tags=["NIAM Notifications"],
    dependencies=[Depends(get_current_identity)],
)


@router.post("/send")
async def send_notification(
    recipient_id: str,
    notification_type: str,
    channel: str,
    subject: str | None = None,
    body: str | None = None,
    context: dict[str, Any] | None = None,
    priority: str = "medium",
    recipient_type: str = "person",
    scheduled_at: datetime | None = None,
    db: AsyncSession = Depends(get_db),
):
    service = NotificationQueueService(db)
    notification = await service.send_notification(
        recipient_id=recipient_id,
        notification_type=notification_type,
        channel=channel,
        subject=subject,
        body=body,
        context=context,
        priority=priority,
        recipient_type=recipient_type,
        scheduled_at=scheduled_at,
    )
    return {"queue_id": notification.queue_id, "status": notification.status}


@router.post("/templates")
async def create_template(
    template_id: str,
    name: str,
    notification_type: str,
    body: str,
    subject: str | None = None,
    variables: list[str] | None = None,
    locale: str = "ar",
    version: str = "1.0",
    db: AsyncSession = Depends(get_db),
):
    service = NotificationQueueService(db)
    template = await service.create_template(
        template_id=template_id,
        name=name,
        notification_type=notification_type,
        body=body,
        subject=subject,
        variables=variables,
        locale=locale,
        version=version,
    )
    return template.to_dict()


@router.get("/templates")
async def list_templates(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    service = NotificationQueueService(db)
    templates = await service.list_templates(skip=skip, limit=limit)
    return [t.to_dict() for t in templates]


@router.get("/queue/{recipient_id}")
async def get_queue(
    recipient_id: str,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    service = NotificationQueueService(db)
    notifications = await service.get_queue_for_recipient(
        recipient_id=recipient_id,
        skip=skip,
        limit=limit,
    )
    return [n.to_dict() for n in notifications]


@router.post("/queue/{queue_id}/read")
async def mark_read(
    queue_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = NotificationQueueService(db)
    notification = await service.mark_read(queue_id)
    if not notification:
        return {"error": "not_found"}
    return {"queue_id": notification.queue_id, "status": notification.status}


@router.get("/preferences/{recipient_id}")
async def get_preferences(
    recipient_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = NotificationQueueService(db)
    preferences = await service.get_preferences(recipient_id)
    return [p.to_dict() for p in preferences]


@router.put("/preferences/{recipient_id}")
async def update_preferences(
    recipient_id: str,
    category: str,
    channel: str,
    enabled: bool,
    recipient_type: str = "person",
    quiet_hours_start: str | None = None,
    quiet_hours_end: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    service = NotificationQueueService(db)
    preference = await service.update_preferences(
        recipient_id=recipient_id,
        category=category,
        channel=channel,
        enabled=enabled,
        recipient_type=recipient_type,
        quiet_hours_start=quiet_hours_start,
        quiet_hours_end=quiet_hours_end,
    )
    return preference.to_dict()


@router.post("/send-template")
async def send_template_notification(
    template_id: str,
    recipient_id: str,
    context: dict[str, Any] | None = None,
    priority: str = "medium",
    recipient_type: str = "person",
    scheduled_at: datetime | None = None,
    db: AsyncSession = Depends(get_db),
):
    service = NotificationQueueService(db)
    notification = await service.send_template(
        template_id=template_id,
        recipient_id=recipient_id,
        context=context,
        priority=priority,
        recipient_type=recipient_type,
        scheduled_at=scheduled_at,
    )
    if not notification:
        return {"error": "template_not_found"}
    return {"queue_id": notification.queue_id, "status": notification.status}


@router.post("/queue/{queue_id}/sent")
async def mark_notification_sent(
    queue_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = NotificationQueueService(db)
    notification = await service.mark_sent(queue_id)
    if not notification:
        return {"error": "not_found"}
    return {"queue_id": notification.queue_id, "status": notification.status}


@router.post("/queue/{queue_id}/delivered")
async def mark_notification_delivered(
    queue_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = NotificationQueueService(db)
    notification = await service.mark_delivered(queue_id)
    if not notification:
        return {"error": "not_found"}
    return {"queue_id": notification.queue_id, "status": notification.status}


@router.get("/pending")
async def get_pending_notifications(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    service = NotificationQueueService(db)
    notifications = await service.get_pending(limit=limit)
    return [n.to_dict() for n in notifications]
