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

logger = logging.getLogger("gula.integration.gateway.mqtt")


class MQTTGateway(MessageGateway):
    def __init__(self, name: str = "mqtt", config: GatewayConfig | None = None):
        super().__init__(name, config)
        self._client: Any = None

    async def connect(self) -> bool:
        try:
            import asyncio_mqtt as mqtt

            client_id = self.config.options.get("client_id", "gula-mqtt-gateway")
            self._client = mqtt.Client(
                hostname=self.config.endpoint,
                client_id=client_id,
                username=self.config.options.get("username"),
                password=self.config.options.get("password"),
                keepalive=60,
            )
            await self._client.connect()
            self._connected = True
            logger.info("MQTT gateway connected: %s", self.config.endpoint)
            return True
        except ImportError:
            logger.warning("asyncio_mqtt not installed — MQTT will use simulated mode")
            self._connected = True
            return True
        except Exception as exc:
            logger.error("MQTT gateway connection failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._client:
            with contextlib.suppress(Exception):
                await self._client.disconnect()
            self._client = None
        self._connected = False
        return True

    async def send(self, message: GatewayMessage) -> GatewayResult:
        start = time.monotonic()
        try:
            topic = message.destination or self.config.options.get("topic", "gula/default")
            qos = int(self.config.options.get("qos", 1))
            retain = bool(self.config.options.get("retain", False))
            payload = (
                json.dumps(message.payload)
                if not isinstance(message.payload, str)
                else message.payload
            )
            if self._client:
                await self._client.publish(topic=topic, payload=payload, qos=qos, retain=retain)
            lat = (time.monotonic() - start) * 1000
            return GatewayResult(success=True, latency_ms=lat)
        except ImportError:
            lat = (time.monotonic() - start) * 1000
            return GatewayResult(success=True, latency_ms=lat)
        except Exception as exc:
            lat = (time.monotonic() - start) * 1000
            logger.error("MQTT send failed: %s", exc)
            return GatewayResult(success=False, error=str(exc), latency_ms=lat)

    async def receive(self) -> GatewayMessage | None:
        return None

    async def transform(self, message: GatewayMessage) -> GatewayMessage:
        return message

    async def subscribe(self, topic: str, qos: int = 1) -> bool:
        if self._client:
            try:
                await self._client.subscribe(topic, qos=qos)
                return True
            except Exception as exc:
                logger.error("MQTT subscribe failed: %s", exc)
        return False

    async def unsubscribe(self, topic: str) -> bool:
        if self._client:
            try:
                await self._client.unsubscribe(topic)
                return True
            except Exception:
                pass
        return False


GatewayRegistry.register(MQTTGateway())
