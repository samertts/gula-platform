from __future__ import annotations

import asyncio
import inspect
import re
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.national.notification_platform.application import interfaces
from app.national.notification_platform.application.interfaces import (
    EmailAdapter,
    FaxAdapter,
    GovernmentGatewayAdapter,
    InAppAdapter,
    NotificationChannelAdapter,
    PushAdapter,
    SendResult,
    SMSAdapter,
    WebSocketAdapter,
    WhatsAppAdapter,
)
from app.national.notification_platform.domain.enums import NotificationChannel


def _run(coro):
    return asyncio.run(coro)


class TestWiringRepoint:
    """Order 18 (#50): the fabricated no-op adapters now delegate to the
    canonical Shared Core notifications provider (app.notifications).
    A provider failure is mapped fail-closed to SendResult(success=False)."""

    def test_interfaces_no_longer_fabricate_success(self):
        source = inspect.getsource(interfaces)
        assert "def _canonical_deliver" in source
        assert "from app.notifications import get_service" in source

    def test_module_no_longer_contains_fabricated_send_success(self):
        source = inspect.getsource(interfaces)
        helper_span = source.index("async def _canonical_deliver")
        helper_end = source.index("@dataclass")
        adapter_source = source[:helper_span] + source[helper_end:]
        fabricated = re.compile(r'provider_message_id=f"[a-z]{2,4}_{recipient\[:8\]}"')
        assert fabricated.search(adapter_source) is None, (
            "fabricated success payloads must be gone from the adapters"
        )

    def test_adapter_send_body_is_canonical_delegation(self):
        for cls in (
            EmailAdapter,
            SMSAdapter,
            PushAdapter,
            WebSocketAdapter,
            InAppAdapter,
            WhatsAppAdapter,
            GovernmentGatewayAdapter,
            FaxAdapter,
        ):
            source = inspect.getsource(cls.send)
            assert "_canonical_deliver(self.channel.value, recipient, subject, body)" in source, cls.__name__

    def test_telegram_and_webhook_keep_real_implementations(self):
        from app.national.notification_platform.application.interfaces import (
            TelegramAdapter,
            WebhookAdapter,
        )

        assert "send_telegram" in inspect.getsource(TelegramAdapter.send)
        assert "httpx.AsyncClient" in inspect.getsource(WebhookAdapter.send)

    def test_canonical_provider_is_shared_core(self):
        import app.notifications
        from app.notifications import get_service

        assert callable(get_service)
        assert hasattr(app.notifications, "NotificationService")


class TestCanonicalDelegation:
    """Behavior-additive: adapters deliver through the canonical
    NotificationService.send() and map NotificationResult fail-closed."""

    def _fake_service(self, *, success=True, error=None):
        service = MagicMock()
        result = MagicMock()
        result.success = success
        result.error = error
        service.send = MagicMock(return_value=result)
        return service

    def test_email_delegates_to_canonical_send(self):
        service = self._fake_service(success=True)

        async def run():
            adapter = EmailAdapter()
            with patch("app.notifications.get_service", return_value=service):
                return await adapter.send("user@example.com", "Subject", "Body")

        res = _run(run())
        assert res.success is True
        service.send.assert_called_once()
        kwargs = service.send.call_args
        assert kwargs[0] == ("email", "user@example.com")
        assert kwargs[1]["subject"] == "Subject"
        assert kwargs[1]["body"] == "Body"

    def test_failed_canonical_result_maps_to_send_result_failure(self):
        service = self._fake_service(success=False, error="SMTP refused")

        async def run():
            adapter = SMSAdapter()
            with patch("app.notifications.get_service", return_value=service):
                return await adapter.send("+964700000000", "S", "B")

        res = _run(run())
        assert res.success is False
        assert res.error == "SMTP refused"

    def test_provider_exception_is_fail_closed(self):
        service = MagicMock()
        service.send = MagicMock(side_effect=RuntimeError("provider down"))

        async def run():
            adapter = PushAdapter()
            with patch("app.notifications.get_service", return_value=service):
                return await adapter.send("token-1", "T", "B")

        res = _run(run())
        assert res.success is False
        assert "provider down" in (res.error or "")

    def test_unsupported_channel_returns_failure_not_fabricated_success(self):
        async def run():
            for cls, channel in (
                (WebSocketAdapter, NotificationChannel.WEBSOCKET),
                (InAppAdapter, NotificationChannel.IN_APP),
                (GovernmentGatewayAdapter, NotificationChannel.GOVERNMENT_GATEWAY),
                (FaxAdapter, NotificationChannel.FAX),
            ):
                assert cls().channel == channel
            return True

        assert _run(run()) is True

    def test_adapters_still_implement_domain_abc(self):
        for cls in (
            EmailAdapter,
            SMSAdapter,
            PushAdapter,
            WebSocketAdapter,
            InAppAdapter,
            WhatsAppAdapter,
            GovernmentGatewayAdapter,
            FaxAdapter,
        ):
            assert issubclass(cls, NotificationChannelAdapter)
            assert isinstance(cls(), NotificationChannelAdapter)
