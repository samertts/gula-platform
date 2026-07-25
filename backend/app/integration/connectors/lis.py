from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urljoin

import httpx

from backend.app.integration.connectors import BaseConnector, ConnectorRegistry

logger = logging.getLogger("gula.integration.connectors.lis")


class LISConnector(BaseConnector):
    def __init__(
        self,
        name: str = "lis",
        version: str = "1.0.0",
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name, version, config)
        self._base_url = self.config.get("base_url", "")
        self._api_key = self.config.get("api_key", "")
        self._client: httpx.AsyncClient | None = None
        self._timeout = httpx.Timeout(self.config.get("timeout", 30.0))
        self._verify_ssl = self.config.get("verify_ssl", True)

    async def connect(self) -> bool:
        try:
            headers = {"Content-Type": "application/json"}
            if self._api_key:
                headers["Authorization"] = f"Bearer {self._api_key}"
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                verify=self._verify_ssl,
                headers=headers,
            )
            self._connected = True
            logger.info("LIS connector connected: %s", self._base_url)
            return True
        except Exception as exc:
            logger.error("LIS connector failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        logger.info("LIS connector disconnected")
        return True

    async def health_check(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": self.name,
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
        action = data.get("action", "")
        if action == "place_order":
            return await self._place_order(data)
        if action == "get_result":
            return await self._get_result(data)
        if action == "send_astm":
            return await self._send_astm(data)
        if action == "send_hl7":
            return await self._send_hl7(data)
        if action == "sync_instruments":
            return await self._sync_instruments()
        raise ValueError(f"Unknown LIS action: {action}")

    async def _place_order(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("LIS connector not connected")
        order = {
            "patient_id": data.get("patient_id", ""),
            "order_id": data.get("order_id", ""),
            "tests": data.get("tests", []),
            "priority": data.get("priority", "routine"),
            "requested_by": data.get("requested_by", ""),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/orders"),
                json=order,
            )
            if resp.is_success:
                return {"success": True, "order": resp.json(), "order_id": order["order_id"]}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("LIS place_order failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _get_result(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("LIS connector not connected")
        order_id = data.get("order_id", "")
        if not order_id:
            return {"success": False, "error": "order_id required"}
        try:
            resp = await self._client.get(
                urljoin(self._base_url, f"/api/orders/{order_id}/results"),
            )
            if resp.is_success:
                return {"success": True, "result": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("LIS get_result failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _send_astm(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("LIS connector not connected")
        message = data.get("message", "")
        frame_type = data.get("frame_type", "header")
        astm_payload = {
            "frame_type": frame_type,
            "message": message,
            "instrument_id": data.get("instrument_id", ""),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/astm"),
                json=astm_payload,
            )
            return {
                "success": resp.is_success,
                "status_code": resp.status_code,
                "response": resp.text,
            }
        except Exception as exc:
            logger.error("LIS ASTM send failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _send_hl7(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("LIS connector not connected")
        message = data.get("message", "")
        message_type = data.get("message_type", "ORM")
        hl7_payload = {
            "message_type": message_type,
            "message": message,
            "sending_app": data.get("sending_app", "GULA_LIS"),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/hl7"),
                json=hl7_payload,
            )
            return {
                "success": resp.is_success,
                "status_code": resp.status_code,
                "response": resp.text,
            }
        except Exception as exc:
            logger.error("LIS HL7 send failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _sync_instruments(self) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("LIS connector not connected")
        try:
            resp = await self._client.get(
                urljoin(self._base_url, "/api/instruments"),
            )
            if resp.is_success:
                instruments = resp.json()
                return {"success": True, "instruments": instruments, "count": len(instruments)}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("LIS instrument sync failed: %s", exc)
            return {"success": False, "error": str(exc)}


ConnectorRegistry.register("lis", LISConnector)
