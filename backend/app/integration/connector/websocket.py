from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Callable
from typing import Any

from backend.app.integration.connector.spec import (
    ConnectorSpec,
    ConnectorStatus,
    ConnectorType,
)

logger = logging.getLogger("gula.integration.connector.websocket")


class WebSocketConnector:
    def __init__(self, spec: ConnectorSpec):
        if spec.connector_type != ConnectorType.WEBSOCKET:
            raise ValueError(
                f"WebSocketConnector requires type WEBSOCKET, got {spec.connector_type.name}"
            )
        self.spec = spec
        self._ws = None
        self._connected = False
        self._listeners: dict[str, list[Callable]] = {}
        self._reconnect_delay = 1.0

    async def connect(self) -> bool:
        try:
            import websockets
        except ImportError:
            logger.error("websockets library not installed")
            self.spec.status = ConnectorStatus.FAILED
            return False

        try:
            url = self.spec.endpoints[0].url if self.spec.endpoints else ""
            self._ws = await websockets.connect(url)
            self._connected = True
            self.spec.status = ConnectorStatus.CONNECTED
            logger.info("WebSocket connected: %s", url)
            return True
        except Exception as exc:
            self.spec.status = ConnectorStatus.FAILED
            self.spec.health.error = str(exc)
            logger.error("WebSocket connection failed: %s", exc)
            return False

    async def disconnect(self) -> None:
        if self._ws:
            await self._ws.close()
            self._ws = None
        self._connected = False
        self.spec.status = ConnectorStatus.DISCONNECTED

    async def publish(self, topic: str, message: Any) -> None:
        if not self._connected or not self._ws:
            raise RuntimeError("WebSocket not connected")
        payload = json.dumps({"topic": topic, "data": message})
        await self._ws.send(payload)

    async def subscribe(self, topic: str, handler: Callable) -> None:
        self._listeners.setdefault(topic, []).append(handler)

    async def listen(self) -> None:
        if not self._connected or not self._ws:
            return
        try:
            async for message in self._ws:
                try:
                    data = json.loads(message)
                    topic = data.get("topic", "")
                    if topic in self._listeners:
                        for handler in self._listeners[topic]:
                            await handler(data.get("data", {}))
                except json.JSONDecodeError:
                    logger.warning("Invalid WebSocket message received")
        except Exception as exc:
            logger.warning("WebSocket listener ended: %s", exc)
            self._connected = False

    async def reconnect(self) -> bool:
        delay = self._reconnect_delay
        for attempt in range(5):
            logger.info("WebSocket reconnect attempt %d...", attempt + 1)
            await asyncio.sleep(delay)
            if await self.connect():
                return True
            delay = min(delay * 2, 30.0)
        return False
