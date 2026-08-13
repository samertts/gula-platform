from __future__ import annotations

import app.routes.telegram_webhook as telegram_route
import pytest
from fastapi import HTTPException
from starlette.requests import Request


def _request(body: bytes, headers: dict[str, str]) -> Request:
    raw_headers = [(key.lower().encode(), value.encode()) for key, value in headers.items()]
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/telegram/webhook",
        "headers": raw_headers,
        "query_string": b"",
        "client": ("127.0.0.1", 1234),
        "server": ("testserver", 443),
        "scheme": "https",
    }

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    return Request(scope, receive)


def test_invalid_secret_is_rejected(monkeypatch):
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET_TOKEN", "expected-secret")
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHAT_IDS", "123")

    request = _request(b"{}", {"X-Telegram-Bot-Api-Secret-Token": "wrong-secret"})
    with pytest.raises(HTTPException) as exc_info:
        telegram_route._authorize_webhook(request, "123")

    assert exc_info.value.status_code == 403


def test_unauthorized_chat_is_rejected(monkeypatch):
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET_TOKEN", "expected-secret")
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHAT_IDS", "123")

    request = _request(b"{}", {"X-Telegram-Bot-Api-Secret-Token": "expected-secret"})
    with pytest.raises(HTTPException) as exc_info:
        telegram_route._authorize_webhook(request, "999")

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_webhook_does_not_leak_exception_text(monkeypatch):
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET_TOKEN", "expected-secret")
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHAT_IDS", "123")

    request = _request(
        b'{"message":{"chat":{"id":123},"text":"/status"}}',
        {"X-Telegram-Bot-Api-Secret-Token": "expected-secret"},
    )

    def fail_command(*_args, **_kwargs):
        raise RuntimeError("database password must never leave the server")

    monkeypatch.setattr(telegram_route, "handle_telegram_command", fail_command)
    with pytest.raises(HTTPException) as exc_info:
        await telegram_route.telegram_webhook(request, db=None)

    assert exc_info.value.status_code == 500
    assert "database password" not in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_authorized_webhook_processes_command(monkeypatch):
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET_TOKEN", "expected-secret")
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHAT_IDS", "123")
    sent: list[tuple[str, str]] = []
    monkeypatch.setattr(telegram_route, "handle_telegram_command", lambda *_args: "ok")
    monkeypatch.setattr(
        telegram_route,
        "send_telegram_message",
        lambda message, chat_id=None: sent.append((message, chat_id)) or True,
    )

    request = _request(
        b'{"message":{"chat":{"id":123},"text":"/status"}}',
        {"X-Telegram-Bot-Api-Secret-Token": "expected-secret"},
    )
    assert await telegram_route.telegram_webhook(request, db=None) == {"status": "ok"}
    assert sent == [("ok", "123")]
