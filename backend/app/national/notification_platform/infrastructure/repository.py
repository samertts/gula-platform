from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.national.notification_platform.domain.entities import (
    DeliveryReport,
    Notification,
    NotificationBatch,
    NotificationPreference,
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
from app.national.notification_platform.infrastructure.models import (
    NationalDeliveryReportModel,
    NationalNotificationBatchModel,
    NationalNotificationModel,
    NationalNotificationPreferenceModel,
    NationalNotificationTemplateModel,
)
from sqlalchemy import func
from sqlalchemy.orm import Session


def _ulid() -> str:
    return str(uuid.uuid4()).replace("-", "").upper()[:26]


def _model_to_notification(m: NationalNotificationModel) -> Notification:
    return Notification(
        id=m.id,
        channel=NotificationChannel(m.channel),
        recipients=m.recipients or [m.recipient or ""],
        subject=m.subject or "",
        body=m.body or "",
        template_id=m.template_id,
        template_data=m.template_data,
        priority=NotificationPriority(m.priority) if m.priority else NotificationPriority.MEDIUM,
        category=NotificationCategory(m.category) if m.category else NotificationCategory.SYSTEM,
        status=NotificationStatus(m.status) if m.status else NotificationStatus.PENDING,
        scheduled_at=m.scheduled_at,
        sent_at=m.sent_at,
        delivered_at=m.delivered_at,
        read_at=m.read_at,
        failed_at=m.failed_at,
        error_message=m.error_message,
        metadata=m.metadata,
        correlation_id=m.correlation_id,
        created_by=m.created_by,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _notification_to_model(m: NationalNotificationModel, e: Notification) -> NationalNotificationModel:
    m.id = e.id
    m.channel = e.channel.value
    m.recipient = e.recipients[0] if e.recipients else ""
    m.recipients = e.recipients
    m.subject = e.subject
    m.body = e.body
    m.template_id = e.template_id
    m.template_data = e.template_data
    m.priority = e.priority.value
    m.category = e.category.value
    m.status = e.status.value
    m.scheduled_at = e.scheduled_at
    m.sent_at = e.sent_at
    m.delivered_at = e.delivered_at
    m.read_at = e.read_at
    m.failed_at = e.failed_at
    m.error_message = e.error_message
    m.metadata = e.metadata
    m.correlation_id = e.correlation_id
    m.created_by = e.created_by
    m.created_at = e.created_at
    m.updated_at = e.updated_at
    return m


def _model_to_template(m: NationalNotificationTemplateModel) -> NotificationTemplate:
    return NotificationTemplate(
        id=m.id,
        name=m.name,
        description=m.description or "",
        channel=NotificationChannel(m.channel) if m.channel else NotificationChannel.EMAIL,
        language=m.language,
        subject_template=m.subject_template or "",
        body_template=m.body_template or "",
        template_engine=TemplateEngine(m.template_engine) if m.template_engine else TemplateEngine.JINJA2,
        variables=m.variables,
        category=NotificationCategory(m.category) if m.category else NotificationCategory.SYSTEM,
        created_by=m.created_by,
        created_at=m.created_at,
        updated_at=m.updated_at,
        version=m.version,
    )


def _model_to_delivery(m: NationalDeliveryReportModel) -> DeliveryReport:
    return DeliveryReport(
        id=m.id,
        notification_id=m.notification_id,
        provider_status=m.provider_status,
        provider_message_id=m.provider_message_id,
        provider_response=m.provider_response,
        status=DeliveryReportStatus(m.status) if m.status else DeliveryReportStatus.SENT_TO_PROVIDER,
        attempted_at=m.attempted_at,
        delivered_at=m.delivered_at,
        error_message=m.error_message,
        attempt=m.attempt,
    )


def _model_to_preference(m: NationalNotificationPreferenceModel) -> NotificationPreference:
    return NotificationPreference(
        user_id=m.user_id,
        channel=NotificationChannel(m.channel) if m.channel else NotificationChannel.EMAIL,
        enabled=m.enabled,
        quiet_hours_start=m.quiet_hours_start,
        quiet_hours_end=m.quiet_hours_end,
        max_daily=m.max_daily,
        categories_opt_in=[NotificationCategory(c) for c in (m.categories_opt_in or [])] if m.categories_opt_in else [],
        categories_opt_out=[NotificationCategory(c) for c in (m.categories_opt_out or [])] if m.categories_opt_out else [],
    )


def _model_to_batch(m: NationalNotificationBatchModel) -> NotificationBatch:
    return NotificationBatch(
        id=m.id,
        batch_key=m.batch_key,
        notifications=m.notification_ids or [],
        status=NotificationStatus(m.status) if m.status else NotificationStatus.PENDING,
        total_count=m.total_count,
        success_count=m.success_count,
        failure_count=m.failure_count,
        created_at=m.created_at,
        completed_at=m.completed_at,
    )


class SQLAlchemyNotificationRepository(NotificationRepository):

    def __init__(self, db: Session) -> None:
        self._db = db

    async def save(self, notification: Notification) -> Notification:
        existing = self._db.query(NationalNotificationModel).filter_by(id=notification.id).first()
        if existing:
            m = _notification_to_model(existing, notification)
        else:
            m = NationalNotificationModel()
            _notification_to_model(m, notification)
            self._db.add(m)
        self._db.commit()
        self._db.refresh(m)
        return _model_to_notification(m)

    async def get(self, notification_id: str) -> Notification | None:
        m = self._db.query(NationalNotificationModel).filter_by(id=notification_id).first()
        if m is None:
            return None
        return _model_to_notification(m)

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[Notification]:
        q = self._db.query(NationalNotificationModel)
        for key, val in filters.items():
            if hasattr(NationalNotificationModel, key):
                q = q.filter(getattr(NationalNotificationModel, key) == val)
        rows = q.order_by(NationalNotificationModel.created_at.desc()).offset(skip).limit(limit).all()
        return [_model_to_notification(r) for r in rows]

    async def find_by_status(
        self,
        status: NotificationStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Notification]:
        rows = (
            self._db.query(NationalNotificationModel)
            .filter_by(status=status.value)
            .order_by(NationalNotificationModel.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [_model_to_notification(r) for r in rows]

    async def find_by_channel(
        self,
        channel: NotificationChannel,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Notification]:
        rows = (
            self._db.query(NationalNotificationModel)
            .filter_by(channel=channel.value)
            .order_by(NationalNotificationModel.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [_model_to_notification(r) for r in rows]

    async def find_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Notification]:
        rows = (
            self._db.query(NationalNotificationModel)
            .filter_by(created_by=user_id)
            .order_by(NationalNotificationModel.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [_model_to_notification(r) for r in rows]

    async def find_by_correlation_id(
        self,
        correlation_id: str,
    ) -> list[Notification]:
        rows = (
            self._db.query(NationalNotificationModel)
            .filter_by(correlation_id=correlation_id)
            .order_by(NationalNotificationModel.created_at.desc())
            .all()
        )
        return [_model_to_notification(r) for r in rows]

    async def count_by_status(self, status: NotificationStatus) -> int:
        return self._db.query(NationalNotificationModel).filter_by(status=status.value).count()

    async def count_by_channel(self, channel: NotificationChannel) -> int:
        return self._db.query(NationalNotificationModel).filter_by(channel=channel.value).count()

    async def get_stats(
        self,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> dict[str, Any]:
        q = self._db.query(NationalNotificationModel)
        if from_date:
            q = q.filter(NationalNotificationModel.created_at >= from_date)
        if to_date:
            q = q.filter(NationalNotificationModel.created_at <= to_date)

        total = q.count()

        status_counts = (
            self._db.query(NationalNotificationModel.status, func.count(NationalNotificationModel.id))
            .group_by(NationalNotificationModel.status)
            .all()
        )

        channel_counts = (
            self._db.query(NationalNotificationModel.channel, func.count(NationalNotificationModel.id))
            .group_by(NationalNotificationModel.channel)
            .all()
        )

        return {
            "total": total,
            "by_status": dict(status_counts),
            "by_channel": dict(channel_counts),
        }


class SQLAlchemyNotificationTemplateRepository(NotificationTemplateRepository):

    def __init__(self, db: Session) -> None:
        self._db = db

    async def save(self, template: NotificationTemplate) -> NotificationTemplate:
        existing = self._db.query(NationalNotificationTemplateModel).filter_by(id=template.id).first()
        if existing:
            existing.name = template.name
            existing.description = template.description
            existing.channel = template.channel.value
            existing.language = template.language
            existing.subject_template = template.subject_template
            existing.body_template = template.body_template
            existing.template_engine = template.template_engine.value
            existing.variables = template.variables
            existing.category = template.category.value
            existing.created_by = template.created_by
            existing.version = template.version
            existing.updated_at = datetime.now(UTC)
            m = existing
        else:
            m = NationalNotificationTemplateModel(
                id=template.id,
                name=template.name,
                description=template.description,
                channel=template.channel.value,
                language=template.language,
                subject_template=template.subject_template,
                body_template=template.body_template,
                template_engine=template.template_engine.value,
                variables=template.variables,
                category=template.category.value,
                created_by=template.created_by,
                version=template.version,
            )
            self._db.add(m)
        self._db.commit()
        self._db.refresh(m)
        return _model_to_template(m)

    async def get(self, template_id: str) -> NotificationTemplate | None:
        m = self._db.query(NationalNotificationTemplateModel).filter_by(id=template_id).first()
        if m is None:
            return None
        return _model_to_template(m)

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[NotificationTemplate]:
        q = self._db.query(NationalNotificationTemplateModel)
        for key, val in filters.items():
            if hasattr(NationalNotificationTemplateModel, key):
                q = q.filter(getattr(NationalNotificationTemplateModel, key) == val)
        rows = q.order_by(NationalNotificationTemplateModel.created_at.desc()).offset(skip).limit(limit).all()
        return [_model_to_template(r) for r in rows]

    async def find_by_channel(
        self,
        channel: NotificationChannel,
        skip: int = 0,
        limit: int = 100,
    ) -> list[NotificationTemplate]:
        rows = (
            self._db.query(NationalNotificationTemplateModel)
            .filter_by(channel=channel.value)
            .order_by(NationalNotificationTemplateModel.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [_model_to_template(r) for r in rows]

    async def find_by_category(
        self,
        category: NotificationCategory,
        skip: int = 0,
        limit: int = 100,
    ) -> list[NotificationTemplate]:
        rows = (
            self._db.query(NationalNotificationTemplateModel)
            .filter_by(category=category.value)
            .order_by(NationalNotificationTemplateModel.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [_model_to_template(r) for r in rows]

    async def find_by_language(
        self,
        language: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[NotificationTemplate]:
        rows = (
            self._db.query(NationalNotificationTemplateModel)
            .filter_by(language=language)
            .order_by(NationalNotificationTemplateModel.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [_model_to_template(r) for r in rows]

    async def delete(self, template_id: str) -> None:
        self._db.query(NationalNotificationTemplateModel).filter_by(id=template_id).delete()
        self._db.commit()


class SQLAlchemyDeliveryReportRepository(DeliveryReportRepository):

    def __init__(self, db: Session) -> None:
        self._db = db

    async def save(self, report: DeliveryReport) -> DeliveryReport:
        m = NationalDeliveryReportModel(
            id=report.id or _ulid(),
            notification_id=report.notification_id,
            provider_status=report.provider_status,
            provider_message_id=report.provider_message_id,
            provider_response=report.provider_response,
            status=report.status.value,
            attempted_at=report.attempted_at,
            delivered_at=report.delivered_at,
            error_message=report.error_message,
            attempt=report.attempt,
        )
        self._db.add(m)
        self._db.commit()
        self._db.refresh(m)
        return _model_to_delivery(m)

    async def get(self, report_id: str) -> DeliveryReport | None:
        m = self._db.query(NationalDeliveryReportModel).filter_by(id=report_id).first()
        if m is None:
            return None
        return _model_to_delivery(m)

    async def find_by_notification(
        self,
        notification_id: str,
    ) -> list[DeliveryReport]:
        rows = (
            self._db.query(NationalDeliveryReportModel)
            .filter_by(notification_id=notification_id)
            .order_by(NationalDeliveryReportModel.attempted_at.desc())
            .all()
        )
        return [_model_to_delivery(r) for r in rows]


class SQLAlchemyNotificationPreferenceRepository(NotificationPreferenceRepository):

    def __init__(self, db: Session) -> None:
        self._db = db

    async def save(self, preference: NotificationPreference) -> NotificationPreference:
        existing = (
            self._db.query(NationalNotificationPreferenceModel)
            .filter_by(user_id=preference.user_id, channel=preference.channel.value)
            .first()
        )
        if existing:
            existing.enabled = preference.enabled
            existing.quiet_hours_start = preference.quiet_hours_start
            existing.quiet_hours_end = preference.quiet_hours_end
            existing.max_daily = preference.max_daily
            existing.categories_opt_in = [c.value for c in (preference.categories_opt_in or [])]
            existing.categories_opt_out = [c.value for c in (preference.categories_opt_out or [])]
            existing.updated_at = datetime.now(UTC)
            m = existing
        else:
            m = NationalNotificationPreferenceModel(
                id=_ulid(),
                user_id=preference.user_id,
                channel=preference.channel.value,
                enabled=preference.enabled,
                quiet_hours_start=preference.quiet_hours_start,
                quiet_hours_end=preference.quiet_hours_end,
                max_daily=preference.max_daily,
                categories_opt_in=[c.value for c in (preference.categories_opt_in or [])],
                categories_opt_out=[c.value for c in (preference.categories_opt_out or [])],
            )
            self._db.add(m)
        self._db.commit()
        self._db.refresh(m)
        return _model_to_preference(m)

    async def get(self, user_id: str, channel: NotificationChannel) -> NotificationPreference | None:
        m = (
            self._db.query(NationalNotificationPreferenceModel)
            .filter_by(user_id=user_id, channel=channel.value)
            .first()
        )
        if m is None:
            return None
        return _model_to_preference(m)

    async def find_by_user(self, user_id: str) -> list[NotificationPreference]:
        rows = (
            self._db.query(NationalNotificationPreferenceModel)
            .filter_by(user_id=user_id)
            .all()
        )
        return [_model_to_preference(r) for r in rows]

    async def find_by_user_and_channel(
        self,
        user_id: str,
        channel: NotificationChannel,
    ) -> NotificationPreference | None:
        return await self.get(user_id, channel)


class SQLAlchemyNotificationBatchRepository(NotificationBatchRepository):

    def __init__(self, db: Session) -> None:
        self._db = db

    async def save(self, batch: NotificationBatch) -> NotificationBatch:
        existing = self._db.query(NationalNotificationBatchModel).filter_by(id=batch.id).first()
        if existing:
            existing.status = batch.status.value
            existing.success_count = batch.success_count
            existing.failure_count = batch.failure_count
            existing.completed_at = batch.completed_at
            m = existing
        else:
            m = NationalNotificationBatchModel(
                id=batch.id,
                batch_key=batch.batch_key,
                notification_ids=batch.notifications,
                status=batch.status.value,
                total_count=batch.total_count,
                success_count=batch.success_count,
                failure_count=batch.failure_count,
                created_by=getattr(batch, "created_by", None),
            )
            self._db.add(m)
        self._db.commit()
        self._db.refresh(m)
        return _model_to_batch(m)

    async def get(self, batch_id: str) -> NotificationBatch | None:
        m = self._db.query(NationalNotificationBatchModel).filter_by(id=batch_id).first()
        if m is None:
            return None
        return _model_to_batch(m)

    async def find_by_status(
        self,
        status: NotificationStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> list[NotificationBatch]:
        rows = (
            self._db.query(NationalNotificationBatchModel)
            .filter_by(status=status.value)
            .order_by(NationalNotificationBatchModel.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [_model_to_batch(r) for r in rows]
