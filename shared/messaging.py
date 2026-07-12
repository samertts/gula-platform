from __future__ import annotations

import json
import logging
from typing import Any, Callable

logger = logging.getLogger("gula.messaging")


class MessageBroker:
    def __init__(self, url: str = "", exchange: str = "gula.events"):
        self._url = url
        self._exchange = exchange
        self._connection = None
        self._channel = None

    def connect(self) -> None:
        if not self._url:
            logger.info("Message broker URL not configured, using stub mode")
            return
        try:
            import pika
            params = pika.URLParameters(self._url)
            self._connection = pika.BlockingConnection(params)
            self._channel = self._connection.channel()
            self._channel.exchange_declare(exchange=self._exchange, exchange_type="topic", durable=True)
            logger.info("Connected to message broker at %s", self._url)
        except Exception as exc:
            logger.warning("Message broker connection failed: %s", exc)

    def publish(self, routing_key: str, message: dict[str, Any]) -> bool:
        if not self._channel:
            logger.warning("No broker connection, message not sent: %s", routing_key)
            return False
        try:
            import pika
            self._channel.basic_publish(
                exchange=self._exchange,
                routing_key=routing_key,
                body=json.dumps(message, ensure_ascii=False, default=str),
                properties=pika.BasicProperties(delivery_mode=2),
            )
            return True
        except Exception as exc:
            logger.error("Publish failed: %s", exc)
            return False

    def consume(self, routing_key: str, handler: Callable[[dict[str, Any]], None]) -> None:
        if not self._channel:
            logger.warning("No broker connection, cannot consume: %s", routing_key)
            return
        result = self._channel.queue_declare(queue="", exclusive=True)
        queue_name = result.method.queue
        self._channel.queue_bind(exchange=self._exchange, queue=queue_name, routing_key=routing_key)

        def callback(ch, method, properties, body):
            try:
                message = json.loads(body)
                handler(message)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as exc:
                logger.error("Consumer callback failed: %s", exc)
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        self._channel.basic_consume(queue=queue_name, on_message_callback=callback)

    def start_consuming(self) -> None:
        if self._channel:
            self._channel.start_consuming()

    def close(self) -> None:
        if self._connection:
            self._connection.close()
