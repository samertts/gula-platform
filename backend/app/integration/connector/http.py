from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urljoin

import httpx

from backend.app.integration.connector.spec import (
    ConnectorEndpoint,
    ConnectorHealth,
    ConnectorSpec,
    ConnectorStatus,
    ConnectorType,
)

logger = logging.getLogger("gula.integration.connector.http")


class HttpConnector:
    def __init__(self, spec: ConnectorSpec):
        if spec.connector_type not in (
            ConnectorType.REST,
            ConnectorType.FHIR,
            ConnectorType.GRAPHQL,
        ):
            raise ValueError(
                f"HttpConnector does not support type {spec.connector_type.name}"
            )
        self.spec = spec
        self._client: httpx.AsyncClient | None = None
        self._timeout = httpx.Timeout(
            max(
                (ep.timeout for ep in spec.endpoints),
                default=30.0,
            )
        )

    async def connect(self) -> bool:
        try:
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                verify=self.spec.config.get("verify_ssl", True),
            )
            self.spec.status = ConnectorStatus.CONNECTED
            logger.info("HTTP connector connected: %s", self.spec.name)
            return True
        except Exception as exc:
            self.spec.status = ConnectorStatus.FAILED
            self.spec.health.error = str(exc)
            logger.error("HTTP connector failed: %s", exc)
            return False

    async def disconnect(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
        self.spec.status = ConnectorStatus.DISCONNECTED

    async def request(
        self,
        method: str,
        path: str = "",
        params: dict[str, Any] | None = None,
        json_data: Any = None,
        headers: dict[str, str] | None = None,
        endpoint_name: str | None = None,
    ) -> httpx.Response:
        if not self._client:
            raise RuntimeError("Connector not connected. Call connect() first.")

        ep = self._resolve_endpoint(endpoint_name)
        url = urljoin(ep.url, path)
        req_headers = dict(ep.headers)
        if headers:
            req_headers.update(headers)

        start = time.monotonic()
        try:
            response = await self._client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=req_headers,
            )
            latency = (time.monotonic() - start) * 1000
            self.spec.metrics.total_requests += 1
            self.spec.metrics.avg_latency_ms = (
                self.spec.metrics.avg_latency_ms * 0.9 + latency * 0.1
            )
            if response.is_success:
                self.spec.metrics.successful += 1
            else:
                self.spec.metrics.failed += 1
            return response
        except Exception as exc:
            latency = (time.monotonic() - start) * 1000
            self.spec.metrics.total_requests += 1
            self.spec.metrics.failed += 1
            self.spec.health.error = str(exc)
            self.spec.health.status = "error"
            logger.warning("HTTP request failed: %s", exc)
            raise

    async def health_check(self) -> ConnectorHealth:
        try:
            start = time.monotonic()
            response = await self._client.get(
                self.spec.config.get("health_url", self.spec.endpoints[0].url)
            )
            latency = (time.monotonic() - start) * 1000
            self.spec.health = ConnectorHealth(
                status="healthy" if response.is_success else "degraded",
                latency_ms=latency,
                last_checked=time.time(),
            )
        except Exception as exc:
            self.spec.health = ConnectorHealth(
                status="unhealthy",
                error=str(exc),
                last_checked=time.time(),
            )
        return self.spec.health

    def _resolve_endpoint(
        self, name: str | None
    ) -> ConnectorEndpoint:
        if name:
            for ep in self.spec.endpoints:
                if ep.url == name:
                    return ep
        return self.spec.endpoints[0] if self.spec.endpoints else ConnectorEndpoint()
