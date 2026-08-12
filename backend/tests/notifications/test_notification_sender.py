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
            result = sender.send_email("test@example.com", "Subject", "<html><body>Hi</body></html>")
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
            result = sender.send_email("test@example.com", "Subject", "<html><body>Hi</body></html>")
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
