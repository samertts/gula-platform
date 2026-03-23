"""
Telegram Notification Gateway — GULA Platform
==============================================
Sends critical alert messages via the Telegram Bot API.
Routed through ExternalGateway for: circuit breaker, rate limiting, retry,
audit logging, and response validation.

Telegram outages must NEVER prevent the core lab workflow from functioning.
All calls use ``fallback=False`` so callers always get a boolean — never an exception.
"""

from __future__ import annotations

import logging
from typing import Any

from app.gateways.base import ExternalGateway

logger = logging.getLogger("gula.telegram")

_TELEGRAM_API = "https://api.telegram.org"


class TelegramGateway(ExternalGateway):
    name                      = "telegram"
    timeout                   = 10.0
    max_retries               = 2
    calls_per_minute          = 30    # stay well under Telegram's 30 msg/s limit
    circuit_failure_threshold = 5
    circuit_recovery_timeout  = 60.0
    cache_ttl                 = 0.0   # notifications are never cached

    def _do_call(self, action: str, **kwargs: Any) -> Any:
        bot_token: str = kwargs["bot_token"]
        chat_id:   str = kwargs["chat_id"]
        message:   str = kwargs["message"]

        url = f"{_TELEGRAM_API}/bot{bot_token}/sendMessage"
        return self._http("post", url, json={"chat_id": chat_id, "text": message})

    def _validate_response(self, response: Any) -> bool:
        # Telegram returns {"ok": true, "result": {...}} on success
        return isinstance(response, dict) and response.get("ok") is True


# Module-level singleton
_gateway = TelegramGateway()


def send_telegram(bot_token: str, chat_id: str, message: str) -> bool:
    """
    Send a Telegram message. Returns True on success, False on any failure.
    Never raises — designed to be fire-and-forget for alert notifications.
    """
    result = _gateway.call(
        action="send_message",
        cache_key=None,       # notifications are never cached
        fallback=False,
        bot_token=bot_token,
        chat_id=chat_id,
        message=message,
    )
    # result is either the Telegram response dict (success) or False (fallback)
    return isinstance(result, dict) and result.get("ok") is True
