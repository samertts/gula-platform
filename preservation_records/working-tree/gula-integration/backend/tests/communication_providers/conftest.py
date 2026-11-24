"""Shared fixtures for the Communication Provider Layer tests (PROGRAM-COMM-002)."""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from shared.communication.model import OutboundMessage
from shared.communication.providers import ProviderDeliveryResult, ProviderOptions


@pytest.fixture
def no_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate provider env: unset every provider-related variable."""
    for key in list(dict(monkeypatch.__dict__.get("env", {})).keys()):  # pragma: no cover
        monkeypatch.delenv(key, raising=False)
    for key in (
        "RESEND_API_KEY",
        "EMAIL_FROM",
        "TELEGRAM_BOT_TOKEN",
        "DISCORD_WEBHOOK_URL",
        "SLACK_WEBHOOK_URL",
        "SLACK_API_TOKEN",
        "TEAMS_WEBHOOK_URL",
        "WEBHOOK_URL",
        "WEBHOOK_AUTH_TOKEN",
        "WEBHOOK_SIGNING_SECRET",
        "GULA_SECRETS_DIR",
    ):
        monkeypatch.delenv(key, raising=False)


def mock_client(handler: Any) -> httpx.Client:
    """Build an httpx client over a MockTransport handler (no network)."""
    return httpx.Client(transport=httpx.MockTransport(handler), timeout=5.0)


def make_message(content: str = "hello", **kwargs: Any) -> OutboundMessage:
    return OutboundMessage(content=content, **kwargs)


class RecordingOptions:
    """ProviderOptions stand-in carrying priority for tests."""

    def __init__(self, priority: str = "normal") -> None:
        self.priority = priority
        self.max_retries = 2
        self.locale = ""
        self.suppress_quiet_hours = False


class FailingResendClient:
    """ResendEmailClient double that always fails with a retryable error."""

    is_configured = True
    _api_key = "re_TEST_REDACTED_KEY"

    def send(self, subject: str, to: list[str], **kwargs: Any) -> Any:
        return type(
            "R",
            (),
            {"success": False, "message_id": "", "error": "resend outage"},
        )()


class FailingTelegramService:
    """TelegramNotificationService double that always fails."""

    is_configured = True
    _bot_token = "123456:TEST_TOKEN_REDACTED"

    def send_text(self, chat_id: str, text: str) -> Any:
        return type("T", (), {"success": False, "message_id": 0, "error": "telegram outage"})()

    def send_html(self, chat_id: str, html: str) -> Any:
        return self.send_text(chat_id, html)

    def send_markdown_v2(self, chat_id: str, text: str) -> Any:
        return self.send_text(chat_id, text)

    def send_alert(self, chat_id: str, message: str, level: str) -> Any:
        return self.send_text(chat_id, message)

    def send_broadcast(self, chat_ids: list[str], text: str, parse_mode: str = "") -> list[Any]:
        return [self.send_text(cid, text) for cid in chat_ids]


def delivery_result(success: bool, *, retryable: bool = False, error: str = "") -> ProviderDeliveryResult:
    return ProviderDeliveryResult(
        success=success,
        channel="test",
        provider="test",
        error=error or None,
        retryable=retryable,
    )


def options(priority: str = "normal") -> ProviderOptions:
    return RecordingOptions(priority=priority)


__all__ = [
    "FailingResendClient",
    "FailingTelegramService",
    "RecordingOptions",
    "delivery_result",
    "make_message",
    "mock_client",
    "no_secrets",
    "options",
]
