from __future__ import annotations

import logging
import time
import uuid
from typing import Any
from urllib.parse import urljoin

import httpx

from backend.app.integration.connectors import BaseConnector, ConnectorRegistry

logger = logging.getLogger("gula.integration.connectors.payment")

SUPPORTED_PROVIDERS = frozenset({"zaincash", "asiacell", "mastercard", "visa"})


class PaymentConnector(BaseConnector):
    def __init__(
        self,
        name: str = "payment",
        version: str = "1.0.0",
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name, version, config)
        self._provider = self.config.get("provider", "zaincash")
        if self._provider not in SUPPORTED_PROVIDERS:
            raise ValueError(
                f"Unsupported payment provider: {self._provider}. Supported: {', '.join(sorted(SUPPORTED_PROVIDERS))}"
            )
        self._base_url = self.config.get("base_url", "")
        self._merchant_id = self.config.get("merchant_id", "")
        self._api_key = self.config.get("api_key", "")
        self._client: httpx.AsyncClient | None = None
        self._timeout = httpx.Timeout(self.config.get("timeout", 30.0))
        self._verify_ssl = self.config.get("verify_ssl", True)

    async def connect(self) -> bool:
        try:
            headers = {
                "Content-Type": "application/json",
                "X-Merchant-ID": self._merchant_id,
            }
            if self._api_key:
                headers["Authorization"] = f"Bearer {self._api_key}"
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                verify=self._verify_ssl,
                headers=headers,
            )
            self._connected = True
            logger.info("Payment connector connected: provider=%s", self._provider)
            return True
        except Exception as exc:
            logger.error("Payment connector failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        logger.info("Payment connector disconnected")
        return True

    async def health_check(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": self.name,
            "provider": self._provider,
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
        if action == "initiate":
            return await self._initiate_payment(data)
        if action == "verify":
            return await self._verify_payment(data)
        if action == "refund":
            return await self._refund_payment(data)
        if action == "history":
            return await self._transaction_history(data)
        raise ValueError(f"Unknown payment action: {action}")

    async def _initiate_payment(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Payment connector not connected")
        transaction_id = str(uuid.uuid4())
        payload = {
            "transaction_id": transaction_id,
            "amount": data.get("amount", 0),
            "currency": data.get("currency", "IQD"),
            "description": data.get("description", ""),
            "customer_id": data.get("customer_id", ""),
            "customer_phone": data.get("customer_phone", ""),
            "callback_url": data.get("callback_url", ""),
            "provider": self._provider,
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, "/api/payments/initiate"),
                json=payload,
            )
            if resp.is_success:
                result = resp.json()
                result["transaction_id"] = transaction_id
                return {"success": True, "payment": result}
            return {
                "success": False,
                "error": resp.text,
                "status_code": resp.status_code,
                "transaction_id": transaction_id,
            }
        except Exception as exc:
            logger.error("Payment initiation failed: %s", exc)
            return {"success": False, "error": str(exc), "transaction_id": transaction_id}

    async def _verify_payment(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Payment connector not connected")
        transaction_id = data.get("transaction_id", "")
        if not transaction_id:
            return {"success": False, "error": "transaction_id required"}
        try:
            resp = await self._client.get(
                urljoin(self._base_url, f"/api/payments/{transaction_id}/verify"),
            )
            if resp.is_success:
                return {"success": True, "verification": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Payment verification failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _refund_payment(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Payment connector not connected")
        transaction_id = data.get("transaction_id", "")
        if not transaction_id:
            return {"success": False, "error": "transaction_id required"}
        refund_payload = {
            "transaction_id": transaction_id,
            "amount": data.get("amount", 0),
            "reason": data.get("reason", ""),
        }
        try:
            resp = await self._client.post(
                urljoin(self._base_url, f"/api/payments/{transaction_id}/refund"),
                json=refund_payload,
            )
            if resp.is_success:
                return {"success": True, "refund": resp.json()}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Payment refund failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _transaction_history(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Payment connector not connected")
        params = {
            "customer_id": data.get("customer_id", ""),
            "start_date": data.get("start_date", ""),
            "end_date": data.get("end_date", ""),
            "limit": data.get("limit", 50),
            "offset": data.get("offset", 0),
        }
        try:
            resp = await self._client.get(
                urljoin(self._base_url, "/api/payments"),
                params=params,
            )
            if resp.is_success:
                txns = resp.json()
                return {"success": True, "transactions": txns, "count": len(txns)}
            return {"success": False, "error": resp.text, "status_code": resp.status_code}
        except Exception as exc:
            logger.error("Payment history failed: %s", exc)
            return {"success": False, "error": str(exc)}


ConnectorRegistry.register("payment", PaymentConnector)
