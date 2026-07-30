from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urljoin

import httpx

from app.integration.connectors import BaseConnector, ConnectorRegistry

logger = logging.getLogger("gula.integration.government.interior")


class InteriorIntegration(BaseConnector):
    def __init__(
        self,
        name: str = "interior",
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
            logger.info("Interior connector connected: %s", self._base_url)
            return True
        except Exception as exc:
            logger.error("Interior connector failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        self._access_token = ""
        logger.info("Interior connector disconnected")
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
        if action == "verify_national_id":
            return await self._verify_national_id(data)
        if action == "issue_passport":
            return await self._issue_passport(data)
        if action == "verify_residency":
            return await self._verify_residency(data)
        if action == "civil_registry_lookup":
            return await self._civil_registry_lookup(data)
        if action == "criminal_record":
            return await self._criminal_record_check(data)
        raise ValueError(f"Unknown Interior action: {action}")

    async def _authenticate(self) -> None:
        if not self._client:
            raise RuntimeError("Interior connector not connected")
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/auth/token"),
                json={
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "grant_type": "client_credentials",
                },
            )
            if resp.is_success:
                result = resp.json()
                self._access_token = result.get("access_token", "")
                self._client.headers["Authorization"] = f"Bearer {self._access_token}"
                logger.info("Interior authenticated")
        except Exception as exc:
            logger.error("Interior authentication failed: %s", exc)

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        if self._api_key:
            headers["X-API-Key"] = self._api_key
        return headers

    async def _verify_national_id(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Interior connector not connected")
        national_id = data.get("national_id", "")
        if not national_id:
            return {"success": False, "error": "national_id required"}
        try:
            resp = await self._client.get(
                urljoin(self._base_url, f"/api/national-id/{national_id}/verify"),
                headers=self._headers(),
            )
            if resp.is_success:
                return {"success": True, "verified": True, "person": resp.json()}
            if resp.status_code == 401:
                await self._authenticate()
                return await self._verify_national_id(data)
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("National ID verification failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _issue_passport(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Interior connector not connected")
        application = {
            "national_id": data.get("national_id", ""),
            "full_name": data.get("full_name", ""),
            "date_of_birth": data.get("date_of_birth", ""),
            "place_of_birth": data.get("place_of_birth", ""),
            "gender": data.get("gender", ""),
            "mother_name": data.get("mother_name", ""),
            "father_name": data.get("father_name", ""),
            "address": data.get("address", ""),
            "phone": data.get("phone", ""),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/passports/issue"),
                json=application,
                headers=self._headers(),
            )
            if resp.is_success:
                return {"success": True, "passport": resp.json()}
            if resp.status_code == 401:
                await self._authenticate()
                return await self._issue_passport(data)
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Passport issuance failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _verify_residency(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Interior connector not connected")
        national_id = data.get("national_id", "")
        if not national_id:
            return {"success": False, "error": "national_id required"}
        try:
            resp = await self._client.get(
                urljoin(self._base_url, f"/api/residency/{national_id}"),
                headers=self._headers(),
            )
            if resp.is_success:
                return {"success": True, "residency": resp.json()}
            if resp.status_code == 401:
                await self._authenticate()
                return await self._verify_residency(data)
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Residency verification failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _civil_registry_lookup(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Interior connector not connected")
        national_id = data.get("national_id", "")
        if not national_id:
            return {"success": False, "error": "national_id required"}
        try:
            resp = await self._client.get(
                urljoin(self._base_url, f"/api/civil-registry/{national_id}"),
                headers=self._headers(),
            )
            if resp.is_success:
                return {"success": True, "record": resp.json()}
            if resp.status_code == 401:
                await self._authenticate()
                return await self._civil_registry_lookup(data)
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Civil registry lookup failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _criminal_record_check(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Interior connector not connected")
        national_id = data.get("national_id", "")
        if not national_id:
            return {"success": False, "error": "national_id required"}
        try:
            resp = await self._client.get(
                urljoin(self._base_url, f"/api/criminal-records/{national_id}"),
                headers=self._headers(),
            )
            if resp.is_success:
                return {
                    "success": True,
                    "has_record": resp.json().get("has_record", False),
                    "details": resp.json(),
                }
            if resp.status_code == 401:
                await self._authenticate()
                return await self._criminal_record_check(data)
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Criminal record check failed: %s", exc)
            return {"success": False, "error": str(exc)}


ConnectorRegistry.register("interior", InteriorIntegration)
