from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import ssl
import time
from collections.abc import Callable
from typing import Any

from .base import BaseConnector, ConnectorConfig, ConnectorResult, ConnectorStatus

logger = logging.getLogger("gula.ecosystem.messaging")


class MessagingConnector(BaseConnector):
    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self._subscribed_topics: dict[str, list[Callable]] = {}
        self._dead_letter_queue: list[dict] = []
        self._max_dead_letter = 1000
        self._running = False
        self._listen_task: asyncio.Task | None = None
        self._active_futures: set[asyncio.Future] = set()

    async def connect(self) -> bool:
        try:
            options = self._config.options or {}
            self._max_dead_letter = options.get("max_dead_letter", 1000)
            self._running = True
            self._connected = True
            self._status = ConnectorStatus.ACTIVE
            return True
        except Exception as exc:
            self._status = ConnectorStatus.ERROR
            self._metrics["last_error"] = str(exc)
            return False

    async def disconnect(self) -> bool:
        try:
            self._running = False
            if self._listen_task and not self._listen_task.done():
                self._listen_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._listen_task
                self._listen_task = None
            self._connected = False
            self._status = ConnectorStatus.INACTIVE
            return True
        except Exception as exc:
            self._metrics["last_error"] = str(exc)
            return False

    async def send(self, data: Any) -> ConnectorResult:
        if not isinstance(data, dict):
            return self._build_result(False, error="data must be a dict with 'topic' and 'message'", status_code=400)

        topic = data.get("topic", "")
        message = data.get("message", "")
        qos = data.get("qos", 1)
        retain = data.get("retain", False)

        if not topic:
            return self._build_result(False, error="topic is required", status_code=400)

        start = time.monotonic()
        try:
            payload = self._serialize_message(message)
            result = await self._publish(topic, payload, qos=qos, retain=retain)
            duration_ms = int((time.monotonic() - start) * 1000)

            if result:
                self._record_success(duration_ms)
                return self._build_result(True, data={"topic": topic, "qos": qos}, duration_ms=duration_ms)
            self._record_failure("publish failed", duration_ms)
            return self._build_result(False, error="publish failed", duration_ms=duration_ms)

        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            self._record_failure(str(exc), duration_ms)
            return self._build_result(False, error=str(exc), duration_ms=duration_ms)

    async def receive(self) -> ConnectorResult:
        return self._build_result(False, error="use subscribe() for message consumption", status_code=400)

    async def subscribe(self, topic: str, callback: Callable) -> None:
        if topic not in self._subscribed_topics:
            self._subscribed_topics[topic] = []
            await self._register_subscription(topic)
        self._subscribed_topics[topic].append(callback)

    async def unsubscribe(self, topic: str, callback: Callable | None = None) -> None:
        if topic not in self._subscribed_topics:
            return
        if callback is None:
            del self._subscribed_topics[topic]
        else:
            self._subscribed_topics[topic] = [c for c in self._subscribed_topics[topic] if c is not callback]
            if not self._subscribed_topics[topic]:
                del self._subscribed_topics[topic]

    async def _publish(self, topic: str, payload: bytes, qos: int = 1, retain: bool = False) -> bool:
        protocol = self._config.protocol.value
        if protocol == "mqtt":
            return await self._publish_mqtt(topic, payload, qos, retain)
        if protocol == "amqp":
            return await self._publish_amqp(topic, payload)
        return False

    async def _register_subscription(self, topic: str) -> None:
        protocol = self._config.protocol.value
        if protocol == "mqtt":
            await self._subscribe_mqtt(topic)
        elif protocol == "amqp":
            await self._subscribe_amqp(topic)

    async def _publish_mqtt(self, topic: str, payload: bytes, qos: int = 1, retain: bool = False) -> bool:
        try:
            options = self._config.options or {}
            import paho.mqtt.client as mqtt

            client_id = options.get("client_id", f"gula-mqtt-{int(time.time())}")
            client = mqtt.Client(client_id=client_id)

            creds = self._config.credentials or {}
            if creds.get("username"):
                client.username_pw_set(creds["username"], creds.get("password", ""))

            tls_opts = options.get("tls", {})
            if tls_opts.get("enabled", False):
                ca_cert = tls_opts.get("ca_cert")
                cert_file = tls_opts.get("cert_file")
                key_file = tls_opts.get("key_file")
                if ca_cert:
                    client.tls_set(
                        ca_certs=ca_cert,
                        certfile=cert_file,
                        keyfile=key_file,
                        cert_reqs=ssl.CERT_REQUIRED if tls_opts.get("verify", True) else ssl.CERT_NONE,
                    )

            client.connect(self._host(), options.get("port", 1883), keepalive=60)
            info = client.publish(topic, payload, qos=qos, retain=retain)
            client.disconnect()
            return info.rc == mqtt.MQTT_ERR_SUCCESS

        except ImportError:
            logger.warning("paho-mqtt not installed, using simulated publish")
            return await self._simulated_publish(topic, payload)
        except Exception as exc:
            logger.error("MQTT publish error: %s", exc)
            return False

    async def _subscribe_mqtt(self, topic: str) -> None:
        try:
            options = self._config.options or {}
            import paho.mqtt.client as mqtt

            def on_message(client, userdata, msg):
                message = self._deserialize_message(msg.payload)
                topic = msg.topic
                if topic in self._subscribed_topics:
                    for callback in self._subscribed_topics[topic]:
                        _future = asyncio.ensure_future(self._safe_callback(callback, message))
                        self._active_futures.add(_future)
                        _future.add_done_callback(self._active_futures.discard)

            client_id = options.get("client_id", f"gula-mqtt-sub-{int(time.time())}")
            client = mqtt.Client(client_id=client_id)
            client.on_message = on_message

            creds = self._config.credentials or {}
            if creds.get("username"):
                client.username_pw_set(creds["username"], creds.get("password", ""))

            client.connect(self._host(), options.get("port", 1883), keepalive=60)
            client.subscribe(topic, qos=options.get("qos", 1))
            client.loop_start()

        except ImportError:
            logger.warning("paho-mqtt not installed, subscription simulated")
        except Exception as exc:
            logger.error("MQTT subscribe error: %s", exc)

    async def _publish_amqp(self, routing_key: str, payload: bytes) -> bool:
        try:
            options = self._config.options or {}
            import aio_pika

            creds = self._config.credentials or {}
            connection = await aio_pika.connect_robust(
                host=self._host(),
                port=options.get("port", 5672),
                login=creds.get("username", "guest"),
                password=creds.get("password", "guest"),
                virtualhost=options.get("vhost", "/"),
            )

            async with connection:
                channel = await connection.channel()
                exchange_name = options.get("exchange", "")
                exchange_type = options.get("exchange_type", "topic")

                exchange = await channel.declare_exchange(exchange_name, aio_pika.ExchangeType(exchange_type), durable=True)
                message = aio_pika.Message(
                    body=payload,
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    headers={"connector": self._config.name},
                )
                await exchange.publish(message, routing_key=routing_key)

            return True

        except ImportError:
            logger.warning("aio-pika not installed, using simulated publish")
            return await self._simulated_publish(routing_key, payload)
        except Exception as exc:
            logger.error("AMQP publish error: %s", exc)
            return False

    async def _subscribe_amqp(self, routing_key: str) -> None:
        self._listen_task = asyncio.create_task(self._amqp_listen_loop(routing_key))

    async def _amqp_listen_loop(self, routing_key: str) -> None:
        try:
            options = self._config.options or {}
            import aio_pika

            creds = self._config.credentials or {}
            connection = await aio_pika.connect_robust(
                host=self._host(),
                port=options.get("port", 5672),
                login=creds.get("username", "guest"),
                password=creds.get("password", "guest"),
                virtualhost=options.get("vhost", "/"),
            )

            async with connection:
                channel = await connection.channel()
                exchange_name = options.get("exchange", "")
                exchange_type = options.get("exchange_type", "topic")

                exchange = await channel.declare_exchange(exchange_name, aio_pika.ExchangeType(exchange_type), durable=True)
                queue_name = options.get("queue", f"gula-queue-{int(time.time())}")
                queue = await channel.declare_queue(queue_name, durable=options.get("durable", True))
                await queue.bind(exchange, routing_key=routing_key)

                async with queue.iterator() as queue_iter:
                    async for message in queue_iter:
                        async with message.process():
                            payload = self._deserialize_message(message.body)
                            if routing_key in self._subscribed_topics:
                                for callback in self._subscribed_topics[routing_key]:
                                    await self._safe_callback(callback, payload)

        except ImportError:
            logger.warning("aio-pika not installed, subscribe simulated")
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.error("AMQP listen error: %s", exc)

    async def _simulated_publish(self, topic: str, payload: bytes) -> bool:
        await asyncio.sleep(0.01)
        return True

    async def _safe_callback(self, callback: Callable, message: Any) -> None:
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(message)
            else:
                callback(message)
        except Exception as exc:
            logger.error("Message callback error: %s", exc)

    def _serialize_message(self, message: Any) -> bytes:
        if isinstance(message, bytes):
            return message
        if isinstance(message, str):
            return message.encode("utf-8")
        return json.dumps(message, default=str).encode("utf-8")

    def _deserialize_message(self, payload: bytes) -> Any:
        try:
            return json.loads(payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return payload.decode("utf-8", errors="replace")

    def move_to_dead_letter(self, message: dict) -> None:
        self._dead_letter_queue.append(message)
        if len(self._dead_letter_queue) > self._max_dead_letter:
            self._dead_letter_queue.pop(0)

    def get_dead_letter_queue(self) -> list[dict]:
        return list(self._dead_letter_queue)

    def clear_dead_letter_queue(self) -> None:
        self._dead_letter_queue.clear()

    def _host(self) -> str:
        endpoint = self._config.endpoint or ""
        if "://" in endpoint:
            endpoint = endpoint.split("://", 1)[1]
        if ":" in endpoint:
            return endpoint.split(":")[0]
        return endpoint
