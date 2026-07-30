from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urljoin

import httpx

from app.integration.connectors import BaseConnector, ConnectorRegistry

logger = logging.getLogger("gula.integration.healthcare.hospitals")


class HospitalIntegration(BaseConnector):
    def __init__(
        self,
        name: str = "hospital_integration",
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
                timeout=self._timeout, verify=self._verify_ssl, headers=headers
            )
            self._connected = True
            logger.info("Hospital integration connected")
            return True
        except Exception as exc:
            logger.error("Hospital integration failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        logger.info("Hospital integration disconnected")
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
        if action == "admit_patient":
            return await self._admit_patient(data)
        if action == "transfer_patient":
            return await self._transfer_patient(data)
        if action == "discharge_patient":
            return await self._discharge_patient(data)
        if action == "get_ward_occupancy":
            return await self._get_ward_occupancy(data)
        if action == "schedule_surgery":
            return await self._schedule_surgery(data)
        if action == "get_patient_history":
            return await self._get_patient_history(data)
        raise ValueError(f"Unknown hospital action: {action}")

    async def _admit_patient(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Hospital connector not connected")
        admission = {
            "patient_id": data.get("patient_id", ""),
            "national_id": data.get("national_id", ""),
            "full_name": data.get("full_name", ""),
            "ward": data.get("ward", ""),
            "bed_number": data.get("bed_number", ""),
            "admitting_doctor": data.get("admitting_doctor", ""),
            "diagnosis": data.get("diagnosis", ""),
            "admission_type": data.get("admission_type", "emergency"),
            "referring_facility": data.get("referring_facility", ""),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/admissions"), json=admission
            )
            if resp.is_success:
                return {"success": True, "admission": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Hospital admission failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _transfer_patient(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Hospital connector not connected")
        transfer = {
            "patient_id": data.get("patient_id", ""),
            "from_ward": data.get("from_ward", ""),
            "to_ward": data.get("to_ward", ""),
            "reason": data.get("reason", ""),
            "transferring_doctor": data.get("transferring_doctor", ""),
        }
        try:
            resp = await self._client.post(urljoin(self._base_url, "/api/transfers"), json=transfer)
            if resp.is_success:
                return {"success": True, "transfer": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Hospital transfer failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _discharge_patient(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Hospital connector not connected")
        discharge = {
            "patient_id": data.get("patient_id", ""),
            "discharge_type": data.get("discharge_type", "home"),
            "discharge_summary": data.get("discharge_summary", ""),
            "medications": data.get("medications", []),
            "follow_up": data.get("follow_up", ""),
            "discharging_doctor": data.get("discharging_doctor", ""),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/discharges"), json=discharge
            )
            if resp.is_success:
                return {"success": True, "discharge": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Hospital discharge failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _get_ward_occupancy(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Hospital connector not connected")
        ward = data.get("ward", "")
        params = {"ward": ward} if ward else {}
        try:
            resp = await self._client.get(
                urljoin(self._base_url, "/api/wards/occupancy"), params=params
            )
            if resp.is_success:
                return {"success": True, "occupancy": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Ward occupancy fetch failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _schedule_surgery(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Hospital connector not connected")
        surgery = {
            "patient_id": data.get("patient_id", ""),
            "procedure": data.get("procedure", ""),
            "surgeon": data.get("surgeon", ""),
            "anesthesiologist": data.get("anesthesiologist", ""),
            "scheduled_date": data.get("scheduled_date", ""),
            "operating_room": data.get("operating_room", ""),
            "notes": data.get("notes", ""),
        }
        try:
            resp = await self._client.post(urljoin(self._base_url, "/api/surgeries"), json=surgery)
            if resp.is_success:
                return {"success": True, "surgery_id": resp.json().get("id", "")}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Surgery scheduling failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _get_patient_history(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Hospital connector not connected")
        patient_id = data.get("patient_id", "")
        if not patient_id:
            return {"success": False, "error": "patient_id required"}
        try:
            resp = await self._client.get(
                urljoin(self._base_url, f"/api/patients/{patient_id}/history")
            )
            if resp.is_success:
                return {"success": True, "history": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Patient history fetch failed: %s", exc)
            return {"success": False, "error": str(exc)}


ConnectorRegistry.register("hospital_integration", HospitalIntegration)
