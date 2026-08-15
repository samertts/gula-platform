from __future__ import annotations

from shared.notifications.sender import NotificationSender


def test_notification_logs_do_not_include_recipient_or_message(caplog, monkeypatch):
    for name in (
        "SMTP_HOST",
        "SMS_API_URL",
        "WHATSAPP_API_URL",
    ):
        monkeypatch.delenv(name, raising=False)

    recipient = "patient@example.test"
    phone = "+9647700000000"
    secret_message = "patient diagnosis must never appear in logs"
    sender = NotificationSender()

    with caplog.at_level("INFO", logger="gula.notifications"):
        assert sender.send_email(recipient, "clinical reminder", secret_message)
        assert sender.send_sms(phone, secret_message)
        assert sender.send_whatsapp(phone, secret_message)

    assert recipient not in caplog.text
    assert phone not in caplog.text
    assert secret_message not in caplog.text
