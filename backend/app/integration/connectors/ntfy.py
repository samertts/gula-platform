from __future__ import annotations

import logging
import os
import time
from typing import Any
from urllib.parse import quote

import httpx

from backend.app.integration.connectors import BaseConnector, ConnectorRegistry

logger = logging.getLogger("gula.integration.connectors.ntfy")


class NtfyConnector(BaseConnector):
    """Free/self-hosted ntfy publisher.

    The connector deliberately sends only the message supplied by the caller. The
    caller remains responsible for removing PHI/PII before publishing operational
    alerts to an ntfy topic.
    """

    def __init__(
        self,
        name: str = "ntfy",
        version: str = "1.0.0",
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name, version, config)
        self._base_url = str(
            self.config.get("base_url", os.getenv("NTFY_BASE_URL", "http://ntfy:80")),
        ).rstrip("/")
        self._default_topic = str(
            self.config.get("topic", os.getenv("NTFY_TOPIC", "gula-ops")),
        )
        self._token = str(self.config.get("token", os.getenv("NTFY_TOKEN", "")))
        self._verify_ssl = bool(self.config.get("verify_ssl", True))
        self._client: httpx.AsyncClient | None = None

    async def connect(self) -> bool:
        try:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(10.0),
                verify=self._verify_ssl,
            )
            self._connected = True
            logger.info("ntfy connector connected: base_url=%s", self._base_url)
            return True
        except Exception as exc:
            logger.error("ntfy connector failed: %s", exc)
            self._connected = False
            return False

    async def disconnect(self) -> bool:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
        self._connected = False
        return True

    async def health_check(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": self.name,
            "provider": "ntfy",
            "base_url": self._base_url,
            "connected": self._connected,
            "timestamp": time.time(),
        }
        if not self._connected or self._client is None:
            result["status"] = "disconnected"
            return result
        try:
            start = time.monotonic()
            response = await self._client.get(f"{self._base_url}/v1/health")
            result["latency_ms"] = (time.monotonic() - start) * 1000
            result["status_code"] = response.status_code
            result["status"] = "healthy" if response.is_success else "degraded"
        except Exception as exc:
            result["status"] = "unhealthy"
            result["error"] = str(exc)
        return result

    async def send(self, data: dict[str, Any]) -> dict[str, Any]:
        if not self._connected or self._client is None:
            raise RuntimeError("ntfy connector not connected")

        topic = str(data.get("topic", self._default_topic)).strip()
        message = str(data.get("message", data.get("body", ""))).strip()
        title = str(data.get("title", "GULA alert")).strip()
        priority = str(data.get("priority", "default")).strip()
        tags = str(data.get("tags", "")).strip()
        click = str(data.get("click", "")).strip()

        if not topic:
            return {"success": False, "error": "topic required", "provider": "ntfy"}
        if not message:
            return {"success": False, "error": "message required", "provider": "ntfy"}
        if len(message) > 4096:
            return {"success": False, "error": "message exceeds 4096 characters", "provider": "ntfy"}

        headers = {
            "Title": title[:250],
            "Priority": priority,
            "Content-Type": "text/plain; charset=utf-8",
        }
        if tags:
            headers["Tags"] = tags[:250]
        if click:
            headers["Click"] = click[:1000]
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        url = f"{self._base_url}/{quote(topic, safe='-_.,')}"
        try:
            response = await self._client.post(url, content=message.encode("utf-8"), headers=headers)
            if response.is_success:
                return {
                    "success": True,
                    "provider": "ntfy",
                    "topic": topic,
                    "status_code": response.status_code,
                }
            return {
                "success": False,
                "provider": "ntfy",
                "topic": topic,
                "status_code": response.status_code,
                "error": response.text[:500],
            }
        except Exception as exc:
            logger.error("ntfy send failed: %s", exc)
            return {"success": False, "provider": "ntfy", "error": str(exc)}


ConnectorRegistry.register("ntfy", NtfyConnector)
