"""Production Telegram Bot notifications via the official Telegram Bot API.

This module is the production Telegram notification provider for the GULA
Platform. It talks directly to the official Bot API
(https://core.telegram.org/bots/api) over HTTPS with:

  - Dependency injection: bot_token / timeout / retries are constructor
    parameters (env-var defaults for the app-wide singleton).
  - Timeout handling: every request has a bounded timeout
    (TELEGRAM_TIMEOUT_SECONDS).
  - Retries: exponential backoff for transient failures only (HTTP 408/429,
    HTTP >= 500, network errors). Permanent errors (400/401/403/404) fail
    immediately.
  - Structured logging: chat id and message id are logged — the bot token is
    NEVER logged or leaked into exceptions or results.
  - Secret redaction: any error message is scrubbed of bot-token-shaped
    strings before it reaches logs or result objects.
  - Robust error handling: typed result dataclass, no bare exceptions.

Secrets policy: the bot token is read ONLY from the environment
(TELEGRAM_BOT_TOKEN) or from an injected constructor argument. It must never
be hardcoded, committed, or written to logs.

chat_id is NEVER a required configuration value — it is supplied dynamically
at call time, so any chat/group/channel can be targeted per notification.
"""

from __future__ import annotations

import logging
import os
import re
import time
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger("gula.notifications.telegram")

API_BASE_URL = "https://api.telegram.org"

# Telegram bot tokens look like `<digits>:<base62-ish secret>`.
_TOKEN_PATTERN = re.compile(r"\b\d{6,}:[A-Za-z0-9_-]{30,}\b")


def redact_secrets(text: str) -> str:
    """Scrub anything that looks like a Telegram bot token from a string."""
    return _TOKEN_PATTERN.sub("[REDACTED]", str(text))


@dataclass
class TelegramSendResult:
    """Outcome of a single Telegram send attempt."""

    success: bool
    message_id: int = 0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "message_id": self.message_id,
            "error": self.error,
        }


def _is_retryable_http(status_code: int) -> bool:
    """Transient Bot API codes: 408 (timeout), 429 (rate limit), all 5xx."""
    return status_code == 408 or status_code == 429 or status_code >= 500


class TelegramNotificationService:
    """Production Telegram sender backed by the official Bot API.

    Usage (dependency injection):

        service = TelegramNotificationService(bot_token="123:ABC")
        result = service.send_text(chat_id=-1001234, text="Hello")

    chat_id is required on every call — it is supplied dynamically and never
    read from configuration.
    """

    def __init__(
        self,
        bot_token: str = "",
        timeout_seconds: int = 30,
        max_retries: int = 3,
        logger_obj: logging.Logger | None = None,
    ) -> None:
        self._bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self._timeout_seconds = int(
            timeout_seconds or os.getenv("TELEGRAM_TIMEOUT_SECONDS", "30"),
        )
        self._max_retries = int(max_retries or os.getenv("TELEGRAM_MAX_RETRIES", "3"))
        self._log = logger_obj or logger

    @property
    def is_configured(self) -> bool:
        return bool(self._bot_token)

    # ── Public API ─────────────────────────────────────────────────────────

    def send_text(
        self,
        chat_id: int | str,
        text: str,
        disable_web_page_preview: bool = False,
        disable_notification: bool = False,
    ) -> TelegramSendResult:
        """Send a plain-text message (no parse mode)."""
        params: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": disable_web_page_preview,
            "disable_notification": disable_notification,
        }
        return self._request("sendMessage", params)

    def send_html(
        self,
        chat_id: int | str,
        html: str,
        disable_notification: bool = False,
    ) -> TelegramSendResult:
        """Send an HTML-formatted message (parse_mode=HTML)."""
        params: dict[str, Any] = {
            "chat_id": chat_id,
            "text": html,
            "parse_mode": "HTML",
            "disable_notification": disable_notification,
        }
        return self._request("sendMessage", params)

    def send_markdown_v2(
        self,
        chat_id: int | str,
        text: str,
        disable_notification: bool = False,
    ) -> TelegramSendResult:
        """Send a MarkdownV2-formatted message (parse_mode=MarkdownV2)."""
        params: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "MarkdownV2",
            "disable_notification": disable_notification,
        }
        return self._request("sendMessage", params)

    def send_photo(
        self,
        chat_id: int | str,
        photo: str | bytes,
        caption: str = "",
        parse_mode: str = "",
        filename: str = "photo.jpg",
        mime_type: str = "image/jpeg",
        disable_notification: bool = False,
    ) -> TelegramSendResult:
        """Send a photo.

        `photo` may be a file_id, an HTTPS URL (str), or raw image bytes.
        """
        params: dict[str, Any] = {
            "chat_id": chat_id,
            "caption": caption,
            "disable_notification": disable_notification,
        }
        if parse_mode:
            params["parse_mode"] = parse_mode
        files: dict[str, Any] | None = None
        if isinstance(photo, bytes):
            files = {"photo": (filename, photo, mime_type)}
        else:
            params["photo"] = photo
        return self._request("sendPhoto", params, files=files)

    def send_document(
        self,
        chat_id: int | str,
        document: str | bytes,
        caption: str = "",
        parse_mode: str = "",
        filename: str = "document.bin",
        mime_type: str = "application/octet-stream",
        disable_notification: bool = False,
    ) -> TelegramSendResult:
        """Send a document / arbitrary file.

        `document` may be a file_id, an HTTPS URL (str), or raw file bytes
        (uploaded as multipart/form-data).
        """
        params: dict[str, Any] = {
            "chat_id": chat_id,
            "caption": caption,
            "disable_notification": disable_notification,
        }
        if parse_mode:
            params["parse_mode"] = parse_mode
        files: dict[str, Any] | None = None
        if isinstance(document, bytes):
            files = {"document": (filename, document, mime_type)}
        else:
            params["document"] = document
        return self._request("sendDocument", params, files=files)

    def send_file(
        self,
        chat_id: int | str,
        file_path: str,
        caption: str = "",
        filename: str = "",
        mime_type: str = "application/octet-stream",
        disable_notification: bool = False,
    ) -> TelegramSendResult:
        """Send a file from the local filesystem (read + multipart upload)."""
        try:
            with open(file_path, "rb") as fh:
                payload = fh.read()
        except OSError as exc:
            self._log.error(
                "telegram_file_read_failed path=%s error_type=%s",
                file_path,
                type(exc).__name__,
            )
            return TelegramSendResult(
                success=False,
                error=f"{type(exc).__name__}: {redact_secrets(str(exc))}",
            )
        return self.send_document(
            chat_id=chat_id,
            document=payload,
            caption=caption,
            filename=filename or file_path.rsplit("/", 1)[-1],
            mime_type=mime_type,
            disable_notification=disable_notification,
        )

    def send_alert(
        self,
        chat_id: int | str,
        message: str,
        level: str = "warning",
        disable_notification: bool = False,
    ) -> TelegramSendResult:
        """Send a severity-tagged HTML alert.

        Supported levels: info, warning, critical. The alert is prefixed
        with the level so monitoring dashboards can parse it.
        """
        level = level.lower()
        if level not in ("info", "warning", "critical"):
            level = "warning"
        title = {"info": "INFO", "warning": "WARNING", "critical": "CRITICAL"}[level]
        html = f"<b>[{title}]</b>\n{message}"
        return self.send_html(
            chat_id,
            html,
            disable_notification=disable_notification or level == "critical",
        )

    def send_monitoring(
        self,
        chat_id: int | str,
        message: str,
        service: str = "gula-platform",
        disable_notification: bool = True,
    ) -> TelegramSendResult:
        """Send a monitoring/health notification with a service tag."""
        html = f"<b>[MONITORING:{service}]</b>\n{message}"
        return self.send_html(chat_id, html, disable_notification=disable_notification)

    # ── Transport ──────────────────────────────────────────────────────────

    def _method_url(self, method: str) -> str:
        return f"{API_BASE_URL}/bot{self._bot_token}/{method}"

    def _request(
        self,
        method: str,
        params: dict[str, Any],
        files: dict[str, Any] | None = None,
    ) -> TelegramSendResult:
        """POST to the official Bot API with bounded timeout and retries."""
        if not self.is_configured:
            self._log.warning(
                "telegram_send_skipped reason=not_configured "
                "hint='set TELEGRAM_BOT_TOKEN in .env or platform secrets'",
            )
            return TelegramSendResult(
                success=False,
                error="Telegram not configured (TELEGRAM_BOT_TOKEN missing)",
            )

        if not params.get("chat_id"):
            return TelegramSendResult(success=False, error="chat_id is required")

        attempt = 0
        while True:
            try:
                result = self._post(method, params, files)
                if result.success:
                    return result
                if not result.error:
                    return result
                # ok=false with an HTTP-level retryable code
                code = getattr(result, "_http_code", 0)
                if not _is_retryable_http(code) or attempt >= self._max_retries:
                    return result
                delay = min(2**attempt, 30)
                self._log.warning(
                    "telegram_send_retry method=%s attempt=%d delay_seconds=%d",
                    method,
                    attempt + 1,
                    delay,
                )
                time.sleep(delay)
                attempt += 1
            except httpx.HTTPStatusError as exc:
                attempt += 1
                retryable = _is_retryable_http(exc.response.status_code)
                if not retryable or attempt > self._max_retries:
                    self._log.error(
                        "telegram_send_failed method=%s attempts=%d retryable=%s error_type=%s",
                        method,
                        attempt,
                        retryable,
                        type(exc).__name__,
                    )
                    return TelegramSendResult(
                        success=False,
                        error=f"{type(exc).__name__}: {redact_secrets(str(exc))}",
                    )
                delay = min(2 ** (attempt - 1), 30)
                self._log.warning(
                    "telegram_send_retry method=%s attempt=%d delay_seconds=%d error_type=%s",
                    method,
                    attempt,
                    delay,
                    type(exc).__name__,
                )
                time.sleep(delay)
            except httpx.RequestError as exc:
                attempt += 1
                retryable = isinstance(
                    exc,
                    (httpx.TimeoutException, httpx.NetworkError, httpx.ConnectError, httpx.ReadError),
                )
                if not retryable or attempt > self._max_retries:
                    self._log.error(
                        "telegram_send_failed method=%s attempts=%d retryable=%s error_type=%s",
                        method,
                        attempt,
                        retryable,
                        type(exc).__name__,
                    )
                    return TelegramSendResult(
                        success=False,
                        error=f"{type(exc).__name__}: {redact_secrets(str(exc))}",
                    )
                delay = min(2 ** (attempt - 1), 30)
                self._log.warning(
                    "telegram_send_retry method=%s attempt=%d delay_seconds=%d error_type=%s",
                    method,
                    attempt,
                    delay,
                    type(exc).__name__,
                )
                time.sleep(delay)
            except Exception as exc:
                self._log.error(
                    "telegram_send_failed method=%s attempts=%d error_type=%s",
                    method,
                    attempt + 1,
                    type(exc).__name__,
                )
                return TelegramSendResult(
                    success=False,
                    error=f"{type(exc).__name__}: {redact_secrets(str(exc))}",
                )

    def _post(
        self,
        method: str,
        params: dict[str, Any],
        files: dict[str, Any] | None = None,
    ) -> TelegramSendResult:
        """Single POST attempt; returns the typed result or raises."""
        payload = params
        if files:
            payload = {k: v for k, v in params.items() if v is not None}
        with httpx.Client(timeout=self._timeout_seconds) as client:
            resp = client.post(
                self._method_url(method),
                data=payload if files else None,
                json=None if files else payload,
                files=files,
            )
        try:
            body = resp.json()
        except ValueError:
            return TelegramSendResult(
                success=False,
                error=f"invalid_response status={resp.status_code}",
            )

        if body.get("ok") is True:
            result = body.get("result") or {}
            message_id = int(result.get("message_id") or 0)
            self._log.info(
                "telegram_sent method=%s chat_id=%s message_id=%s",
                method,
                params.get("chat_id"),
                message_id,
            )
            return TelegramSendResult(success=True, message_id=message_id)

        description = redact_secrets(body.get("description", "unknown error"))
        code = int(body.get("error_code") or resp.status_code or 0)
        result = TelegramSendResult(success=False, error=description)
        object.__setattr__(result, "_http_code", code)
        self._log.error(
            "telegram_send_failed method=%s chat_id=%s error_code=%s",
            method,
            params.get("chat_id"),
            code,
        )
        return result

    def close(self) -> None:
        """No-op kept for interface parity with other notification senders."""


_service: TelegramNotificationService | None = None


def get_telegram_service(
    bot_token: str = "",
    timeout_seconds: int = 30,
    max_retries: int = 3,
) -> TelegramNotificationService:
    """Return the app-wide Telegram service (lazy singleton).

    Accepts overrides for tests / DI; production uses env-var defaults.
    """
    global _service
    if _service is None:
        _service = TelegramNotificationService(
            bot_token=bot_token,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
        )
    return _service


def send_telegram(
    chat_id: int | str,
    text: str,
    parse_mode: str = "",
    **kwargs: Any,
) -> TelegramSendResult:
    """Module-level convenience: send via the shared service.

    parse_mode may be "", "HTML" or "MarkdownV2".
    """
    if parse_mode == "HTML":
        return get_telegram_service().send_html(chat_id, text, **kwargs)
    if parse_mode == "MarkdownV2":
        return get_telegram_service().send_markdown_v2(chat_id, text, **kwargs)
    return get_telegram_service().send_text(chat_id, text, **kwargs)


__all__ = [
    "TelegramNotificationService",
    "TelegramSendResult",
    "get_telegram_service",
    "redact_secrets",
    "send_telegram",
]
