from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urljoin

import httpx

from app.integration.connectors import BaseConnector, ConnectorRegistry

logger = logging.getLogger("gula.integration.healthcare.laboratories")


class LaboratoryIntegration(BaseConnector):
    def __init__(
        self,
        name: str = "laboratory_integration",
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
            headers["X-LIS-Version"] = self.config.get("lis_version", "2.0")
            self._client = httpx.AsyncClient(timeout=self._timeout, verify=self._verify_ssl, headers=headers)
            self._connected = True
            logger.info("Laboratory integration connected")
            return True
        except Exception as exc:
            logger.error("Laboratory integration failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        logger.info("Laboratory integration disconnected")
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
        if action == "create_order":
            return await self._create_lab_order(data)
        if action == "submit_result":
            return await self._submit_result(data)
        if action == "get_test_catalog":
            return await self._get_test_catalog(data)
        if action == "sync_panel":
            return await self._sync_test_panel(data)
        if action == "validate_result":
            return await self._validate_result(data)
        if action == "get_patient_results":
            return await self._get_patient_results(data)
        raise ValueError(f"Unknown laboratory action: {action}")

    async def _create_lab_order(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Laboratory connector not connected")
        order = {
            "patient_id": data.get("patient_id", ""),
            "national_id": data.get("national_id", ""),
            "tests": data.get("tests", []),
            "priority": data.get("priority", "routine"),
            "ordering_doctor": data.get("ordering_doctor", ""),
            "diagnosis": data.get("diagnosis", ""),
            "specimen_type": data.get("specimen_type", ""),
            "notes": data.get("notes", ""),
        }
        try:
            resp = await self._client.post(urljoin(self._base_url, "/api/orders"), json=order)
            if resp.is_success:
                return {"success": True, "order": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Lab order creation failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _submit_result(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Laboratory connector not connected")
        result = {
            "order_id": data.get("order_id", ""),
            "test_code": data.get("test_code", ""),
            "test_name": data.get("test_name", ""),
            "value": data.get("value", ""),
            "unit": data.get("unit", ""),
            "reference_range": data.get("reference_range", ""),
            "flag": data.get("flag", "normal"),
            "performed_by": data.get("performed_by", ""),
            "performed_at": data.get("performed_at", ""),
            "instrument_id": data.get("instrument_id", ""),
        }
        try:
            resp = await self._client.post(urljoin(self._base_url, "/api/results"), json=result)
            if resp.is_success:
                return {"success": True, "result_id": resp.json().get("id", "")}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Lab result submission failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _get_test_catalog(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Laboratory connector not connected")
        try:
            resp = await self._client.get(urljoin(self._base_url, "/api/tests"))
            if resp.is_success:
                tests = resp.json()
                return {"success": True, "tests": tests, "count": len(tests) if isinstance(tests, list) else 0}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Test catalog fetch failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _sync_test_panel(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Laboratory connector not connected")
        panel = {
            "panel_code": data.get("panel_code", ""),
            "panel_name": data.get("panel_name", ""),
            "tests": data.get("tests", []),
            "department": data.get("department", ""),
            "active": data.get("active", True),
        }
        try:
            resp = await self._client.post(urljoin(self._base_url, "/api/panels/sync"), json=panel)
            if resp.is_success:
                return {"success": True, "panel": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Panel sync failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _validate_result(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Laboratory connector not connected")
        validation = {
            "result_id": data.get("result_id", ""),
            "validated_by": data.get("validated_by", ""),
            "validated_at": data.get("validated_at", ""),
            "notes": data.get("notes", ""),
        }
        try:
            resp = await self._client.post(urljoin(self._base_url, "/api/results/validate"), json=validation)
            if resp.is_success:
                return {"success": True, "validated": True}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Result validation failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _get_patient_results(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Laboratory connector not connected")
        patient_id = data.get("patient_id", "")
        national_id = data.get("national_id", "")
        if not patient_id and not national_id:
            return {"success": False, "error": "patient_id or national_id required"}
        params = {}
        if patient_id:
            params["patient_id"] = patient_id
        if national_id:
            params["national_id"] = national_id
        try:
            resp = await self._client.get(urljoin(self._base_url, "/api/results"), params=params)
            if resp.is_success:
                results = resp.json()
                return {"success": True, "results": results, "count": len(results) if isinstance(results, list) else 0}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Patient results fetch failed: %s", exc)
            return {"success": False, "error": str(exc)}


ConnectorRegistry.register("laboratory_integration", LaboratoryIntegration)
