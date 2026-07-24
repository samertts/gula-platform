from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app._compat import UTC

from .models import NotificationPreference, NotificationQueue, NotificationTemplate


class NotificationService:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def send_notification(
        self,
        recipient_id: str,
        notification_type: str,
        channel: str,
        subject: str | None = None,
        body: str | None = None,
        context: dict[str, Any] | None = None,
        priority: str = "medium",
        recipient_type: str = "person",
        scheduled_at: datetime | None = None,
    ) -> NotificationQueue:
        queue_id = str(uuid.uuid4()).replace("-", "").upper()[:26]
        now = datetime.now(UTC)

        notification = NotificationQueue(
            id=...,
            uuid=str(uuid.uuid4()),
            queue_id=queue_id,
            recipient_id=recipient_id,
            recipient_type=recipient_type,
            notification_type=notification_type,
            channel=channel,
            template_id=None,
            subject=subject,
            body=body,
            context=context or {},
            priority=priority,
            status="queued",
            sent_at=None,
            delivered_at=None,
            read_at=None,
            error_count=0,
            max_retries=3,
            last_error=None,
            scheduled_at=scheduled_at or now,
            is_active=True,
        )
        self.session.add(notification)
        await self.session.flush()
        return notification

    async def send_template(
        self,
        template_id: str,
        recipient_id: str,
        context: dict[str, Any] | None = None,
        priority: str = "medium",
        recipient_type: str = "person",
        scheduled_at: datetime | None = None,
    ) -> NotificationQueue | None:
        stmt = select(NotificationTemplate).where(
            NotificationTemplate.template_id == template_id,
            NotificationTemplate.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        template = result.scalar_one_or_none()
        if not template:
            return None

        rendered_subject = template.subject
        rendered_body = template.body
        if context:
            for key, val in context.items():
                placeholder = "{{" + key + "}}"
                if rendered_subject:
                    rendered_subject = rendered_subject.replace(placeholder, str(val))
                rendered_body = rendered_body.replace(placeholder, str(val))

        queue_id = str(uuid.uuid4()).replace("-", "").upper()[:26]
        now = datetime.now(UTC)

        notification = NotificationQueue(
            id=...,
            uuid=str(uuid.uuid4()),
            queue_id=queue_id,
            recipient_id=recipient_id,
            recipient_type=recipient_type,
            notification_type=template.notification_type,
            channel=template.notification_type,
            template_id=template_id,
            subject=rendered_subject,
            body=rendered_body,
            context=context or {},
            priority=priority,
            status="queued",
            sent_at=None,
            delivered_at=None,
            read_at=None,
            error_count=0,
            max_retries=3,
            last_error=None,
            scheduled_at=scheduled_at or now,
            is_active=True,
        )
        self.session.add(notification)
        await self.session.flush()
        return notification

    async def mark_sent(self, queue_id: str) -> NotificationQueue | None:
        stmt = select(NotificationQueue).where(
            NotificationQueue.queue_id == queue_id,
        )
        result = await self.session.execute(stmt)
        notification = result.scalar_one_or_none()
        if not notification:
            return None
        notification.status = "sent"
        notification.sent_at = datetime.now(UTC)
        await self.session.flush()
        return notification

    async def mark_delivered(self, queue_id: str) -> NotificationQueue | None:
        stmt = select(NotificationQueue).where(
            NotificationQueue.queue_id == queue_id,
        )
        result = await self.session.execute(stmt)
        notification = result.scalar_one_or_none()
        if not notification:
            return None
        notification.status = "delivered"
        notification.delivered_at = datetime.now(UTC)
        await self.session.flush()
        return notification

    async def mark_read(self, queue_id: str) -> NotificationQueue | None:
        stmt = select(NotificationQueue).where(
            NotificationQueue.queue_id == queue_id,
        )
        result = await self.session.execute(stmt)
        notification = result.scalar_one_or_none()
        if not notification:
            return None
        notification.status = "read"
        notification.read_at = datetime.now(UTC)
        await self.session.flush()
        return notification

    async def get_pending(self, limit: int = 50) -> list[NotificationQueue]:
        stmt = (
            select(NotificationQueue)
            .where(
                NotificationQueue.status == "queued",
                NotificationQueue.is_active.is_(True),
            )
            .order_by(NotificationQueue.priority.asc(), NotificationQueue.scheduled_at)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_preferences(
        self,
        recipient_id: str,
    ) -> list[NotificationPreference]:
        stmt = select(NotificationPreference).where(
            NotificationPreference.recipient_id == recipient_id,
            NotificationPreference.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_preferences(
        self,
        recipient_id: str,
        category: str,
        channel: str,
        enabled: bool,
        recipient_type: str = "person",
        quiet_hours_start: str | None = None,
        quiet_hours_end: str | None = None,
    ) -> NotificationPreference:
        stmt = select(NotificationPreference).where(
            NotificationPreference.recipient_id == recipient_id,
            NotificationPreference.category == category,
            NotificationPreference.channel == channel,
            NotificationPreference.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        preference = result.scalar_one_or_none()

        if preference:
            preference.enabled = enabled
            if quiet_hours_start is not None:
                preference.quiet_hours_start = quiet_hours_start
            if quiet_hours_end is not None:
                preference.quiet_hours_end = quiet_hours_end
        else:
            preference_id = str(uuid.uuid4()).replace("-", "").upper()[:26]
            preference = NotificationPreference(
                id=...,
                uuid=str(uuid.uuid4()),
                preference_id=preference_id,
                recipient_id=recipient_id,
                recipient_type=recipient_type,
                category=category,
                channel=channel,
                enabled=enabled,
                quiet_hours_start=quiet_hours_start,
                quiet_hours_end=quiet_hours_end,
                is_active=True,
            )
            self.session.add(preference)

        await self.session.flush()
        return preference

    async def create_template(
        self,
        template_id: str,
        name: str,
        notification_type: str,
        body: str,
        subject: str | None = None,
        variables: list[str] | None = None,
        locale: str = "ar",
        version: str = "1.0",
    ) -> NotificationTemplate:
        template = NotificationTemplate(
            id=...,
            uuid=str(uuid.uuid4()),
            template_id=template_id,
            name=name,
            notification_type=notification_type,
            subject=subject,
            body=body,
            variables=variables or [],
            locale=locale,
            version=version,
            is_active=False,
        )
        self.session.add(template)
        await self.session.flush()
        return template

    async def list_templates(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[NotificationTemplate]:
        stmt = (
            select(NotificationTemplate)
            .order_by(NotificationTemplate.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_queue_for_recipient(
        self,
        recipient_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> list[NotificationQueue]:
        stmt = (
            select(NotificationQueue)
            .where(
                NotificationQueue.recipient_id == recipient_id,
                NotificationQueue.is_active.is_(True),
            )
            .order_by(NotificationQueue.scheduled_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
