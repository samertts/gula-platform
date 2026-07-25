from __future__ import annotations

import contextlib
import json
import logging
import time
from typing import Any

from backend.app.integration.gateway.base import (
    GatewayConfig,
    GatewayMessage,
    GatewayResult,
    MessageGateway,
)
from backend.app.integration.gateway.registry import GatewayRegistry

logger = logging.getLogger("gula.integration.gateway.websocket")


class WebSocketGateway(MessageGateway):
    def __init__(self, name: str = "websocket", config: GatewayConfig | None = None):
        super().__init__(name, config)
        self._connection: Any = None
        self._message_buffer: list[GatewayMessage] = []

    async def connect(self) -> bool:
        try:
            import websockets

            self._connection = await websockets.connect(
                self.config.endpoint,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=5,
            )
            self._connected = True
            logger.info("WebSocket gateway connected: %s", self.config.endpoint)
            return True
        except ImportError:
            logger.warning("websockets not installed — WebSocket will use simulated mode")
            self._connected = True
            return True
        except Exception as exc:
            logger.error("WebSocket gateway connection failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._connection:
            with contextlib.suppress(Exception):
                await self._connection.close()
            self._connection = None
        self._connected = False
        self._message_buffer.clear()
        return True

    async def send(self, message: GatewayMessage) -> GatewayResult:
        start = time.monotonic()
        try:
            payload = (
                json.dumps(message.payload)
                if not isinstance(message.payload, str)
                else message.payload
            )
            if self._connection:
                await self._connection.send(payload)
            lat = (time.monotonic() - start) * 1000
            return GatewayResult(success=True, latency_ms=lat)
        except Exception as exc:
            lat = (time.monotonic() - start) * 1000
            logger.error("WebSocket send failed: %s", exc)
            return GatewayResult(success=False, error=str(exc), latency_ms=lat)

    async def receive(self) -> GatewayMessage | None:
        if self._message_buffer:
            return self._message_buffer.pop(0)
        if self._connection:
            try:
                raw = await self._connection.recv()
                data = json.loads(raw) if isinstance(raw, str) else raw
                return GatewayMessage(payload=data)
            except Exception:
                pass
        return None

    async def transform(self, message: GatewayMessage) -> GatewayMessage:
        return message

    async def subscribe(self, channel: str) -> bool:
        return True

    async def unsubscribe(self, channel: str) -> bool:
        return True


GatewayRegistry.register(WebSocketGateway())
