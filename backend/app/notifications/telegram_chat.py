"""Private Telegram conversation gateway.

Incoming messages are accepted only from TELEGRAM_ADMIN_USER_ID. Other users
remain notification-only: their updates are acknowledged but never answered.
"""

from __future__ import annotations

import hmac
import logging
import os
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request, status
from fastapi.concurrency import run_in_threadpool

from app.ai.orchestrator import orchestrator
from .telegram import send_telegram

logger = logging.getLogger("gula.notifications.telegram_chat")

router = APIRouter(prefix="/api/v1/telegram", tags=["Telegram Conversation"])

_MAX_TELEGRAM_MESSAGE = 4096


def _configured_admin_id() -> str:
    return os.getenv("TELEGRAM_ADMIN_USER_ID", "").strip()


def _is_admin(update: dict[str, Any]) -> bool:
    admin_id = _configured_admin_id()
    sender = update.get("message", {}).get("from", {})
    sender_id = sender.get("id")
    return bool(admin_id and sender_id is not None and hmac.compare_digest(str(sender_id), admin_id))


def _message_parts(update: dict[str, Any]) -> tuple[str, str] | None:
    message = update.get("message") or {}
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text")
    if chat_id is None or not isinstance(text, str) or not text.strip():
        return None
    return str(chat_id), text.strip()


def _split_message(text: str) -> list[str]:
    return [text[i : i + _MAX_TELEGRAM_MESSAGE] for i in range(0, len(text), _MAX_TELEGRAM_MESSAGE)] or [""]


def _response_text(result: dict[str, Any]) -> str:
    if result.get("error"):
        return "تعذر تنفيذ الطلب داخل المنصة حاليًا."
    for key in ("response", "rag_response"):
        value = result.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    if result.get("type") == "agent_execution":
        steps = result.get("steps") or []
        return "تم تنفيذ الطلب.\n" + "\n".join(
            f"- {step.get('agent', 'agent')}: {'نجح' if step.get('success') else 'فشل'}"
            for step in steps
        )
    return "تمت معالجة الطلب، لكن لم تُرجع المنصة نصًا للعرض."


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict[str, bool]:
    """Receive Telegram updates; only the configured admin may converse."""
    expected_secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()
    if expected_secret and not hmac.compare_digest(x_telegram_bot_api_secret_token or "", expected_secret):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    update = await request.json()
    if not isinstance(update, dict):
        return {"ok": True}

    if not _is_admin(update):
        # Keep a uniform 200 response so unauthorized users cannot use the
        # webhook as an account-enumeration oracle. Notifications to them are
        # still delivered by the existing outbound notification service.
        logger.warning("Ignored Telegram conversation update from unauthorized user")
        return {"ok": True}

    parsed = _message_parts(update)
    if parsed is None:
        # Voice/media is intentionally not enabled until a production STT/TTS
        # provider is configured; it must never broaden access beyond the admin.
        return {"ok": True}

    chat_id, text = parsed
    session_id = f"telegram:{chat_id}"
    result = await orchestrator.process_query(text, session_id=session_id)
    reply = _response_text(result)
    for part in _split_message(reply):
        await run_in_threadpool(send_telegram, os.getenv("TELEGRAM_BOT_TOKEN", ""), chat_id, part)
    return {"ok": True}


__all__ = ["router"]
