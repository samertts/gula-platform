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

logger = logging.getLogger("gula.integration.gateway.amqp")


class AMQPGateway(MessageGateway):
    def __init__(self, name: str = "amqp", config: GatewayConfig | None = None):
        super().__init__(name, config)
        self._connection: Any = None
        self._channel: Any = None

    async def connect(self) -> bool:
        try:
            import aio_pika
            self._connection = await aio_pika.connect_robust(
                self.config.endpoint,
                timeout=self.config.timeout,
            )
            self._channel = await self._connection.channel()
            self._connected = True
            logger.info("AMQP gateway connected: %s", self.config.endpoint)
            return True
        except ImportError:
            logger.warning("aio_pika not installed — AMQP will use simulated mode")
            self._connected = True
            return True
        except Exception as exc:
            logger.error("AMQP gateway connection failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._channel:
            with contextlib.suppress(Exception):
                await self._channel.close()
            self._channel = None
        if self._connection:
            with contextlib.suppress(Exception):
                await self._connection.close()
            self._connection = None
        self._connected = False
        return True

    async def send(self, message: GatewayMessage) -> GatewayResult:
        start = time.monotonic()
        try:
            import aio_pika
            if not self._channel:
                return GatewayResult(success=False, error="Not connected")
            exchange_name = self.config.options.get("exchange", "")
            routing_key = message.destination or self.config.options.get("routing_key", "")
            body = json.dumps(message.payload) if not isinstance(message.payload, str) else message.payload
            if exchange_name:
                exchange = await self._channel.get_exchange(exchange_name)
                await exchange.send(
                    aio_pika.Message(
                        body=body.encode(),
                        correlation_id=message.correlation_id,
                        headers=message.headers,
                    ),
                    routing_key=routing_key,
                )
            else:
                await self._channel.default_exchange.publish(
                    aio_pika.Message(
                        body=body.encode(),
                        correlation_id=message.correlation_id,
                        headers=message.headers,
                    ),
                    routing_key=routing_key,
                )
            lat = (time.monotonic() - start) * 1000
            return GatewayResult(success=True, latency_ms=lat)
        except ImportError:
            lat = (time.monotonic() - start) * 1000
            return GatewayResult(success=True, latency_ms=lat)
        except Exception as exc:
            lat = (time.monotonic() - start) * 1000
            logger.error("AMQP send failed: %s", exc)
            return GatewayResult(success=False, error=str(exc), latency_ms=lat)

    async def receive(self) -> GatewayMessage | None:
        return None

    async def transform(self, message: GatewayMessage) -> GatewayMessage:
        return message

    async def declare_queue(self, queue_name: str, durable: bool = True) -> bool:
        if self._channel:
            try:
                await self._channel.declare_queue(queue_name, durable=durable)
                return True
            except Exception:
                pass
        return False


GatewayRegistry.register(AMQPGateway())
