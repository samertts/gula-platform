from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urljoin

import httpx

from backend.app.integration.connectors import BaseConnector, ConnectorRegistry
from backend.app.notifications.service import NotificationResult, get_service

logger = logging.getLogger("gula.integration.connectors.email")


class EmailConnector(BaseConnector):
    def __init__(
        self,
        name: str = "email",
        version: str = "1.0.0",
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name, version, config)
        self._smtp_host = self.config.get("smtp_host", "")
        self._smtp_port = self.config.get("smtp_port", 587)
        self._smtp_user = self.config.get("smtp_user", "")
        self._smtp_password = self.config.get("smtp_password", "")
        self._from_address = self.config.get("from_address", "noreply@gula.iq")
        self._from_name = self.config.get("from_name", "GULA Platform")
        self._api_url = self.config.get("api_url", "")
        self._api_key = self.config.get("api_key", "")
        self._use_api = bool(self._api_url and self._api_key)
        self._notification_service = get_service()
        self._client: httpx.AsyncClient | None = None

    async def connect(self) -> bool:
        try:
            if self._use_api:
                self._client = httpx.AsyncClient(
                    timeout=httpx.Timeout(30.0),
                    verify=self.config.get("verify_ssl", True),
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                )
            logger.info("Email connector connected: use_api=%s", self._use_api)
            self._connected = True
            return True
        except Exception as exc:
            logger.error("Email connector failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        logger.info("Email connector disconnected")
        return True

    async def health_check(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": self.name,
            "connected": self._connected,
            "timestamp": time.time(),
        }
        if self._use_api and self._client:
            try:
                start = time.monotonic()
                resp = await self._client.get(urljoin(self._api_url, "/health"))
                result["latency_ms"] = (time.monotonic() - start) * 1000
                result["status"] = "healthy" if resp.is_success else "degraded"
                result["status_code"] = resp.status_code
            except Exception as exc:
                result["status"] = "unhealthy"
                result["error"] = str(exc)
        else:
            result["status"] = "healthy" if self._connected else "disconnected"
        return result

    async def send(self, data: dict[str, Any]) -> dict[str, Any]:
        action = data.get("action", "send")
        if action == "send":
            return await self._send_email(data)
        if action == "send_template":
            return await self._send_template(data)
        if action == "send_with_attachment":
            return await self._send_with_attachment(data)
        raise ValueError(f"Unknown email action: {action}")

    async def _send_email(self, data: dict[str, Any]) -> dict[str, Any]:
        to = data.get("to", "")
        subject = data.get("subject", "")
        body = data.get("body", "")
        html_body = data.get("html_body", "")
        cc = data.get("cc", [])
        bcc = data.get("bcc", [])
        if not to or not subject:
            return {"success": False, "error": "recipient (to) and subject required"}

        if self._use_api:
            return await self._send_via_api(to, subject, body, html_body, cc, bcc)
        return self._send_via_smtp(to, subject, body)

    async def _send_via_api(self, to: str, subject: str, body: str, html_body: str, cc: list[str], bcc: list[str]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Email connector not connected")
        payload = {
            "from": f"{self._from_name} <{self._from_address}>",
            "to": [to] if isinstance(to, str) else to,
            "subject": subject,
            "text": body,
            "html": html_body or None,
        }
        if cc:
            payload["cc"] = cc if isinstance(cc, list) else [cc]
        if bcc:
            payload["bcc"] = bcc if isinstance(bcc, list) else [bcc]
        try:
            resp = await self._client.post(
                urljoin(self._api_url, "/api/email/send"),
                json=payload,
            )
            if resp.is_success:
                result = resp.json()
                return {"success": True, "message_id": result.get("id", ""), "channel": "email_api"}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Email API send failed: %s", exc)
            return {"success": False, "error": str(exc)}

    def _send_via_smtp(self, to: str, subject: str, body: str) -> dict[str, Any]:
        try:
            result: NotificationResult = self._notification_service.send_email(
                to=to,
                subject=subject,
                body=body,
            )
            if result.success:
                return {"success": True, "channel": "email_smtp", "audit_log_id": result.audit_log_id}
            return {"success": False, "error": result.error, "channel": "email_smtp"}
        except Exception as exc:
            logger.error("Email SMTP send failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _send_template(self, data: dict[str, Any]) -> dict[str, Any]:
        to = data.get("to", "")
        template_id = data.get("template_id", "")
        template_data = data.get("template_data", {})
        if not to or not template_id:
            return {"success": False, "error": "to and template_id required"}
        try:
            result: NotificationResult = self._notification_service.send_template(
                template_id=template_id,
                channel="email",
                to=to,
                data=template_data,
            )
            if result.success:
                return {"success": True, "channel": "email_template", "audit_log_id": result.audit_log_id}
            return {"success": False, "error": result.error}
        except Exception as exc:
            logger.error("Email template send failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _send_with_attachment(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Email connector not connected")
        to = data.get("to", "")
        subject = data.get("subject", "")
        body = data.get("body", "")
        attachments = data.get("attachments", [])
        if not to or not subject:
            return {"success": False, "error": "to and subject required"}
        if not attachments:
            return await self._send_email(data)
        payload = {
            "from": f"{self._from_name} <{self._from_address}>",
            "to": [to] if isinstance(to, str) else to,
            "subject": subject,
            "text": body,
            "attachments": attachments,
        }
        try:
            resp = await self._client.post(
                urljoin(self._api_url, "/api/email/send"),
                json=payload,
            )
            if resp.is_success:
                return {"success": True, "message_id": resp.json().get("id", ""), "attachment_count": len(attachments)}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Email with attachment failed: %s", exc)
            return {"success": False, "error": str(exc)}


ConnectorRegistry.register("email", EmailConnector)
