from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urljoin

import httpx

from backend.app.integration.connectors import BaseConnector, ConnectorRegistry

logger = logging.getLogger("gula.integration.government.finance")


class FinanceIntegration(BaseConnector):
    def __init__(
        self,
        name: str = "finance",
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
            logger.info("Finance connector connected: %s", self._base_url)
            return True
        except Exception as exc:
            logger.error("Finance connector failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        self._access_token = ""
        logger.info("Finance connector disconnected")
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
        if action == "submit_tax":
            return await self._submit_tax_report(data)
        if action == "sync_budget":
            return await self._sync_budget(data)
        if action == "process_payment":
            return await self._process_government_payment(data)
        if action == "get_funding":
            return await self._get_funding_info(data)
        if action == "audit_report":
            return await self._submit_audit_report(data)
        raise ValueError(f"Unknown Finance action: {action}")

    async def _authenticate(self) -> None:
        if not self._client:
            raise RuntimeError("Finance connector not connected")
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
                logger.info("Finance authenticated")
        except Exception as exc:
            logger.error("Finance authentication failed: %s", exc)

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        if self._api_key:
            headers["X-API-Key"] = self._api_key
        return headers

    async def _submit_tax_report(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Finance connector not connected")
        report = {
            "tax_period": data.get("tax_period", ""),
            "facility_id": data.get("facility_id", ""),
            "tax_id": data.get("tax_id", ""),
            "revenue": data.get("revenue", 0),
            "tax_amount": data.get("tax_amount", 0),
            "currency": data.get("currency", "IQD"),
            "filing_date": data.get("filing_date", ""),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/tax/submit"),
                json=report,
                headers=self._headers(),
            )
            if resp.is_success:
                return {"success": True, "submission_id": resp.json().get("id", "")}
            if resp.status_code == 401:
                await self._authenticate()
                return await self._submit_tax_report(data)
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Tax report failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _sync_budget(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Finance connector not connected")
        budget = {
            "fiscal_year": data.get("fiscal_year", ""),
            "facility_id": data.get("facility_id", ""),
            "total_budget": data.get("total_budget", 0),
            "allocated": data.get("allocated", 0),
            "spent": data.get("spent", 0),
            "category": data.get("category", ""),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/budget/sync"),
                json=budget,
                headers=self._headers(),
            )
            if resp.is_success:
                return {"success": True, "budget": resp.json()}
            if resp.status_code == 401:
                await self._authenticate()
                return await self._sync_budget(data)
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Budget sync failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _process_government_payment(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Finance connector not connected")
        payment = {
            "payment_id": data.get("payment_id", ""),
            "amount": data.get("amount", 0),
            "currency": data.get("currency", "IQD"),
            "payee_id": data.get("payee_id", ""),
            "purpose": data.get("purpose", ""),
            "budget_code": data.get("budget_code", ""),
            "payment_date": data.get("payment_date", ""),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/payments/process"),
                json=payment,
                headers=self._headers(),
            )
            if resp.is_success:
                return {"success": True, "payment": resp.json()}
            if resp.status_code == 401:
                await self._authenticate()
                return await self._process_government_payment(data)
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Gov payment failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _get_funding_info(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Finance connector not connected")
        facility_id = data.get("facility_id", "")
        params = {}
        if facility_id:
            params["facility_id"] = facility_id
        try:
            resp = await self._client.get(
                urljoin(self._base_url, "/api/funding"),
                params=params,
                headers=self._headers(),
            )
            if resp.is_success:
                return {"success": True, "funding": resp.json()}
            if resp.status_code == 401:
                await self._authenticate()
                return await self._get_funding_info(data)
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Funding info fetch failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _submit_audit_report(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Finance connector not connected")
        report = {
            "facility_id": data.get("facility_id", ""),
            "audit_period": data.get("audit_period", ""),
            "audit_type": data.get("audit_type", "financial"),
            "findings": data.get("findings", []),
            "recommendations": data.get("recommendations", []),
            "auditor": data.get("auditor", ""),
            "report_date": data.get("report_date", ""),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/audit/submit"),
                json=report,
                headers=self._headers(),
            )
            if resp.is_success:
                return {"success": True, "report_id": resp.json().get("id", "")}
            if resp.status_code == 401:
                await self._authenticate()
                return await self._submit_audit_report(data)
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Audit report failed: %s", exc)
            return {"success": False, "error": str(exc)}


ConnectorRegistry.register("finance", FinanceIntegration)
