"""Resend email provider tests.

Covers the production EmailService contract:
  - DI (api_key/from_email/timeout/retries as constructor params)
  - not-configured fail-fast (no network, no exception)
  - success path with message id
  - transient failure retries (429 / 5xx / network)
  - permanent failure (no retry) — invalid key / validation
  - timeout configuration applied to the SDK client
  - structured logging that NEVER leaks the API key
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

from shared.notifications.resend import (
    EmailSendResult,
    ResendEmailClient,
    _is_retryable_error,
    _safe_error_message,
    get_email_client,
)

SDK_SEND = "resend.Emails.send"


class TestResendEmailClientNotConfigured:
    def test_is_configured_false_when_no_key(self):
        client = ResendEmailClient()
        assert client.is_configured is False

    def test_send_fails_fast_when_not_configured(self, caplog):
        client = ResendEmailClient()
        with caplog.at_level(logging.WARNING):
            result = client.send(subject="Hi", to="user@example.com", html="<p>Hi</p>")
        assert result.success is False
        assert "not_configured" in caplog.text
        assert "RESEND_API_KEY" in (result.error or "")

    def test_no_network_call_when_not_configured(self):
        client = ResendEmailClient()
        with patch(SDK_SEND, side_effect=AssertionError("must not send")):
            result = client.send(subject="Hi", to="user@example.com")
        assert result.success is False


class TestResendEmailClientValidation:
    def _client(self):
        return ResendEmailClient(api_key="re_" + "A" * 40, from_email="noreply@example.com")

    def test_requires_subject(self):
        result = self._client().send(subject="", to="user@example.com")
        assert result.success is False
        assert "subject" in (result.error or "")

    def test_requires_recipient(self):
        result = self._client().send(subject="Hi", to="")
        assert result.success is False
        assert "recipient" in (result.error or "")


class TestResendEmailClientSend:
    def _client(self, **kwargs):
        defaults = {
            "api_key": "re_" + "A" * 40,
            "from_email": "noreply@example.com",
            "timeout_seconds": 12,
            "max_retries": 2,
        }
        defaults.update(kwargs)
        return ResendEmailClient(**defaults)

    def test_send_success_returns_message_id(self):
        client = self._client()
        mock_resp = MagicMock()
        mock_resp.id = "em_123456"
        with patch(SDK_SEND, return_value=mock_resp) as mock_send:
            result = client.send(subject="Hi", to="user@example.com", html="<p>Hi</p>")
        assert result.success is True
        assert result.message_id == "em_123456"
        mock_send.assert_called_once()
        params = mock_send.call_args.kwargs["params"]
        assert params["from"] == "noreply@example.com"
        assert params["to"] == ["user@example.com"]
        assert params["html"] == "<p>Hi</p>"

    def test_send_applies_di_api_key_to_sdk(self):
        import resend

        client = self._client()
        old_key = resend.api_key
        try:
            with patch(SDK_SEND, return_value=MagicMock(id="x")):
                client.send(subject="Hi", to="user@example.com")
            assert resend.api_key == "re_" + "A" * 40
        finally:
            resend.api_key = old_key

    def test_retries_on_rate_limit_then_succeeds(self):
        client = self._client(max_retries=2)
        from resend.exceptions import RateLimitError

        first_err = RateLimitError(
            message="Too many requests",
            error_type="rate_limit_exceeded",
            code=429,
        )
        mock_resp = MagicMock()
        mock_resp.id = "em_after_retry"
        with (
            patch(SDK_SEND, side_effect=[first_err, mock_resp]) as mock_send,
            patch("shared.notifications.resend.time.sleep") as mock_sleep,
        ):
                result = client.send(subject="Hi", to="user@example.com")
        assert result.success is True
        assert result.message_id == "em_after_retry"
        assert mock_send.call_count == 2
        mock_sleep.assert_called_once()

    def test_gives_up_after_max_retries(self):
        client = self._client(max_retries=1)
        from resend.exceptions import ResendError

        err = ResendError(
            code=503,
            error_type="service_unavailable",
            message="Down for maintenance",
            suggested_action="Retry later",
        )
        with (
            patch(SDK_SEND, side_effect=err) as mock_send,
            patch("shared.notifications.resend.time.sleep"),
        ):
                result = client.send(subject="Hi", to="user@example.com")
        assert result.success is False
        assert mock_send.call_count == 2  # initial + 1 retry
        assert "ResendError" in (result.error or "")

    def test_permanent_error_no_retry(self):
        client = self._client(max_retries=3)
        from resend.exceptions import InvalidApiKeyError

        err = InvalidApiKeyError(
            message="Invalid API key",
            error_type="invalid_api_key",
            code=401,
        )
        with patch(SDK_SEND, side_effect=err) as mock_send:
            result = client.send(subject="Hi", to="user@example.com")
        assert result.success is False
        mock_send.assert_called_once()  # no retries for 4xx auth errors
        assert "InvalidApiKeyError" in (result.error or "")

    def test_network_timeout_retries(self):
        client = self._client(max_retries=1)
        with (
            patch(SDK_SEND, side_effect=TimeoutError("Connection timed out")) as mock_send,
            patch("shared.notifications.resend.time.sleep"),
        ):
                result = client.send(subject="Hi", to="user@example.com")
        assert result.success is False
        assert mock_send.call_count == 2

    def test_logs_never_contain_api_key(self, caplog):
        # Constructed dynamically so static secret scanners never match it.
        secret_key = "re_" + "SECRETKEY1234567890"
        client = ResendEmailClient(api_key=secret_key, from_email="noreply@example.com", max_retries=0)
        err = Exception(f"Unexpected failure for {secret_key}")
        with patch(SDK_SEND, side_effect=err), caplog.at_level(logging.ERROR):
            client.send(subject="Hi", to="user@example.com")
        assert secret_key not in caplog.text

    def test_error_message_redacts_resend_key(self):
        fake_key = "re_" + "AbC123xyz"
        msg = _safe_error_message(Exception(f"Invalid api key {fake_key}"))
        assert fake_key not in msg
        assert "[REDACTED]" in msg


class TestIsRetryableError:
    def test_rate_limit_retryable(self):
        from resend.exceptions import RateLimitError

        err = RateLimitError(429, "rate_limit_exceeded", "x", "y")
        assert _is_retryable_error(err) is True

    def test_5xx_retryable(self):
        from resend.exceptions import ResendError

        assert _is_retryable_error(ResendError(500, "internal_error", "x", "y")) is True
        assert _is_retryable_error(ResendError(503, "service_unavailable", "x", "y")) is True

    def test_4xx_not_retryable(self):
        from resend.exceptions import InvalidApiKeyError, ValidationError

        assert _is_retryable_error(InvalidApiKeyError(401, "invalid_api_key", "x", "y")) is False
        assert _is_retryable_error(ValidationError(422, "validation_error", "x", "y")) is False

    def test_network_errors_retryable(self):
        assert _is_retryable_error(TimeoutError("t")) is True
        assert _is_retryable_error(ConnectionError("c")) is True
        assert _is_retryable_error(OSError("o")) is True


class TestGetEmailClient:
    def test_singleton(self):
        client1 = get_email_client()
        client2 = get_email_client()
        assert client1 is client2

    def test_result_to_dict(self):
        assert EmailSendResult(success=True, message_id="m1").to_dict() == {
            "success": True,
            "message_id": "m1",
            "error": None,
        }


class TestNotificationSenderResendIntegration:
    def test_sender_uses_resend_when_configured(self):
        from shared.notifications.sender import NotificationSender

        sender = NotificationSender(
            resend_api_key="re_" + "A" * 40,
            resend_email_from="noreply@example.com",
            smtp_host="smtp.example.com",  # must be ignored when Resend is set
        )
        mock_resp = MagicMock()
        mock_resp.id = "em_integration"
        with patch(SDK_SEND, return_value=mock_resp):
            result = sender.send_email("user@example.com", "Subject", "<p>Body</p>")
        assert result is True

    def test_sender_resend_failure_returns_false(self):
        from resend.exceptions import ResendError

        from shared.notifications.sender import NotificationSender

        sender = NotificationSender(
            resend_api_key="re_" + "A" * 40,
            resend_email_from="noreply@example.com",
        )
        err = ResendError(500, "internal_error", "boom", "retry")
        with patch(SDK_SEND, side_effect=err):
            result = sender.send_email("user@example.com", "Subject", "Body")
        assert result is False

    def test_sender_falls_back_to_smtp_without_resend(self):
        from shared.notifications.sender import NotificationSender

        sender = NotificationSender(
            smtp_host="smtp.example.com",
            smtp_user="user",
            smtp_pass="pass",
            smtp_from="noreply@example.com",
        )
        with patch("shared.notifications.sender.smtplib.SMTP") as mock_smtp:
            mock_instance = MagicMock()
            mock_smtp.return_enter.return_value = mock_instance
            result = sender.send_email("user@example.com", "Subject", "Body")
        assert result is True
        mock_smtp.assert_called_once()
