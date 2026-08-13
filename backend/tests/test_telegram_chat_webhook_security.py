from __future__ import annotations

import app.notifications.telegram_chat as telegram_chat
import pytest
from fastapi import HTTPException
from starlette.requests import Request


def _request(body: bytes) -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/telegram/webhook",
        "headers": [(b"content-type", b"application/json")],
        "query_string": b"",
        "client": ("127.0.0.1", 1234),
        "server": ("testserver", 443),
        "scheme": "https",
    }

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    return Request(scope, receive)


def _update(chat_id: int = 123, sender_id: int = 123) -> bytes:
    return (
        f'{{"message":{{"chat":{{"id":{chat_id}}},"from":{{"id":{sender_id}}},"text":"/status"}}}}'
    ).encode()


def test_active_route_requires_secret(monkeypatch):
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET_TOKEN", "expected-secret")
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHAT_IDS", "123")

    with pytest.raises(HTTPException) as exc_info:
        telegram_chat._authorize_update(
            {"message": {"chat": {"id": 123}}},
            "wrong-secret",
        )

    assert exc_info.value.status_code == 403


def test_active_route_requires_allowlisted_chat(monkeypatch):
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET_TOKEN", "expected-secret")
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHAT_IDS", "123")

    with pytest.raises(HTTPException) as exc_info:
        telegram_chat._authorize_update(
            {"message": {"chat": {"id": 999}}},
            "expected-secret",
        )

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_active_route_rejects_unauthorized_sender(monkeypatch):
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET_TOKEN", "expected-secret")
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHAT_IDS", "123")
    monkeypatch.setenv("TELEGRAM_ADMIN_USER_ID", "123")

    request = _request(_update(chat_id=123, sender_id=999))
    with pytest.raises(HTTPException) as exc_info:
        await telegram_chat.telegram_webhook(request, "expected-secret")

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_active_route_processes_only_fully_authorized_update(monkeypatch):
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET_TOKEN", "expected-secret")
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHAT_IDS", "123")
    monkeypatch.setenv("TELEGRAM_ADMIN_USER_ID", "123")
    calls: list[tuple[str, str]] = []

    async def process_query(text: str, session_id: str):
        calls.append((text, session_id))
        return {"response": "authorized response"}

    sent: list[tuple[str, str, str]] = []
    monkeypatch.setattr(telegram_chat.orchestrator, "process_query", process_query)
    monkeypatch.setattr(
        telegram_chat,
        "send_telegram",
        lambda token, chat_id, text: sent.append((token, chat_id, text)),
    )
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")

    request = _request(_update(chat_id=123, sender_id=123))
    assert await telegram_chat.telegram_webhook(request, "expected-secret") == {"ok": True}
    assert calls == [("/status", "telegram:123")]
    assert sent == [("test-token", "123", "authorized response")]


@pytest.mark.asyncio
async def test_active_route_returns_sanitized_processing_error(monkeypatch):
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET_TOKEN", "expected-secret")
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHAT_IDS", "123")
    monkeypatch.setenv("TELEGRAM_ADMIN_USER_ID", "123")

    async def fail(*_args, **_kwargs):
        raise RuntimeError("secret database details")

    monkeypatch.setattr(telegram_chat.orchestrator, "process_query", fail)
    request = _request(_update(chat_id=123, sender_id=123))
    with pytest.raises(HTTPException) as exc_info:
        await telegram_chat.telegram_webhook(request, "expected-secret")

    assert exc_info.value.status_code == 500
    assert "secret database details" not in str(exc_info.value.detail)
