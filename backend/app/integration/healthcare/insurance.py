from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urljoin

import httpx

from backend.app.integration.connectors import BaseConnector, ConnectorRegistry

logger = logging.getLogger("gula.integration.healthcare.insurance")


class InsuranceIntegration(BaseConnector):
    def __init__(
        self,
        name: str = "insurance_integration",
        version: str = "1.0.0",
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name, version, config)
        self._base_url = self.config.get("base_url", "")
        self._api_key = self.config.get("api_key", "")
        self._provider_id = self.config.get("provider_id", "")
        self._client: httpx.AsyncClient | None = None
        self._timeout = httpx.Timeout(self.config.get("timeout", 30.0))
        self._verify_ssl = self.config.get("verify_ssl", True)

    async def connect(self) -> bool:
        try:
            headers = {"Content-Type": "application/json", "X-Provider-ID": self._provider_id}
            if self._api_key:
                headers["Authorization"] = f"Bearer {self._api_key}"
            self._client = httpx.AsyncClient(timeout=self._timeout, verify=self._verify_ssl, headers=headers)
            self._connected = True
            logger.info("Insurance integration connected")
            return True
        except Exception as exc:
            logger.error("Insurance integration failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        logger.info("Insurance integration disconnected")
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
        if action == "verify_coverage":
            return await self._verify_coverage(data)
        if action == "submit_claim":
            return await self._submit_claim(data)
        if action == "check_claim_status":
            return await self._check_claim_status(data)
        if action == "get_authorization":
            return await self._get_authorization(data)
        if action == "process_eligibility":
            return await self._process_eligibility(data)
        raise ValueError(f"Unknown insurance action: {action}")

    async def _verify_coverage(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Insurance connector not connected")
        coverage = {
            "member_id": data.get("member_id", ""),
            "national_id": data.get("national_id", ""),
            "insurance_provider": data.get("insurance_provider", ""),
            "service_type": data.get("service_type", "laboratory"),
            "service_code": data.get("service_code", ""),
        }
        try:
            resp = await self._client.post(urljoin(self._base_url, "/api/coverage/verify"), json=coverage)
            if resp.is_success:
                return {"success": True, "coverage": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Coverage verification failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _submit_claim(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Insurance connector not connected")
        claim = {
            "member_id": data.get("member_id", ""),
            "patient_id": data.get("patient_id", ""),
            "service_date": data.get("service_date", ""),
            "services": data.get("services", []),
            "diagnosis_codes": data.get("diagnosis_codes", []),
            "total_amount": data.get("total_amount", 0),
            "currency": data.get("currency", "IQD"),
            "provider_id": self._provider_id,
        }
        try:
            resp = await self._client.post(urljoin(self._base_url, "/api/claims"), json=claim)
            if resp.is_success:
                return {"success": True, "claim": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Claim submission failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _check_claim_status(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Insurance connector not connected")
        claim_id = data.get("claim_id", "")
        if not claim_id:
            return {"success": False, "error": "claim_id required"}
        try:
            resp = await self._client.get(urljoin(self._base_url, f"/api/claims/{claim_id}"))
            if resp.is_success:
                return {"success": True, "claim": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Claim status check failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _get_authorization(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Insurance connector not connected")
        authorization = {
            "member_id": data.get("member_id", ""),
            "service_type": data.get("service_type", ""),
            "service_code": data.get("service_code", ""),
            "reason": data.get("reason", ""),
            "ordering_provider": data.get("ordering_provider", ""),
            "estimated_cost": data.get("estimated_cost", 0),
        }
        try:
            resp = await self._client.post(urljoin(self._base_url, "/api/authorizations"), json=authorization)
            if resp.is_success:
                return {"success": True, "authorization": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Authorization request failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _process_eligibility(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Insurance connector not connected")
        eligibility = {
            "member_id": data.get("member_id", ""),
            "national_id": data.get("national_id", ""),
            "date_of_service": data.get("date_of_service", ""),
            "service_type": data.get("service_type", ""),
        }
        try:
            resp = await self._client.post(urljoin(self._base_url, "/api/eligibility"), json=eligibility)
            if resp.is_success:
                return {"success": True, "eligible": resp.json().get("eligible", False), "details": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Eligibility check failed: %s", exc)
            return {"success": False, "error": str(exc)}


ConnectorRegistry.register("insurance_integration", InsuranceIntegration)
