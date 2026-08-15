from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.integration.gateway.base import (
    GatewayConfig,
    GatewayMessage,
    GatewayResult,
    MessageGateway,
)
from app.integration.gateway.registry import GatewayRegistry

logger = logging.getLogger("gula.integration.gateway.graphql")


class GraphQLGateway(MessageGateway):
    def __init__(self, name: str = "graphql", config: GatewayConfig | None = None):
        super().__init__(name, config)
        self._client: httpx.AsyncClient | None = None

    async def connect(self) -> bool:
        try:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout),
                headers={"Content-Type": "application/json", **self.config.headers},
            )
            self._connected = True
            logger.info("GraphQL gateway connected: %s", self.config.endpoint)
            return True
        except Exception as exc:
            logger.error("GraphQL gateway connection failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        return True

    async def send(self, message: GatewayMessage) -> GatewayResult:
        if not self._client:
            return GatewayResult(success=False, error="Not connected")
        start = time.monotonic()
        try:
            query = message.payload if isinstance(message.payload, str) else message.payload.get("query", "")
            variables = message.payload.get("variables", {}) if isinstance(message.payload, dict) else {}
            operation_name = message.payload.get("operationName") if isinstance(message.payload, dict) else None
            body = {"query": query, "variables": variables}
            if operation_name:
                body["operationName"] = operation_name
            resp = await self._client.post(self.config.endpoint, json=body)
            lat = (time.monotonic() - start) * 1000
            data = resp.json() if resp.is_success else None
            errors = data.get("errors") if data else None
            return GatewayResult(
                success=resp.is_success and not errors,
                status_code=resp.status_code,
                data=data,
                latency_ms=lat,
            )
        except Exception as exc:
            lat = (time.monotonic() - start) * 1000
            logger.error("GraphQL send failed: %s", exc)
            return GatewayResult(success=False, error=str(exc), latency_ms=lat)

    async def receive(self) -> GatewayMessage | None:
        return None

    async def transform(self, message: GatewayMessage) -> GatewayMessage:
        return message

    async def execute(self, query: str, variables: dict[str, Any] | None = None) -> GatewayResult:
        return await self.send(GatewayMessage(payload={"query": query, "variables": variables or {}}))


GatewayRegistry.register(GraphQLGateway())
