"""Authenticated Telegram conversation gateway.

Incoming messages require both Telegram transport authentication and an
explicit chat allowlist. An optional administrator user ID further restricts
who may issue commands inside an authorized chat.
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


def _configured_secret() -> str:
    # TELEGRAM_WEBHOOK_SECRET is retained only as a migration fallback. New
    # deployments must use the explicit *_SECRET_TOKEN name.
    return (
        os.getenv("TELEGRAM_WEBHOOK_SECRET_TOKEN", "").strip()
        or os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()
    )


def _allowed_chat_ids() -> set[str]:
    configured = os.getenv("TELEGRAM_ALLOWED_CHAT_IDS", "").strip()
    if not configured:
        configured = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not configured:
        # Private Telegram chats normally use the same numeric value for the
        # user and chat. This fallback supports the existing admin setup while
        # still requiring an explicit server-side identity configuration.
        configured = os.getenv("TELEGRAM_ADMIN_USER_ID", "").strip()
    return {item.strip() for item in configured.split(",") if item.strip()}


def _configured_admin_id() -> str:
    return os.getenv("TELEGRAM_ADMIN_USER_ID", "").strip()


def _chat_id(update: dict[str, Any]) -> str | None:
    message = update.get("message") or {}
    chat_id = message.get("chat", {}).get("id")
    return None if chat_id is None else str(chat_id)


def _message_parts(update: dict[str, Any]) -> tuple[str, str] | None:
    chat_id = _chat_id(update)
    text = (update.get("message") or {}).get("text")
    if chat_id is None or not isinstance(text, str) or not text.strip():
        return None
    return chat_id, text.strip()


def _authorize_update(update: dict[str, Any], supplied_secret: str | None) -> str | None:
    expected_secret = _configured_secret()
    if not expected_secret:
        logger.error("Telegram webhook rejected: secret token is not configured")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Telegram webhook is not configured")
    if not supplied_secret or not hmac.compare_digest(supplied_secret, expected_secret):
        logger.warning("Telegram webhook rejected: invalid secret token")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Telegram webhook authorization")

    chat_id = _chat_id(update)
    if chat_id is None:
        return None
    allowed_chat_ids = _allowed_chat_ids()
    if not allowed_chat_ids:
        logger.error("Telegram webhook rejected: no allowed chat IDs are configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram webhook recipients are not configured",
        )
    if chat_id not in allowed_chat_ids:
        logger.warning("Telegram webhook rejected: unauthorized chat_id=%s", chat_id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Telegram chat is not authorized")

    admin_id = _configured_admin_id()
    sender_id = (update.get("message") or {}).get("from", {}).get("id")
    if admin_id and (sender_id is None or not hmac.compare_digest(str(sender_id), admin_id)):
        logger.warning("Telegram webhook rejected: unauthorized sender in allowed chat")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Telegram sender is not authorized")
    return chat_id


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
            f"- {step.get('agent', 'agent')}: {'نجح' if step.get('success') else 'فشل'}" for step in steps
        )
    return "تمت معالجة الطلب، لكن لم تُرجع المنصة نصًا للعرض."


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict[str, bool]:
    """Receive Telegram updates only after transport and chat authorization."""
    try:
        update = await request.json()
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Telegram update") from None
    if not isinstance(update, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Telegram update")

    chat_id = _authorize_update(update, x_telegram_bot_api_secret_token)
    if chat_id is None:
        return {"ok": True}

    parsed = _message_parts(update)
    if parsed is None:
        return {"ok": True}
    _, text = parsed
    session_id = f"telegram:{chat_id}"
    try:
        result = await orchestrator.process_query(text, session_id=session_id)
        reply = _response_text(result)
        for part in _split_message(reply):
            await run_in_threadpool(send_telegram, os.getenv("TELEGRAM_BOT_TOKEN", ""), chat_id, part)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Telegram authorized command processing failed")
        raise HTTPException(status_code=500, detail="Telegram command processing failed") from None
    return {"ok": True}


__all__ = ["router"]
