from __future__ import annotations

import hmac
import logging
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.lab_user import LabUser
from app.security.rbac import require_role
from app.services.telegram_bot import notify_critical_alert, send_telegram_message
from app.services.telegram_bot_commands import handle_telegram_command

logger = logging.getLogger("gula.telegram.webhook")
router = APIRouter(prefix="/telegram", tags=["telegram"])


def _configured_secret() -> str:
    return os.getenv("TELEGRAM_WEBHOOK_SECRET_TOKEN", "").strip()


def _allowed_chat_ids() -> set[str]:
    configured = os.getenv("TELEGRAM_ALLOWED_CHAT_IDS", "").strip()
    if not configured:
        # Backwards-compatible single administrator chat fallback. Production
        # deployments should prefer the explicit allowlist variable.
        configured = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    return {item.strip() for item in configured.split(",") if item.strip()}


def _authorize_webhook(request: Request, chat_id: str) -> None:
    """Fail closed unless Telegram transport and destination are configured."""
    expected = _configured_secret()
    supplied = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if not expected:
        logger.error("Telegram webhook rejected: secret token is not configured")
        raise HTTPException(status_code=503, detail="Telegram webhook is not configured")
    if not supplied or not hmac.compare_digest(supplied, expected):
        logger.warning("Telegram webhook rejected: invalid secret token")
        raise HTTPException(status_code=403, detail="Invalid Telegram webhook authorization")

    allowed = _allowed_chat_ids()
    if not allowed:
        logger.error("Telegram webhook rejected: no allowed chat IDs are configured")
        raise HTTPException(status_code=503, detail="Telegram webhook recipients are not configured")
    if chat_id not in allowed:
        logger.warning("Telegram webhook ignored unauthorized chat_id=%s", chat_id)
        raise HTTPException(status_code=403, detail="Telegram chat is not authorized")


@router.post("/webhook")
async def telegram_webhook(request: Request, db: Session = Depends(get_db)):
    """Receive an authenticated update from the configured Telegram bot."""
    try:
        body: dict[str, Any] = await request.json()
        message = body.get("message")
        if not isinstance(message, dict):
            return {"status": "ignored"}

        chat_id = str(message.get("chat", {}).get("id", ""))
        if not chat_id:
            return {"status": "ignored"}
        _authorize_webhook(request, chat_id)

        text = message.get("text", "")
        if isinstance(text, str) and text.startswith("/"):
            response_text = handle_telegram_command(text, chat_id, db)
            send_telegram_message(response_text, chat_id=chat_id)

        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Telegram webhook processing failed")
        # Do not return exception text, stack traces, database errors, or
        # provider responses to an external webhook caller.
        raise HTTPException(status_code=500, detail="Telegram webhook processing failed") from None


@router.post("/test-alert")
def test_telegram_alert(
    _current_user: LabUser = Depends(require_role("master_admin", "ministry_admin")),
):
    """Send a platform status notification for an authenticated administrator."""
    success = notify_critical_alert(
        alert_title="System Integration Test",
        patient_name="Demo Patient",
        details="All tenant isolation, AI fabric, and Telegram monitoring checks are operating normally.",
    )
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to send Telegram message. Verify the Telegram integration configuration.",
        )
    return {"status": "success", "message": "Telegram monitoring notification sent successfully."}
