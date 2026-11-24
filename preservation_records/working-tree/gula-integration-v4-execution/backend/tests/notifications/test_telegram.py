"""Telegram Bot notification service tests.

Covers the production TelegramNotificationService contract:
  - DI (bot_token/timeout/retries as constructor params)
  - not-configured fail-fast (no network, no exception)
  - chat_id supplied dynamically (never from configuration)
  - text / HTML / MarkdownV2 / photo / document / file / alert / monitoring
  - transient-failure retries (HTTP 408/429/5xx, network) with backoff
  - permanent failures (400/401/403/404) without retry
  - structured logging that NEVER leaks the bot token
  - secret redaction in errors and logs
"""

from __future__ import annotations

import io
import logging
from unittest.mock import patch

import httpx

from shared.notifications.telegram import (
    TelegramNotificationService,
    _is_retryable_http,
    redact_secrets,
)

# A clearly-fake token shape that never matches a real secret.
FAKE_TOKEN = "142536" + ":" + "A" * 40

POST = "httpx.Client.post"


def _client(**kwargs):
    defaults = {
        "bot_token": FAKE_TOKEN,
        "timeout_seconds": 12,
        "max_retries": 2,
    }
    defaults.update(kwargs)
    return TelegramNotificationService(**defaults)


def _resp(payload, status_code=200):
    request = httpx.Request("POST", "https://api.telegram.org")
    return httpx.Response(status_code, json=payload, request=request)


def _ok_response(override=None):
    payload = {"ok": True, "result": {"message_id": 42}}
    if override:
        payload.update(override)
    return _resp(payload)


def _err_response(description="bad request", error_code=400):
    return _resp({"ok": False, "description": description, "error_code": error_code})


def _http_error(status_code=500):
    return _resp({}, status_code=status_code)


class TestNotConfigured:
    def test_is_configured_false_when_no_token(self):
        assert TelegramNotificationService().is_configured is False

    def test_send_fails_fast_when_not_configured(self, caplog):
        service = TelegramNotificationService()
        with caplog.at_level(logging.WARNING):
            result = service.send_text(chat_id=123, text="Hi")
        assert result.success is False
        assert "not_configured" in caplog.text
        assert "TELEGRAM_BOT_TOKEN" in (result.error or "")

    def test_no_network_call_when_not_configured(self):
        service = TelegramNotificationService()
        with patch(POST, side_effect=AssertionError("must not send")):
            result = service.send_text(chat_id=123, text="Hi")
        assert result.success is False

    def test_requires_chat_id_even_when_configured(self):
        result = _client().send_text(chat_id="", text="Hi")
        assert result.success is False
        assert "chat_id" in (result.error or "")


class TestSendText:
    def test_success_returns_message_id(self):
        with patch(POST, return_value=_ok_response()) as mock_post:
            result = _client().send_text(chat_id=-1001234, text="Hello")
        assert result.success is True
        assert result.message_id == 42
        kwargs = mock_post.call_args.kwargs
        assert kwargs["json"]["chat_id"] == -1001234
        assert kwargs["json"]["text"] == "Hello"

    def test_dynamic_chat_id(self):
        with patch(POST, return_value=_ok_response()) as mock_post:
            _client().send_text(chat_id=987654321, text="dynamic chat")
        kwargs = mock_post.call_args.kwargs
        assert kwargs["json"]["chat_id"] == 987654321

    def test_chat_id_can_be_string_username(self):
        with patch(POST, return_value=_ok_response()) as mock_post:
            _client().send_text(chat_id="@ops_channel", text="Hi")
        kwargs = mock_post.call_args.kwargs
        assert kwargs["json"]["chat_id"] == "@ops_channel"

    def test_disable_web_page_preview(self):
        with patch(POST, return_value=_ok_response()) as mock_post:
            _client().send_text(chat_id=1, text="https://example.com", disable_web_page_preview=True)
        kwargs = mock_post.call_args.kwargs
        assert kwargs["json"]["disable_web_page_preview"] is True


class TestParsingModes:
    def test_send_html(self):
        with patch(POST, return_value=_ok_response()) as mock_post:
            result = _client().send_html(chat_id=1, html="<b>bold</b>")
        assert result.success is True
        kwargs = mock_post.call_args.kwargs
        assert kwargs["json"]["parse_mode"] == "HTML"
        assert kwargs["json"]["text"] == "<b>bold</b>"

    def test_send_markdown_v2(self):
        with patch(POST, return_value=_ok_response()) as mock_post:
            result = _client().send_markdown_v2(chat_id=1, text="*bold*")
        assert result.success is True
        kwargs = mock_post.call_args.kwargs
        assert kwargs["json"]["parse_mode"] == "MarkdownV2"
        assert kwargs["json"]["text"] == "*bold*"

    def test_send_photo_file_id(self):
        with patch(POST, return_value=_ok_response()) as mock_post:
            result = _client().send_photo(chat_id=1, photo="AgACAgxyz", caption="cap")
        assert result.success is True
        kwargs = mock_post.call_args.kwargs
        assert kwargs["json"]["photo"] == "AgACAgxyz"
        assert kwargs["json"]["caption"] == "cap"

    def test_send_photo_bytes_upload(self):
        with patch(POST, return_value=_ok_response()) as mock_post:
            result = _client().send_photo(
                chat_id=1, photo=b"\x89PNG\r\n", filename="cap.png", mime_type="image/png",
            )
        assert result.success is True
        files = mock_post.call_args.kwargs["files"]
        assert files["photo"][0] == "cap.png"
        assert files["photo"][1] == b"\x89PNG\r\n"
        assert files["photo"][2] == "image/png"

    def test_send_document_file_id(self):
        with patch(POST, return_value=_ok_response()) as mock_post:
            result = _client().send_document(chat_id=1, document="BQAC:AB", caption="doc")
        assert result.success is True
        kwargs = mock_post.call_args.kwargs
        assert kwargs["json"]["document"] == "BQAC:AB"

    def test_send_document_bytes_upload(self):
        with patch(POST, return_value=_ok_response()) as mock_post:
            result = _client().send_document(
                chat_id=1,
                document=b"%PDF-1.4",
                filename="report.pdf",
                mime_type="application/pdf",
            )
        assert result.success is True
        files = mock_post.call_args.kwargs["files"]
        assert files["document"][0] == "report.pdf"
        assert files["document"][1] == b"%PDF-1.4"
        assert files["document"][2] == "application/pdf"

    def test_send_file_from_disk(self, tmp_path):
        fpath = tmp_path / "log.txt"
        fpath.write_bytes(b"line1\n")
        with patch(POST, return_value=_ok_response()) as mock_post:
            result = _client().send_file(chat_id=1, file_path=str(fpath))
        assert result.success is True
        files = mock_post.call_args.kwargs["files"]
        assert files["document"][1] == b"line1\n"

    def test_send_file_missing(self):
        result = _client().send_file(chat_id=1, file_path="/nonexistent/nope.txt")
        assert result.success is False

    def test_send_alert_prefixed(self):
        with patch(POST, return_value=_ok_response()) as mock_post:
            result = _client().send_alert(chat_id=1, message="disk full", level="critical")
        assert result.success is True
        kwargs = mock_post.call_args.kwargs
        assert kwargs["json"]["parse_mode"] == "HTML"
        assert "[CRITICAL]" in kwargs["json"]["text"]

    def test_send_alert_invalid_level_defaults_to_warning(self):
        with patch(POST, return_value=_ok_response()) as mock_post:
            _client().send_alert(chat_id=1, message="x", level="nonsense")
        kwargs = mock_post.call_args.kwargs
        assert "[WARNING]" in kwargs["json"]["text"]

    def test_send_monitoring(self):
        with patch(POST, return_value=_ok_response()) as mock_post:
            result = _client().send_monitoring(
                chat_id=1, message="all healthy", service="gula-platform",
            )
        assert result.success is True
        kwargs = mock_post.call_args.kwargs
        assert "[MONITORING:gula-platform]" in kwargs["json"]["text"]


class TestRetries:
    def test_429_is_retryable_http(self):
        assert _is_retryable_http(429) is True

    def test_408_is_retryable_http(self):
        assert _is_retryable_http(408) is True

    def test_500_is_retryable_http(self):
        assert _is_retryable_http(500) is True

    def test_400_is_not_retryable_http(self):
        assert _is_retryable_http(400) is False

    def test_403_is_not_retryable_http(self):
        assert _is_retryable_http(403) is False

    def test_permanent_error_no_retry(self):
        with patch(POST, return_value=_err_response("unauthorized", 401)) as mock_post:
            result = _client(max_retries=3).send_text(chat_id=1, text="Hi")
        assert result.success is False
        assert mock_post.call_count == 1
        assert "unauthorized" in (result.error or "")

    def test_transient_error_retries_then_succeeds(self):
        with patch(POST, side_effect=[_http_error(500), _ok_response()]) as mock_post:
            result = _client(max_retries=3).send_text(chat_id=1, text="Hi")
        assert result.success is True
        assert mock_post.call_count == 2

    def test_transient_error_exhausts_retries(self):
        with patch(POST, return_value=_http_error(500)) as mock_post:
            result = _client(max_retries=2).send_text(chat_id=1, text="Hi")
        assert result.success is False
        assert mock_post.call_count == 3  # initial + 2 retries

    def test_ok_false_with_retryable_code_retries_then_gives_up(self):
        with patch(POST, side_effect=[_err_response("flood", 429), _err_response("flood", 429)]) as mock_post:
            result = _client(max_retries=1).send_text(chat_id=1, text="Hi")
        assert result.success is False
        assert mock_post.call_count == 2  # initial + 1 retry

    def test_ok_false_retryable_then_success(self):
        with patch(POST, side_effect=[_err_response("flood", 429), _ok_response()]) as mock_post:
            result = _client(max_retries=3).send_text(chat_id=1, text="Hi")
        assert result.success is True
        assert mock_post.call_count == 2

    def test_network_error_retries(self):
        from httpx import ConnectError

        request = httpx.Request("POST", "https://api.telegram.org")
        err = ConnectError("boom", request=request)
        with patch(POST, side_effect=[err, _ok_response()]) as mock_post:
            result = _client(max_retries=2).send_text(chat_id=1, text="Hi")
        assert result.success is True
        assert mock_post.call_count == 2

    def test_raised_http_status_error_retries_when_retryable(self):
        request = httpx.Request("POST", "https://api.telegram.org")
        err = httpx.HTTPStatusError(
            "boom", request=request, response=_resp({}, status_code=502),
        )
        with patch(POST, side_effect=[err, _ok_response()]) as mock_post:
            result = _client(max_retries=2).send_text(chat_id=1, text="Hi")
        assert result.success is True
        assert mock_post.call_count == 2

    def test_raised_http_status_error_no_retry_when_permanent(self):
        request = httpx.Request("POST", "https://api.telegram.org")
        err = httpx.HTTPStatusError(
            "forbidden", request=request, response=_resp({}, status_code=403),
        )
        with patch(POST, side_effect=err) as mock_post:
            result = _client(max_retries=3).send_text(chat_id=1, text="Hi")
        assert result.success is False
        assert mock_post.call_count == 1


class TestSecretRedaction:
    def test_redact_secrets_removes_token_shape(self):
        original = "Failed: 987654321:ABCDEF1234567890abcdefghijklmnop"
        assert redact_secrets(original) == "Failed: [REDACTED]"

    def test_redact_secrets_does_not_touch_normal_text(self):
        text = "delivery ok chat=123 message_id=42"
        assert redact_secrets(text) == text

    def test_error_message_redacts_token(self):
        with patch(
            POST,
            return_value=_err_response("invalid token 987654321:ABCDEFGHIJKLMNOPQRSTUVWXYZ012345", 401),
        ):
            result = _client().send_text(chat_id=1, text="Hi")
        assert "987654321:ABCDEFGHIJKLMNOPQRSTUVWXYZ012345" not in (result.error or "")
        assert "[REDACTED]" in (result.error or "")

    def test_logs_never_contain_token(self):
        logger_capture = io.StringIO()
        handler = logging.StreamHandler(logger_capture)
        handler.setFormatter(logging.Formatter("%(name)s %(message)s"))
        logger_fake = logging.getLogger("test.gula.telegram")
        logger_fake.addHandler(handler)
        logger_fake.setLevel(logging.INFO)

        service = TelegramNotificationService(
            bot_token=FAKE_TOKEN,
            timeout_seconds=1,
            max_retries=2,
            logger_obj=logger_fake,
        )
        with patch(POST, side_effect=_http_error(500)):
            service.send_text(chat_id=1, text="Hi")
        logs = logger_capture.getvalue()
        assert FAKE_TOKEN not in logs
        assert "142536" not in logs
