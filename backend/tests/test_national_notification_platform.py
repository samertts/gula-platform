from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pytest

from app._compat import UTC
from app.national.notification_platform.application.service import NotificationPlatformService
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
from app.national.notification_platform.exceptions import (
    ChannelNotAvailableError,
    NotificationNotFoundError,
    QuietHoursBlockedError,
    RecipientNotSpecifiedError,
    TemplateNotFoundError,
    TemplateRenderError,
)



def _now() -> datetime:
    return datetime.now(UTC)


def _ulid() -> str:
    import uuid
    return str(uuid.uuid4()).replace("-", "").upper()[:26]


# ── In-Memory Repository Implementations ──


class InMemoryNotificationRepo(NotificationRepository):
    def __init__(self):
        self._store: dict[str, Notification] = {}

    async def save(self, notification: Notification) -> Notification:
        self._store[notification.id] = notification
        return notification

    async def get(self, notification_id: str) -> Notification | None:
        return self._store.get(notification_id)

    async def list(self, skip: int = 0, limit: int = 100, **filters: Any) -> list[Notification]:
        items = list(self._store.values())
        for k, v in filters.items():
            if hasattr(v, "value"):
                items = [i for i in items if getattr(i, k, None) == v]
            elif v is not None:
                items = [i for i in items if getattr(i, k, None) == v]
        return items[skip:skip + limit]

    async def find_by_status(self, status: NotificationStatus, skip: int = 0, limit: int = 100) -> list[Notification]:
        return [n for n in self._store.values() if n.status == status][skip:skip + limit]

    async def find_by_channel(self, channel: NotificationChannel, skip: int = 0, limit: int = 100) -> list[Notification]:
        return [n for n in self._store.values() if n.channel == channel][skip:skip + limit]

    async def find_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> list[Notification]:
        return [n for n in self._store.values() if user_id in (n.recipients or [])][skip:skip + limit]

    async def find_by_correlation_id(self, correlation_id: str) -> list[Notification]:
        return [n for n in self._store.values() if n.correlation_id == correlation_id]

    async def count_by_status(self, status: NotificationStatus) -> int:
        return sum(1 for n in self._store.values() if n.status == status)

    async def count_by_channel(self, channel: NotificationChannel) -> int:
        return sum(1 for n in self._store.values() if n.channel == channel)

    async def get_stats(self, from_date: datetime | None = None, to_date: datetime | None = None) -> dict[str, Any]:
        items = self._store.values()
        if from_date:
            items = [n for n in items if n.created_at >= from_date]
        if to_date:
            items = [n for n in items if n.created_at <= to_date]
        return {"total": len(items)}


class InMemoryTemplateRepo(NotificationTemplateRepository):
    def __init__(self):
        self._store: dict[str, NotificationTemplate] = {}

    async def save(self, template: NotificationTemplate) -> NotificationTemplate:
        self._store[template.id] = template
        return template

    async def get(self, template_id: str) -> NotificationTemplate | None:
        return self._store.get(template_id)

    async def list(self, skip: int = 0, limit: int = 100, **filters: Any) -> list[NotificationTemplate]:
        items = list(self._store.values())
        for k, v in filters.items():
            if hasattr(v, "value"):
                items = [i for i in items if getattr(i, k, None) == v]
        return items[skip:skip + limit]

    async def find_by_channel(self, channel: NotificationChannel, skip: int = 0, limit: int = 100) -> list[NotificationTemplate]:
        return [t for t in self._store.values() if t.channel == channel][skip:skip + limit]

    async def find_by_category(self, category: NotificationCategory, skip: int = 0, limit: int = 100) -> list[NotificationTemplate]:
        return [t for t in self._store.values() if t.category == category][skip:skip + limit]

    async def find_by_language(self, language: str, skip: int = 0, limit: int = 100) -> list[NotificationTemplate]:
        return [t for t in self._store.values() if t.language == language][skip:skip + limit]

    async def delete(self, template_id: str) -> None:
        self._store.pop(template_id, None)


class InMemoryDeliveryRepo(DeliveryReportRepository):
    def __init__(self):
        self._store: dict[str, DeliveryReport] = {}

    async def save(self, report: DeliveryReport) -> DeliveryReport:
        self._store[report.id] = report
        return report

    async def get(self, report_id: str) -> DeliveryReport | None:
        return self._store.get(report_id)

    async def find_by_notification(self, notification_id: str) -> list[DeliveryReport]:
        return [r for r in self._store.values() if r.notification_id == notification_id]


class InMemoryPreferenceRepo(NotificationPreferenceRepository):
    def __init__(self):
        self._store: dict[str, NotificationPreference] = {}

    async def save(self, preference: NotificationPreference) -> NotificationPreference:
        key = f"{preference.user_id}:{preference.channel.value}"
        self._store[key] = preference
        return preference

    async def get(self, user_id: str, channel: NotificationChannel) -> NotificationPreference | None:
        return self._store.get(f"{user_id}:{channel.value}")

    async def find_by_user(self, user_id: str) -> list[NotificationPreference]:
        return [p for k, p in self._store.items() if k.startswith(f"{user_id}:")]

    async def find_by_user_and_channel(self, user_id: str, channel: NotificationChannel) -> NotificationPreference | None:
        return self._store.get(f"{user_id}:{channel.value}")


class InMemoryBatchRepo(NotificationBatchRepository):
    def __init__(self):
        self._store: dict[str, NotificationBatch] = {}

    async def save(self, batch: NotificationBatch) -> NotificationBatch:
        self._store[batch.id] = batch
        return batch

    async def get(self, batch_id: str) -> NotificationBatch | None:
        return self._store.get(batch_id)

    async def find_by_status(self, status: NotificationStatus, skip: int = 0, limit: int = 100) -> list[NotificationBatch]:
        return [b for b in self._store.values() if b.status == status][skip:skip + limit]


@pytest.fixture()
def repos():
    return {
        "notification": InMemoryNotificationRepo(),
        "template": InMemoryTemplateRepo(),
        "delivery": InMemoryDeliveryRepo(),
        "preference": InMemoryPreferenceRepo(),
        "batch": InMemoryBatchRepo(),
    }


@pytest.fixture()
def svc(repos):
    return NotificationPlatformService(
        notification_repo=repos["notification"],
        template_repo=repos["template"],
        delivery_repo=repos["delivery"],
        preference_repo=repos["preference"],
        batch_repo=repos["batch"],
        legacy_service=None,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Domain Entity Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestNotificationEntity:
    def test_create_minimal(self):
        n = Notification(id="n1", channel=NotificationChannel.EMAIL, recipients=["a@b.com"])
        assert n.status == NotificationStatus.PENDING
        assert n.priority == NotificationPriority.MEDIUM
        assert n.category == NotificationCategory.SYSTEM

    def test_create_full(self):
        n = Notification(
            id="n1", channel=NotificationChannel.SMS, recipients=["+964700000000"],
            subject="Test", body="Hello", priority=NotificationPriority.HIGH,
            category=NotificationCategory.LAB_RESULT, status=NotificationStatus.SENT,
            correlation_id="corr-1", created_by="user-1",
        )
        assert n.status == NotificationStatus.SENT
        assert n.priority == NotificationPriority.HIGH
        assert n.category == NotificationCategory.LAB_RESULT

    def test_status_transitions(self):
        n = Notification(id="n1", channel=NotificationChannel.EMAIL, recipients=["a@b.com"])
        n.status = NotificationStatus.QUEUED
        n.status = NotificationStatus.SENT
        n.sent_at = _now()
        n.status = NotificationStatus.DELIVERED
        n.delivered_at = _now()
        n.status = NotificationStatus.READ
        n.read_at = _now()
        assert n.read_at is not None
        assert n.delivered_at is not None


class TestNotificationTemplateEntity:
    def test_create(self):
        t = NotificationTemplate(
            id="t1", name="Welcome", channel=NotificationChannel.EMAIL,
            subject_template="Hello {{name}}", body_template="Welcome {{name}}!",
        )
        assert t.version == 1
        assert t.template_engine == TemplateEngine.JINJA2
        assert t.language == "ar"

    def test_version_increments_on_update(self):
        t = NotificationTemplate(id="t1", name="Test", channel=NotificationChannel.SMS,
                                  subject_template="Hi", body_template="Body")
        t.version += 1
        assert t.version == 2


class TestDeliveryReportEntity:
    def test_create(self):
        r = DeliveryReport(
            id="r1", notification_id="n1",
            status=DeliveryReportStatus.SENT_TO_PROVIDER,
        )
        assert r.attempt == 1
        assert r.status == DeliveryReportStatus.SENT_TO_PROVIDER


class TestNotificationPreferenceEntity:
    def test_create(self):
        p = NotificationPreference(
            user_id="u1", channel=NotificationChannel.EMAIL, enabled=True,
        )
        assert p.max_daily == 50
        assert p.enabled is True

    def test_opt_out_category(self):
        p = NotificationPreference(
            user_id="u1", channel=NotificationChannel.SMS, enabled=True,
            categories_opt_out=[NotificationCategory.PROMOTIONAL],
        )
        assert NotificationCategory.PROMOTIONAL in (p.categories_opt_out or [])


class TestNotificationBatchEntity:
    def test_create(self):
        b = NotificationBatch(id="b1", batch_key="batch-1", notifications=["n1", "n2"],
                               total_count=2)
        assert b.total_count == 2
        assert b.status == NotificationStatus.PENDING
        assert b.success_count == 0
        assert b.failure_count == 0


# ═══════════════════════════════════════════════════════════════════════════════
# NotificationPlatformService Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestSend:
    @pytest.mark.asyncio
    async def test_send_basic(self, svc):
        n = await svc.send(
            channel=NotificationChannel.EMAIL,
            recipients=["user@example.com"],
            subject="Hello", body="World",
        )
        assert n.id is not None
        assert n.channel == NotificationChannel.EMAIL
        assert n.subject == "Hello"
        assert n.body == "World"
        assert n.status == NotificationStatus.SENT

    @pytest.mark.asyncio
    async def test_send_multiple_recipients(self, svc):
        n = await svc.send(
            channel=NotificationChannel.SMS,
            recipients=["+964700000001", "+964700000002"],
            body="Alert",
        )
        assert len(n.recipients) == 2
        assert n.status == NotificationStatus.SENT

    @pytest.mark.asyncio
    async def test_send_empty_recipients_raises(self, svc):
        with pytest.raises(RecipientNotSpecifiedError):
            await svc.send(channel=NotificationChannel.EMAIL, recipients=[])

    @pytest.mark.asyncio
    async def test_send_scheduled(self, svc):
        future = _now() + timedelta(hours=1)
        n = await svc.send(
            channel=NotificationChannel.EMAIL,
            recipients=["user@example.com"],
            subject="Scheduled",
            scheduled_at=future,
        )
        assert n.status == NotificationStatus.QUEUED
        assert n.scheduled_at is not None

    @pytest.mark.asyncio
    async def test_send_with_template(self, svc, repos):
        template = await repos["template"].save(NotificationTemplate(
            id=_ulid(), name="Test Template", channel=NotificationChannel.EMAIL,
            subject_template="Hello {{name}}", body_template="Welcome {{name}}!",
        ))
        n = await svc.send(
            channel=NotificationChannel.EMAIL,
            recipients=["user@example.com"],
            template_id=template.id,
            template_data={"name": "Ali"},
        )
        assert "Ali" in n.subject
        assert "Ali" in n.body

    @pytest.mark.asyncio
    async def test_send_invalid_template_raises(self, svc):
        with pytest.raises(TemplateNotFoundError):
            await svc.send(
                channel=NotificationChannel.EMAIL,
                recipients=["user@example.com"],
                template_id="nonexistent",
                template_data={"name": "Test"},
            )

    @pytest.mark.asyncio
    async def test_send_via_all_channels(self, svc):
        for channel in NotificationChannel:
            extra = {}
            if channel == NotificationChannel.TELEGRAM:
                extra["metadata"] = {"bot_token": "test:token"}
            n = await svc.send(
                channel=channel,
                recipients=["test@example.com"],
                subject=f"Test via {channel.value}",
                body="OK",
                **extra,
            )
            assert n.channel == channel
            assert n.status in (NotificationStatus.SENT, NotificationStatus.FAILED)

    @pytest.mark.asyncio
    async def test_send_with_correlation_id(self, svc):
        n = await svc.send(
            channel=NotificationChannel.EMAIL,
            recipients=["a@b.com"],
            correlation_id="order-123",
        )
        found = await svc._notification_repo.find_by_correlation_id("order-123")
        assert len(found) == 1
        assert found[0].id == n.id

    @pytest.mark.asyncio
    async def test_send_with_metadata(self, svc):
        n = await svc.send(
            channel=NotificationChannel.EMAIL,
            recipients=["a@b.com"],
            metadata={"source": "test", "version": 1},
        )
        assert n.metadata == {"source": "test", "version": 1}

    @pytest.mark.asyncio
    async def test_send_with_priority(self, svc):
        for p in NotificationPriority:
            n = await svc.send(
                channel=NotificationChannel.EMAIL,
                recipients=["a@b.com"],
                priority=p,
            )
            assert n.priority == p

    @pytest.mark.asyncio
    async def test_send_with_category(self, svc):
        for c in NotificationCategory:
            n = await svc.send(
                channel=NotificationChannel.EMAIL,
                recipients=["a@b.com"],
                category=c,
            )
            assert n.category == c


class TestSendBatch:
    @pytest.mark.asyncio
    async def test_send_batch(self, svc):
        notifications = [
            Notification(id=_ulid(), channel=NotificationChannel.EMAIL, recipients=["a@b.com"], subject="A"),
            Notification(id=_ulid(), channel=NotificationChannel.SMS, recipients=["+964000"], body="B"),
        ]
        batch = await svc.send_batch("batch-key", notifications)
        assert batch.batch_key == "batch-key"
        assert batch.total_count == 2
        assert len(batch.notifications) == 2

    @pytest.mark.asyncio
    async def test_send_batch_ids_generated(self, svc):
        notifications = [
            Notification(id="", channel=NotificationChannel.EMAIL, recipients=["a@b.com"]),
        ]
        batch = await svc.send_batch("auto-id", notifications)
        assert len(batch.notifications) == 1
        assert batch.notifications[0] != ""


class TestTemplates:
    @pytest.mark.asyncio
    async def test_create_template(self, svc):
        t = await svc.create_template(
            name="Welcome Email", channel=NotificationChannel.EMAIL,
            subject_template="Hello {{name}}", body_template="Welcome!",
        )
        assert t.id is not None
        assert t.name == "Welcome Email"

    @pytest.mark.asyncio
    async def test_render_jinja2(self, svc, repos):
        t = await repos["template"].save(NotificationTemplate(
            id=_ulid(), name="J", channel=NotificationChannel.EMAIL,
            subject_template="Hi {{user}}", body_template="Body: {{msg}}",
            template_engine=TemplateEngine.JINJA2,
        ))
        subject, body = await svc.render_template(t.id, NotificationChannel.EMAIL, {"user": "Ali", "msg": "Test"})
        assert subject == "Hi Ali"
        assert body == "Body: Test"

    @pytest.mark.asyncio
    async def test_render_mustache(self, svc, repos):
        t = await repos["template"].save(NotificationTemplate(
            id=_ulid(), name="M", channel=NotificationChannel.EMAIL,
            subject_template="Hi {{user}}", body_template="Body: {{msg}}",
            template_engine=TemplateEngine.MUSTACHE,
        ))
        subject, body = await svc.render_template(t.id, NotificationChannel.EMAIL, {"user": "Ali", "msg": "Test"})
        assert "Hi Ali" in subject
        assert "Body: Test" in body

    @pytest.mark.asyncio
    async def test_render_nonexistent_template_raises(self, svc):
        with pytest.raises(TemplateNotFoundError):
            await svc.render_template("no-such-id", NotificationChannel.EMAIL, {})

    @pytest.mark.asyncio
    async def test_render_invalid_template_raises(self, svc, repos):
        t = await repos["template"].save(NotificationTemplate(
            id=_ulid(), name="Bad", channel=NotificationChannel.EMAIL,
            subject_template="{{ broken", body_template="x",
            template_engine=TemplateEngine.JINJA2,
        ))
        with pytest.raises(TemplateRenderError):
            await svc.render_template(t.id, NotificationChannel.EMAIL, {})

    @pytest.mark.asyncio
    async def test_list_templates(self, svc, repos):
        await repos["template"].save(NotificationTemplate(id=_ulid(), name="A", channel=NotificationChannel.EMAIL,
                                                           subject_template="a", body_template="b"))
        await repos["template"].save(NotificationTemplate(id=_ulid(), name="B", channel=NotificationChannel.SMS,
                                                           subject_template="c", body_template="d"))
        all_t = await svc.list_templates()
        assert len(all_t) == 2

    @pytest.mark.asyncio
    async def test_get_template(self, svc, repos):
        t = await repos["template"].save(NotificationTemplate(id=_ulid(), name="GetMe",
                                                               channel=NotificationChannel.EMAIL,
                                                               subject_template="s", body_template="b"))
        found = await svc.get_template(t.id)
        assert found.name == "GetMe"

    @pytest.mark.asyncio
    async def test_get_nonexistent_template_raises(self, svc):
        with pytest.raises(TemplateNotFoundError):
            await svc.get_template("missing")

    @pytest.mark.asyncio
    async def test_update_template(self, svc, repos):
        t = await repos["template"].save(NotificationTemplate(id=_ulid(), name="Old", channel=NotificationChannel.EMAIL,
                                                               subject_template="s", body_template="b"))
        updated = await svc.update_template(t.id, name="New", subject_template="updated")
        assert updated.name == "New"
        assert updated.subject_template == "updated"
        assert updated.version == 2

    @pytest.mark.asyncio
    async def test_delete_template(self, svc, repos):
        t = await repos["template"].save(NotificationTemplate(id=_ulid(), name="Del", channel=NotificationChannel.EMAIL,
                                                               subject_template="s", body_template="b"))
        await svc.delete_template(t.id)
        with pytest.raises(TemplateNotFoundError):
            await svc.get_template(t.id)


class TestPreferences:
    @pytest.mark.asyncio
    async def test_update_preferences_create(self, svc):
        pref = await svc.update_preferences(
            user_id="user-1", channel=NotificationChannel.EMAIL,
            enabled=True, max_daily=20,
        )
        assert pref.user_id == "user-1"
        assert pref.channel == NotificationChannel.EMAIL
        assert pref.max_daily == 20

    @pytest.mark.asyncio
    async def test_update_preferences_modify(self, svc):
        await svc.update_preferences(user_id="user-1", channel=NotificationChannel.EMAIL, enabled=True)
        pref = await svc.update_preferences(
            user_id="user-1", channel=NotificationChannel.EMAIL,
            enabled=False, max_daily=10,
        )
        assert pref.enabled is False
        assert pref.max_daily == 10

    @pytest.mark.asyncio
    async def test_get_preferences(self, svc):
        await svc.update_preferences(user_id="u1", channel=NotificationChannel.EMAIL, enabled=True)
        await svc.update_preferences(user_id="u1", channel=NotificationChannel.SMS, enabled=False)
        prefs = await svc.get_preferences("u1")
        assert len(prefs) == 2

    @pytest.mark.asyncio
    async def test_quiet_hours_blocks_send(self, svc, repos):
        pref = NotificationPreference(
            user_id="u-qh", channel=NotificationChannel.EMAIL,
            enabled=True, quiet_hours_start="08:00", quiet_hours_end="18:00",
        )
        await repos["preference"].save(pref)
        with pytest.raises(QuietHoursBlockedError):
            await svc.send(
                channel=NotificationChannel.EMAIL,
                recipients=["u-qh"],
                subject="During quiet hours",
            )

    @pytest.mark.asyncio
    async def test_opt_out_category(self, svc, repos):
        pref = NotificationPreference(
            user_id="u-optout", channel=NotificationChannel.EMAIL,
            enabled=True, categories_opt_out=[NotificationCategory.PROMOTIONAL],
        )
        await repos["preference"].save(pref)
        with pytest.raises(ChannelNotAvailableError):
            await svc.send(
                channel=NotificationChannel.EMAIL, recipients=["u-optout"],
                category=NotificationCategory.PROMOTIONAL,
            )

    @pytest.mark.asyncio
    async def test_opt_in_required(self, svc, repos):
        pref = NotificationPreference(
            user_id="u-optin", channel=NotificationChannel.SMS,
            enabled=True, categories_opt_in=[NotificationCategory.ALERT],
        )
        await repos["preference"].save(pref)
        with pytest.raises(ChannelNotAvailableError):
            await svc.send(
                channel=NotificationChannel.SMS, recipients=["u-optin"],
                category=NotificationCategory.PROMOTIONAL,
            )

    @pytest.mark.asyncio
    async def test_disabled_channel_blocks(self, svc, repos):
        pref = NotificationPreference(
            user_id="u-disabled", channel=NotificationChannel.PUSH,
            enabled=False,
        )
        await repos["preference"].save(pref)
        with pytest.raises(ChannelNotAvailableError):
            await svc.send(
                channel=NotificationChannel.PUSH, recipients=["u-disabled"],
            )


class TestDeliveryReports:
    @pytest.mark.asyncio
    async def test_get_delivery_reports(self, svc, repos):
        n = await svc.send(channel=NotificationChannel.EMAIL, recipients=["a@b.com"])
        reports = await svc.get_delivery_report(n.id)
        assert len(reports) >= 1

    @pytest.mark.asyncio
    async def test_get_delivery_report_nonexistent(self, svc):
        with pytest.raises(NotificationNotFoundError):
            await svc.get_delivery_report("no-such-id")


class TestLifecycle:
    @pytest.mark.asyncio
    async def test_cancel_queued(self, svc):
        future = _now() + timedelta(days=1)
        n = await svc.send(channel=NotificationChannel.EMAIL, recipients=["a@b.com"],
                            subject="Cancel me", scheduled_at=future)
        assert n.status == NotificationStatus.QUEUED
        cancelled = await svc.cancel(n.id)
        assert cancelled.status == NotificationStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_scheduled(self, svc):
        future = _now() + timedelta(days=1)
        n = await svc.send(channel=NotificationChannel.EMAIL, recipients=["a@b.com"],
                            scheduled_at=future)
        assert n.status == NotificationStatus.QUEUED
        cancelled = await svc.cancel(n.id)
        assert cancelled.status == NotificationStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_raises(self, svc):
        with pytest.raises(NotificationNotFoundError):
            await svc.cancel("missing")

    @pytest.mark.asyncio
    async def test_mark_read(self, svc):
        n = await svc.send(channel=NotificationChannel.EMAIL, recipients=["a@b.com"])
        read = await svc.mark_read(n.id, "user-1")
        assert read.status == NotificationStatus.READ
        assert read.read_at is not None

    @pytest.mark.asyncio
    async def test_mark_delivered(self, svc):
        n = await svc.send(channel=NotificationChannel.EMAIL, recipients=["a@b.com"])
        delivered = await svc.mark_delivered(n.id)
        assert delivered.status == NotificationStatus.DELIVERED
        assert delivered.delivered_at is not None

    @pytest.mark.asyncio
    async def test_get_notification(self, svc):
        n = await svc.send(channel=NotificationChannel.EMAIL, recipients=["a@b.com"])
        found = await svc.get_notification(n.id)
        assert found.id == n.id

    @pytest.mark.asyncio
    async def test_get_nonexistent_notification_raises(self, svc):
        with pytest.raises(NotificationNotFoundError):
            await svc.get_notification("missing")

    @pytest.mark.asyncio
    async def test_list_notifications(self, svc):
        await svc.send(channel=NotificationChannel.EMAIL, recipients=["a@b.com"])
        await svc.send(channel=NotificationChannel.SMS, recipients=["+964000"])
        all_n = await svc.list_notifications()
        assert len(all_n) >= 2

    @pytest.mark.asyncio
    async def test_list_notifications_filtered(self, svc):
        await svc.send(channel=NotificationChannel.EMAIL, recipients=["a@b.com"], category=NotificationCategory.ALERT)
        await svc.send(channel=NotificationChannel.SMS, recipients=["+964000"], category=NotificationCategory.SYSTEM)
        alerts = await svc.list_notifications(category=NotificationCategory.ALERT)
        assert all(n.category == NotificationCategory.ALERT for n in alerts)


class TestSchedule:
    @pytest.mark.asyncio
    async def test_schedule_notification(self, svc):
        future = _now() + timedelta(hours=2)
        n = await svc.send(channel=NotificationChannel.EMAIL, recipients=["a@b.com"])
        schedule = await svc.schedule_notification(n.id, future, timezone="Asia/Baghdad")
        assert schedule.timezone == "Asia/Baghdad"
        assert schedule.recurring is False

    @pytest.mark.asyncio
    async def test_schedule_nonexistent_raises(self, svc):
        with pytest.raises(NotificationNotFoundError):
            await svc.schedule_notification("missing", _now())


class TestStats:
    @pytest.mark.asyncio
    async def test_get_stats(self, svc):
        await svc.send(channel=NotificationChannel.EMAIL, recipients=["a@b.com"])
        stats = await svc.get_stats()
        assert stats["total"] >= 1



