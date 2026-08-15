from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urljoin

import httpx

from app.integration.connectors import BaseConnector, ConnectorRegistry

logger = logging.getLogger("gula.integration.healthcare.blood_bank")


class BloodBankIntegration(BaseConnector):
    def __init__(
        self,
        name: str = "blood_bank_integration",
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
            self._client = httpx.AsyncClient(timeout=self._timeout, verify=self._verify_ssl, headers=headers)
            self._connected = True
            logger.info("Blood bank integration connected")
            return True
        except Exception as exc:
            logger.error("Blood bank integration failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        logger.info("Blood bank integration disconnected")
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
        if action == "register_donor":
            return await self._register_donor(data)
        if action == "check_blood_inventory":
            return await self._check_inventory(data)
        if action == "request_blood":
            return await self._request_blood(data)
        if action == "record_donation":
            return await self._record_donation(data)
        if action == "crossmatch":
            return await self._crossmatch(data)
        raise ValueError(f"Unknown blood bank action: {action}")

    async def _register_donor(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Blood bank connector not connected")
        donor = {
            "national_id": data.get("national_id", ""),
            "full_name": data.get("full_name", ""),
            "blood_type": data.get("blood_type", ""),
            "rh_factor": data.get("rh_factor", "+"),
            "date_of_birth": data.get("date_of_birth", ""),
            "phone": data.get("phone", ""),
            "address": data.get("address", ""),
            "weight_kg": data.get("weight_kg", 0),
            "medical_history": data.get("medical_history", ""),
        }
        try:
            resp = await self._client.post(urljoin(self._base_url, "/api/donors"), json=donor)
            if resp.is_success:
                return {"success": True, "donor": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Donor registration failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _check_inventory(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Blood bank connector not connected")
        blood_type = data.get("blood_type", "")
        params = {"blood_type": blood_type} if blood_type else {}
        try:
            resp = await self._client.get(urljoin(self._base_url, "/api/inventory"), params=params)
            if resp.is_success:
                return {"success": True, "inventory": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Blood inventory check failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _request_blood(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Blood bank connector not connected")
        request = {
            "patient_id": data.get("patient_id", ""),
            "blood_type": data.get("blood_type", ""),
            "units_needed": data.get("units_needed", 1),
            "priority": data.get("priority", "urgent"),
            "requesting_doctor": data.get("requesting_doctor", ""),
            "facility_id": data.get("facility_id", ""),
            "reason": data.get("reason", ""),
        }
        try:
            resp = await self._client.post(urljoin(self._base_url, "/api/requests"), json=request)
            if resp.is_success:
                return {"success": True, "request": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Blood request failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _record_donation(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Blood bank connector not connected")
        donation = {
            "donor_id": data.get("donor_id", ""),
            "donation_date": data.get("donation_date", ""),
            "volume_ml": data.get("volume_ml", 450),
            "blood_type": data.get("blood_type", ""),
            "hemoglobin": data.get("hemoglobin", 0),
            "screening_results": data.get("screening_results", {}),
            "collected_by": data.get("collected_by", ""),
        }
        try:
            resp = await self._client.post(urljoin(self._base_url, "/api/donations"), json=donation)
            if resp.is_success:
                return {"success": True, "donation": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Donation recording failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _crossmatch(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Blood bank connector not connected")
        crossmatch = {
            "patient_id": data.get("patient_id", ""),
            "patient_blood_type": data.get("patient_blood_type", ""),
            "donor_unit_id": data.get("donor_unit_id", ""),
            "donor_blood_type": data.get("donor_blood_type", ""),
        }
        try:
            resp = await self._client.post(urljoin(self._base_url, "/api/crossmatch"), json=crossmatch)
            if resp.is_success:
                return {"success": True, "crossmatch": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Crossmatch failed: %s", exc)
            return {"success": False, "error": str(exc)}


ConnectorRegistry.register("blood_bank_integration", BloodBankIntegration)
