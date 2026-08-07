from __future__ import annotations

import asyncio
import importlib.util
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.identity.base import IdentityBaseEntity, _ensure_identity_id
from app.notifications.models import (
    NotificationPreference,
    NotificationQueue,
    NotificationTemplate,
)
from app.notifications.routes import router as notifications_router
from app.notifications.services import NotificationQueueService
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.execute = AsyncMock()
    session.execute.return_value = MagicMock()
    return session


class TestPromotedModels:
    """Regression: models moved to canonical app.notifications keep their
    identity base, table names, and the id=... Ellipsis resolution."""

    def test_canonical_import_paths(self):
        assert importlib.util.find_spec("app.notifications.models") is not None
        assert importlib.util.find_spec("app.notifications.services") is not None
        assert importlib.util.find_spec("app.notifications.routes") is not None

    def test_old_namespace_vacated(self):
        assert importlib.util.find_spec("app.identity.notifications") is None

    def test_table_names_unchanged(self):
        assert NotificationTemplate.__tablename__ == "niam_notif_templates"
        assert NotificationQueue.__tablename__ == "niam_notif_queue"
        assert NotificationPreference.__tablename__ == "niam_notif_preferences"

    def test_models_still_extend_identity_base(self):
        for cls in (NotificationTemplate, NotificationQueue, NotificationPreference):
            assert issubclass(cls, IdentityBaseEntity)

    def test_ellipsis_id_resolution_listener_applies(self):
        q = NotificationQueue(id=..., uuid=str(uuid.uuid4()), queue_id="Q-1")
        assert q.id is Ellipsis
        _ensure_identity_id(None, None, q)
        assert isinstance(q.id, str) and len(q.id) == 26

    def test_to_dict_serialization(self):
        q = NotificationQueue(
            id="id1",
            uuid=str(uuid.uuid4()),
            queue_id="Q-1",
            recipient_id="u1",
            status="queued",
        )
        d = q.to_dict()
        assert d["queue_id"] == "Q-1"
        assert d["status"] == "queued"


class TestQueueService:
    def test_class_renamed_and_importable(self):
        assert NotificationQueueService.__name__ == "NotificationQueueService"
        svc = NotificationQueueService(mock := MagicMock(spec=AsyncSession))
        assert svc.session is mock

    def test_send_notification_creates_queued_record(self, mock_session):
        svc = NotificationQueueService(mock_session)
        n = await_coro(svc.send_notification(
            recipient_id="u1",
            notification_type="lab_result",
            channel="email",
            subject="Result ready",
            body="Your result is ready",
            context={"lab": "L1"},
            priority="high",
        ))
        assert mock_session.add.called
        assert mock_session.flush.await_count == 1
        captured = mock_session.add.call_args.args[0]
        assert isinstance(captured, NotificationQueue)
        assert captured.status == "queued"
        assert captured.priority == "high"
        assert captured.max_retries == 3
        assert captured.template_id is None
        assert captured.queue_id == n.queue_id
        assert captured.queue_id.upper() == captured.queue_id
        assert captured.scheduled_at is not None

    def test_send_template_renders_placeholders(self, mock_session):
        template = NotificationTemplate(
            id="t1",
            uuid=str(uuid.uuid4()),
            template_id="TMP-LOGIN-ALERT",
            name="Login Alert",
            notification_type="email",
            subject="Hello {{name}}",
            body="Hi {{name}}, welcome",
            is_active=True,
        )
        mock_session.execute.return_value.scalar_one_or_none.return_value = template
        svc = NotificationQueueService(mock_session)
        result = await_coro(svc.send_template(
            template_id="TMP-LOGIN-ALERT",
            recipient_id="u1",
            context={"name": "Ali"},
        ))
        assert result is not None
        captured = mock_session.add.call_args.args[0]
        assert captured.subject == "Hello Ali"
        assert captured.body == "Hi Ali, welcome"
        assert captured.channel == "email"
        assert captured.template_id == "TMP-LOGIN-ALERT"

    def test_send_template_returns_none_when_missing(self, mock_session):
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        svc = NotificationQueueService(mock_session)
        result = await_coro(svc.send_template(template_id="NOPE", recipient_id="u1"))
        assert result is None

    def test_mark_sent(self, mock_session):
        q = NotificationQueue(id="id1", uuid=str(uuid.uuid4()), queue_id="Q-1")
        mock_session.execute.return_value.scalar_one_or_none.return_value = q
        svc = NotificationQueueService(mock_session)
        result = await_coro(svc.mark_sent("Q-1"))
        assert result.status == "sent"
        assert result.sent_at is not None

    def test_mark_delivered(self, mock_session):
        q = NotificationQueue(id="id1", uuid=str(uuid.uuid4()), queue_id="Q-1")
        mock_session.execute.return_value.scalar_one_or_none.return_value = q
        svc = NotificationQueueService(mock_session)
        result = await_coro(svc.mark_delivered("Q-1"))
        assert result.status == "delivered"
        assert result.delivered_at is not None

    def test_mark_read(self, mock_session):
        q = NotificationQueue(id="id1", uuid=str(uuid.uuid4()), queue_id="Q-1")
        mock_session.execute.return_value.scalar_one_or_none.return_value = q
        svc = NotificationQueueService(mock_session)
        result = await_coro(svc.mark_read("Q-1"))
        assert result.status == "read"
        assert result.read_at is not None

    def test_mark_not_found_returns_none(self, mock_session):
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        svc = NotificationQueueService(mock_session)
        assert await_coro(svc.mark_sent("NOPE")) is None

    def test_get_pending(self, mock_session):
        q = NotificationQueue(id="id1", uuid=str(uuid.uuid4()), queue_id="Q-1")
        mock_session.execute.return_value.scalars.return_value.all.return_value = [q]
        svc = NotificationQueueService(mock_session)
        result = await_coro(svc.get_pending(limit=10))
        assert result == [q]
        assert mock_session.execute.await_count == 1

    def test_get_preferences(self, mock_session):
        p = NotificationPreference(id="id1", uuid=str(uuid.uuid4()), preference_id="P-1")
        mock_session.execute.return_value.scalars.return_value.all.return_value = [p]
        svc = NotificationQueueService(mock_session)
        result = await_coro(svc.get_preferences("u1"))
        assert result == [p]

    def test_update_preferences_updates_existing(self, mock_session):
        p = NotificationPreference(
            id="id1",
            uuid=str(uuid.uuid4()),
            preference_id="P-1",
            recipient_id="u1",
            category="alerts",
            channel="email",
            enabled=True,
        )
        mock_session.execute.return_value.scalar_one_or_none.return_value = p
        svc = NotificationQueueService(mock_session)
        result = await_coro(svc.update_preferences("u1", "alerts", "email", enabled=False))
        assert result.enabled is False
        assert mock_session.add.call_count == 0

    def test_update_preferences_creates_when_missing(self, mock_session):
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        svc = NotificationQueueService(mock_session)
        result = await_coro(svc.update_preferences(
            "u1",
            "alerts",
            "sms",
            enabled=True,
            quiet_hours_start="22:00",
            quiet_hours_end="06:00",
        ))
        assert isinstance(result, NotificationPreference)
        assert result.enabled is True
        assert result.quiet_hours_start == "22:00"
        captured = mock_session.add.call_args.args[0]
        assert captured.preference_id == result.preference_id

    def test_create_template_inactive_by_default(self, mock_session):
        svc = NotificationQueueService(mock_session)
        t = await_coro(svc.create_template(
            template_id="TMP-1",
            name="Login Alert",
            notification_type="email",
            body="Body",
            subject="Subject",
        ))
        assert t.is_active is False
        captured = mock_session.add.call_args.args[0]
        assert captured.template_id == "TMP-1"
        assert captured.locale == "ar"
        assert captured.version == "1.0"

    def test_list_templates(self, mock_session):
        t = NotificationTemplate(id="id1", uuid=str(uuid.uuid4()), template_id="TMP-1")
        mock_session.execute.return_value.scalars.return_value.all.return_value = [t]
        svc = NotificationQueueService(mock_session)
        result = await_coro(svc.list_templates(skip=0, limit=50))
        assert result == [t]

    def test_get_queue_for_recipient(self, mock_session):
        q = NotificationQueue(id="id1", uuid=str(uuid.uuid4()), queue_id="Q-1")
        mock_session.execute.return_value.scalars.return_value.all.return_value = [q]
        svc = NotificationQueueService(mock_session)
        result = await_coro(svc.get_queue_for_recipient("u1"))
        assert result == [q]


class TestPromotedRoutes:
    def test_router_prefix_and_tags_unchanged(self):
        assert notifications_router.prefix == "/notifications"
        assert notifications_router.tags == ["NIAM Notifications"]

    def test_niam_router_still_includes_notifications(self):
        from app.identity.api import router as identity_router

        niam = identity_router.router
        assert niam.prefix == "/niam"
        assert any(type(r).__name__ == "_IncludedRouter" for r in niam.routes)


def await_coro(coro):
    return asyncio.run(coro)
