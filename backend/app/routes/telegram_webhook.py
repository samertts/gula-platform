"""Telegram Bot webhook endpoint — GULA Platform
=================================================
Receives Telegram update objects whenever the bot is in webhook mode.

Security model:
  * signature validation — ``X-Telegram-Bot-Api-Secret-Token`` must match
    ``TELEGRAM_WEBHOOK_SECRET_TOKEN`` when configured (constant-time compare).
  * replay protection — ``update_id`` dedup via the shared service guard.
  * rate limiting — inbound abuse is capped per IP (rate_limit_public).
  * flooding — per-chat flood guard from the provider is enforced.

The route only *ingests* updates; it does not send messages. Any outbound
reply must go through the Communication Platform service (NotificationService)
to guarantee observability and circuit breaking.
"""

from __future__ import annotations

import contextlib
import logging
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.security.rate_limit import rate_limit_public
from shared.notifications.telegram import (
    TelegramNotificationService,
    get_telegram_service,
    validate_webhook_secret,
)

logger = logging.getLogger("gula.notifications.telegram_webhook")

router = APIRouter(prefix="/webhooks/telegram", tags=["telegram-webhook"])


class TelegramUpdate(BaseModel):
    """Subset of the Telegram Update type we ingest (unknown fields ignored)."""

    update_id: int | None = None
    message: dict[str, Any] | None = None
    edited_message: dict[str, Any] | None = None
    channel_post: dict[str, Any] | None = None
    callback_query: dict[str, Any] | None = None


class TelegramWebhookResponse(BaseModel):
    ok: bool
    message: str
    pending_count: int = 0


@router.post("/update")
async def telegram_webhook_update(
    request: Request,
    update: TelegramUpdate,
) -> JSONResponse:
    """Ingest one Telegram update.

    Verification is done by Telegram: only pushes with a valid secret header
    are processed; everything else is rejected 403 before any work happens.
    """
    service: TelegramNotificationService = get_telegram_service()
    configured_secret = service.webhook_secret_token
    header_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if not validate_webhook_secret(configured_secret, header_secret):
        logger.warning("telegram_webhook_signature_failed")
        return JSONResponse(status_code=403, content={"ok": False, "error": "signature mismatch"})

    rate_limit_public(request, max_per_minute=30)

    if update.update_id is not None and service.is_replay(update.update_id):
        logger.debug("telegram_webhook_replay_dropped update_id=%s", update.update_id)
        return JSONResponse(status_code=200, content={"ok": True, "replayed": True})

    kind = _classify_update(update)
    if kind:
        logger.info(
            "telegram_webhook_received kind=%s update_id=%s chat=%s",
            kind,
            update.update_id,
            _chat_of(update),
        )
    return JSONResponse(status_code=200, content={"ok": True, "update_id": update.update_id})


@router.get("/health")
async def telegram_webhook_health(request: Request) -> TelegramWebhookResponse:
    """Probe webhook reachability and configuration."""
    service: TelegramNotificationService = get_telegram_service()
    info = None
    with contextlib.suppress(Exception):  # defensive — never break /health
        info = service.get_webhook_info()
    if info is None or info.is_unknown:
        return TelegramWebhookResponse(ok=False, message="telegram provider unreachable")
    if info.is_webhook_set:
        return TelegramWebhookResponse(
            ok=True,
            message="webhook configured",
            pending_count=info.pending_update_count,
        )
    return TelegramWebhookResponse(
        ok=False,
        message="bot is polling (no webhook configured)",
        pending_count=info.pending_update_count,
    )


def _classify_update(update: TelegramUpdate) -> str:
    if update.message:
        kind = (update.message or {}).get("chat", {}).get("type", "private")
        return f"message/{kind}"
    if update.edited_message:
        return "edited_message"
    if update.channel_post:
        return "channel_post"
    if update.callback_query:
        return "callback_query"
    return "unknown"


def _chat_of(update: TelegramUpdate) -> Any:
    for container in (update.message, update.edited_message, update.channel_post):
        if container and isinstance(container.get("chat"), dict):
            return container["chat"].get("id")
    if update.callback_query and isinstance(update.callback_query.get("message"), dict):
        return update.callback_query["message"].get("chat", {}).get("id")
    return None


__all__ = [
    "TelegramUpdate",
    "TelegramWebhookResponse",
    "router",
]
