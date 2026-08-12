from __future__ import annotations

import json
import logging
import time
from typing import Any

import httpx

from backend.app.integration.connectors import BaseConnector, ConnectorRegistry

logger = logging.getLogger("gula.integration.connectors.push")

SUPPORTED_PROVIDERS = frozenset({"fcm", "apns", "webpush"})


class PushNotificationConnector(BaseConnector):
    def __init__(
        self,
        name: str = "push",
        version: str = "1.0.0",
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name, version, config)
        self._provider = self.config.get("provider", "fcm")
        if self._provider not in SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported push provider: {self._provider}. Supported: {', '.join(sorted(SUPPORTED_PROVIDERS))}")
        self._fcm_server_key = self.config.get("fcm_server_key", "")
        self._apns_key_id = self.config.get("apns_key_id", "")
        self._apns_team_id = self.config.get("apns_team_id", "")
        self._apns_key = self.config.get("apns_private_key", "")
        self._webpush_public_key = self.config.get("webpush_public_key", "")
        self._webpush_private_key = self.config.get("webpush_private_key", "")
        self._client: httpx.AsyncClient | None = None

    async def connect(self) -> bool:
        try:
            headers = {"Content-Type": "application/json"}
            if self._provider == "fcm" and self._fcm_server_key:
                headers["Authorization"] = f"key={self._fcm_server_key}"
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                verify=self.config.get("verify_ssl", True),
                headers=headers,
            )
            self._connected = True
            logger.info("Push notification connector connected: provider=%s", self._provider)
            return True
        except Exception as exc:
            logger.error("Push notification connector failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        logger.info("Push notification connector disconnected")
        return True

    async def health_check(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": self.name,
            "provider": self._provider,
            "connected": self._connected,
            "timestamp": time.time(),
        }
        if self._provider == "fcm":
            try:
                start = time.monotonic()
                resp = await self._client.post(
                    "https://fcm.googleapis.com/fcm/send",
                    json={"to": "/topics/health", "data": {"ping": "1"}},
                )
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
            return await self._send_push(data)
        if action == "send_topic":
            return await self._send_to_topic(data)
        if action == "send_condition":
            return await self._send_by_condition(data)
        if action == "subscribe":
            return await self._subscribe_topic(data)
        raise ValueError(f"Unknown push action: {action}")

    async def _send_push(self, data: dict[str, Any]) -> dict[str, Any]:
        token = data.get("token", "")
        title = data.get("title", "")
        body = data.get("body", "")
        extra_data = data.get("data", {})
        if not token:
            return {"success": False, "error": "device token required"}

        if self._provider == "fcm":
            return await self._send_fcm(token, title, body, extra_data)
        if self._provider == "apns":
            return await self._send_apns(token, title, body, extra_data)
        if self._provider == "webpush":
            return await self._send_webpush(token, title, body, extra_data)
        return {"success": False, "error": f"Unsupported provider: {self._provider}"}

    async def _send_fcm(self, token: str, title: str, body: str, extra_data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Push connector not connected")
        payload = {
            "to": token,
            "notification": {
                "title": title,
                "body": body,
                "sound": "default",
            },
            "data": extra_data,
            "priority": "high",
        }
        try:
            resp = await self._client.post(
                "https://fcm.googleapis.com/fcm/send",
                json=payload,
            )
            if resp.is_success:
                result = resp.json()
                success_count = result.get("success", 0)
                return {
                    "success": success_count > 0,
                    "message_id": result.get("results", [{}])[0].get("message_id", "") if result.get("results") else "",
                    "provider": "fcm",
                }
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("FCM send failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _send_apns(self, token: str, title: str, body: str, extra_data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Push connector not connected")
        apns_topic = self.config.get("apns_topic", "")
        payload = {
            "aps": {
                "alert": {"title": title, "body": body},
                "sound": "default",
                "badge": extra_data.get("badge", 1),
            },
            "data": extra_data,
        }
        headers = {
            "authorization": f"bearer {self._apns_key}",
            "apns-topic": apns_topic,
            "apns-push-type": "alert",
        }
        if self._apns_key_id:
            headers["apns-key-id"] = self._apns_key_id
        if self._apns_team_id:
            headers["apns-team-id"] = self._apns_team_id
        fcm_apns_url = "https://fcm.googleapis.com/fcm/send"
        try:
            resp = await self._client.post(
                fcm_apns_url,
                json={"to": token, "content_available": True, "apns": payload, "data": extra_data},
                headers=headers,
            )
            return {"success": resp.is_success, "status_code": resp.status_code, "provider": "apns"}
        except Exception as exc:
            logger.error("APNS send failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _send_webpush(self, endpoint: str, title: str, body: str, extra_data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Push connector not connected")
        payload = json.dumps({
            "title": title,
            "body": body,
            "icon": extra_data.get("icon", ""),
            "data": extra_data,
        })
        headers = {
            "Content-Type": "application/json",
            "TTL": "86400",
        }
        if self._webpush_public_key:
            headers["Authorization"] = f"vapid t={self._webpush_public_key}"
        try:
            resp = await self._client.post(endpoint, content=payload, headers=headers)
            return {"success": resp.is_success, "status_code": resp.status_code, "provider": "webpush"}
        except Exception as exc:
            logger.error("Web push failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _send_to_topic(self, data: dict[str, Any]) -> dict[str, Any]:
        if self._provider != "fcm":
            return {"success": False, "error": "topic send only supported for FCM"}
        topic = data.get("topic", "")
        title = data.get("title", "")
        body = data.get("body", "")
        if not topic:
            return {"success": False, "error": "topic required"}
        return await self._send_fcm(f"/topics/{topic}", title, body, data.get("data", {}))

    async def _send_by_condition(self, data: dict[str, Any]) -> dict[str, Any]:
        if self._provider != "fcm":
            return {"success": False, "error": "condition send only supported for FCM"}
        condition = data.get("condition", "")
        title = data.get("title", "")
        body = data.get("body", "")
        if not condition:
            return {"success": False, "error": "condition required"}
        if not self._client:
            raise RuntimeError("Push connector not connected")
        payload = {
            "condition": condition,
            "notification": {"title": title, "body": body, "sound": "default"},
            "data": data.get("data", {}),
            "priority": "high",
        }
        try:
            resp = await self._client.post(
                "https://fcm.googleapis.com/fcm/send",
                json=payload,
            )
            return {"success": resp.is_success, "status_code": resp.status_code, "provider": "fcm"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def _subscribe_topic(self, data: dict[str, Any]) -> dict[str, Any]:
        if self._provider != "fcm":
            return {"success": False, "error": "topic management only supported for FCM"}
        tokens = data.get("tokens", [])
        topic = data.get("topic", "")
        if not tokens or not topic:
            return {"success": False, "error": "tokens and topic required"}
        if not self._client:
            raise RuntimeError("Push connector not connected")
        payload = {
            "to": f"/topics/{topic}",
            "registration_tokens": tokens if isinstance(tokens, list) else [tokens],
        }
        try:
            resp = await self._client.post(
                "https://iid.googleapis.com/iid/v1:batchAdd",
                json=payload,
            )
            return {"success": resp.is_success, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("FCM subscribe failed: %s", exc)
            return {"success": False, "error": str(exc)}


ConnectorRegistry.register("push", PushNotificationConnector)
