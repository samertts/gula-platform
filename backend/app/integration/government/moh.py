from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urljoin

import httpx

from app.integration.connectors import BaseConnector, ConnectorRegistry

logger = logging.getLogger("gula.integration.government.moh")


class MinistryOfHealth(BaseConnector):
    def __init__(
        self,
        name: str = "ministry_of_health",
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
            logger.info("MoH connector connected: %s", self._base_url)
            return True
        except Exception as exc:
            logger.error("MoH connector failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        self._access_token = ""
        logger.info("MoH connector disconnected")
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
        if action == "report_disease":
            return await self._report_disease(data)
        if action == "submit_lab_data":
            return await self._submit_lab_data(data)
        if action == "get_health_policies":
            return await self._get_health_policies(data)
        if action == "sync_facility":
            return await self._sync_facility(data)
        if action == "report_vaccination":
            return await self._report_vaccination(data)
        if action == "get_epidemiological_data":
            return await self._get_epidemiological_data(data)
        raise ValueError(f"Unknown MoH action: {action}")

    async def _authenticate(self) -> None:
        if not self._client:
            raise RuntimeError("MoH connector not connected")
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/auth/token"),
                json={"client_id": self._client_id, "client_secret": self._client_secret, "grant_type": "client_credentials"},
            )
            if resp.is_success:
                result = resp.json()
                self._access_token = result.get("access_token", "")
                self._client.headers["Authorization"] = f"Bearer {self._access_token}"
                logger.info("MoH authenticated")
        except Exception as exc:
            logger.error("MoH authentication failed: %s", exc)

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        if self._api_key:
            headers["X-API-Key"] = self._api_key
        return headers

    async def _report_disease(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("MoH connector not connected")
        report = {
            "disease_code": data.get("disease_code", ""),
            "disease_name": data.get("disease_name", ""),
            "num_cases": data.get("num_cases", 0),
            "num_deaths": data.get("num_deaths", 0),
            "reporting_period": data.get("reporting_period", ""),
            "facility_id": data.get("facility_id", ""),
            "region": data.get("region", ""),
            "notes": data.get("notes", ""),
        }
        try:
            resp = await self._client.post(urljoin(self._base_url, "/api/notifiable-diseases"), json=report, headers=self._headers())
            if resp.is_success:
                return {"success": True, "report_id": resp.json().get("id", "")}
            if resp.status_code == 401:
                await self._authenticate()
                return await self._report_disease(data)
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Disease reporting failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _submit_lab_data(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("MoH connector not connected")
        payload = {
            "lab_id": data.get("lab_id", ""),
            "facility_name": data.get("facility_name", ""),
            "report_type": data.get("report_type", "daily"),
            "period_start": data.get("period_start", ""),
            "period_end": data.get("period_end", ""),
            "tests_performed": data.get("tests_performed", 0),
            "tests_positive": data.get("tests_positive", 0),
            "tests_negative": data.get("tests_negative", 0),
            "data": data.get("data", {}),
        }
        try:
            resp = await self._client.post(urljoin(self._base_url, "/api/lab-data/submit"), json=payload, headers=self._headers())
            if resp.is_success:
                return {"success": True, "submission_id": resp.json().get("id", "")}
            if resp.status_code == 401:
                await self._authenticate()
                return await self._submit_lab_data(data)
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Lab data submission failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _get_health_policies(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("MoH connector not connected")
        try:
            resp = await self._client.get(urljoin(self._base_url, "/api/policies"), headers=self._headers())
            if resp.is_success:
                return {"success": True, "policies": resp.json()}
            if resp.status_code == 401:
                await self._authenticate()
                return await self._get_health_policies(data)
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Health policies fetch failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _sync_facility(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("MoH connector not connected")
        facility = {
            "facility_id": data.get("facility_id", ""),
            "facility_name": data.get("facility_name", ""),
            "facility_type": data.get("facility_type", ""),
            "address": data.get("address", ""),
            "governorate": data.get("governorate", ""),
            "phone": data.get("phone", ""),
            "status": data.get("status", "active"),
        }
        try:
            resp = await self._client.post(urljoin(self._base_url, "/api/facilities/sync"), json=facility, headers=self._headers())
            if resp.is_success:
                return {"success": True, "facility": resp.json()}
            if resp.status_code == 401:
                await self._authenticate()
                return await self._sync_facility(data)
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Facility sync failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _report_vaccination(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("MoH connector not connected")
        report = {
            "vaccine_type": data.get("vaccine_type", ""),
            "doses_administered": data.get("doses_administered", 0),
            "target_population": data.get("target_population", ""),
            "reporting_period": data.get("reporting_period", ""),
            "facility_id": data.get("facility_id", ""),
            "region": data.get("region", ""),
        }
        try:
            resp = await self._client.post(urljoin(self._base_url, "/api/vaccinations/report"), json=report, headers=self._headers())
            if resp.is_success:
                return {"success": True, "report_id": resp.json().get("id", "")}
            if resp.status_code == 401:
                await self._authenticate()
                return await self._report_vaccination(data)
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Vaccination report failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _get_epidemiological_data(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("MoH connector not connected")
        params = {
            "disease": data.get("disease", ""),
            "region": data.get("region", ""),
            "start_date": data.get("start_date", ""),
            "end_date": data.get("end_date", ""),
        }
        try:
            resp = await self._client.get(urljoin(self._base_url, "/api/epidemiology"), params=params, headers=self._headers())
            if resp.is_success:
                return {"success": True, "data": resp.json()}
            if resp.status_code == 401:
                await self._authenticate()
                return await self._get_epidemiological_data(data)
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Epidemiological data fetch failed: %s", exc)
            return {"success": False, "error": str(exc)}


ConnectorRegistry.register("ministry_of_health", MinistryOfHealth)
