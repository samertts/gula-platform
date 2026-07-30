from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urljoin

import httpx

from app.integration.connectors import BaseConnector, ConnectorRegistry

logger = logging.getLogger("gula.integration.connectors.sms")

SUPPORTED_PROVIDERS = frozenset({"twilio", "nexmo", "infobip", "custom"})


class SMSConnector(BaseConnector):
    def __init__(
        self,
        name: str = "sms",
        version: str = "1.0.0",
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name, version, config)
        self._provider = self.config.get("provider", "custom")
        if self._provider not in SUPPORTED_PROVIDERS:
            raise ValueError(
                f"Unsupported SMS provider: {self._provider}. Supported: {', '.join(sorted(SUPPORTED_PROVIDERS))}"
            )
        self._base_url = self.config.get("base_url", "")
        self._api_key = self.config.get("api_key", "")
        self._api_secret = self.config.get("api_secret", "")
        self._sender_id = self.config.get("sender_id", "GULA")
        self._client: httpx.AsyncClient | None = None
        self._timeout = httpx.Timeout(self.config.get("timeout", 30.0))
        self._verify_ssl = self.config.get("verify_ssl", True)

    async def connect(self) -> bool:
        try:
            headers = {"Content-Type": "application/json"}
            if self._api_key:
                headers["Authorization"] = f"Bearer {self._api_key}"
            if self._provider == "twilio":
                headers["Authorization"] = ""
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                verify=self._verify_ssl,
                headers=headers,
            )
            self._connected = True
            logger.info("SMS connector connected: provider=%s", self._provider)
            return True
        except Exception as exc:
            logger.error("SMS connector failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        logger.info("SMS connector disconnected")
        return True

    async def health_check(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": self.name,
            "provider": self._provider,
            "connected": self._connected,
            "timestamp": time.time(),
        }
        if not self._client:
            result["status"] = "disconnected"
            return result
        try:
            start = time.monotonic()
            resp = await self._client.get(urljoin(self._base_url, "/health"))
            result["latency_ms"] = (time.monotonic() - start) * 1000
            result["status"] = "healthy" if resp.is_success else "degraded"
            result["status_code"] = resp.status_code
        except Exception as exc:
            result["status"] = "unhealthy"
            result["error"] = str(exc)
        return result

    async def send(self, data: dict[str, Any]) -> dict[str, Any]:
        action = data.get("action", "send")
        if action == "send":
            return await self._send_sms(data)
        if action == "send_bulk":
            return await self._send_bulk(data)
        if action == "send_template":
            return await self._send_template(data)
        if action == "track_delivery":
            return await self._track_delivery(data)
        raise ValueError(f"Unknown SMS action: {action}")

    async def _send_sms(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("SMS connector not connected")
        to = data.get("to", "")
        message = data.get("message", "")
        if not to or not message:
            return {"success": False, "error": "recipient (to) and message required"}
        payload = {
            "to": to,
            "message": message,
            "sender_id": data.get("sender_id", self._sender_id),
            "provider": self._provider,
        }
        if self._provider == "twilio":
            return await self._send_via_twilio(payload)
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/sms/send"),
                json=payload,
            )
            if resp.is_success:
                result = resp.json()
                return {
                    "success": True,
                    "message_id": result.get("message_id", ""),
                    "status": result.get("status", "sent"),
                    "provider": self._provider,
                }
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("SMS send failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _send_via_twilio(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("SMS connector not connected")
        twilio_account = self.config.get("twilio_account_sid", "")
        twilio_token = self._api_secret
        try:
            auth = httpx.BasicAuth(twilio_account, twilio_token)
            twilio_payload = {
                "To": payload["to"],
                "From": payload["sender_id"],
                "Body": payload["message"],
            }
            resp = await self._client.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{twilio_account}/Messages.json",
                data=twilio_payload,
                auth=auth,
            )
            if resp.is_success:
                result = resp.json()
                return {
                    "success": True,
                    "message_id": result.get("sid", ""),
                    "status": result.get("status", "sent"),
                    "provider": "twilio",
                }
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Twilio SMS failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _send_bulk(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("SMS connector not connected")
        recipients = data.get("recipients", [])
        message = data.get("message", "")
        if not recipients or not message:
            return {"success": False, "error": "recipients and message required"}
        results = []
        for recipient in recipients:
            result = await self._send_sms(
                {"to": recipient, "message": message, "sender_id": data.get("sender_id")}
            )
            results.append(result)
        successful = sum(1 for r in results if r.get("success"))
        return {
            "success": successful == len(recipients),
            "total": len(recipients),
            "successful": successful,
            "failed": len(recipients) - successful,
            "results": results,
        }

    async def _send_template(self, data: dict[str, Any]) -> dict[str, Any]:
        template_id = data.get("template_id", "")
        to = data.get("to", "")
        variables = data.get("variables", {})
        if not template_id or not to:
            return {"success": False, "error": "template_id and to required"}
        message = self._render_template(template_id, variables)
        if not message:
            return {"success": False, "error": f"Template not found: {template_id}"}
        return await self._send_sms(
            {"to": to, "message": message, "sender_id": data.get("sender_id")}
        )

    async def _track_delivery(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("SMS connector not connected")
        message_id = data.get("message_id", "")
        if not message_id:
            return {"success": False, "error": "message_id required"}
        try:
            resp = await self._client.get(
                urljoin(self._base_url, f"/api/sms/{message_id}/status"),
            )
            if resp.is_success:
                return {"success": True, "delivery": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("SMS delivery tracking failed: %s", exc)
            return {"success": False, "error": str(exc)}

    def _render_template(self, template_id: str, variables: dict[str, str]) -> str:
        templates = self.config.get("templates", {})
        template = templates.get(template_id, "")
        if not template:
            return ""
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{{${key}}}}}", value).replace(f"{{{{{key}}}}}", value)
        return result


ConnectorRegistry.register("sms", SMSConnector)
