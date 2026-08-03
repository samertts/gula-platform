"""Production email delivery via the official Resend SDK.

This module is the production email provider for the GULA Platform. It wraps
the official `resend` Python SDK with:

  - Dependency injection: api_key / from_email / timeouts / retries are
    constructor parameters (env-var defaults for the app-wide singleton).
  - Timeout handling: the SDK HTTP client is configured with a bounded
    request timeout (RESEND_TIMEOUT_SECONDS).
  - Retries: exponential backoff for transient failures only (HTTP 429,
    HTTP >= 500, network errors). Permanent errors (4xx) fail immediately.
  - Structured logging: recipient, message id and error type are logged —
    the API key is NEVER logged or leaked into exceptions.
  - Robust error handling: typed result dataclass, no bare exceptions.

Secrets policy: the API key is read ONLY from the environment
(RESEND_API_KEY) or from an injected constructor argument. It must never be
hardcoded, committed, or written to logs.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("gula.notifications.resend")


@dataclass
class EmailSendResult:
    """Outcome of a single email send attempt."""

    success: bool
    message_id: str = ""
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "message_id": self.message_id,
            "error": self.error,
        }


def _is_retryable_error(exc: Exception) -> bool:
    """Return True only for transient failures worth retrying.

    Permanent failures (validation, invalid/missing API key, application
    errors on the recipient side) must NOT be retried — they will never
    succeed and retrying only adds latency and quota consumption.
    """
    import resend.exceptions as resend_exc

    if isinstance(exc, resend_exc.RateLimitError):
        return True
    if isinstance(exc, resend_exc.ResendError):
        code = exc.code
        # HTTP 429 (rate limit) and all 5xx are transient.
        if code == 429:
            return True
        if isinstance(code, int) and code >= 500:
            return True
        # SDK-internal HTTP client failures (timeouts, DNS, connection).
        return exc.error_type == "HttpClientError"
    # Non-SDK exceptions (requests.Timeout, ConnectionError, ...) are
    # network-level failures — safe to retry.
    return isinstance(exc, (TimeoutError, ConnectionError, OSError))


class ResendEmailClient:
    """Production email sender backed by the official Resend SDK.

    Usage (dependency injection):

        client = ResendEmailClient(api_key="re_...", from_email="noreply@...")
        result = client.send(subject="...", to=["a@b.c"], html="<p>hi</p>")

    When api_key is empty, the client is "not configured": sends fail fast
    with a clear result and a warning log (no network call, no exception).
    """

    def __init__(
        self,
        api_key: str = "",
        from_email: str = "",
        timeout_seconds: int = 30,
        max_retries: int = 3,
        logger_obj: logging.Logger | None = None,
    ) -> None:
        self._api_key = api_key or os.getenv("RESEND_API_KEY", "")
        self._from_email = from_email or os.getenv("EMAIL_FROM", "noreply@gula-platform.org")
        self._timeout_seconds = int(timeout_seconds or os.getenv("RESEND_TIMEOUT_SECONDS", "30"))
        self._max_retries = int(max_retries or os.getenv("RESEND_MAX_RETRIES", "3"))
        self._log = logger_obj or logger
        self._sdk_configured = False

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key) and bool(self._from_email)

    def _configure_sdk(self) -> None:
        """Apply DI values to the (global) SDK and bound the request timeout."""
        import resend

        resend.api_key = self._api_key
        if not self._sdk_configured:
            from resend.http_client_requests import RequestsClient

            resend.default_http_client = RequestsClient(timeout=self._timeout_seconds)
            self._sdk_configured = True

    def send(
        self,
        subject: str,
        to: str | list[str],
        html: str = "",
        text: str = "",
        reply_to: str = "",
        cc: str | list[str] | None = None,
        bcc: str | list[str] | None = None,
        tags: list[dict[str, str]] | None = None,
        idempotency_key: str = "",
    ) -> EmailSendResult:
        """Send an email via Resend with bounded timeout and transient retries.

        Raises nothing: failures are returned as EmailSendResult(success=False).
        """
        if not self.is_configured:
            self._log.warning(
                "email_send_skipped reason=not_configured hint='set RESEND_API_KEY and EMAIL_FROM in .env or platform secrets'",
            )
            return EmailSendResult(success=False, error="Resend not configured (RESEND_API_KEY/EMAIL_FROM missing)")

        if not subject or not to:
            return EmailSendResult(success=False, error="subject and recipient (to) are required")

        recipients = [to] if isinstance(to, str) else to
        recipients = [r for r in recipients if r]
        if not recipients:
            return EmailSendResult(success=False, error="recipient (to) is required")

        params: dict[str, Any] = {
            "from": self._from_email,
            "to": recipients,
            "subject": subject,
        }
        if html:
            params["html"] = html
        if text:
            params["text"] = text
        if reply_to:
            params["reply_to"] = reply_to
        if cc:
            params["cc"] = [cc] if isinstance(cc, str) else cc
        if bcc:
            params["bcc"] = [bcc] if isinstance(bcc, str) else bcc
        if tags:
            params["tags"] = tags
        if idempotency_key:
            params["options"] = {"idempotency_key": idempotency_key}

        attempt = 0
        while True:
            try:
                return self._do_send(params, recipients)
            except Exception as exc:
                attempt += 1
                retryable = _is_retryable_error(exc)
                if not retryable or attempt > self._max_retries:
                    self._log.error(
                        "email_send_failed to=%s attempts=%d retryable=%s error_type=%s",
                        ",".join(recipients),
                        attempt,
                        retryable,
                        type(exc).__name__,
                    )
                    return EmailSendResult(
                        success=False,
                        error=f"{type(exc).__name__}: {_safe_error_message(exc)}",
                    )
                delay = min(2 ** (attempt - 1), 30)
                self._log.warning(
                    "email_send_retry to=%s attempt=%d delay_seconds=%d error_type=%s",
                    ",".join(recipients),
                    attempt,
                    delay,
                    type(exc).__name__,
                )
                time.sleep(delay)

    def _do_send(self, params: dict[str, Any], recipients: list[str]) -> EmailSendResult:
        import resend

        self._configure_sdk()
        options = params.pop("options", None) or {}
        # Never send the API key to the transport — it stays in the SDK.
        resp = resend.Emails.send(params=params, options=options)
        message_id = getattr(resp, "id", "")
        self._log.info(
            "email_sent to=%s message_id=%s",
            ",".join(recipients),
            message_id,
        )
        return EmailSendResult(success=True, message_id=message_id)

    def close(self) -> None:
        """No-op kept for interface parity with other notification senders."""
        self._sdk_configured = False


def _safe_error_message(exc: Exception) -> str:
    """Extract an error message that can never contain the API key."""
    message = str(exc)
    # Belt-and-braces: strip anything that looks like a Resend API key
    # (re_<base62>) before it reaches logs or result objects.
    import re

    return re.sub(r"re_[A-Za-z0-9]+", "[REDACTED]", message)


_client: ResendEmailClient | None = None


def get_email_client(
    api_key: str = "",
    from_email: str = "",
    timeout_seconds: int = 30,
    max_retries: int = 3,
) -> ResendEmailClient:
    """Return the app-wide Resend email client (lazy singleton).

    Accepts overrides for tests / DI; production uses env-var defaults.
    """
    global _client
    if _client is None:
        _client = ResendEmailClient(
            api_key=api_key,
            from_email=from_email,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
        )
    return _client


def send_email(
    subject: str,
    to: str | list[str],
    html: str = "",
    text: str = "",
    **kwargs: Any,
) -> EmailSendResult:
    """Module-level convenience: send via the shared client."""
    return get_email_client().send(subject=subject, to=to, html=html, text=text, **kwargs)


__all__ = [
    "EmailSendResult",
    "ResendEmailClient",
    "get_email_client",
    "send_email",
]
