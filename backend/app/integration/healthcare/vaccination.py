from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urljoin

import httpx

from backend.app.integration.connectors import BaseConnector, ConnectorRegistry

logger = logging.getLogger("gula.integration.healthcare.vaccination")


class VaccinationIntegration(BaseConnector):
    def __init__(
        self,
        name: str = "vaccination_integration",
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
            logger.info("Vaccination integration connected")
            return True
        except Exception as exc:
            logger.error("Vaccination integration failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        logger.info("Vaccination integration disconnected")
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
        if action == "record_vaccination":
            return await self._record_vaccination(data)
        if action == "get_vaccination_record":
            return await self._get_vaccination_record(data)
        if action == "sync_vaccine_inventory":
            return await self._sync_vaccine_inventory(data)
        if action == "schedule_appointment":
            return await self._schedule_appointment(data)
        if action == "report_adverse_event":
            return await self._report_adverse_event(data)
        raise ValueError(f"Unknown vaccination action: {action}")

    async def _record_vaccination(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Vaccination connector not connected")
        record = {
            "patient_id": data.get("patient_id", ""),
            "national_id": data.get("national_id", ""),
            "vaccine_code": data.get("vaccine_code", ""),
            "vaccine_name": data.get("vaccine_name", ""),
            "dose_number": data.get("dose_number", 1),
            "batch_number": data.get("batch_number", ""),
            "administration_date": data.get("administration_date", ""),
            "administered_by": data.get("administered_by", ""),
            "facility_id": data.get("facility_id", ""),
            "route": data.get("route", "IM"),
            "site": data.get("site", "left_deltoid"),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/vaccinations"), json=record
            )
            if resp.is_success:
                return {"success": True, "vaccination_id": resp.json().get("id", "")}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Vaccination recording failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _get_vaccination_record(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Vaccination connector not connected")
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
            resp = await self._client.get(
                urljoin(self._base_url, "/api/vaccinations"), params=params
            )
            if resp.is_success:
                records = resp.json()
                return {
                    "success": True,
                    "vaccinations": records,
                    "count": len(records) if isinstance(records, list) else 0,
                }
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Vaccination record fetch failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _sync_vaccine_inventory(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Vaccination connector not connected")
        sync = {
            "facility_id": data.get("facility_id", ""),
            "vaccines": data.get("vaccines", []),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/vaccines/inventory/sync"), json=sync
            )
            if resp.is_success:
                return {"success": True, "inventory": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Vaccine inventory sync failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _schedule_appointment(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Vaccination connector not connected")
        appointment = {
            "patient_id": data.get("patient_id", ""),
            "vaccine_code": data.get("vaccine_code", ""),
            "scheduled_date": data.get("scheduled_date", ""),
            "scheduled_time": data.get("scheduled_time", ""),
            "facility_id": data.get("facility_id", ""),
            "notes": data.get("notes", ""),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/appointments"), json=appointment
            )
            if resp.is_success:
                return {"success": True, "appointment": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Appointment scheduling failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _report_adverse_event(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Vaccination connector not connected")
        event = {
            "vaccination_id": data.get("vaccination_id", ""),
            "patient_id": data.get("patient_id", ""),
            "event_date": data.get("event_date", ""),
            "symptoms": data.get("symptoms", []),
            "severity": data.get("severity", "mild"),
            "treatment": data.get("treatment", ""),
            "reported_by": data.get("reported_by", ""),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/adverse-events"), json=event
            )
            if resp.is_success:
                return {"success": True, "event_id": resp.json().get("id", "")}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Adverse event report failed: %s", exc)
            return {"success": False, "error": str(exc)}


ConnectorRegistry.register("vaccination_integration", VaccinationIntegration)
