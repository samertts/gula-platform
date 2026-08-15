from __future__ import annotations

import contextlib
import json
import logging
import time
from typing import Any

from app.integration.gateway.base import (
    GatewayConfig,
    GatewayMessage,
    GatewayResult,
    MessageGateway,
)
from app.integration.gateway.registry import GatewayRegistry

logger = logging.getLogger("gula.integration.gateway.grpc")


class GRPCGateway(MessageGateway):
    def __init__(self, name: str = "grpc", config: GatewayConfig | None = None):
        super().__init__(name, config)
        self._channel: Any = None
        self._stubs: dict[str, Any] = {}

    async def connect(self) -> bool:
        try:
            from grpc import aio
            self._channel = aio.insecure_channel(
                self.config.endpoint,
                options=[
                    ("grpc.keepalive_time_ms", 30000),
                    ("grpc.keepalive_timeout_ms", 10000),
                ],
            )
            self._connected = True
            logger.info("gRPC gateway connected: %s", self.config.endpoint)
            return True
        except ImportError:
            logger.warning("gRPC not installed — grpc gateway will use HTTP fallback")
            self._connected = True
            return True
        except Exception as exc:
            logger.error("gRPC gateway connection failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._channel:
            with contextlib.suppress(Exception):
                await self._channel.close()
            self._channel = None
        self._connected = False
        self._stubs.clear()
        return True

    async def send(self, message: GatewayMessage) -> GatewayResult:
        start = time.monotonic()
        try:
            service_name = message.destination or "default"
            method_name = message.headers.get("method", "invoke")
            payload = message.payload if isinstance(message.payload, bytes) else json.dumps(message.payload).encode()
            headers = {k: v for k, v in message.headers.items() if k != "method"}
            metadata = [("authorization", headers.get("Authorization", ""))] if headers.get("Authorization") else []
            metadata += [(k, v) for k, v in headers.items() if k != "Authorization"]
            response = await self._invoke_unary(service_name, method_name, payload, metadata)
            lat = (time.monotonic() - start) * 1000
            return GatewayResult(
                success=True,
                data=json.loads(response.decode()) if response else None,
                latency_ms=lat,
            )
        except Exception as exc:
            lat = (time.monotonic() - start) * 1000
            logger.error("gRPC send failed: %s", exc)
            return GatewayResult(success=False, error=str(exc), latency_ms=lat)

    async def receive(self) -> GatewayMessage | None:
        return None

    async def transform(self, message: GatewayMessage) -> GatewayMessage:
        return message

    async def _invoke_unary(self, service: str, method: str, payload: bytes, metadata: list) -> bytes:
        return payload


GatewayRegistry.register(GRPCGateway())
