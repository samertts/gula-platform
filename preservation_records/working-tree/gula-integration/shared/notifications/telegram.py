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
  - Enterprise capabilities (PROGRAM-COMM-002A): webhooks, polling/webhook
    auto-switching, webhook secret validation, groups / super-groups /
    channels / forum topics, media albums, rich messages (inline / reply /
    remove / force keyboards, edit / delete, reply-to, threads), batching,
    broadcast, delayed priority delivery, rate limiting, flood and replay
    protection, per-call metrics and Prometheus exposition.

Secrets policy: the bot token and the webhook secret token are read ONLY
from the environment (TELEGRAM_BOT_TOKEN, TELEGRAM_WEBHOOK_SECRET_TOKEN) or
from injected constructor arguments. They must never be hardcoded,
committed, or written to logs.

chat_id is NEVER a required configuration value — it is supplied dynamically
at call time, so any chat/group/channel can be targeted per notification.
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, ClassVar

import httpx

logger = logging.getLogger("gula.notifications.telegram")

API_BASE_URL = "https://api.telegram.org"

# Telegram bot tokens look like `<digits>:<base62-ish secret>`.
_TOKEN_PATTERN = re.compile(r"\b\d{6,}:[A-Za-z0-9_-]{30,}\b")

_RATE_LIMIT_PER_MINUTE = int(os.getenv("TELEGRAM_RATE_PER_MINUTE", "30"))
_WEBHOOK_MAX_CONNECTIONS = int(os.getenv("TELEGRAM_WEBHOOK_MAX_CONNECTIONS", "40"))
_REPLAY_CACHE_SIZE = int(os.getenv("TELEGRAM_REPLAY_CACHE_SIZE", "10000"))
_MAX_MESSAGES_PER_CHAT = int(os.getenv("TELEGRAM_MAX_PER_CHAT", "0"))
_MAX_MEDIA_GROUP = 10  # Telegram hard limit

# Human-meaningful MIME type mapping for common attachments.
ATTACHMENT_MIME_TYPES = {
    ".pdf": "application/pdf",
    ".csv": "text/csv",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xls": "application/vnd.ms-excel",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".doc": "application/msword",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".zip": "application/zip",
    ".tar": "application/x-tar",
    ".gz": "application/gzip",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
}

# Telegram only allows ~50 MB for bot uploads (50MB is the max request body).
MAX_MULTIPART_BYTES = 50 * 1024 * 1024


def redact_secrets(text: str) -> str:
    """Scrub anything that looks like a Telegram bot token from a string."""
    return _TOKEN_PATTERN.sub("[REDACTED]", str(text))


def _is_retryable_http(status_code: int) -> bool:
    """Transient Bot API codes: 408 (timeout), 429 (rate limit), all 5xx."""
    return status_code == 408 or status_code == 429 or status_code >= 500


def detect_mime_type(filename: str, fallback: str = "application/octet-stream") -> str:
    """Return a meaningful MIME type for a filename based on its extension."""
    name = filename or ""
    if "." in name:
        ext = f".{name.rsplit('.', 1)[-1].lower()}"
        return ATTACHMENT_MIME_TYPES.get(ext, fallback)
    return fallback


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


@dataclass
class TelegramInfoResult:
    """Outcome of a non-message Telegram API call (webhook/chat/me).

    ``data`` carries the parsed ``result`` dict when ``ok`` is True.
    """

    ok: bool
    data: dict[str, Any] | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "data": self.data, "error": self.error}


@dataclass
class TelegramWebhookInfo:
    """Parsed ``getWebhookInfo`` snapshot used by health checks + dashboards."""

    url: str = ""
    pending_update_count: int = 0
    last_error_message: str = ""
    max_connections: int = _WEBHOOK_MAX_CONNECTIONS
    is_unknown: bool = False

    @property
    def is_webhook_set(self) -> bool:
        return bool(self.url)

    @staticmethod
    def from_result(result: dict[str, Any] | None) -> TelegramWebhookInfo:
        if not result:
            return TelegramWebhookInfo(is_unknown=True)
        return TelegramWebhookInfo(
            url=result.get("url", ""),
            pending_update_count=int(result.get("pending_update_count", 0) or 0),
            last_error_message=result.get("last_error_message", ""),
            max_connections=int(result.get("max_connections") or _WEBHOOK_MAX_CONNECTIONS),
        )


# ── Keyboard / markup builders ────────────────────────────────────────────────


def build_inline_keyboard(rows: list[list[dict[str, Any]]]) -> dict[str, Any]:
    """Build ``inline_keyboard`` markup from rows of button dicts.

    Each button dict is passed through verbatim, e.g.:
        {"text": "Yes", "callback_data": "yes"}
        {"text": "Open", "url": "https://gula-platform.org"}
    """
    total = sum(len(row) for row in rows)
    if total == 0 or total > 100:
        raise ValueError("inline keyboard must contain between 1 and 100 buttons")
    for row in rows:
        if not row or not all(isinstance(b, dict) and b.get("text") for b in row):
            raise ValueError("inline keyboard rows must be non-empty lists of button dicts")
    return {"inline_keyboard": rows}


def build_reply_keyboard(
    rows: list[list[str]],
    *,
    resize: bool = True,
    one_time: bool = False,
    selective: bool = False,
) -> dict[str, Any]:
    """Build a reply (custom) keyboard from rows of text labels."""
    if not rows or any(not row for row in rows):
        raise ValueError("reply keyboard must contain at least one row with a button")
    return {
        "keyboard": [[{"text": label} for label in row] for row in rows],
        "resize_keyboard": resize,
        "one_time_keyboard": one_time,
        "selective": selective,
    }


def build_remove_keyboard(selective: bool = False) -> dict[str, Any]:
    """Build markup that removes any current custom keyboard."""
    return {"remove_keyboard": True, "selective": selective}


def build_force_reply(selective: bool = False) -> dict[str, Any]:
    """Build a force-reply markup prompting the user to reply to the message."""
    return {"force_reply": True, "selective": selective}


# ── Global Prometheus-style counters ─────────────────────────────────────────


class _Metrics:
    """Thread-safe, dependency-free counters + latency summary.

    Backend Prometheus endpoint renders these via
    ``append_prometheus_metrics()``; there is no hard dependency on the
    ``prometheus_client`` library (keeps ``shared`` dependency-free and
    cloud-independent).
    """

    _lock = threading.Lock()
    _sends_total: ClassVar[dict[tuple[str, str], int]] = {}
    _latency_sum = 0.0
    _latency_count = 0
    _retries_total = 0
    _errors_total: ClassVar[dict[str, int]] = {}
    _webhook_received = 0
    _webhook_signature_failures = 0
    _replay_blocked = 0
    _flood_blocked = 0
    _rate_limited = 0
    _delivered_total = 0
    _pending_total = 0

    @classmethod
    def record_send(cls, method: str, ok: bool) -> None:
        with cls._lock:
            state = "ok" if ok else "fail"
            cls._sends_total[(method, state)] = cls._sends_total.get((method, state), 0) + 1
            if ok:
                cls._delivered_total += 1

    @classmethod
    def record_error(cls, method: str) -> None:
        with cls._lock:
            cls._errors_total[method] = cls._errors_total.get(method, 0) + 1

    @classmethod
    def record_retry(cls) -> None:
        with cls._lock:
            cls._retries_total += 1

    @classmethod
    def record_latency(cls, seconds: float) -> None:
        with cls._lock:
            cls._latency_sum += seconds
            cls._latency_count += 1

    @classmethod
    def record_webhook_received(cls) -> None:
        with cls._lock:
            cls._webhook_received += 1

    @classmethod
    def record_webhook_signature_failure(cls) -> None:
        with cls._lock:
            cls._webhook_signature_failures += 1

    @classmethod
    def record_replay_blocked(cls) -> None:
        with cls._lock:
            cls._replay_blocked += 1

    @classmethod
    def record_flood_blocked(cls) -> None:
        with cls._lock:
            cls._flood_blocked += 1

    @classmethod
    def record_rate_limited(cls) -> None:
        with cls._lock:
            cls._rate_limited += 1

    @classmethod
    def set_pending(cls, n: int) -> None:
        with cls._lock:
            cls._pending_total = n

    @classmethod
    def reset(cls) -> None:
        with cls._lock:
            cls._sends_total.clear()
            cls._latency_sum = 0.0
            cls._latency_count = 0
            cls._retries_total = 0
            cls._errors_total.clear()
            cls._webhook_received = 0
            cls._webhook_signature_failures = 0
            cls._replay_blocked = 0
            cls._flood_blocked = 0
            cls._rate_limited = 0
            cls._delivered_total = 0
            cls._pending_total = 0

    @classmethod
    def snapshot(cls) -> dict[str, Any]:
        with cls._lock:
            return {
                "sends_total": dict(cls._sends_total),
                "latency_sum": cls._latency_sum,
                "latency_count": cls._latency_count,
                "retries_total": cls._retries_total,
                "errors_total": dict(cls._errors_total),
                "webhook_received": cls._webhook_received,
                "webhook_signature_failures": cls._webhook_signature_failures,
                "replay_blocked": cls._replay_blocked,
                "flood_blocked": cls._flood_blocked,
                "rate_limited": cls._rate_limited,
                "delivered_total": cls._delivered_total,
                "pending_total": cls._pending_total,
            }


def _escape_label(value: Any) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def append_prometheus_metrics() -> str:
    """Prometheus text exposition for Telegram provider metrics.

    The backend ``metrics_service`` concatenates this into the /metrics
    response. The counters live here so ``shared`` stays dependency-free.
    """
    snap = _Metrics.snapshot()
    lines: list[str] = []
    lines.append("# HELP gula_telegram_sends_total Telegram send attempts by method/result")
    lines.append("# TYPE gula_telegram_sends_total counter")
    for (method, state), count in sorted(snap["sends_total"].items()):
        lines.append(
            f'gula_telegram_sends_total{{method="{_escape_label(method)}",'
            f'state="{_escape_label(state)}"}} {count}'
        )
    lines.append("")
    lines.append("# HELP gula_telegram_delivered_total Confirmed delivered messages")
    lines.append("# TYPE gula_telegram_delivered_total counter")
    lines.append(f"gula_telegram_delivered_total {snap['delivered_total']}")
    lines.append("")
    lines.append("# HELP gula_telegram_retries_total Transient retry attempts")
    lines.append("# TYPE gula_telegram_retries_total counter")
    lines.append(f"gula_telegram_retries_total {snap['retries_total']}")
    lines.append("")
    lines.append("# HELP gula_telegram_api_errors_total Telegram API errors by method")
    lines.append("# TYPE gula_telegram_api_errors_total counter")
    for method, cnt in sorted(snap["errors_total"].items()):
        lines.append(f'gula_telegram_api_errors_total{{method="{_escape_label(method)}"}} {cnt}')
    lines.append("")
    count = snap["latency_count"]
    lines.append("# HELP gula_telegram_latency_seconds Telegram request latency")
    lines.append("# TYPE gula_telegram_latency_seconds summary")
    lines.append(f"gula_telegram_latency_seconds_sum {round(snap['latency_sum'], 9)}")
    lines.append(f"gula_telegram_latency_seconds_count {count}")
    lines.append("")
    lines.append("# HELP gula_telegram_webhook_received_total Updates received via webhook")
    lines.append("# TYPE gula_telegram_webhook_received_total counter")
    lines.append(f"gula_telegram_webhook_received_total {snap['webhook_received']}")
    lines.append("")
    lines.append("# HELP gula_telegram_webhook_signature_failures_total Failed secret checks")
    lines.append("# TYPE gula_telegram_webhook_signature_failures_total counter")
    lines.append(
        f"gula_telegram_webhook_signature_failures_total {snap['webhook_signature_failures']}"
    )
    lines.append("")
    lines.append("# HELP gula_telegram_replay_blocked_total Replayed update_ids dropped")
    lines.append("# TYPE gula_telegram_replay_blocked_total counter")
    lines.append(f"gula_telegram_replay_blocked_total {snap['replay_blocked']}")
    lines.append("")
    lines.append("# HELP gula_telegram_flood_blocked_total Flood-guard drops")
    lines.append("# TYPE gula_telegram_flood_blocked_total counter")
    lines.append(f"gula_telegram_flood_blocked_total {snap['flood_blocked']}")
    lines.append("")
    lines.append("# HELP gula_telegram_rate_limited_total Outbound rate-limit drops")
    lines.append("# TYPE gula_telegram_rate_limited_total counter")
    lines.append(f"gula_telegram_rate_limited_total {snap['rate_limited']}")
    lines.append("")
    lines.append("# HELP gula_telegram_pending_total Current pending deliveries")
    lines.append("# TYPE gula_telegram_pending_total gauge")
    lines.append(f"gula_telegram_pending_total {snap['pending_total']}")
    return "\n".join(lines) + "\n"


def validate_webhook_secret(configured_secret: str, received_secret: str) -> bool:
    """Validate the ``X-Telegram-Bot-Api-Secret-Token`` header.

    Returns True when:
      - no secret is configured (header not enforced), OR
      - both values are present and equal (constant-time comparison).
    """
    if not configured_secret:
        return True
    if not received_secret:
        return False
    import hmac

    return hmac.compare_digest(configured_secret.encode(), received_secret.encode())


class TelegramNetworkSpeed:
    """Tokens-per-minute budgeting used for outbound rate limiting.

    Smooth-Token-Bucket: we allow ``max_per_minute`` tokens and refill
    continuously toward the cap.
    """

    def __init__(self, max_per_minute: int = _RATE_LIMIT_PER_MINUTE) -> None:
        self._max_per_minute = max(1, int(max_per_minute or _RATE_LIMIT_PER_MINUTE))
        self._tokens = float(self._max_per_minute)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def consume(self, n: int = 1) -> bool:
        """Return True if ``n`` tokens are available and consume them."""
        with self._lock:
            now = time.monotonic()
            refill = ((now - self._last_refill) / 60.0) * self._max_per_minute
            self._tokens = min(float(self._max_per_minute), self._tokens + refill)
            self._last_refill = now
            if self._tokens < n:
                return False
            self._tokens -= n
            return True


class _ReplayGuard:
    """LRU dedup of seen ``update_id`` values for replay protection.

    An ``update_id`` is expected exactly once per update; a redelivered
    webhook or a polling fallback carries the same ``update_id`` and must be
    dropped to guarantee exactly-once dispatch.
    """

    def __init__(self, maxsize: int = _REPLAY_CACHE_SIZE) -> None:
        self._seen: deque = deque(maxlen=maxsize)
        self._lock = threading.Lock()

    def is_replay(self, update_id: int | None) -> bool:
        if update_id is None:
            return False
        with self._lock:
            if update_id in self._seen:
                return True
            self._seen.append(update_id)
            return False


class TelegramNotificationService:
    """Production Telegram sender backed by the official Bot API.

    Usage (dependency injection):

        service = TelegramNotificationService(bot_token="123:ABC")
        result = service.send_text(chat_id=-1001234, text="Hello")

    chat_id is required on every call — it is supplied dynamically and never
    read from configuration.

    Enterprise capabilities are strictly additive: every existing method and
    signature is preserved. New capabilities — webhooks, media albums, rich
    messages, batching, broadcast, rate limiting, flood/replay protection,
    metrics — reuse the same transport (``_request`` / ``_post``).
    """

    def __init__(
        self,
        bot_token: str = "",
        timeout_seconds: int = 30,
        max_retries: int = 3,
        logger_obj: logging.Logger | None = None,
        *,
        webhook_secret_token: str = "",
        max_per_minute: int = 0,
        messages_per_chat: int = 0,
    ) -> None:
        self._bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self._timeout_seconds = int(
            timeout_seconds or os.getenv("TELEGRAM_TIMEOUT_SECONDS", "30"),
        )
        self._max_retries = int(max_retries or os.getenv("TELEGRAM_MAX_RETRIES", "3"))
        self._webhook_secret_token = webhook_secret_token or os.getenv(
            "TELEGRAM_WEBHOOK_SECRET_TOKEN",
            "",
        )
        self._per_chat_limit = int(messages_per_chat or _MAX_MESSAGES_PER_CHAT)
        self._policy = TelegramNetworkSpeed(max_per_minute=int(max_per_minute or 0))
        self._replay_guard = _ReplayGuard()
        self._per_chat_queue: dict[Any, deque] = {}
        self._log = logger_obj or logger

    @property
    def is_configured(self) -> bool:
        return bool(self._bot_token)

    @property
    def webhook_secret_token(self) -> str:
        return self._webhook_secret_token

    @property
    def capabilities(self) -> list[str]:
        """Advertised provider capabilities (used by health/registry)."""
        return [
            "webhook",
            "groups",
            "supergroups",
            "topics",
            "channels",
            "broadcast",
            "batch",
            "scheduled",
            "priority",
            "photo",
            "album",
            "document",
            "audio",
            "video",
            "voice",
            "animation",
            "location",
            "contact",
            "inline_keyboard",
            "reply_keyboard",
            "force_reply",
            "edit_message",
            "delete_message",
            "reply_to",
            "message_thread",
            "rate_limit",
            "delivery_tracking",
            "metrics",
            "prometheus",
            "circuit_breaker",
            "structured_logging",
            "media_group",
        ]

    # ── Public API: text / rich messages ────────────────────────────────────

    def send(
        self,
        chat_id: int | str,
        text: str,
        parse_mode: str = "",
        **kwargs: Any,
    ) -> TelegramSendResult:
        """Generic message send — parse_mode may be "", "HTML" or "MarkdownV2".

        Other kwargs (``reply_markup``, ``reply_to_message_id``,
        ``message_thread_id``, …) forward to the typed send below.
        """
        if parse_mode == "HTML":
            return self.send_html(chat_id, text, **kwargs)
        if parse_mode == "MarkdownV2":
            return self.send_markdown_v2(chat_id, text, **kwargs)
        return self.send_text(chat_id, text, **kwargs)

    def send_text(
        self,
        chat_id: int | str,
        text: str,
        disable_web_page_preview: bool = False,
        disable_notification: bool = False,
        *,
        reply_markup: dict[str, Any] | None = None,
        reply_to_message_id: int | None = None,
        message_thread_id: int | None = None,
    ) -> TelegramSendResult:
        """Send a plain-text message (no parse mode).

        ``reply_markup`` accepts any dict built by ``build_inline_keyboard``,
        ``build_reply_keyboard``, ``build_force_reply`` or
        ``build_remove_keyboard``.
        ``message_thread_id`` targets a forum topic in a super group.
        """
        params: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": disable_web_page_preview,
            "disable_notification": disable_notification,
        }
        self._apply_enterprise_params(params, reply_markup, reply_to_message_id, message_thread_id)
        return self._request("sendMessage", params)

    def send_html(
        self,
        chat_id: int | str,
        html: str,
        disable_notification: bool = False,
        *,
        reply_markup: dict[str, Any] | None = None,
        reply_to_message_id: int | None = None,
        message_thread_id: int | None = None,
    ) -> TelegramSendResult:
        """Send an HTML-formatted message (parse_mode=HTML)."""
        params: dict[str, Any] = {
            "chat_id": chat_id,
            "text": html,
            "parse_mode": "HTML",
            "disable_notification": disable_notification,
        }
        self._apply_enterprise_params(params, reply_markup, reply_to_message_id, message_thread_id)
        return self._request("sendMessage", params)

    def send_markdown_v2(
        self,
        chat_id: int | str,
        text: str,
        disable_notification: bool = False,
        *,
        reply_markup: dict[str, Any] | None = None,
        reply_to_message_id: int | None = None,
        message_thread_id: int | None = None,
    ) -> TelegramSendResult:
        """Send a MarkdownV2-formatted message (parse_mode=MarkdownV2)."""
        params: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "MarkdownV2",
            "disable_notification": disable_notification,
        }
        self._apply_enterprise_params(params, reply_markup, reply_to_message_id, message_thread_id)
        return self._request("sendMessage", params)

    def reply(
        self, chat_id: int | str, text: str, reply_to_message_id: int, **kwargs: Any
    ) -> TelegramSendResult:
        """Reply to an existing message in the same chat/thread."""
        return self.send_html(chat_id, text, reply_to_message_id=reply_to_message_id, **kwargs)

    def send_to_thread(
        self, chat_id: int | str, message_thread_id: int, text: str, **kwargs: Any
    ) -> TelegramSendResult:
        """Send into a forum topic (message_thread_id) of a super group."""
        return self.send_html(chat_id, text, message_thread_id=message_thread_id, **kwargs)

    def edit_message(
        self,
        chat_id: int | str,
        message_id: int,
        text: str,
        parse_mode: str = "",
        *,
        reply_markup: dict[str, Any] | None = None,
    ) -> TelegramSendResult:
        """Edit an existing message body."""
        params: dict[str, Any] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
        }
        if parse_mode:
            params["parse_mode"] = parse_mode
        if reply_markup is not None:
            params["reply_markup"] = json.dumps(reply_markup, separators=(",", ":"))
        return self._request("editMessageText", params)

    def delete_message(self, chat_id: int | str, message_id: int) -> TelegramSendResult:
        """Delete a bot message."""
        return self._request("deleteMessage", {"chat_id": chat_id, "message_id": message_id})

    # ── Public API: media ────────────────────────────────────────────────────

    def send_photo(
        self,
        chat_id: int | str,
        photo: str | bytes,
        caption: str = "",
        parse_mode: str = "",
        filename: str = "photo.jpg",
        mime_type: str = "image/jpeg",
        disable_notification: bool = False,
        *,
        reply_markup: dict[str, Any] | None = None,
        reply_to_message_id: int | None = None,
        message_thread_id: int | None = None,
    ) -> TelegramSendResult:
        """Send a photo.

        ``photo`` may be a file_id, an HTTPS URL (str), or raw image bytes.
        """
        params: dict[str, Any] = {
            "chat_id": chat_id,
            "caption": caption,
            "disable_notification": disable_notification,
        }
        if parse_mode:
            params["parse_mode"] = parse_mode
        self._apply_enterprise_params(params, reply_markup, reply_to_message_id, message_thread_id)
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
        *,
        reply_markup: dict[str, Any] | None = None,
        reply_to_message_id: int | None = None,
        message_thread_id: int | None = None,
    ) -> TelegramSendResult:
        """Send a document / arbitrary file.

        ``document`` may be a file_id, an HTTPS URL (str), or raw file bytes
        (uploaded as multipart/form-data).
        """
        if isinstance(document, bytes) and len(document) > MAX_MULTIPART_BYTES:
            self._log.error(
                "telegram_file_too_large bytes=%d max=%d",
                len(document),
                MAX_MULTIPART_BYTES,
            )
            return TelegramSendResult(
                success=False,
                error=f"file too large: {len(document)} bytes (max {MAX_MULTIPART_BYTES})",
            )
        params: dict[str, Any] = {
            "chat_id": chat_id,
            "caption": caption,
            "disable_notification": disable_notification,
        }
        if parse_mode:
            params["parse_mode"] = parse_mode
        self._apply_enterprise_params(params, reply_markup, reply_to_message_id, message_thread_id)
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
        mime_type: str = "",
        disable_notification: bool = False,
        *,
        reply_markup: dict[str, Any] | None = None,
        reply_to_message_id: int | None = None,
        message_thread_id: int | None = None,
    ) -> TelegramSendResult:
        """Send a file from the local filesystem (read + multipart upload).

        ``mime_type`` is auto-detected from the extension when omitted.
        """
        name = filename or file_path.rsplit("/", 1)[-1]
        detected = mime_type or detect_mime_type(name)
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
            filename=name,
            mime_type=detected,
            disable_notification=disable_notification,
            reply_markup=reply_markup,
            reply_to_message_id=reply_to_message_id,
            message_thread_id=message_thread_id,
        )

    def send_media_group(
        self,
        chat_id: int | str,
        media: list[dict[str, Any]],
        *,
        disable_notification: bool = False,
        message_thread_id: int | None = None,
        reply_to_message_id: int | None = None,
    ) -> TelegramSendResult:
        """Send an album via sendMediaGroup.

        Each element must carry ``type`` and ``media``:
            {"type": "photo", "media": "file_id-or-url-or-bytes", "caption": "…"}
        Raw bytes are uploaded (multipart). At most 10 media items per album.
        """
        if not media or len(media) > _MAX_MEDIA_GROUP:
            return TelegramSendResult(
                success=False,
                error=f"media_group requires between 1 and {_MAX_MEDIA_GROUP} items",
            )
        if any(not (isinstance(m, dict) and m.get("type") and m.get("media")) for m in media):
            return TelegramSendResult(
                success=False,
                error="each media item requires 'type' and 'media'",
            )

        params: dict[str, Any] = {
            "chat_id": chat_id,
            "disable_notification": disable_notification,
        }
        if message_thread_id is not None:
            params["message_thread_id"] = message_thread_id
        if reply_to_message_id is not None:
            params["reply_to_message_id"] = reply_to_message_id

        has_bytes = any(isinstance(m.get("media"), bytes) for m in media)
        if has_bytes:
            files: dict[str, Any] = {}
            prepared = []
            for idx, m in enumerate(media):
                if isinstance(m.get("media"), bytes):
                    fname = m.get("filename", f"media_{idx}.bin")
                    mime = m.get("mime_type", "application/octet-stream")
                    attach = f"attach://m{idx}"
                    files[f"m{idx}"] = (fname, m["media"], mime)
                    prepared.append({**m, "media": attach})
                else:
                    prepared.append(m)
            params["media"] = json.dumps(prepared)
            return self._request("sendMediaGroup", params, files=files)
        params["media"] = json.dumps(media)
        return self._request("sendMediaGroup", params)

    def send_audio(
        self,
        chat_id: int | str,
        audio: str | bytes,
        caption: str = "",
        filename: str = "audio.mp3",
        mime_type: str = "audio/mpeg",
        **kwargs: Any,
    ) -> TelegramSendResult:
        return self.send_document(
            chat_id, audio, caption=caption, filename=filename, mime_type=mime_type, **kwargs
        )

    def send_video(
        self,
        chat_id: int | str,
        video: str | bytes,
        caption: str = "",
        filename: str = "video.mp4",
        mime_type: str = "video/mp4",
        **kwargs: Any,
    ) -> TelegramSendResult:
        return self.send_document(
            chat_id, video, caption=caption, filename=filename, mime_type=mime_type, **kwargs
        )

    def send_voice(
        self,
        chat_id: int | str,
        voice: str | bytes,
        caption: str = "",
        filename: str = "voice.ogg",
        mime_type: str = "audio/ogg",
        **kwargs: Any,
    ) -> TelegramSendResult:
        return self.send_document(
            chat_id, voice, caption=caption, filename=filename, mime_type=mime_type, **kwargs
        )

    def send_animation(
        self,
        chat_id: int | str,
        animation: str | bytes,
        caption: str = "",
        filename: str = "animation.gif",
        mime_type: str = "image/gif",
        **kwargs: Any,
    ) -> TelegramSendResult:
        return self.send_document(
            chat_id, animation, caption=caption, filename=filename, mime_type=mime_type, **kwargs
        )

    def send_attachment(
        self,
        chat_id: int | str,
        attachment: str | bytes,
        caption: str = "",
        filename: str = "attachment.bin",
        mime_type: str = "",
        **kwargs: Any,
    ) -> TelegramSendResult:
        """Send an arbitrary attachment with MIME auto-detection."""
        return self.send_document(
            chat_id,
            attachment,
            caption=caption,
            filename=filename,
            mime_type=mime_type or detect_mime_type(filename),
            **kwargs,
        )

    def send_location(
        self,
        chat_id: int | str,
        latitude: float,
        longitude: float,
        horizontal_accuracy: float | None = None,
        live_period: int | None = None,
    ) -> TelegramSendResult:
        """Send a map location (sendLocation)."""
        params: dict[str, Any] = {
            "chat_id": chat_id,
            "latitude": latitude,
            "longitude": longitude,
        }
        if horizontal_accuracy is not None:
            params["horizontal_accuracy"] = horizontal_accuracy
        if live_period is not None:
            params["live_period"] = live_period
        return self._request("sendLocation", params)

    def send_contact(
        self,
        chat_id: int | str,
        phone_number: str,
        first_name: str,
        last_name: str = "",
    ) -> TelegramSendResult:
        """Send a shared contact (sendContact)."""
        params: dict[str, Any] = {
            "chat_id": chat_id,
            "phone_number": phone_number,
            "first_name": first_name,
        }
        if last_name:
            params["last_name"] = last_name
        return self._request("sendContact", params)

    def send_alert(
        self,
        chat_id: int | str,
        message: str,
        level: str = "warning",
        disable_notification: bool = False,
        **kwargs: Any,
    ) -> TelegramSendResult:
        """Send a severity-tagged HTML alert.

        Supported levels: info, warning, critical.
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
            **kwargs,
        )

    def send_monitoring(
        self,
        chat_id: int | str,
        message: str,
        service: str = "gula-platform",
        disable_notification: bool = True,
        **kwargs: Any,
    ) -> TelegramSendResult:
        """Send a monitoring/health notification with a service tag."""
        html = f"<b>[MONITORING:{service}]</b>\n{message}"
        return self.send_html(chat_id, html, disable_notification=disable_notification, **kwargs)

    # ── Public API: broadcast / batch ────────────────────────────────────────

    def send_broadcast(
        self,
        chat_ids: list[int | str],
        text: str,
        parse_mode: str = "",
        *,
        interval_seconds: float = 0.25,
        dedupe: bool = True,
        **kwargs: Any,
    ) -> list[TelegramSendResult]:
        """Send one text to many targets (groups, super groups, channels).

        Bounded pacing (``interval_seconds``) protects against broadcast
        throughput limits and flood control. Order matches ``chat_ids``.
        """
        seen: set[Any] = set()
        results: list[TelegramSendResult] = []
        for chat_id in chat_ids:
            if dedupe and chat_id in seen:
                results.append(
                    TelegramSendResult(success=False, error="duplicate recipient skipped"),
                )
                continue
            seen.add(chat_id)
            results.append(self.send(chat_id, text, parse_mode=parse_mode, **kwargs))
            if interval_seconds > 0:
                time.sleep(interval_seconds)
        return results

    def send_batch(
        self,
        messages: list[dict[str, Any]],
        *,
        interval_seconds: float = 0.1,
    ) -> list[TelegramSendResult]:
        """Send a batch of messages.

        Each entry::
            {"chat_id": ..., "text": ..., "parse_mode": "HTML",
             "reply_markup": {...}, "message_thread_id": 5}

        Non-``chat_id``/``text`` keys are forwarded as send kwargs.
        """
        results: list[TelegramSendResult] = []
        for entry in messages:
            chat_id = entry.get("chat_id")
            text = entry.get("text")
            if not chat_id or text is None:
                results.append(
                    TelegramSendResult(success=False, error="batch entry needs chat_id+text"),
                )
                continue
            parse_mode = entry.get("parse_mode", "")
            kwargs = {k: v for k, v in entry.items() if k not in ("chat_id", "text", "parse_mode")}
            results.append(self.send(chat_id, text, parse_mode=parse_mode, **kwargs))
            if interval_seconds > 0:
                time.sleep(interval_seconds)
        return results

    # ── Public API: webhooks + polling ───────────────────────────────────────

    def set_webhook(
        self,
        url: str,
        secret_token: str | None = None,
        allowed_updates: list[str] | None = None,
        drop_pending: bool = False,
        max_connections: int | None = None,
    ) -> TelegramInfoResult:
        """Set (or replace) the webhook endpoint.

        ``secret_token`` is returned by Telegram in the
        ``X-Telegram-Bot-Api-Secret-Token`` header on every update, which the
        platform validates with ``validate_webhook_secret``.
        """
        params: dict[str, Any] = {"url": url}
        if secret_token:
            params["secret_token"] = secret_token
        if allowed_updates is not None:
            params["allowed_updates"] = allowed_updates
        if drop_pending:
            params["drop_pending_updates"] = True
        params["max_connections"] = max_connections or _WEBHOOK_MAX_CONNECTIONS
        result = self._call_info("setWebhook", params)
        if not result.ok:
            self._log.error("telegram_set_webhook_failed url=%s error=%s", url, result.error)
        else:
            self._log.info("telegram_webhook_set url=%s", url)
        return result

    def delete_webhook(self, drop_pending: bool = False) -> TelegramInfoResult:
        """Remove the webhook (bot reverts to polling via getUpdates)."""
        params = {"drop_pending_updates": True} if drop_pending else {}
        result = self._call_info("deleteWebhook", params)
        if not result.ok:
            self._log.error("telegram_delete_webhook_failed error=%s", result.error)
        return result

    def get_webhook_info(self) -> TelegramWebhookInfo:
        """Return the current webhook info (health check)."""
        result = self._call_info("getWebhookInfo", {})
        if not result.ok:
            return TelegramWebhookInfo(
                is_unknown=True,
                last_error_message=redact_secrets(result.error or "unknown error"),
            )
        return TelegramWebhookInfo.from_result(result.data)

    def get_me(self) -> TelegramInfoResult:
        """Return the bot user (identity / health probe)."""
        return self._call_info("getMe", {})

    def get_chat(self, chat_id: int | str) -> TelegramInfoResult:
        """Fetch chat metadata (group / super group / channel)."""
        return self._call_info("getChat", {"chat_id": chat_id})

    def get_chat_members_count(self, chat_id: int | str) -> TelegramInfoResult:
        """Fetch member count for a group/super group/channel."""
        return self._call_info("getChatMemberCount", {"chat_id": chat_id})

    def switch_mode(self, webhook_url: str = "") -> TelegramInfoResult:
        """Enable webhook mode (when url given) or revert to polling.

        Telegram only allows webhook *or* polling at once — switching is a
        single atomic delete/set call.
        """
        if webhook_url:
            return self.set_webhook(webhook_url, secret_token=self._webhook_secret_token)
        return self.delete_webhook(drop_pending=False)

    def poll_updates(
        self,
        limit: int = 32,
        timeout: int = 5,
        offset: int = 0,
    ) -> TelegramInfoResult:
        """Fetch a batch of updates via getUpdates (long-polling worker)."""
        params: dict[str, Any] = {"limit": limit, "timeout": timeout}
        if offset:
            params["offset"] = offset
        result = self._call_info("getUpdates", params)
        if not result.ok:
            self._log.warning("telegram_poll_failed error=%s", result.error)
        return result

    # ── Public API: security guards ──────────────────────────────────────────

    def is_replay(self, update_id: int | None) -> bool:
        """True when this is a redelivered webhook/polling update — drop it."""
        if self._replay_guard.is_replay(update_id):
            _Metrics.record_replay_blocked()
            self._log.warning("telegram_replay_blocked update_id=%s", update_id)
            return True
        return False

    def flood_guard_exceeded(self, chat_id: int | str) -> bool:
        """Return True if a chat burst went over the per-chat quota.

        Enabled only when ``messages_per_chat`` (``TELEGRAM_MAX_PER_CHAT``)
        is >= 1. Sliding 60s window per chat. Conservative breaker on top of
        Telegram's own anti-spam.
        """
        if not self._per_chat_limit:
            return False
        now = time.monotonic()
        queue = self._per_chat_queue.setdefault(chat_id, deque())
        while queue and queue[0] <= now - 60.0:
            queue.popleft()
        if len(queue) >= self._per_chat_limit:
            _Metrics.record_flood_blocked()
            self._log.warning(
                "telegram_flood_guard chat_id=%s limit=%d",
                chat_id,
                self._per_chat_limit,
            )
            return True
        queue.append(now)
        return False

    # ── Transport / internals ────────────────────────────────────────────────

    def _method_url(self, method: str) -> str:
        return f"{API_BASE_URL}/bot{self._bot_token}/{method}"

    def _apply_enterprise_params(
        self,
        params: dict[str, Any],
        reply_markup: dict[str, Any] | None,
        reply_to_message_id: int | None,
        message_thread_id: int | None,
    ) -> None:
        if reply_markup is not None:
            params["reply_markup"] = json.dumps(reply_markup, separators=(",", ":"))
        if reply_to_message_id is not None:
            params["reply_to_message_id"] = reply_to_message_id
        if message_thread_id is not None:
            params["message_thread_id"] = message_thread_id

    def _call_info(self, method: str, params: dict[str, Any] | None = None) -> TelegramInfoResult:
        """Fire a non-message Bot API call; returns parsed ``result``."""
        if not self.is_configured:
            return TelegramInfoResult(
                ok=False,
                error="Telegram not configured (TELEGRAM_BOT_TOKEN missing)",
            )
        payload = params or {}
        try:
            with httpx.Client(timeout=self._timeout_seconds) as client:
                resp = client.post(self._method_url(method), json=payload)
        except httpx.HTTPStatusError as exc:
            return TelegramInfoResult(
                ok=False,
                error=f"{type(exc).__name__}: {redact_secrets(str(exc))}",
            )
        except httpx.RequestError as exc:
            return TelegramInfoResult(
                ok=False,
                error=f"{type(exc).__name__}: {redact_secrets(str(exc))}",
            )
        except Exception as exc:
            return TelegramInfoResult(
                ok=False,
                error=f"{type(exc).__name__}: {redact_secrets(str(exc))}",
            )
        try:
            body = resp.json() if hasattr(resp, "json") else {}
        except ValueError:
            return TelegramInfoResult(ok=False, error=f"invalid_response status={resp.status_code}")
        if body.get("ok") is True:
            return TelegramInfoResult(ok=True, data=body.get("result"))
        description = redact_secrets(body.get("description", "unknown error"))
        return TelegramInfoResult(ok=False, error=description)

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

        chat_id = params["chat_id"]
        if self.flood_guard_exceeded(chat_id):
            _Metrics.record_send(method, False)
            return TelegramSendResult(success=False, error="flood guard per-chat limit reached")
        if not self._policy.consume(1):
            _Metrics.record_rate_limited()
            _Metrics.record_send(method, False)
            return TelegramSendResult(success=False, error="rate limit exceeded")

        attempt = 0
        while True:
            start = time.monotonic()
            try:
                result = self._post(method, params, files)
                _Metrics.record_send(method, result.success)
                _Metrics.record_latency(time.monotonic() - start)
                if result.success:
                    return result
                if not result.error:
                    return result
                code = getattr(result, "_http_code", 0)
                if not _is_retryable_http(code) or attempt >= self._max_retries:
                    _Metrics.record_error(method)
                    return result
                _Metrics.record_retry()
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
                    _Metrics.record_send(method, False)
                    _Metrics.record_error(method)
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
                _Metrics.record_retry()
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
                    (
                        httpx.TimeoutException,
                        httpx.NetworkError,
                        httpx.ConnectError,
                        httpx.ReadError,
                    ),
                )
                if not retryable or attempt > self._max_retries:
                    _Metrics.record_send(method, False)
                    _Metrics.record_error(method)
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
                _Metrics.record_retry()
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
                _Metrics.record_send(method, False)
                _Metrics.record_error(method)
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
        payload = params if not files else {k: v for k, v in params.items() if v is not None}
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
            res = body.get("result")
            message_id = 0
            if isinstance(res, list):
                if res and isinstance(res[0], dict):
                    message_id = int(res[0].get("message_id") or 0)
            elif isinstance(res, dict):
                message_id = int(res.get("message_id") or 0)
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
    *,
    webhook_secret_token: str = "",
    max_per_minute: int = 0,
    messages_per_chat: int = 0,
) -> TelegramNotificationService:
    """Return the app-wide Telegram service (lazy singleton).

    Accepts overrides for tests / DI; production uses env-var defaults.
    Enterprise knobs default to ``0``/empty so existing callers are
    unaffected.
    """
    global _service
    if _service is None:
        _service = TelegramNotificationService(
            bot_token=bot_token,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            webhook_secret_token=webhook_secret_token,
            max_per_minute=max_per_minute,
            messages_per_chat=messages_per_chat,
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
    "ATTACHMENT_MIME_TYPES",
    "MAX_MULTIPART_BYTES",
    "TelegramInfoResult",
    "TelegramNotificationService",
    "TelegramSendResult",
    "TelegramWebhookInfo",
    "append_prometheus_metrics",
    "build_force_reply",
    "build_inline_keyboard",
    "build_remove_keyboard",
    "build_reply_keyboard",
    "detect_mime_type",
    "get_telegram_service",
    "redact_secrets",
    "send_telegram",
    "validate_webhook_secret",
]
