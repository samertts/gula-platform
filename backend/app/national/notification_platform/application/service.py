from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.national.notification_platform.application.interfaces import (
    EmailAdapter,
    FaxAdapter,
    GovernmentGatewayAdapter,
    InAppAdapter,
    NotificationChannelAdapter,
    PushAdapter,
    SendResult,
    SMSAdapter,
    TelegramAdapter,
    WebhookAdapter,
    WebSocketAdapter,
    WhatsAppAdapter,
)
from app.national.notification_platform.domain.entities import (
    DeliveryReport,
    Notification,
    NotificationBatch,
    NotificationPreference,
    NotificationSchedule,
    NotificationTemplate,
)
from app.national.notification_platform.domain.enums import (
    DeliveryReportStatus,
    NotificationCategory,
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
    TemplateEngine,
)
from app.national.notification_platform.domain.repository import (
    DeliveryReportRepository,
    NotificationBatchRepository,
    NotificationPreferenceRepository,
    NotificationRepository,
    NotificationTemplateRepository,
)
from app.national.notification_platform.exceptions import (
    SCHEDULING_UNAVAILABLE_REASON,
    NotificationSchedulingUnavailable,
    ChannelNotAvailableError,
    NotificationNotFoundError,
    QuietHoursBlockedError,
    RecipientNotSpecifiedError,
    TemplateNotFoundError,
    TemplateRenderError,
)
from app.notifications import NotificationService
from app.notifications import get_service as get_notification_service
from app.tasks.queue import task_queue
from app.tasks.schema import TaskPayload

logger = logging.getLogger("gula.national.notification_platform.service")


def _now() -> datetime:
    return datetime.now(UTC)


def _ulid() -> str:
    return str(uuid.uuid4()).replace("-", "").upper()[:26]


_CHANNEL_REGISTRY: dict[NotificationChannel, type[NotificationChannelAdapter]] = {
    NotificationChannel.EMAIL: EmailAdapter,
    NotificationChannel.SMS: SMSAdapter,
    NotificationChannel.PUSH: PushAdapter,
    NotificationChannel.WEBSOCKET: WebSocketAdapter,
    NotificationChannel.IN_APP: InAppAdapter,
    NotificationChannel.WHATSAPP: WhatsAppAdapter,
    NotificationChannel.TELEGRAM: TelegramAdapter,
    NotificationChannel.GOVERNMENT_GATEWAY: GovernmentGatewayAdapter,
    NotificationChannel.WEBHOOK: WebhookAdapter,
    NotificationChannel.FAX: FaxAdapter,
}


class NotificationPlatformService:

    def __init__(
        self,
        notification_repo: NotificationRepository,
        template_repo: NotificationTemplateRepository,
        delivery_repo: DeliveryReportRepository,
        preference_repo: NotificationPreferenceRepository,
        batch_repo: NotificationBatchRepository,
        legacy_service: NotificationService | None = None,
    ) -> None:
        self._notification_repo = notification_repo
        self._template_repo = template_repo
        self._delivery_repo = delivery_repo
        self._preference_repo = preference_repo
        self._batch_repo = batch_repo
        self._legacy_service = legacy_service or get_notification_service()

    def _get_adapter(self, channel: NotificationChannel) -> NotificationChannelAdapter:
        adapter_cls = _CHANNEL_REGISTRY.get(channel)
        if adapter_cls is None:
            raise ChannelNotAvailableError(channel.value)
        return adapter_cls()

    async def send(
        self,
        channel: NotificationChannel,
        recipients: list[str],
        subject: str = "",
        body: str = "",
        template_id: str | None = None,
        template_data: dict[str, Any] | None = None,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        category: NotificationCategory = NotificationCategory.SYSTEM,
        scheduled_at: datetime | None = None,
        correlation_id: str | None = None,
        created_by: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Notification:
        if not recipients:
            raise RecipientNotSpecifiedError()

        for recipient in recipients:
            await self._check_preferences(recipient, channel, category)

        rendered_subject, rendered_body = subject, body
        if template_id:
            rendered_subject, rendered_body = await self.render_template(
                template_id, channel, template_data or {},
            )

        notification_id = _ulid()
        notification = Notification(
            id=notification_id,
            channel=channel,
            recipients=recipients,
            subject=rendered_subject,
            body=rendered_body,
            template_id=template_id,
            template_data=template_data,
            priority=priority,
            category=category,
            status=NotificationStatus.QUEUED if scheduled_at else NotificationStatus.PENDING,
            scheduled_at=scheduled_at,
            correlation_id=correlation_id,
            created_by=created_by,
            metadata=metadata,
        )

        await self._notification_repo.save(notification)

        if scheduled_at:
            notification.status = NotificationStatus.QUEUED
            await self._notification_repo.save(notification)
            return notification

        await self._dispatch(notification)
        return notification

    async def send_batch(
        self,
        batch_key: str,
        notifications: list[Notification],
        created_by: str | None = None,
    ) -> NotificationBatch:
        saved_ids: list[str] = []
        for n in notifications:
            if not n.id:
                n.id = _ulid()
            await self._notification_repo.save(n)
            saved_ids.append(n.id)

        batch = NotificationBatch(
            id=_ulid(),
            batch_key=batch_key,
            notifications=saved_ids,
            status=NotificationStatus.PENDING,
            total_count=len(saved_ids),
            created_by=created_by,
        )
        await self._batch_repo.save(batch)

        for n_id in saved_ids:
            await task_queue.enqueue(
                TaskPayload(
                    type="national_notification_deliver",
                    payload={"notification_id": n_id, "batch_id": batch.id},
                ),
            )

        return batch

    async def create_template(
        self,
        name: str,
        channel: NotificationChannel,
        subject_template: str,
        body_template: str,
        template_engine: TemplateEngine = TemplateEngine.JINJA2,
        description: str = "",
        language: str = "ar",
        variables: list[str] | None = None,
        category: NotificationCategory = NotificationCategory.SYSTEM,
        created_by: str | None = None,
    ) -> NotificationTemplate:
        template = NotificationTemplate(
            id=_ulid(),
            name=name,
            description=description,
            channel=channel,
            language=language,
            subject_template=subject_template,
            body_template=body_template,
            template_engine=template_engine,
            variables=variables or [],
            category=category,
            created_by=created_by,
        )
        return await self._template_repo.save(template)


    async def render_template(
        self,
        template_id: str,
        channel: NotificationChannel,
        data: dict[str, Any],
    ) -> tuple[str, str]:
        template = await self._template_repo.get(template_id)
        if template is None:
            raise TemplateNotFoundError(template_id)

        try:
            if template.template_engine == TemplateEngine.JINJA2:
                from jinja2 import Template

                subject_t = Template(template.subject_template) if template.subject_template else None
                body_t = Template(template.body_template) if template.body_template else None
            elif template.template_engine == TemplateEngine.MUSTACHE:
                import chevron

                subject_str = chevron.render(template.subject_template, data) if template.subject_template else ""
                body_str = chevron.render(template.body_template, data) if template.body_template else ""
                return subject_str, body_str
            else:
                subject_t = None
                body_t = None

            rendered_subject = subject_t.render(**data) if subject_t else template.subject_template

            rendered_body = body_t.render(**data) if body_t else template.body_template

            return rendered_subject, rendered_body
        except Exception as exc:
            raise TemplateRenderError(template_id, str(exc)) from exc

    async def get_delivery_report(self, notification_id: str) -> list[DeliveryReport]:
        notification = await self._notification_repo.get(notification_id)
        if notification is None:
            raise NotificationNotFoundError(notification_id)
        return await self._delivery_repo.find_by_notification(notification_id)

    async def update_preferences(
        self,
        user_id: str,
        channel: NotificationChannel,
        enabled: bool | None = None,
        quiet_hours_start: str | None = None,
        quiet_hours_end: str | None = None,
        max_daily: int | None = None,
        categories_opt_in: list[NotificationCategory] | None = None,
        categories_opt_out: list[NotificationCategory] | None = None,
    ) -> NotificationPreference:
        existing = await self._preference_repo.find_by_user_and_channel(user_id, channel)
        if existing:
            if enabled is not None:
                existing.enabled = enabled
            if quiet_hours_start is not None:
                existing.quiet_hours_start = quiet_hours_start
            if quiet_hours_end is not None:
                existing.quiet_hours_end = quiet_hours_end
            if max_daily is not None:
                existing.max_daily = max_daily
            if categories_opt_in is not None:
                existing.categories_opt_in = categories_opt_in
            if categories_opt_out is not None:
                existing.categories_opt_out = categories_opt_out
            return await self._preference_repo.save(existing)

        pref = NotificationPreference(
            user_id=user_id,
            channel=channel,
            enabled=enabled if enabled is not None else True,
            quiet_hours_start=quiet_hours_start,
            quiet_hours_end=quiet_hours_end,
            max_daily=max_daily or 50,
            categories_opt_in=categories_opt_in or [],
            categories_opt_out=categories_opt_out or [],
        )
        return await self._preference_repo.save(pref)

    async def schedule_notification(
        self,
        notification_id: str,
        scheduled_at: datetime,
        timezone: str = "UTC",
        recurring: bool = False,
        cron_expression: str | None = None,
        recurring_end_at: datetime | None = None,
    ) -> NotificationSchedule:
        notification = await self._notification_repo.get(notification_id)
        if notification is None:
            raise NotificationNotFoundError(notification_id)

        schedule = NotificationSchedule(
            id=_ulid(),
            notification_id=notification_id,
            scheduled_at=scheduled_at,
            timezone=timezone,
            recurring=recurring,
            cron_expression=cron_expression,
            recurring_end_at=recurring_end_at,
        )

        # IA-080. ``delay_s`` was computed here and then used only as the
        # task's ``timeout_s``, which is a timeout, not a delay. TaskPayload
        # carries no delay, run_at or eta field and TaskQueue.enqueue accepts
        # none, so the delivery task ran immediately with an inflated timeout
        # while the persisted NotificationSchedule row said otherwise, and the
        # route answered 201 echoing the future date back to the caller.
        #
        # Nothing reads these rows either: the only reader of
        # NotificationSchedule is the GET /schedules listing.
        # ``find_due_schedules`` belongs to background_platform and a different
        # repository, so no poller would pick a future schedule up even if the
        # task were withheld.
        #
        # A future schedule is therefore refused and named rather than
        # delivered now under a schedule the platform cannot honour. Building
        # the missing primitive would mean choosing retry, visibility and
        # recurrence semantics for a clinical notification path, which is not a
        # decision to make while passing through.
        if scheduled_at > _now():
            raise NotificationSchedulingUnavailable(
                f"cannot schedule notification {notification_id} for "
                f"{scheduled_at.isoformat()}: {SCHEDULING_UNAVAILABLE_REASON}",
            )
        if recurring or cron_expression:
            raise NotificationSchedulingUnavailable(
                f"cannot schedule a recurring notification "
                f"(recurring={recurring}, cron={cron_expression!r}): "
                f"{SCHEDULING_UNAVAILABLE_REASON}",
            )

        notification.status = NotificationStatus.QUEUED
        notification.scheduled_at = scheduled_at
        await self._notification_repo.save(notification)

        await task_queue.enqueue(
            TaskPayload(
                type="national_notification_deliver",
                payload={"notification_id": notification_id, "scheduled": True},
            ),
        )

        return schedule

    async def cancel(self, notification_id: str) -> Notification:
        notification = await self._notification_repo.get(notification_id)
        if notification is None:
            raise NotificationNotFoundError(notification_id)

        if notification.status in (NotificationStatus.SENT, NotificationStatus.DELIVERED):
            raise ValueError(f"Cannot cancel notification in status {notification.status.value}")

        notification.status = NotificationStatus.CANCELLED
        await self._notification_repo.save(notification)
        return notification

    async def _dispatch(self, notification: Notification) -> Notification:
        success_count = 0
        failure_count = 0
        errors: list[str] = []

        for recipient in notification.recipients:
            result = await self._send_single(notification, recipient)
            if result.success:
                success_count += 1
            else:
                failure_count += 1
                if result.error:
                    errors.append(result.error)

        if success_count == len(notification.recipients):
            notification.status = NotificationStatus.SENT
            notification.sent_at = _now()
        elif success_count > 0:
            notification.status = NotificationStatus.SENT
            notification.sent_at = _now()
            notification.error_message = "; ".join(errors[:5])
        else:
            notification.status = NotificationStatus.FAILED
            notification.failed_at = _now()
            notification.error_message = "; ".join(errors[:5])

        await self._notification_repo.save(notification)
        return notification

    async def _send_single(
        self,
        notification: Notification,
        recipient: str,
    ) -> SendResult:
        adapter = self._get_adapter(notification.channel)
        result = await adapter.send(
            recipient=recipient,
            subject=notification.subject,
            body=notification.body,
            metadata=notification.metadata,
        )

        report = DeliveryReport(
            id=_ulid(),
            notification_id=notification.id,
            provider_status="sent" if result.success else "failed",
            provider_message_id=result.provider_message_id,
            provider_response=result.provider_response,
            status=DeliveryReportStatus.SENT_TO_PROVIDER if result.success else DeliveryReportStatus.FAILED_TEMPORARY,
            attempted_at=_now(),
            error_message=result.error,
        )
        await self._delivery_repo.save(report)

        return result

    async def dispatch_scheduled(self, notification_id: str) -> None:
        notification = await self._notification_repo.get(notification_id)
        if notification is None:
            raise NotificationNotFoundError(notification_id)

        if notification.status != NotificationStatus.QUEUED:
            logger.warning("Skipping dispatch of %s — status is %s", notification_id, notification.status)
            return

        await self._dispatch(notification)

    async def _check_preferences(
        self,
        user_id: str,
        channel: NotificationChannel,
        category: NotificationCategory,
    ) -> None:
        pref = await self._preference_repo.find_by_user_and_channel(user_id, channel)
        if pref is None:
            return

        if not pref.enabled:
            raise ChannelNotAvailableError(channel.value)

        if pref.quiet_hours_start and pref.quiet_hours_end:
            now_str = _now().strftime("%H:%M")
            if pref.quiet_hours_start <= now_str <= pref.quiet_hours_end:
                raise QuietHoursBlockedError(channel.value, user_id)

        if pref.categories_opt_out and category in pref.categories_opt_out:
            raise ChannelNotAvailableError(f"{channel.value} (opt-out for {category.value})")

        if pref.categories_opt_in and category not in pref.categories_opt_in:
            raise ChannelNotAvailableError(f"{channel.value} (not opted-in for {category.value})")

    async def get_stats(
        self,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> dict[str, Any]:
        return await self._notification_repo.get_stats(from_date=from_date, to_date=to_date)

    async def get_notification(self, notification_id: str) -> Notification:
        notification = await self._notification_repo.get(notification_id)
        if notification is None:
            raise NotificationNotFoundError(notification_id)
        return notification

    async def list_notifications(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[Notification]:
        return await self._notification_repo.list(skip=skip, limit=limit, **filters)

    async def list_templates(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[NotificationTemplate]:
        return await self._template_repo.list(skip=skip, limit=limit, **filters)

    async def get_template(self, template_id: str) -> NotificationTemplate:
        template = await self._template_repo.get(template_id)
        if template is None:
            raise TemplateNotFoundError(template_id)
        return template

    async def update_template(
        self,
        template_id: str,
        name: str | None = None,
        description: str | None = None,
        subject_template: str | None = None,
        body_template: str | None = None,
        language: str | None = None,
        variables: list[str] | None = None,
    ) -> NotificationTemplate:
        template = await self._template_repo.get(template_id)
        if template is None:
            raise TemplateNotFoundError(template_id)

        if name is not None:
            template.name = name
        if description is not None:
            template.description = description
        if subject_template is not None:
            template.subject_template = subject_template
        if body_template is not None:
            template.body_template = body_template
        if language is not None:
            template.language = language
        if variables is not None:
            template.variables = variables

        template.version += 1
        template.updated_at = _now()
        return await self._template_repo.save(template)

    async def delete_template(self, template_id: str) -> None:
        template = await self._template_repo.get(template_id)
        if template is None:
            raise TemplateNotFoundError(template_id)
        await self._template_repo.delete(template_id)

    async def get_preferences(self, user_id: str) -> list[NotificationPreference]:
        return await self._preference_repo.find_by_user(user_id)

    async def mark_read(self, notification_id: str, user_id: str) -> Notification:
        notification = await self._notification_repo.get(notification_id)
        if notification is None:
            raise NotificationNotFoundError(notification_id)

        notification.status = NotificationStatus.READ
        notification.read_at = _now()
        await self._notification_repo.save(notification)
        return notification

    async def mark_delivered(self, notification_id: str) -> Notification:
        notification = await self._notification_repo.get(notification_id)
        if notification is None:
            raise NotificationNotFoundError(notification_id)

        notification.status = NotificationStatus.DELIVERED
        notification.delivered_at = _now()
        await self._notification_repo.save(notification)
        return notification


from app.tasks.registry import task_handler


@task_handler("national_notification_deliver")
async def handle_national_notification_deliver(payload: dict) -> dict:
    from app.database import SessionLocal
    from app.national.notification_platform.infrastructure.repository import (
        SQLAlchemyDeliveryReportRepository,
        SQLAlchemyNotificationBatchRepository,
        SQLAlchemyNotificationPreferenceRepository,
        SQLAlchemyNotificationRepository,
        SQLAlchemyNotificationTemplateRepository,
    )

    notification_id = payload.get("notification_id", "")
    batch_id = payload.get("batch_id")

    db = SessionLocal()
    try:
        notification_repo = SQLAlchemyNotificationRepository(db)
        batch_repo = SQLAlchemyNotificationBatchRepository(db)

        service = NotificationPlatformService(
            notification_repo=notification_repo,
            template_repo=SQLAlchemyNotificationTemplateRepository(db),
            delivery_repo=SQLAlchemyDeliveryReportRepository(db),
            preference_repo=SQLAlchemyNotificationPreferenceRepository(db),
            batch_repo=batch_repo,
        )

        notification = await service.get_notification(notification_id)
        await service._dispatch(notification)

        if batch_id:
            batch = await batch_repo.get(batch_id)
            if batch:
                all_notifications = [
                    await notification_repo.get(nid) or None
                    for nid in batch.notifications
                ]
                sent = sum(1 for n in all_notifications if n and n.status == NotificationStatus.SENT)
                failed = sum(1 for n in all_notifications if n and n.status == NotificationStatus.FAILED)
                batch.success_count = sent
                batch.failure_count = failed
                if sent + failed == batch.total_count:
                    batch.status = NotificationStatus.DELIVERED if failed == 0 else NotificationStatus.FAILED
                    batch.completed_at = _now()
                await batch_repo.save(batch)

        return {"delivered": True, "notification_id": notification_id}
    except Exception as exc:
        logger.error("Task handler failed for %s: %s", notification_id, exc)
        return {"delivered": False, "error": str(exc)}
    finally:
        db.close()
