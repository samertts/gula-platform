from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urljoin

import httpx

from backend.app.integration.connectors import BaseConnector, ConnectorRegistry

logger = logging.getLogger("gula.integration.connectors.national_id")


class NationalIDConnector(BaseConnector):
    def __init__(
        self,
        name: str = "national_id",
        version: str = "1.0.0",
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name, version, config)
        self._base_url = self.config.get("base_url", "")
        self._api_key = self.config.get("api_key", "")
        self._hmac_key = self.config.get("hmac_key", "")
        self._client: httpx.AsyncClient | None = None
        self._timeout = httpx.Timeout(self.config.get("timeout", 30.0))
        self._verify_ssl = self.config.get("verify_ssl", True)

    async def connect(self) -> bool:
        try:
            headers = {"Content-Type": "application/json"}
            if self._api_key:
                headers["Authorization"] = f"Bearer {self._api_key}"
            if self._hmac_key:
                headers["X-HMAC-Key"] = self._hmac_key
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                verify=self._verify_ssl,
                headers=headers,
            )
            self._connected = True
            logger.info("National ID connector connected")
            return True
        except Exception as exc:
            logger.error("National ID connector failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        logger.info("National ID connector disconnected")
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
        if action == "verify":
            return await self._verify_national_id(data)
        if action == "biometric_verify":
            return await self._biometric_verify(data)
        if action == "civil_status":
            return await self._civil_status_query(data)
        if action == "lookup":
            return await self._lookup(data)
        raise ValueError(f"Unknown national ID action: {action}")

    async def _verify_national_id(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("National ID connector not connected")
        national_id = data.get("national_id", "")
        full_name = data.get("full_name", "")
        date_of_birth = data.get("date_of_birth", "")
        if not national_id:
            return {"success": False, "error": "national_id required"}
        payload = {
            "national_id": national_id,
            "full_name": full_name,
            "date_of_birth": date_of_birth,
            "mother_name": data.get("mother_name", ""),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/national-id/verify"),
                json=payload,
            )
            if resp.is_success:
                result = resp.json()
                return {
                    "success": True,
                    "verified": result.get("verified", False),
                    "confidence": result.get("confidence", 0),
                    "details": result,
                }
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("National ID verification failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _biometric_verify(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("National ID connector not connected")
        national_id = data.get("national_id", "")
        biometric_data = data.get("biometric_data", "")
        biometric_type = data.get("biometric_type", "fingerprint")
        if not national_id or not biometric_data:
            return {"success": False, "error": "national_id and biometric_data required"}
        payload = {
            "national_id": national_id,
            "biometric_type": biometric_type,
            "biometric_data": biometric_data,
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/national-id/biometric"),
                json=payload,
            )
            if resp.is_success:
                result = resp.json()
                return {
                    "success": True,
                    "matched": result.get("matched", False),
                    "match_score": result.get("match_score", 0),
                    "details": result,
                }
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Biometric verification failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _civil_status_query(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("National ID connector not connected")
        national_id = data.get("national_id", "")
        if not national_id:
            return {"success": False, "error": "national_id required"}
        try:
            resp = await self._client.get(
                urljoin(self._base_url, f"/api/national-id/{national_id}/civil-status"),
            )
            if resp.is_success:
                result = resp.json()
                return {
                    "success": True,
                    "civil_status": result.get("civil_status", {}),
                    "details": result,
                }
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Civil status query failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _lookup(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("National ID connector not connected")
        national_id = data.get("national_id", "")
        if not national_id:
            return {"success": False, "error": "national_id required"}
        try:
            resp = await self._client.get(
                urljoin(self._base_url, f"/api/national-id/{national_id}"),
            )
            if resp.is_success:
                result = resp.json()
                return {
                    "success": True,
                    "person": result.get("person", {}),
                    "details": result,
                }
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("National ID lookup failed: %s", exc)
            return {"success": False, "error": str(exc)}


ConnectorRegistry.register("national_id", NationalIDConnector)
