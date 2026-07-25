from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import time
from typing import Any

import httpx

from .base import BaseConnector, ConnectorConfig, ConnectorResult, ConnectorStatus

logger = logging.getLogger("gula.ecosystem.webhook")


class WebhookConnector(BaseConnector):
    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self._client: httpx.AsyncClient | None = None
        self._registrations: dict[str, dict] = {}
        self._delivery_log: list[dict] = []
        self._max_delivery_log = 10000
        self._hmac_secret: str = ""

    async def connect(self) -> bool:
        try:
            options = self._config.options or {}
            self._hmac_secret = options.get("hmac_secret", "")
            self._max_delivery_log = options.get("max_delivery_log", 10000)
            timeout = httpx.Timeout(self._config.timeout_seconds)
            self._client = httpx.AsyncClient(timeout=timeout)
            self._connected = True
            self._status = ConnectorStatus.ACTIVE
            return True
        except Exception as exc:
            self._status = ConnectorStatus.ERROR
            self._metrics["last_error"] = str(exc)
            return False

    async def disconnect(self) -> bool:
        try:
            if self._client:
                await self._client.aclose()
                self._client = None
            self._connected = False
            self._status = ConnectorStatus.INACTIVE
            return True
        except Exception as exc:
            self._metrics["last_error"] = str(exc)
            return False

    async def send(self, data: Any) -> ConnectorResult:
        if not isinstance(data, dict):
            return self._build_result(
                False, error="data must be a dict with 'event' and 'payload'", status_code=400,
            )

        event = data.get("event", "")
        payload = data.get("payload", {})
        targets = data.get("targets")

        if not event:
            return self._build_result(False, error="event is required", status_code=400)

        start = time.monotonic()
        try:
            if targets:
                urls = targets if isinstance(targets, list) else [targets]
            else:
                urls = self._get_subscribers(event)

            if not urls:
                duration_ms = int((time.monotonic() - start) * 1000)
                return self._build_result(
                    True,
                    data={"delivered": 0, "message": "no subscribers"},
                    duration_ms=duration_ms,
                )

            results = []
            for url in urls:
                result = await self._deliver(url, event, payload)
                results.append(result)

            duration_ms = int((time.monotonic() - start) * 1000)
            success_count = sum(1 for r in results if r["success"])
            self._record_success(duration_ms)
            return self._build_result(
                True,
                data={"delivered": success_count, "total": len(results), "results": results},
                duration_ms=duration_ms,
            )

        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            self._record_failure(str(exc), duration_ms)
            return self._build_result(False, error=str(exc), duration_ms=duration_ms)

    async def receive(self) -> ConnectorResult:
        return self._build_result(
            False, error="use register_webhook() for receiving webhooks", status_code=400,
        )

    async def register_webhook(self, webhook_id: str, config: dict) -> None:
        self._registrations[webhook_id] = {
            "id": webhook_id,
            "url": config.get("url", ""),
            "events": config.get("events", ["*"]),
            "secret": config.get("secret", ""),
            "headers": config.get("headers", {}),
            "retry_count": config.get("retry_count", self._config.retry_count),
            "retry_delay": config.get("retry_delay_seconds", self._config.retry_delay_seconds),
            "created_at": time.time(),
            "status": "active",
        }

    async def unregister_webhook(self, webhook_id: str) -> bool:
        return self._registrations.pop(webhook_id, None) is not None

    def list_webhooks(self) -> list[dict]:
        return list(self._registrations.values())

    def verify_signature(
        self, payload: bytes, signature_header: str, secret: str | None = None,
    ) -> bool:
        secret = secret or self._hmac_secret
        if not secret:
            return True
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature_header)

    async def _deliver(self, url: str, event: str, payload: Any) -> dict:
        delivery = {
            "url": url,
            "event": event,
            "success": False,
            "status_code": 0,
            "duration_ms": 0,
            "attempts": 0,
            "error": None,
        }

        webhook_config = self._find_registration(url)
        retry_count = (
            webhook_config.get("retry_count", self._config.retry_count)
            if webhook_config
            else self._config.retry_count
        )
        retry_delay = (
            webhook_config.get("retry_delay", self._config.retry_delay_seconds)
            if webhook_config
            else self._config.retry_delay_seconds
        )
        secret = webhook_config.get("secret", "") if webhook_config else ""

        start = time.monotonic()
        for attempt in range(retry_count + 1):
            try:
                body = json.dumps(
                    {"event": event, "payload": payload, "timestamp": time.time()},
                ).encode()
                headers = {"Content-Type": "application/json"}

                sig = webhook_config.get("headers", {}).copy() if webhook_config else {}
                headers.update(sig)

                if secret:
                    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
                    headers["X-Webhook-Signature"] = f"sha256={signature}"

                headers["X-Webhook-Event"] = event

                if self._client:
                    response = await self._client.post(url, content=body, headers=headers)
                    delivery["status_code"] = response.status_code
                    delivery["attempts"] = attempt + 1

                    if response.is_success:
                        delivery["success"] = True
                        delivery["duration_ms"] = int((time.monotonic() - start) * 1000)
                        break
                    delivery["error"] = f"HTTP {response.status_code}"

            except httpx.TimeoutException:
                delivery["error"] = "timeout"
            except httpx.RequestError as exc:
                delivery["error"] = str(exc)
            except Exception as exc:
                delivery["error"] = str(exc)

            if attempt < retry_count:
                await asyncio.sleep(retry_delay * (2**attempt))

        if not delivery["duration_ms"]:
            delivery["duration_ms"] = int((time.monotonic() - start) * 1000)

        self._delivery_log.append(delivery)
        if len(self._delivery_log) > self._max_delivery_log:
            self._delivery_log.pop(0)

        return delivery

    def _get_subscribers(self, event: str) -> list[str]:
        urls: set[str] = set()
        for reg in self._registrations.values():
            if reg["status"] != "active":
                continue
            if "*" in reg["events"] or event in reg["events"]:
                urls.add(reg["url"])
        return list(urls)

    def _find_registration(self, url: str) -> dict | None:
        for reg in self._registrations.values():
            if reg["url"] == url:
                return reg
        return None

    def get_delivery_log(self, limit: int = 100) -> list[dict]:
        return list(self._delivery_log[-limit:])

    def get_delivery_stats(self) -> dict:
        total = len(self._delivery_log)
        successes = sum(1 for d in self._delivery_log if d["success"])
        failures = total - successes
        return {
            "total_deliveries": total,
            "successful": successes,
            "failed": failures,
            "success_rate": round(successes / total * 100, 2) if total else 100.0,
        }
