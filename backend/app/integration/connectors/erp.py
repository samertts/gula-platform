from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urljoin

import httpx

from app.integration.connectors import BaseConnector, ConnectorRegistry

logger = logging.getLogger("gula.integration.connectors.erp")


class ERPConnector(BaseConnector):
    def __init__(
        self,
        name: str = "erp",
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
                timeout=self._timeout,
                verify=self._verify_ssl,
                headers=headers,
            )
            self._connected = True
            logger.info("ERP connector connected: %s", self._base_url)
            return True
        except Exception as exc:
            logger.error("ERP connector failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        logger.info("ERP connector disconnected")
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
            resp = await self._client.get(urljoin(self._base_url, "/api/health"))
            result["latency_ms"] = (time.monotonic() - start) * 1000
            result["status"] = "healthy" if resp.is_success else "degraded"
            result["status_code"] = resp.status_code
        except Exception as exc:
            result["status"] = "unhealthy"
            result["error"] = str(exc)
        return result

    async def send(self, data: dict[str, Any]) -> dict[str, Any]:
        action = data.get("action", "")
        if action == "sync_invoice":
            return await self._sync_invoice(data)
        if action == "sync_payment":
            return await self._sync_payment(data)
        if action == "sync_inventory":
            return await self._sync_inventory(data)
        if action == "create_procurement":
            return await self._create_procurement(data)
        if action == "get_inventory":
            return await self._get_inventory(data)
        if action == "get_financial_report":
            return await self._get_financial_report(data)
        raise ValueError(f"Unknown ERP action: {action}")

    async def _sync_invoice(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("ERP connector not connected")
        invoice = {
            "invoice_number": data.get("invoice_number", ""),
            "amount": data.get("amount", 0),
            "currency": data.get("currency", "IQD"),
            "customer_id": data.get("customer_id", ""),
            "items": data.get("items", []),
            "issued_date": data.get("issued_date", ""),
            "due_date": data.get("due_date", ""),
            "status": data.get("status", "draft"),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/finance/invoices"),
                json=invoice,
            )
            if resp.is_success:
                return {"success": True, "invoice": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("ERP invoice sync failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _sync_payment(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("ERP connector not connected")
        payment = {
            "payment_id": data.get("payment_id", ""),
            "invoice_number": data.get("invoice_number", ""),
            "amount": data.get("amount", 0),
            "currency": data.get("currency", "IQD"),
            "payment_method": data.get("payment_method", ""),
            "payment_date": data.get("payment_date", ""),
            "reference": data.get("reference", ""),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/finance/payments"),
                json=payment,
            )
            if resp.is_success:
                return {"success": True, "payment": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("ERP payment sync failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _sync_inventory(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("ERP connector not connected")
        items = data.get("items", [])
        if not items:
            return {"success": False, "error": "items required"}
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/inventory/sync"),
                json={"items": items},
            )
            return {"success": resp.is_success, "status_code": resp.status_code, "response": resp.text}
        except Exception as exc:
            logger.error("ERP inventory sync failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _create_procurement(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("ERP connector not connected")
        procurement = {
            "purchase_order": data.get("purchase_order", ""),
            "supplier": data.get("supplier", ""),
            "items": data.get("items", []),
            "total_amount": data.get("total_amount", 0),
            "currency": data.get("currency", "IQD"),
            "delivery_date": data.get("delivery_date", ""),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/procurement/orders"),
                json=procurement,
            )
            if resp.is_success:
                return {"success": True, "procurement": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("ERP procurement failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _get_inventory(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("ERP connector not connected")
        category = data.get("category", "")
        params = {}
        if category:
            params["category"] = category
        try:
            resp = await self._client.get(
                urljoin(self._base_url, "/api/inventory"),
                params=params,
            )
            if resp.is_success:
                items = resp.json()
                return {"success": True, "items": items, "count": len(items)}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("ERP get_inventory failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _get_financial_report(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("ERP connector not connected")
        report_type = data.get("report_type", "summary")
        params = {
            "report_type": report_type,
            "start_date": data.get("start_date", ""),
            "end_date": data.get("end_date", ""),
        }
        try:
            resp = await self._client.get(
                urljoin(self._base_url, "/api/finance/reports"),
                params=params,
            )
            if resp.is_success:
                return {"success": True, "report": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("ERP financial report failed: %s", exc)
            return {"success": False, "error": str(exc)}


ConnectorRegistry.register("erp", ERPConnector)
