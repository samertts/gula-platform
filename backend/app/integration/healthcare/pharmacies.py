from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urljoin

import httpx

from app.integration.connectors import BaseConnector, ConnectorRegistry

logger = logging.getLogger("gula.integration.healthcare.pharmacies")


class PharmacyIntegration(BaseConnector):
    def __init__(
        self,
        name: str = "pharmacy_integration",
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
            logger.info("Pharmacy integration connected")
            return True
        except Exception as exc:
            logger.error("Pharmacy integration failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        logger.info("Pharmacy integration disconnected")
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
        if action == "dispense_medication":
            return await self._dispense_medication(data)
        if action == "check_drug_interaction":
            return await self._check_drug_interaction(data)
        if action == "sync_inventory":
            return await self._sync_inventory(data)
        if action == "verify_prescription":
            return await self._verify_prescription(data)
        if action == "get_drug_info":
            return await self._get_drug_info(data)
        raise ValueError(f"Unknown pharmacy action: {action}")

    async def _dispense_medication(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Pharmacy connector not connected")
        dispensing = {
            "prescription_id": data.get("prescription_id", ""),
            "patient_id": data.get("patient_id", ""),
            "medication_code": data.get("medication_code", ""),
            "medication_name": data.get("medication_name", ""),
            "dosage": data.get("dosage", ""),
            "quantity": data.get("quantity", 0),
            "dispensed_by": data.get("dispensed_by", ""),
            "notes": data.get("notes", ""),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/dispense"), json=dispensing
            )
            if resp.is_success:
                return {"success": True, "dispensing": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Medication dispensing failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _check_drug_interaction(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Pharmacy connector not connected")
        check = {
            "medications": data.get("medications", []),
            "patient_id": data.get("patient_id", ""),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/interactions/check"), json=check
            )
            if resp.is_success:
                return {"success": True, "interactions": resp.json().get("interactions", [])}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Drug interaction check failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _sync_inventory(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Pharmacy connector not connected")
        inventory = {
            "items": data.get("items", []),
            "facility_id": data.get("facility_id", ""),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/inventory/sync"), json=inventory
            )
            if resp.is_success:
                return {"success": True, "sync_result": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Pharmacy inventory sync failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _verify_prescription(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Pharmacy connector not connected")
        prescription = {
            "prescription_id": data.get("prescription_id", ""),
            "patient_id": data.get("patient_id", ""),
            "prescriber": data.get("prescriber", ""),
            "medications": data.get("medications", []),
            "issue_date": data.get("issue_date", ""),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/prescriptions/verify"), json=prescription
            )
            if resp.is_success:
                return {
                    "success": True,
                    "verified": resp.json().get("verified", False),
                    "details": resp.json(),
                }
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Prescription verification failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _get_drug_info(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Pharmacy connector not connected")
        drug_code = data.get("drug_code", "")
        if not drug_code:
            return {"success": False, "error": "drug_code required"}
        try:
            resp = await self._client.get(urljoin(self._base_url, f"/api/drugs/{drug_code}"))
            if resp.is_success:
                return {"success": True, "drug": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Drug info fetch failed: %s", exc)
            return {"success": False, "error": str(exc)}


ConnectorRegistry.register("pharmacy_integration", PharmacyIntegration)
