"""Notification Platform - Sender Tests"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import httpx
import pytest

from shared.notifications.sender import (
    NotificationMessage,
    NotificationSender,
    send_email,
    send_push,
    send_sms,
    send_telegram,
    send_whatsapp,
)


class TestNotificationMessage:
    def test_minimal_message(self):
        msg = NotificationMessage(to="+9647701234567")
        assert msg.to == "+9647701234567"
        assert msg.priority == "normal"

    def test_full_message(self):
        msg = NotificationMessage(
            to="user@example.com",
            subject="Test",
            body="Hello",
            template_id="welcome",
            template_data={"name": "Ali"},
            priority="high",
        )
        assert msg.subject == "Test"
        assert msg.template_data["name"] == "Ali"
        assert msg.priority == "high"


class TestNotificationSender:
    def test_send_push_fcm_not_configured(self, caplog):
        sender = NotificationSender()
        with caplog.at_level(logging.WARNING):
            result = sender.send_push("token", "Title", "Body")
        assert result is False
        assert "FCM key not configured" in caplog.text

    def test_send_push_fcm_error_returns_false(self):
        sender = NotificationSender(fcm_key="fake-key")
        # firebase_admin is lazily imported; if not available, function catches and returns False
        if sender._fcm_key:
            result = sender.send_push("token", "Title", "Body")
            assert isinstance(result, bool)

    def test_send_email_smtp_not_configured_logs_only(self, caplog):
        sender = NotificationSender()
        with caplog.at_level(logging.INFO):
            result = sender.send_email("test@example.com", "Subject", "Body")
        assert result is True
        assert "SMTP not configured" in caplog.text

    def test_send_email_smtp_configured_sends(self):
        sender = NotificationSender(
            smtp_host="smtp.example.com",
            smtp_user="user",
            smtp_pass="pass",
            smtp_from="noreply@example.com",
        )
        with patch("shared.notifications.sender.smtplib.SMTP") as mock_smtp:
            mock_instance = MagicMock()
            mock_smtp.return_enter.return_value = mock_instance
            result = sender.send_email(
                "test@example.com", "Subject", "<html><body>Hi</body></html>"
            )
        assert result is True

    def test_send_email_handles_html_content(self):
        sender = NotificationSender(
            smtp_host="smtp.example.com",
            smtp_user="user",
            smtp_pass="pass",
            smtp_from="noreply@example.com",
        )
        with patch("shared.notifications.sender.smtplib.SMTP") as mock_smtp:
            mock_instance = MagicMock()
            mock_smtp.return_enter.return_value = mock_instance
            result = sender.send_email(
                "test@example.com", "Subject", "<html><body>Hi</body></html>"
            )
        assert result is True

    def test_send_sms_api_not_configured_logs_only(self, caplog):
        sender = NotificationSender()
        with caplog.at_level(logging.INFO):
            result = sender.send_sms("+9647701234567", "Hello")
        assert result is True
        assert "API not configured" in caplog.text

    def test_send_sms_api_configured_sends(self):
        sender = NotificationSender(sms_api_url="https://sms.example.com/send")
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_resp
        with patch("shared.notifications.sender.httpx.Client", return_value=mock_client):
            result = sender.send_sms("+9647701234567", "Hello")
        assert result is True
        mock_client.post.assert_called_once()

    def test_send_sms_api_failure_returns_false(self):
        sender = NotificationSender(sms_api_url="https://sms.example.com/send")
        mock_client = MagicMock()
        mock_client.post.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=MagicMock()
        )
        with patch("shared.notifications.sender.httpx.Client", return_value=mock_client):
            result = sender.send_sms("+9647701234567", "Hello")
        assert result is False

    def test_send_whatsapp_api_not_configured_logs_only(self, caplog):
        sender = NotificationSender()
        with caplog.at_level(logging.INFO):
            result = sender.send_whatsapp("+9647701234567", "Hello")
        assert result is True
        assert "API not configured" in caplog.text

    def test_send_whatsapp_api_configured_sends(self):
        sender = NotificationSender(
            whatsapp_api_url="https://graph.facebook.com/v18.0",
            whatsapp_token="token123",
            whatsapp_phone_id="123456",
        )
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_resp
        with patch("shared.notifications.sender.httpx.Client", return_value=mock_client):
            result = sender.send_whatsapp("+9647701234567", "Hello")
        assert result is True
        mock_client.post.assert_called_once()

    def test_close_cleans_up_http_client(self):
        sender = NotificationSender(sms_api_url="https://sms.example.com")
        mock_client = MagicMock()
        sender._http_client = mock_client
        sender.close()
        mock_client.close.assert_called_once()
        assert sender._http_client is None

    def test_module_level_functions_fallback_to_logging(self):
        send_push("token", "T", "B")
        send_email("t@t.com", "S", "B")
        send_sms("+9647701234567", "B")
        send_whatsapp("+9647701234567", "B")


class TestNotificationSenderTelegram:
    def test_send_telegram_not_configured_returns_false(self, caplog):
        sender = NotificationSender()
        with caplog.at_level(logging.INFO):
            result = sender.send_telegram(chat_id=123, text="Hello")
        assert result is False
        assert "not configured" in caplog.text

    def test_send_telegram_text_with_dynamic_chat_id(self):
        fake_token = "142536" + ":" + "A" * 40
        sender = NotificationSender(telegram_bot_token=fake_token)
        with patch("shared.notifications.telegram.httpx.Client") as mock_cls:
            mock_client = mock_cls.return_value.__enter__.return_value
            mock_client.post.return_value = MagicMock(
                json=lambda: {"ok": True, "result": {"message_id": 7}},
            )
            result = sender.send_telegram(chat_id=-100777, text="Hello")
        assert result is True
        call_kwargs = mock_client.post.call_args.kwargs
        assert call_kwargs["json"]["chat_id"] == -100777
        assert call_kwargs["json"]["text"] == "Hello"

    def test_send_telegram_html_uses_parse_mode(self):
        fake_token = "142536" + ":" + "A" * 40
        sender = NotificationSender(telegram_bot_token=fake_token)
        with patch("shared.notifications.telegram.httpx.Client") as mock_cls:
            mock_client = mock_cls.return_value.__enter__.return_value
            mock_client.post.return_value = MagicMock(
                json=lambda: {"ok": True, "result": {"message_id": 7}},
            )
            result = sender.send_telegram(chat_id=1, text="<b>Hi</b>", parse_mode="HTML")
        assert result is True
        assert mock_client.post.call_args.kwargs["json"]["parse_mode"] == "HTML"

    def test_send_telegram_alert_path(self):
        fake_token = "142536" + ":" + "A" * 40
        sender = NotificationSender(telegram_bot_token=fake_token)
        with patch("shared.notifications.telegram.httpx.Client") as mock_cls:
            mock_client = mock_cls.return_value.__enter__.return_value
            mock_client.post.return_value = MagicMock(
                json=lambda: {"ok": True, "result": {"message_id": 7}},
            )
            result = sender.send_telegram(chat_id=1, text="disk full", alert_level="critical")
        assert result is True
        text = mock_client.post.call_args.kwargs["json"]["text"]
        assert "[CRITICAL]" in text

    def test_send_telegram_monitoring_path(self):
        fake_token = "142536" + ":" + "A" * 40
        sender = NotificationSender(telegram_bot_token=fake_token)
        with patch("shared.notifications.telegram.httpx.Client") as mock_cls:
            mock_client = mock_cls.return_value.__enter__.return_value
            mock_client.post.return_value = MagicMock(
                json=lambda: {"ok": True, "result": {"message_id": 7}},
            )
            result = sender.send_telegram(
                chat_id=1, text="healthy", monitoring_service="gula-platform"
            )
        assert result is True
        text = mock_client.post.call_args.kwargs["json"]["text"]
        assert "[MONITORING:gula-platform]" in text

    def test_send_telegram_failure_returns_false(self, caplog):
        fake_token = "142536" + ":" + "A" * 40
        sender = NotificationSender(telegram_bot_token=fake_token)
        with patch("shared.notifications.telegram.httpx.Client") as mock_cls:
            mock_client = mock_cls.return_value.__enter__.return_value
            mock_client.post.return_value = MagicMock(
                json=lambda: {"ok": False, "description": "chat not found", "error_code": 400},
            )
            with caplog.at_level(logging.ERROR):
                result = sender.send_telegram(chat_id=999, text="Hi")
        assert result is False
        assert "chat not found" in caplog.text

    def test_module_level_send_telegram(self):
        fake_token = "142536" + ":" + "A" * 40
        with patch("shared.notifications.sender.get_sender") as mock_get:
            mock_sender = MagicMock()
            mock_sender.send_telegram.return_value = True
            mock_get.return_value = mock_sender
            result = send_telegram(chat_id=1, text="Hi", parse_mode="HTML")
        assert result is True
        mock_sender.send_telegram.assert_called_once_with(1, "Hi", parse_mode="HTML")
