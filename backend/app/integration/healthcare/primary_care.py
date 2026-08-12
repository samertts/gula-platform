from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urljoin

import httpx

from backend.app.integration.connectors import BaseConnector, ConnectorRegistry

logger = logging.getLogger("gula.integration.healthcare.primary_care")


class PrimaryCareIntegration(BaseConnector):
    def __init__(
        self,
        name: str = "primary_care_integration",
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
            logger.info("Primary care integration connected")
            return True
        except Exception as exc:
            logger.error("Primary care integration failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        logger.info("Primary care integration disconnected")
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
        if action == "register_patient":
            return await self._register_patient(data)
        if action == "create_visit":
            return await self._create_visit(data)
        if action == "refer_patient":
            return await self._refer_patient(data)
        if action == "get_medical_history":
            return await self._get_medical_history(data)
        if action == "update_vitals":
            return await self._update_vitals(data)
        raise ValueError(f"Unknown primary care action: {action}")

    async def _register_patient(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Primary care connector not connected")
        patient = {
            "national_id": data.get("national_id", ""),
            "first_name": data.get("first_name", ""),
            "last_name": data.get("last_name", ""),
            "date_of_birth": data.get("date_of_birth", ""),
            "gender": data.get("gender", ""),
            "phone": data.get("phone", ""),
            "address": data.get("address", ""),
            "governorate": data.get("governorate", ""),
            "district": data.get("district", ""),
        }
        try:
            resp = await self._client.post(urljoin(self._base_url, "/api/patients"), json=patient)
            if resp.is_success:
                return {"success": True, "patient": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Patient registration failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _create_visit(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Primary care connector not connected")
        visit = {
            "patient_id": data.get("patient_id", ""),
            "visit_date": data.get("visit_date", ""),
            "visit_type": data.get("visit_type", "routine"),
            "complaint": data.get("complaint", ""),
            "diagnosis": data.get("diagnosis", ""),
            "doctor": data.get("doctor", ""),
            "facility_id": data.get("facility_id", ""),
            "notes": data.get("notes", ""),
        }
        try:
            resp = await self._client.post(urljoin(self._base_url, "/api/visits"), json=visit)
            if resp.is_success:
                return {"success": True, "visit": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Visit creation failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _refer_patient(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Primary care connector not connected")
        referral = {
            "patient_id": data.get("patient_id", ""),
            "from_facility": data.get("from_facility", ""),
            "to_facility": data.get("to_facility", ""),
            "specialty": data.get("specialty", ""),
            "reason": data.get("reason", ""),
            "referring_doctor": data.get("referring_doctor", ""),
            "priority": data.get("priority", "routine"),
        }
        try:
            resp = await self._client.post(urljoin(self._base_url, "/api/referrals"), json=referral)
            if resp.is_success:
                return {"success": True, "referral": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Patient referral failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _get_medical_history(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Primary care connector not connected")
        patient_id = data.get("patient_id", "")
        if not patient_id:
            return {"success": False, "error": "patient_id required"}
        try:
            resp = await self._client.get(urljoin(self._base_url, f"/api/patients/{patient_id}/history"))
            if resp.is_success:
                return {"success": True, "history": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Medical history fetch failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _update_vitals(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Primary care connector not connected")
        vitals = {
            "patient_id": data.get("patient_id", ""),
            "visit_id": data.get("visit_id", ""),
            "blood_pressure_systolic": data.get("blood_pressure_systolic", 0),
            "blood_pressure_diastolic": data.get("blood_pressure_diastolic", 0),
            "heart_rate": data.get("heart_rate", 0),
            "temperature": data.get("temperature", 0.0),
            "respiratory_rate": data.get("respiratory_rate", 0),
            "oxygen_saturation": data.get("oxygen_saturation", 0),
            "weight_kg": data.get("weight_kg", 0.0),
            "height_cm": data.get("height_cm", 0.0),
            "measured_at": data.get("measured_at", ""),
        }
        try:
            resp = await self._client.post(urljoin(self._base_url, "/api/vitals"), json=vitals)
            if resp.is_success:
                return {"success": True, "vitals": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Vitals update failed: %s", exc)
            return {"success": False, "error": str(exc)}


ConnectorRegistry.register("primary_care_integration", PrimaryCareIntegration)
