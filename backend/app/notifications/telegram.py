"""
Telegram Notification Gateway — GULA Platform
==============================================
Trust level: ENRICHMENT — notifications are informational, never drive clinical logic.

Telegram outages must never affect the core lab workflow.
All calls return bool — never raise — via the ExternalGateway fallback system.
"""

from __future__ import annotations

from typing import Any

from app.gateways.base import (
    DataTrustLevel,
    ExternalGateway,
    FieldRule,
    validate_schema,
)

_TELEGRAM_API = "https://api.telegram.org"


class TelegramGateway(ExternalGateway):
    name                      = "telegram"
    trust_level               = DataTrustLevel.ENRICHMENT
    timeout                   = 10.0
    max_retries               = 2
    calls_per_minute          = 30
    circuit_failure_threshold = 5
    circuit_recovery_timeout  = 60.0
    cache_ttl                 = 0.0     # notifications are never cached
    stale_threshold           = 0.0

    _SCHEMA = [
        FieldRule("ok", bool, required=True, allowed=[True]),
    ]

    def _validate_response(self, response: Any) -> None:
        validate_schema(response, self._SCHEMA, context="telegram")

    def _do_call(self, action: str, **kwargs: Any) -> Any:
        bot_token: str = kwargs["bot_token"]
        chat_id:   str = kwargs["chat_id"]
        message:   str = kwargs["message"]
        url = f"{_TELEGRAM_API}/bot{bot_token}/sendMessage"
        return self._http("post", url, json={"chat_id": chat_id, "text": message})


_gateway = TelegramGateway()


def send_telegram(bot_token: str, chat_id: str, message: str) -> bool:
    """Send a Telegram message. Returns True on success, False on any failure."""
    result = _gateway.call(
        action="send_message",
        cache_key=None,
        fallback={"ok": False},
        bot_token=bot_token,
        chat_id=chat_id,
        message=message,
    )
    return bool(result.data.get("ok")) if isinstance(result.data, dict) else False
