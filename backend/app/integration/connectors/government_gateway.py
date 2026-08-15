from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urljoin

import httpx

from app.integration.connectors import BaseConnector, ConnectorRegistry

logger = logging.getLogger("gula.integration.connectors.government_gateway")


class GovernmentGatewayConnector(BaseConnector):
    def __init__(
        self,
        name: str = "government_gateway",
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
        self._timeout = httpx.Timeout(self.config.get("timeout", 60.0))
        self._verify_ssl = self.config.get("verify_ssl", True)

    async def connect(self) -> bool:
        try:
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                verify=self._verify_ssl,
            )
            if self._client_id and self._client_secret:
                await self._authenticate()
            self._connected = True
            logger.info("Government Gateway connector connected")
            return True
        except Exception as exc:
            logger.error("Government Gateway connector failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        self._access_token = ""
        logger.info("Government Gateway connector disconnected")
        return True

    async def health_check(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": self.name,
            "connected": self._connected,
            "authenticated": bool(self._access_token),
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
        if action == "submit_document":
            return await self._submit_document(data)
        if action == "query_document":
            return await self._query_document(data)
        if action == "regulatory_report":
            return await self._regulatory_report(data)
        if action == "service_request":
            return await self._service_request(data)
        if action == "exchange_document":
            return await self._exchange_document(data)
        raise ValueError(f"Unknown Government Gateway action: {action}")

    async def _authenticate(self) -> None:
        if not self._client:
            raise RuntimeError("Government Gateway not connected")
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
                logger.info("Government Gateway authenticated")
        except Exception as exc:
            logger.error("Government Gateway authentication failed: %s", exc)

    def _ensure_auth_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        if self._api_key:
            headers["X-API-Key"] = self._api_key
        return headers

    async def _submit_document(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Government Gateway not connected")
        document = {
            "document_id": data.get("document_id", ""),
            "document_type": data.get("document_type", ""),
            "title": data.get("title", ""),
            "content": data.get("content", ""),
            "format": data.get("format", "pdf"),
            "department": data.get("department", ""),
        }
        if not document["document_id"] or not document["document_type"]:
            return {"success": False, "error": "document_id and document_type required"}
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/documents/submit"),
                json=document,
                headers=self._ensure_auth_headers(),
            )
            if resp.is_success:
                result = resp.json()
                return {
                    "success": True,
                    "submission_id": result.get("submission_id", ""),
                    "status": result.get("status", "received"),
                    "timestamp": result.get("timestamp", ""),
                }
            if resp.status_code == 401:
                await self._authenticate()
                return await self._submit_document(data)
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Document submission failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _query_document(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Government Gateway not connected")
        submission_id = data.get("submission_id", "")
        document_id = data.get("document_id", "")
        if not submission_id and not document_id:
            return {"success": False, "error": "submission_id or document_id required"}
        params = {}
        if submission_id:
            params["submission_id"] = submission_id
        if document_id:
            params["document_id"] = document_id
        try:
            resp = await self._client.get(
                urljoin(self._base_url, "/api/documents"),
                params=params,
                headers=self._ensure_auth_headers(),
            )
            if resp.is_success:
                return {"success": True, "document": resp.json()}
            if resp.status_code == 401:
                await self._authenticate()
                return await self._query_document(data)
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Document query failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _regulatory_report(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Government Gateway not connected")
        report = {
            "report_type": data.get("report_type", ""),
            "reporting_period": data.get("reporting_period", ""),
            "facility_id": data.get("facility_id", ""),
            "data": data.get("report_data", {}),
            "format": data.get("format", "json"),
        }
        if not report["report_type"]:
            return {"success": False, "error": "report_type required"}
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/regulatory/reports"),
                json=report,
                headers=self._ensure_auth_headers(),
            )
            if resp.is_success:
                result = resp.json()
                return {
                    "success": True,
                    "report_id": result.get("report_id", ""),
                    "status": result.get("status", "submitted"),
                }
            if resp.status_code == 401:
                await self._authenticate()
                return await self._regulatory_report(data)
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Regulatory report failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _service_request(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Government Gateway not connected")
        request = {
            "service_code": data.get("service_code", ""),
            "request_data": data.get("request_data", {}),
            "requester_id": data.get("requester_id", ""),
        }
        if not request["service_code"]:
            return {"success": False, "error": "service_code required"}
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/services/request"),
                json=request,
                headers=self._ensure_auth_headers(),
            )
            if resp.is_success:
                result = resp.json()
                return {
                    "success": True,
                    "request_id": result.get("request_id", ""),
                    "status": result.get("status", "pending"),
                    "estimated_completion": result.get("estimated_completion", ""),
                }
            if resp.status_code == 401:
                await self._authenticate()
                return await self._service_request(data)
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Government service request failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _exchange_document(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Government Gateway not connected")
        exchange = {
            "document_id": data.get("document_id", ""),
            "sender": data.get("sender", "GULA"),
            "recipient": data.get("recipient", ""),
            "document_type": data.get("document_type", ""),
            "payload": data.get("payload", {}),
            "encryption": data.get("encryption", "none"),
        }
        if not exchange["recipient"] or not exchange["document_type"]:
            return {"success": False, "error": "recipient and document_type required"}
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/documents/exchange"),
                json=exchange,
                headers=self._ensure_auth_headers(),
            )
            if resp.is_success:
                return {"success": True, "exchange": resp.json()}
            if resp.status_code == 401:
                await self._authenticate()
                return await self._exchange_document(data)
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Document exchange failed: %s", exc)
            return {"success": False, "error": str(exc)}


ConnectorRegistry.register("government_gateway", GovernmentGatewayConnector)
