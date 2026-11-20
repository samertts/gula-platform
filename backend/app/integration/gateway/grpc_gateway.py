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
    """Real gRPC unary gateway.

    The previous implementation reported success when ``grpc`` was missing and
    ``_invoke_unary`` returned the request payload as if it were a response.
    This class now fails closed unless a live channel exists and performs a
    real RPC; it never synthesizes a successful reply.
    """

    def __init__(self, name: str = "grpc", config: GatewayConfig | None = None):
        super().__init__(name, config)
        self._channel: Any = None
        self._stubs: dict[str, Any] = {}
        self._last_error: str | None = None

    async def connect(self) -> bool:
        self._last_error = None
        if not self.config.endpoint:
            self._last_error = "grpc_endpoint_not_configured"
            self._connected = False
            logger.error("gRPC gateway has no endpoint configured")
            return False

        try:
            from grpc import aio
        except ImportError:
            # No HTTP fallback exists. Reporting connected here caused callers
            # to believe messages had been delivered when nothing happened.
            self._last_error = "grpc_package_unavailable"
            self._connected = False
            logger.error("gRPC package unavailable; gateway is disabled")
            return False

        try:
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
        except Exception as exc:
            self._last_error = f"grpc_channel_failed: {exc}"
            self._connected = False
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
        if not self._connected or self._channel is None:
            lat = (time.monotonic() - start) * 1000
            error = self._last_error or "grpc_gateway_not_connected"
            return GatewayResult(success=False, error=error, latency_ms=lat)

        try:
            service_name = message.destination or "default"
            method_name = message.headers.get("method", "invoke")
            payload = (
                message.payload
                if isinstance(message.payload, bytes)
                else json.dumps(message.payload).encode()
            )
            headers = {k: v for k, v in message.headers.items() if k != "method"}
            metadata = [("authorization", headers["Authorization"])] if headers.get("Authorization") else []
            metadata += [(str(k).lower(), str(v)) for k, v in headers.items() if k != "Authorization"]
            response = await self._invoke_unary(service_name, method_name, payload, metadata)
            lat = (time.monotonic() - start) * 1000
            return GatewayResult(
                success=True,
                data=json.loads(response.decode()) if response else None,
                latency_ms=lat,
            )
        except Exception as exc:
            lat = (time.monotonic() - start) * 1000
            self._last_error = str(exc)
            logger.error("gRPC send failed: %s", exc)
            return GatewayResult(success=False, error=str(exc), latency_ms=lat)

    async def receive(self) -> GatewayMessage | None:
        return None

    async def transform(self, message: GatewayMessage) -> GatewayMessage:
        return message

    async def _invoke_unary(
        self,
        service: str,
        method: str,
        payload: bytes,
        metadata: list[tuple[str, str]],
    ) -> bytes:
        if self._channel is None:
            raise RuntimeError("grpc_channel_unavailable")
        call = self._channel.unary_unary(f"/{service}/{method}")
        response = await call(
            payload,
            metadata=metadata,
            timeout=self.config.timeout,
            wait_for_ready=True,
        )
        if not isinstance(response, bytes):
            raise TypeError("gRPC response must be bytes; refusing to echo request payload")
        return response


GatewayRegistry.register(GRPCGateway())
