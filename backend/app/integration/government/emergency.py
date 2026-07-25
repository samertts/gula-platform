from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urljoin

import httpx

from backend.app.integration.connectors import BaseConnector, ConnectorRegistry

logger = logging.getLogger("gula.integration.government.emergency")


class EmergencyServices(BaseConnector):
    def __init__(
        self,
        name: str = "emergency_services",
        version: str = "1.0.0",
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name, version, config)
        self._base_url = self.config.get("base_url", "")
        self._api_key = self.config.get("api_key", "")
        self._client: httpx.AsyncClient | None = None
        self._timeout = httpx.Timeout(self.config.get("timeout", 15.0))
        self._verify_ssl = self.config.get("verify_ssl", True)

    async def connect(self) -> bool:
        try:
            headers = {"Content-Type": "application/json"}
            if self._api_key:
                headers["Authorization"] = f"Bearer {self._api_key}"
            self._client = httpx.AsyncClient(
                timeout=self._timeout, verify=self._verify_ssl, headers=headers
            )
            self._connected = True
            logger.info("Emergency services connector connected")
            return True
        except Exception as exc:
            logger.error("Emergency services connector failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        logger.info("Emergency services connector disconnected")
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
        if action == "alert":
            return await self._send_emergency_alert(data)
        if action == "dispatch":
            return await self._dispatch_ambulance(data)
        if action == "status":
            return await self._get_emergency_status(data)
        if action == "mass_notification":
            return await self._mass_notification(data)
        raise ValueError(f"Unknown Emergency action: {action}")

    async def _send_emergency_alert(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Emergency connector not connected")
        alert = {
            "alert_type": data.get("alert_type", "medical"),
            "severity": data.get("severity", "low"),
            "location": data.get("location", {}),
            "description": data.get("description", ""),
            "reported_by": data.get("reported_by", ""),
            "facility_id": data.get("facility_id", ""),
            "num_casualties": data.get("num_casualties", 0),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/emergency/alerts"),
                json=alert,
            )
            if resp.is_success:
                return {
                    "success": True,
                    "alert_id": resp.json().get("id", ""),
                    "acknowledged": True,
                }
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Emergency alert failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _dispatch_ambulance(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Emergency connector not connected")
        dispatch = {
            "incident_location": data.get("incident_location", {}),
            "destination": data.get("destination", ""),
            "patient_condition": data.get("patient_condition", ""),
            "priority": data.get("priority", "normal"),
            "requested_by": data.get("requested_by", ""),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/emergency/dispatch"),
                json=dispatch,
            )
            if resp.is_success:
                result = resp.json()
                return {
                    "success": True,
                    "ambulance_id": result.get("ambulance_id", ""),
                    "eta_minutes": result.get("eta_minutes", 0),
                }
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Ambulance dispatch failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _get_emergency_status(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Emergency connector not connected")
        alert_id = data.get("alert_id", "")
        if not alert_id:
            return {"success": False, "error": "alert_id required"}
        try:
            resp = await self._client.get(
                urljoin(self._base_url, f"/api/emergency/alerts/{alert_id}")
            )
            if resp.is_success:
                return {"success": True, "status": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Emergency status fetch failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _mass_notification(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Emergency connector not connected")
        notification = {
            "channels": data.get("channels", ["sms", "push"]),
            "message": data.get("message", ""),
            "severity": data.get("severity", "info"),
            "region": data.get("region", ""),
            "target_groups": data.get("target_groups", ["all"]),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/emergency/notifications"),
                json=notification,
            )
            if resp.is_success:
                return {
                    "success": True,
                    "notification_id": resp.json().get("id", ""),
                    "recipients_reached": resp.json().get("recipients", 0),
                }
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Mass notification failed: %s", exc)
            return {"success": False, "error": str(exc)}


ConnectorRegistry.register("emergency_services", EmergencyServices)
