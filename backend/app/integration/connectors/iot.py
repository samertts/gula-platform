from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from backend.app.integration.connectors import BaseConnector, ConnectorRegistry

logger = logging.getLogger("gula.integration.connectors.iot")

SUPPORTED_PROTOCOLS = frozenset({"mqtt", "coap", "http", "lorawan", "zigbee"})


class IoTConnector(BaseConnector):
    def __init__(
        self,
        name: str = "iot",
        version: str = "1.0.0",
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name, version, config)
        self._protocol = self.config.get("protocol", "mqtt")
        if self._protocol not in SUPPORTED_PROTOCOLS:
            raise ValueError(
                f"Unsupported IoT protocol: {self._protocol}. "
                f"Supported: {', '.join(sorted(SUPPORTED_PROTOCOLS))}"
            )
        self._broker_url = self.config.get("broker_url", "")
        self._hub_url = self.config.get("hub_url", "")
        self._device_id = self.config.get("device_id", "")
        self._device_key = self.config.get("device_key", "")
        self._api_key = self.config.get("api_key", "")
        self._client: httpx.AsyncClient | None = None
        self._timeout = httpx.Timeout(self.config.get("timeout", 30.0))
        self._verify_ssl = self.config.get("verify_ssl", True)

    async def connect(self) -> bool:
        try:
            headers = {"Content-Type": "application/json"}
            if self._api_key:
                headers["Authorization"] = f"Bearer {self._api_key}"
            if self._device_key:
                headers["X-Device-Key"] = self._device_key
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                verify=self._verify_ssl,
                headers=headers,
            )
            self._connected = True
            logger.info("IoT connector connected: protocol=%s device=%s", self._protocol, self._device_id)
            return True
        except Exception as exc:
            logger.error("IoT connector failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        logger.info("IoT connector disconnected")
        return True

    async def health_check(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": self.name,
            "protocol": self._protocol,
            "device_id": self._device_id,
            "connected": self._connected,
            "timestamp": time.time(),
        }
        if not self._client:
            result["status"] = "disconnected"
            return result
        try:
            start = time.monotonic()
            base = self._hub_url or self._broker_url
            if base:
                resp = await self._client.get(f"{base.rstrip('/')}/health")
                result["latency_ms"] = (time.monotonic() - start) * 1000
                result["status"] = "healthy" if resp.is_success else "degraded"
                result["status_code"] = resp.status_code
            else:
                result["status"] = "unknown"
        except Exception as exc:
            result["status"] = "unhealthy"
            result["error"] = str(exc)
        return result

    async def send(self, data: dict[str, Any]) -> dict[str, Any]:
        action = data.get("action", "")
        if action == "publish_telemetry":
            return await self._publish_telemetry(data)
        if action == "send_command":
            return await self._send_command(data)
        if action == "register_device":
            return await self._register_device(data)
        if action == "get_device_twin":
            return await self._get_device_twin(data)
        if action == "update_device_twin":
            return await self._update_device_twin(data)
        if action == "list_devices":
            return await self._list_devices(data)
        if action == "get_telemetry":
            return await self._get_telemetry(data)
        raise ValueError(f"Unknown IoT action: {action}")

    async def _publish_telemetry(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("IoT connector not connected")
        device_id = data.get("device_id", self._device_id)
        telemetry = data.get("telemetry", {})
        timestamp = data.get("timestamp", time.time())
        if not device_id:
            return {"success": False, "error": "device_id required"}
        if not telemetry:
            return {"success": False, "error": "telemetry data required"}
        payload = {
            "device_id": device_id,
            "protocol": self._protocol,
            "timestamp": timestamp,
            "data": telemetry,
            "metadata": data.get("metadata", {}),
        }
        try:
            base = self._hub_url or self._broker_url
            url = f"{base.rstrip('/')}/api/devices/{device_id}/telemetry"
            resp = await self._client.post(url, json=payload)
            if resp.is_success:
                return {"success": True, "device_id": device_id, "message_id": resp.json().get("id", "")}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("IoT telemetry publish failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _send_command(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("IoT connector not connected")
        device_id = data.get("device_id", self._device_id)
        command = data.get("command", "")
        params = data.get("params", {})
        if not device_id or not command:
            return {"success": False, "error": "device_id and command required"}
        payload = {
            "command": command,
            "params": params,
            "protocol": self._protocol,
        }
        try:
            base = self._hub_url or self._broker_url
            url = f"{base.rstrip('/')}/api/devices/{device_id}/commands"
            resp = await self._client.post(url, json=payload)
            if resp.is_success:
                return {"success": True, "device_id": device_id, "result": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("IoT command send failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _register_device(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("IoT connector not connected")
        device_id = data.get("device_id", "")
        device_type = data.get("device_type", "generic")
        if not device_id:
            return {"success": False, "error": "device_id required"}
        payload = {
            "device_id": device_id,
            "device_type": device_type,
            "protocol": self._protocol,
            "name": data.get("name", device_id),
            "location": data.get("location", ""),
            "tags": data.get("tags", []),
            "properties": data.get("properties", {}),
        }
        try:
            base = self._hub_url or self._broker_url
            url = f"{base.rstrip('/')}/api/devices"
            resp = await self._client.post(url, json=payload)
            if resp.is_success:
                return {"success": True, "device_id": device_id, "device": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("IoT device registration failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _get_device_twin(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("IoT connector not connected")
        device_id = data.get("device_id", self._device_id)
        if not device_id:
            return {"success": False, "error": "device_id required"}
        try:
            base = self._hub_url or self._broker_url
            url = f"{base.rstrip('/')}/api/devices/{device_id}/twin"
            resp = await self._client.get(url)
            if resp.is_success:
                return {"success": True, "device_id": device_id, "twin": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("IoT device twin fetch failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _update_device_twin(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("IoT connector not connected")
        device_id = data.get("device_id", self._device_id)
        properties = data.get("properties", {})
        if not device_id or not properties:
            return {"success": False, "error": "device_id and properties required"}
        try:
            base = self._hub_url or self._broker_url
            url = f"{base.rstrip('/')}/api/devices/{device_id}/twin"
            resp = await self._client.patch(url, json={"properties": properties})
            if resp.is_success:
                return {"success": True, "device_id": device_id, "twin": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("IoT device twin update failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _list_devices(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("IoT connector not connected")
        params: dict[str, Any] = {
            "limit": data.get("limit", 100),
            "offset": data.get("offset", 0),
        }
        if data.get("device_type"):
            params["device_type"] = data["device_type"]
        if data.get("status"):
            params["status"] = data["status"]
        try:
            base = self._hub_url or self._broker_url
            url = f"{base.rstrip('/')}/api/devices"
            resp = await self._client.get(url, params=params)
            if resp.is_success:
                body = resp.json()
                devices = body.get("devices", body.get("items", []))
                return {"success": True, "devices": devices, "count": len(devices)}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("IoT device list failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _get_telemetry(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("IoT connector not connected")
        device_id = data.get("device_id", self._device_id)
        if not device_id:
            return {"success": False, "error": "device_id required"}
        params: dict[str, Any] = {
            "limit": data.get("limit", 100),
            "offset": data.get("offset", 0),
        }
        if data.get("from"):
            params["from"] = data["from"]
        if data.get("to"):
            params["to"] = data["to"]
        metric = data.get("metric", "")
        if metric:
            params["metric"] = metric
        try:
            base = self._hub_url or self._broker_url
            url = f"{base.rstrip('/')}/api/devices/{device_id}/telemetry"
            resp = await self._client.get(url, params=params)
            if resp.is_success:
                body = resp.json()
                telemetry = body.get("telemetry", body.get("data", []))
                return {"success": True, "device_id": device_id, "telemetry": telemetry, "count": len(telemetry)}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("IoT telemetry fetch failed: %s", exc)
            return {"success": False, "error": str(exc)}


ConnectorRegistry.register("iot", IoTConnector)
