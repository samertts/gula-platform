from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db

from .services import NotificationService

router = APIRouter(prefix="/notifications", tags=["NIAM Notifications"])


@router.post("/send")
def send_notification(
    recipient_id: str,
    notification_type: str,
    channel: str,
    subject: str | None = None,
    body: str | None = None,
    context: dict[str, Any] | None = None,
    priority: str = "medium",
    recipient_type: str = "person",
    scheduled_at: datetime | None = None,
    db: Session = Depends(get_db),
):
    service = NotificationService(db)
    notification = service.send_notification(
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
def create_template(
    template_id: str,
    name: str,
    notification_type: str,
    body: str,
    subject: str | None = None,
    variables: list[str] | None = None,
    locale: str = "ar",
    version: str = "1.0",
    db: Session = Depends(get_db),
):
    service = NotificationService(db)
    template = service.create_template(
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
def list_templates(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    service = NotificationService(db)
    templates = service.list_templates(skip=skip, limit=limit)
    return [t.to_dict() for t in templates]


@router.get("/queue/{recipient_id}")
def get_queue(
    recipient_id: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    service = NotificationService(db)
    notifications = service.get_queue_for_recipient(
        recipient_id=recipient_id,
        skip=skip,
        limit=limit,
    )
    return [n.to_dict() for n in notifications]


@router.post("/queue/{queue_id}/read")
def mark_read(
    queue_id: str,
    db: Session = Depends(get_db),
):
    service = NotificationService(db)
    notification = service.mark_read(queue_id)
    if not notification:
        return {"error": "not_found"}
    return {"queue_id": notification.queue_id, "status": notification.status}


@router.get("/preferences/{recipient_id}")
def get_preferences(
    recipient_id: str,
    db: Session = Depends(get_db),
):
    service = NotificationService(db)
    preferences = service.get_preferences(recipient_id)
    return [p.to_dict() for p in preferences]


@router.put("/preferences/{recipient_id}")
def update_preferences(
    recipient_id: str,
    category: str,
    channel: str,
    enabled: bool,
    recipient_type: str = "person",
    quiet_hours_start: str | None = None,
    quiet_hours_end: str | None = None,
    db: Session = Depends(get_db),
):
    service = NotificationService(db)
    preference = service.update_preferences(
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
def send_template_notification(
    template_id: str,
    recipient_id: str,
    context: dict[str, Any] | None = None,
    priority: str = "medium",
    recipient_type: str = "person",
    scheduled_at: datetime | None = None,
    db: Session = Depends(get_db),
):
    service = NotificationService(db)
    notification = service.send_template(
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
def mark_notification_sent(
    queue_id: str,
    db: Session = Depends(get_db),
):
    service = NotificationService(db)
    notification = service.mark_sent(queue_id)
    if not notification:
        return {"error": "not_found"}
    return {"queue_id": notification.queue_id, "status": notification.status}


@router.post("/queue/{queue_id}/delivered")
def mark_notification_delivered(
    queue_id: str,
    db: Session = Depends(get_db),
):
    service = NotificationService(db)
    notification = service.mark_delivered(queue_id)
    if not notification:
        return {"error": "not_found"}
    return {"queue_id": notification.queue_id, "status": notification.status}


@router.get("/pending")
def get_pending_notifications(
    limit: int = 50,
    db: Session = Depends(get_db),
):
    service = NotificationService(db)
    notifications = service.get_pending(limit=limit)
    return [n.to_dict() for n in notifications]
