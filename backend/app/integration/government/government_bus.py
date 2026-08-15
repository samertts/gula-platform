from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urljoin

import httpx

from app.integration.connectors import BaseConnector, ConnectorRegistry

logger = logging.getLogger("gula.integration.government.gov_bus")


class GovernmentBus(BaseConnector):
    def __init__(
        self,
        name: str = "government_bus",
        version: str = "1.0.0",
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name, version, config)
        self._base_url = self.config.get("base_url", "")
        self._api_key = self.config.get("api_key", "")
        self._client_id = self.config.get("client_id", "")
        self._client_secret = self.config.get("client_secret", "")
        self._access_token: str = ""
        self._client: httpx.AsyncClient | None = None
        self._timeout = httpx.Timeout(self.config.get("timeout", 30.0))
        self._verify_ssl = self.config.get("verify_ssl", True)

    async def connect(self) -> bool:
        try:
            self._client = httpx.AsyncClient(timeout=self._timeout, verify=self._verify_ssl)
            if self._client_id and self._client_secret:
                await self._authenticate()
            self._connected = True
            logger.info("GovBus connector connected: %s", self._base_url)
            return True
        except Exception as exc:
            logger.error("GovBus connector failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        self._access_token = ""
        logger.info("GovBus connector disconnected")
        return True

    async def health_check(self) -> dict[str, Any]:
        result: dict[str, Any] = {"name": self.name, "connected": self._connected, "timestamp": time.time()}
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
        action = data.get("action", "")
        if action == "publish_message":
            return await self._publish_message(data)
        if action == "subscribe_channel":
            return await self._subscribe_channel(data)
        if action == "request_service":
            return await self._request_service(data)
        if action == "exchange_data":
            return await self._exchange_data(data)
        if action == "get_service_status":
            return await self._get_service_status(data)
        raise ValueError(f"Unknown GovBus action: {action}")

    async def _authenticate(self) -> None:
        if not self._client:
            raise RuntimeError("GovBus connector not connected")
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/auth/token"),
                json={"client_id": self._client_id, "client_secret": self._client_secret, "grant_type": "client_credentials"},
            )
            if resp.is_success:
                result = resp.json()
                self._access_token = result.get("access_token", "")
                self._client.headers["Authorization"] = f"Bearer {self._access_token}"
                logger.info("GovBus authenticated")
        except Exception as exc:
            logger.error("GovBus authentication failed: %s", exc)

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        if self._api_key:
            headers["X-API-Key"] = self._api_key
        return headers

    async def _publish_message(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("GovBus connector not connected")
        message = {
            "channel": data.get("channel", ""),
            "event_type": data.get("event_type", ""),
            "payload": data.get("payload", {}),
            "priority": data.get("priority", "normal"),
            "correlation_id": data.get("correlation_id", ""),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/bus/publish"),
                json=message,
                headers=self._headers(),
            )
            if resp.is_success:
                return {"success": True, "message_id": resp.json().get("message_id", "")}
            if resp.status_code == 401:
                await self._authenticate()
                return await self._publish_message(data)
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("GovBus publish failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _subscribe_channel(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("GovBus connector not connected")
        subscription = {
            "channel": data.get("channel", ""),
            "callback_url": data.get("callback_url", ""),
            "events": data.get("events", ["*"]),
            "description": data.get("description", ""),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/bus/subscribe"),
                json=subscription,
                headers=self._headers(),
            )
            if resp.is_success:
                return {"success": True, "subscription": resp.json()}
            if resp.status_code == 401:
                await self._authenticate()
                return await self._subscribe_channel(data)
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("GovBus subscribe failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _request_service(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("GovBus connector not connected")
        request = {
            "service_code": data.get("service_code", ""),
            "request_data": data.get("request_data", {}),
            "requester_id": data.get("requester_id", ""),
            "callback_url": data.get("callback_url", ""),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/bus/services/request"),
                json=request,
                headers=self._headers(),
            )
            if resp.is_success:
                return {"success": True, "request_id": resp.json().get("request_id", ""), "status": resp.json().get("status", "pending")}
            if resp.status_code == 401:
                await self._authenticate()
                return await self._request_service(data)
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("GovBus service request failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _exchange_data(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("GovBus connector not connected")
        exchange = {
            "sender": data.get("sender", "GULA"),
            "recipient": data.get("recipient", ""),
            "data_type": data.get("data_type", ""),
            "payload": data.get("payload", {}),
            "encryption": data.get("encryption", "none"),
            "ttl_seconds": data.get("ttl_seconds", 3600),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/bus/exchange"),
                json=exchange,
                headers=self._headers(),
            )
            if resp.is_success:
                return {"success": True, "exchange_id": resp.json().get("exchange_id", "")}
            if resp.status_code == 401:
                await self._authenticate()
                return await self._exchange_data(data)
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("GovBus data exchange failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _get_service_status(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("GovBus connector not connected")
        service_code = data.get("service_code", "")
        if not service_code:
            return {"success": False, "error": "service_code required"}
        try:
            resp = await self._client.get(
                urljoin(self._base_url, f"/api/bus/services/{service_code}/status"),
                headers=self._headers(),
            )
            if resp.is_success:
                return {"success": True, "status": resp.json()}
            if resp.status_code == 401:
                await self._authenticate()
                return await self._get_service_status(data)
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("GovBus service status failed: %s", exc)
            return {"success": False, "error": str(exc)}


ConnectorRegistry.register("government_bus", GovernmentBus)
