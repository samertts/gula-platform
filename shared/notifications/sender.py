from __future__ import annotations

import logging
import os
import smtplib
import ssl
from dataclasses import dataclass, field
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import httpx

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
    def __init__(
        self,
        fcm_key: str = "",
        apns_key: str = "",
        smtp_host: str = "",
        smtp_port: int = 587,
        smtp_user: str = "",
        smtp_pass: str = "",
        smtp_from: str = "",
        smtp_use_tls: bool = True,
        sms_api_url: str = "",
        sms_api_key: str = "",
        sms_sender: str = "",
        whatsapp_api_url: str = "",
        whatsapp_token: str = "",
        whatsapp_phone_id: str = "",
    ):
        self._fcm_key = fcm_key
        self._apns_key = apns_key
        self._smtp_host = smtp_host or os.getenv("SMTP_HOST", "")
        self._smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self._smtp_user = smtp_user or os.getenv("SMTP_USER", "")
        self._smtp_pass = smtp_pass or os.getenv("SMTP_PASS", "")
        self._smtp_from = smtp_from or os.getenv("SMTP_FROM", "")
        self._smtp_use_tls = smtp_use_tls or os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        self._sms_api_url = sms_api_url or os.getenv("SMS_API_URL", "")
        self._sms_api_key = sms_api_key or os.getenv("SMS_API_KEY", "")
        self._sms_sender = sms_sender or os.getenv("SMS_SENDER", "")
        self._whatsapp_api_url = whatsapp_api_url or os.getenv("WHATSAPP_API_URL", "")
        self._whatsapp_token = whatsapp_token or os.getenv("WHATSAPP_TOKEN", "")
        self._whatsapp_phone_id = whatsapp_phone_id or os.getenv("WHATSAPP_PHONE_ID", "")
        self._ntfy_base_url = os.getenv("NTFY_BASE_URL", "").rstrip("/")
        self._ntfy_token = os.getenv("NTFY_TOKEN", "")
        self._ntfy_topic = os.getenv("NTFY_TOPIC", "gula-ops")
        self._http_client: httpx.Client | None = None

    @property
    def http(self) -> httpx.Client:
        if self._http_client is None:
            self._http_client = httpx.Client(timeout=30.0)
        return self._http_client

    def send_push(self, token: str, title: str, body: str, data: dict[str, Any] | None = None) -> bool:
        if not self._fcm_key:
            logger.warning("FCM key not configured, skipping push notification")
            return False
        try:
            from firebase_admin import messaging
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
        if not self._smtp_host:
            logger.info("[EMAIL] SMTP not configured; notification not delivered")
            return True
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = self._smtp_from
            msg["To"] = to
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "html" if "<html" in body else "plain"))

            context = ssl.create_default_context()
            with smtplib.SMTP(self._smtp_host, self._smtp_port) as server:
                if self._smtp_use_tls:
                    server.starttls(context=context)
                if self._smtp_user:
                    server.login(self._smtp_user, self._smtp_pass)
                server.sendmail(self._smtp_from, [to], msg.as_string())

            logger.info("[EMAIL] Notification delivered")
            return True
        except smtplib.SMTPException as exc:
            logger.error("[EMAIL] SMTP delivery failed: %s", exc)
            return False
        except Exception as exc:
            logger.error("[EMAIL] Delivery failed: %s", exc)
            return False

    def send_sms(self, to: str, body: str) -> bool:
        if not self._sms_api_url:
            logger.info("[SMS] API not configured; notification not delivered")
            return True
        try:
            payload = {
                "to": to,
                "text": body,
                "sender": self._sms_sender or None,
            }
            headers = {"Authorization": f"Bearer {self._sms_api_key}"} if self._sms_api_key else {}
            resp = self.http.post(self._sms_api_url, json=payload, headers=headers)
            resp.raise_for_status()
            logger.info("[SMS] Notification delivered")
            return True
        except httpx.HTTPError as exc:
            logger.error("[SMS] Delivery failed: %s", exc)
            return False
        except Exception as exc:
            logger.error("[SMS] Delivery failed: %s", exc)
            return False

    def send_ntfy(
        self,
        message: str,
        title: str = "GULA alert",
        topic: str = "",
        priority: str = "default",
        tags: str = "",
    ) -> bool:
        """Publish a non-sensitive operational alert to a local/self-hosted ntfy server."""
        if not self._ntfy_base_url:
            logger.warning("ntfy base URL not configured, skipping operational notification")
            return False
        if not message or len(message) > 4096:
            logger.warning("ntfy message is empty or exceeds 4096 characters")
            return False
        headers = {
            "Title": title[:250],
            "Priority": priority[:20],
            "Content-Type": "text/plain; charset=utf-8",
        }
        if tags:
            headers["Tags"] = tags[:250]
        if self._ntfy_token:
            headers["Authorization"] = f"Bearer {self._ntfy_token}"
        target_topic = topic or self._ntfy_topic
        url = f"{self._ntfy_base_url}/{target_topic}"
        try:
            resp = self.http.post(url, content=message.encode("utf-8"), headers=headers)
            resp.raise_for_status()
            logger.info("[NTFY] Delivered topic=%s", target_topic)
            return True
        except httpx.HTTPError as exc:
            logger.error("[NTFY] Delivery failed topic=%s: %s", target_topic, exc)
            return False
        except Exception as exc:
            logger.error("[NTFY] Delivery failed topic=%s: %s", target_topic, exc)
            return False

    def send_whatsapp(self, to: str, body: str) -> bool:
        if not self._whatsapp_api_url:
            logger.info("[WHATSAPP] API not configured; notification not delivered")
            return True
        try:
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": body},
            }
            headers = {
                "Authorization": f"Bearer {self._whatsapp_token}",
                "Content-Type": "application/json",
            }
            url = f"{self._whatsapp_api_url}/{self._whatsapp_phone_id}/messages"
            resp = self.http.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            logger.info("[WHATSAPP] Notification delivered")
            return True
        except httpx.HTTPError as exc:
            logger.error("[WHATSAPP] Delivery failed: %s", exc)
            return False
        except Exception as exc:
            logger.error("[WHATSAPP] Delivery failed: %s", exc)
            return False

    def close(self) -> None:
        if self._http_client:
            self._http_client.close()
            self._http_client = None


_sender: NotificationSender | None = None


def get_sender(
    fcm_key: str = "",
    apns_key: str = "",
    smtp_host: str = "",
    smtp_port: int = 587,
    smtp_user: str = "",
    smtp_pass: str = "",
    smtp_from: str = "",
    sms_api_url: str = "",
    sms_api_key: str = "",
    sms_sender: str = "",
    whatsapp_api_url: str = "",
    whatsapp_token: str = "",
    whatsapp_phone_id: str = "",
) -> NotificationSender:
    global _sender
    if _sender is None:
        _sender = NotificationSender(
            fcm_key=fcm_key,
            apns_key=apns_key,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_user=smtp_user,
            smtp_pass=smtp_pass,
            smtp_from=smtp_from,
            sms_api_url=sms_api_url,
            sms_api_key=sms_api_key,
            sms_sender=sms_sender,
            whatsapp_api_url=whatsapp_api_url,
            whatsapp_token=whatsapp_token,
            whatsapp_phone_id=whatsapp_phone_id,
        )
    return _sender


def send_push(token: str, title: str, body: str, data: dict[str, Any] | None = None) -> bool:
    return get_sender().send_push(token, title, body, data)


def send_email(to: str, subject: str, body: str) -> bool:
    return get_sender().send_email(to, subject, body)


def send_sms(to: str, body: str) -> bool:
    return get_sender().send_sms(to, body)


def send_whatsapp(to: str, body: str) -> bool:
    return get_sender().send_whatsapp(to, body)


def send_ntfy(
    message: str,
    title: str = "GULA alert",
    topic: str = "",
    priority: str = "default",
    tags: str = "",
) -> bool:
    return get_sender().send_ntfy(message, title, topic, priority, tags)
