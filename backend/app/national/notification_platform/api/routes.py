from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.national.notification_platform.application.service import NotificationPlatformService
from app.national.notification_platform.domain.entities import (
    Notification,
    NotificationTemplate,
)
from app.national.notification_platform.domain.enums import (
    NotificationCategory,
    NotificationChannel,
    NotificationPriority,
    TemplateEngine,
)
from app.national.notification_platform.exceptions import (
    ChannelNotAvailableError,
    NotificationNotFoundError,
    QuietHoursBlockedError,
    RateLimitExceededError,
    RecipientNotSpecifiedError,
    TemplateNotFoundError,
    TemplateRenderError,
)
from app.national.notification_platform.infrastructure.repository import (
    SQLAlchemyDeliveryReportRepository,
    SQLAlchemyNotificationBatchRepository,
    SQLAlchemyNotificationPreferenceRepository,
    SQLAlchemyNotificationRepository,
    SQLAlchemyNotificationTemplateRepository,
)
from app.security.dependencies import get_current_user

router = APIRouter(
    prefix="/national/notifications",
    tags=["National Notifications"],
    dependencies=[Depends(get_current_user)],
)


class SendRequest(BaseModel):
    channel: str
    recipients: list[str]
    subject: str = ""
    body: str = ""
    template_id: str | None = None
    template_data: dict[str, Any] | None = None
    priority: str = "medium"
    category: str = "system"
    scheduled_at: str | None = None
    correlation_id: str | None = None
    created_by: str | None = None
    metadata: dict[str, Any] | None = None


class BatchSendRequest(BaseModel):
    batch_key: str
    notifications: list[SendRequest]
    created_by: str | None = None


class TemplateCreateRequest(BaseModel):
    name: str
    description: str = ""
    channel: str = "email"
    language: str = "ar"
    subject_template: str = ""
    body_template: str = ""
    template_engine: str = "jinja2"
    variables: list[str] | None = None
    category: str = "system"
    created_by: str | None = None


class TemplateUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    subject_template: str | None = None
    body_template: str | None = None
    language: str | None = None
    variables: list[str] | None = None


class PreferenceUpdateRequest(BaseModel):
    user_id: str
    channel: str
    enabled: bool | None = None
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    max_daily: int | None = None
    categories_opt_in: list[str] | None = None
    categories_opt_out: list[str] | None = None


class ScheduleRequest(BaseModel):
    notification_id: str
    scheduled_at: str
    timezone: str = "UTC"
    recurring: bool = False
    cron_expression: str | None = None
    recurring_end_at: str | None = None


def _get_service(db: Session = Depends(get_db)) -> NotificationPlatformService:
    return NotificationPlatformService(
        notification_repo=SQLAlchemyNotificationRepository(db),
        template_repo=SQLAlchemyNotificationTemplateRepository(db),
        delivery_repo=SQLAlchemyDeliveryReportRepository(db),
        preference_repo=SQLAlchemyNotificationPreferenceRepository(db),
        batch_repo=SQLAlchemyNotificationBatchRepository(db),
    )


def _notification_to_dict(n: Notification) -> dict[str, Any]:
    return {
        "id": n.id,
        "channel": n.channel.value,
        "recipients": n.recipients,
        "subject": n.subject,
        "body": n.body,
        "template_id": n.template_id,
        "priority": n.priority.value,
        "category": n.category.value,
        "status": n.status.value,
        "scheduled_at": n.scheduled_at.isoformat() if n.scheduled_at else None,
        "sent_at": n.sent_at.isoformat() if n.sent_at else None,
        "delivered_at": n.delivered_at.isoformat() if n.delivered_at else None,
        "read_at": n.read_at.isoformat() if n.read_at else None,
        "failed_at": n.failed_at.isoformat() if n.failed_at else None,
        "error_message": n.error_message,
        "correlation_id": n.correlation_id,
        "created_by": n.created_by,
        "created_at": n.created_at.isoformat() if n.created_at else None,
    }


def _template_to_dict(t: NotificationTemplate) -> dict[str, Any]:
    return {
        "id": t.id,
        "name": t.name,
        "description": t.description,
        "channel": t.channel.value,
        "language": t.language,
        "template_engine": t.template_engine.value,
        "variables": t.variables,
        "category": t.category.value,
        "created_by": t.created_by,
        "version": t.version,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


@router.post(
    "/send",
    status_code=status.HTTP_201_CREATED,
    operation_id="send_notification_national_notifications_send_post",
    summary="Send Notification",
)
async def send_platform_notification(
    body: SendRequest,
    service: NotificationPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        scheduled_at: datetime | None = None
        if body.scheduled_at:
            scheduled_at = datetime.fromisoformat(body.scheduled_at)

        notification = await service.send(
            channel=NotificationChannel(body.channel),
            recipients=body.recipients,
            subject=body.subject,
            body=body.body,
            template_id=body.template_id,
            template_data=body.template_data,
            priority=NotificationPriority(body.priority)
            if body.priority
            else NotificationPriority.MEDIUM,
            category=NotificationCategory(body.category)
            if body.category
            else NotificationCategory.SYSTEM,
            scheduled_at=scheduled_at,
            correlation_id=body.correlation_id,
            created_by=body.created_by,
            metadata=body.metadata,
        )
        return _notification_to_dict(notification)
    except ChannelNotAvailableError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request",
        ) from e
    except RecipientNotSpecifiedError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Validation error",
        ) from e
    except QuietHoursBlockedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied") from e
    except RateLimitExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests",
        ) from e
    except TemplateNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e
    except TemplateRenderError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Validation error",
        ) from e


@router.post("/send/batch", status_code=status.HTTP_201_CREATED)
async def send_batch(
    body: BatchSendRequest,
    service: NotificationPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    notifications: list[Notification] = []
    for req in body.notifications:
        scheduled_at: datetime | None = None
        if req.scheduled_at:
            scheduled_at = datetime.fromisoformat(req.scheduled_at)
        notifications.append(
            Notification(
                id="",
                channel=NotificationChannel(req.channel),
                recipients=req.recipients,
                subject=req.subject,
                body=req.body,
                template_id=req.template_id,
                template_data=req.template_data,
                priority=NotificationPriority(req.priority),
                category=NotificationCategory(req.category),
                scheduled_at=scheduled_at,
                correlation_id=req.correlation_id,
                metadata=req.metadata,
            ),
        )

    batch = await service.send_batch(
        batch_key=body.batch_key,
        notifications=notifications,
        created_by=body.created_by,
    )
    return {
        "id": batch.id,
        "batch_key": batch.batch_key,
        "total_count": batch.total_count,
        "status": batch.status.value,
        "notification_ids": batch.notifications,
    }


@router.get("/")
async def list_notifications(
    status: str | None = Query(None),
    channel: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: NotificationPlatformService = Depends(_get_service),
) -> list[dict[str, Any]]:
    filters: dict[str, Any] = {}
    if status:
        filters["status"] = status
    if channel:
        filters["channel"] = channel
    notifications = await service.list_notifications(skip=skip, limit=limit, **filters)
    return [_notification_to_dict(n) for n in notifications]


@router.get("/dashboard")
async def get_dashboard(
    service: NotificationPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    return await service.get_stats()


@router.get("/{notification_id}")
async def get_notification(
    notification_id: str,
    service: NotificationPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        notification = await service.get_notification(notification_id)
        return _notification_to_dict(notification)
    except NotificationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e


@router.delete("/{notification_id}", status_code=status.HTTP_200_OK)
async def cancel_notification(
    notification_id: str,
    service: NotificationPlatformService = Depends(_get_service),
) -> dict[str, str]:
    try:
        await service.cancel(notification_id)
        return {"status": "cancelled", "id": notification_id}
    except NotificationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource conflict") from e


@router.post("/templates", status_code=status.HTTP_201_CREATED)
async def create_template(
    body: TemplateCreateRequest,
    service: NotificationPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    template = await service.create_template(
        name=body.name,
        channel=NotificationChannel(body.channel),
        subject_template=body.subject_template,
        body_template=body.body_template,
        template_engine=TemplateEngine(body.template_engine)
        if body.template_engine
        else TemplateEngine.JINJA2,
        description=body.description,
        language=body.language,
        variables=body.variables,
        category=NotificationCategory(body.category)
        if body.category
        else NotificationCategory.SYSTEM,
        created_by=body.created_by,
    )
    return _template_to_dict(template)


@router.get("/templates")
async def list_templates(
    channel: str | None = Query(None),
    category: str | None = Query(None),
    language: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: NotificationPlatformService = Depends(_get_service),
) -> list[dict[str, Any]]:
    filters: dict[str, Any] = {}
    if channel:
        filters["channel"] = channel
    if category:
        filters["category"] = category
    if language:
        filters["language"] = language
    templates = await service.list_templates(skip=skip, limit=limit, **filters)
    return [_template_to_dict(t) for t in templates]


@router.get("/templates/{template_id}")
async def get_template(
    template_id: str,
    service: NotificationPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        template = await service.get_template(template_id)
        return _template_to_dict(template)
    except TemplateNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e


@router.put("/templates/{template_id}")
async def update_template(
    template_id: str,
    body: TemplateUpdateRequest,
    service: NotificationPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        template = await service.update_template(
            template_id=template_id,
            name=body.name,
            description=body.description,
            subject_template=body.subject_template,
            body_template=body.body_template,
            language=body.language,
            variables=body.variables,
        )
        return _template_to_dict(template)
    except TemplateNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: str,
    service: NotificationPlatformService = Depends(_get_service),
) -> None:
    try:
        await service.delete_template(template_id)
    except TemplateNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e


@router.post("/templates/{template_id}/render")
async def render_template(
    template_id: str,
    body: dict[str, Any],
    service: NotificationPlatformService = Depends(_get_service),
) -> dict[str, str]:
    try:
        channel = NotificationChannel(body.pop("channel", "email"))
        data = body.pop("data", body)
        subject, rendered = await service.render_template(template_id, channel, data)
        return {"subject": subject, "body": rendered}
    except TemplateNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e
    except TemplateRenderError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Validation error",
        ) from e


@router.get("/delivery/{notification_id}")
async def get_delivery_report(
    notification_id: str,
    service: NotificationPlatformService = Depends(_get_service),
) -> list[dict[str, Any]]:
    try:
        reports = await service.get_delivery_report(notification_id)
        return [
            {
                "id": r.id,
                "notification_id": r.notification_id,
                "provider_status": r.provider_status,
                "provider_message_id": r.provider_message_id,
                "status": r.status.value,
                "attempted_at": r.attempted_at.isoformat() if r.attempted_at else None,
                "delivered_at": r.delivered_at.isoformat() if r.delivered_at else None,
                "error_message": r.error_message,
                "attempt": r.attempt,
            }
            for r in reports
        ]
    except NotificationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e


@router.get("/preferences")
async def get_preferences(
    user_id: str = Query(..., description="User ID to fetch preferences for"),
    service: NotificationPlatformService = Depends(_get_service),
) -> list[dict[str, Any]]:
    prefs = await service.get_preferences(user_id)
    return [
        {
            "user_id": p.user_id,
            "channel": p.channel.value,
            "enabled": p.enabled,
            "quiet_hours_start": p.quiet_hours_start,
            "quiet_hours_end": p.quiet_hours_end,
            "max_daily": p.max_daily,
            "categories_opt_in": [c.value for c in (p.categories_opt_in or [])],
            "categories_opt_out": [c.value for c in (p.categories_opt_out or [])],
        }
        for p in prefs
    ]


@router.put("/preferences")
async def update_preferences(
    body: PreferenceUpdateRequest,
    service: NotificationPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    categories_opt_in: list[NotificationCategory] | None = None
    categories_opt_out: list[NotificationCategory] | None = None
    if body.categories_opt_in is not None:
        categories_opt_in = [NotificationCategory(c) for c in body.categories_opt_in]
    if body.categories_opt_out is not None:
        categories_opt_out = [NotificationCategory(c) for c in body.categories_opt_out]

    pref = await service.update_preferences(
        user_id=body.user_id,
        channel=NotificationChannel(body.channel),
        enabled=body.enabled,
        quiet_hours_start=body.quiet_hours_start,
        quiet_hours_end=body.quiet_hours_end,
        max_daily=body.max_daily,
        categories_opt_in=categories_opt_in,
        categories_opt_out=categories_opt_out,
    )
    return {
        "user_id": pref.user_id,
        "channel": pref.channel.value,
        "enabled": pref.enabled,
        "quiet_hours_start": pref.quiet_hours_start,
        "quiet_hours_end": pref.quiet_hours_end,
        "max_daily": pref.max_daily,
        "categories_opt_in": [c.value for c in (pref.categories_opt_in or [])],
        "categories_opt_out": [c.value for c in (pref.categories_opt_out or [])],
    }


@router.get("/channels")
async def list_channels() -> list[dict[str, Any]]:
    return [
        {
            "channel": c.value,
            "name": c.name,
        }
        for c in NotificationChannel
    ]


@router.get("/stats")
async def get_stats(
    from_date: str | None = Query(None),
    to_date: str | None = Query(None),
    service: NotificationPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    from_dt: datetime | None = None
    to_dt: datetime | None = None
    if from_date:
        from_dt = datetime.fromisoformat(from_date)
    if to_date:
        to_dt = datetime.fromisoformat(to_date)
    return await service.get_stats(from_date=from_dt, to_date=to_dt)


@router.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "module": "national_notification_platform", "version": "1.0.0"}


@router.post("/schedules", status_code=status.HTTP_201_CREATED)
async def schedule_notification(
    body: ScheduleRequest,
    service: NotificationPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        scheduled_at = datetime.fromisoformat(body.scheduled_at)
        recurring_end_at: datetime | None = None
        if body.recurring_end_at:
            recurring_end_at = datetime.fromisoformat(body.recurring_end_at)

        schedule = await service.schedule_notification(
            notification_id=body.notification_id,
            scheduled_at=scheduled_at,
            timezone=body.timezone,
            recurring=body.recurring,
            cron_expression=body.cron_expression,
            recurring_end_at=recurring_end_at,
        )
        return {
            "id": schedule.id,
            "notification_id": schedule.notification_id,
            "scheduled_at": schedule.scheduled_at.isoformat() if schedule.scheduled_at else None,
            "timezone": schedule.timezone,
            "recurring": schedule.recurring,
            "cron_expression": schedule.cron_expression,
        }
    except NotificationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e


@router.get("/schedules")
async def list_schedules(
    service: NotificationPlatformService = Depends(_get_service),
) -> list[dict[str, Any]]:
    notifications = await service.list_notifications(limit=1000)
    schedules = []
    for n in notifications:
        if n.scheduled_at:
            schedules.append(
                {
                    "notification_id": n.id,
                    "channel": n.channel.value,
                    "recipients": n.recipients,
                    "status": n.status.value,
                    "scheduled_at": n.scheduled_at.isoformat() if n.scheduled_at else None,
                    "created_at": n.created_at.isoformat() if n.created_at else None,
                },
            )
    return schedules
