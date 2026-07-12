from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("gula.notifications")


@dataclass
class NotificationMessage:
    to: str
    subject: str = ""
    body: str = ""
    template_id: str = ""
    template_data: dict[str, Any] = field(default_factory=dict)
    priority: str = "normal"


class NotificationSender:
    def __init__(self, fcm_key: str = "", apns_key: str = ""):
        self._fcm_key = fcm_key
        self._apns_key = apns_key

    def send_push(self, token: str, title: str, body: str, data: dict[str, Any] | None = None) -> bool:
        if not self._fcm_key:
            logger.warning("FCM key not configured, skipping push notification")
            return False
        try:
            import firebase_admin
            from firebase_admin import credentials, messaging
            msg = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data={k: str(v) for k, v in (data or {}).items()},
                token=token,
            )
            messaging.send(msg)
            return True
        except Exception as exc:
            logger.error("Push notification failed: %s", exc)
            return False

    def send_email(self, to: str, subject: str, body: str) -> bool:
        logger.info("[EMAIL] To=%s Subject=%s", to, subject)
        return True

    def send_sms(self, to: str, body: str) -> bool:
        logger.info("[SMS] To=%s Body=%s", to, body[:50])
        return True

    def send_whatsapp(self, to: str, body: str) -> bool:
        logger.info("[WHATSAPP] To=%s Body=%s", to, body[:50])
        return True


_sender: NotificationSender | None = None


def get_sender(fcm_key: str = "", apns_key: str = "") -> NotificationSender:
    global _sender
    if _sender is None:
        _sender = NotificationSender(fcm_key, apns_key)
    return _sender


def send_push(token: str, title: str, body: str, data: dict[str, Any] | None = None) -> bool:
    return get_sender().send_push(token, title, body, data)


def send_email(to: str, subject: str, body: str) -> bool:
    return get_sender().send_email(to, subject, body)


def send_sms(to: str, body: str) -> bool:
    return get_sender().send_sms(to, body)


def send_whatsapp(to: str, body: str) -> bool:
    return get_sender().send_whatsapp(to, body)
