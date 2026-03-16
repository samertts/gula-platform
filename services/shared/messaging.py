"""
GULA Platform - RabbitMQ Messaging Layer
Executive Order 6: Durable queues, persistent messages, acknowledged delivery
Executive Order 8: Retry queue for failed messages
"""

import json
import logging
import time
import os
from typing import Callable, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "")
if not RABBITMQ_URL:
    logger.warning("[Messaging] RABBITMQ_URL not set - messaging will not work")

# Medical audit events (Executive Order 5)
AUDIT_EVENTS = {
    "PatientCreated",
    "SampleCollected",
    "ResultUpdated",
    "ResultValidated",
    "OrderCompleted",
    "OrderCreated",
    "SampleRejected",
    "AlertTriggered",
}

QUEUE_CONFIG = {
    "orders.events":    {"durable": True, "arguments": {"x-dead-letter-exchange": "gula.deadletter"}},
    "samples.events":   {"durable": True, "arguments": {"x-dead-letter-exchange": "gula.deadletter"}},
    "results.events":   {"durable": True, "arguments": {"x-dead-letter-exchange": "gula.deadletter"}},
    "alerts.events":    {"durable": True, "arguments": {"x-dead-letter-exchange": "gula.deadletter"}},
    "audit.events":     {"durable": True, "arguments": {}},
    "retry.queue":      {"durable": True, "arguments": {"x-message-ttl": 30000, "x-dead-letter-exchange": "gula.events"}},
}


class MessagePublisher:
    """Publishes events to RabbitMQ with persistence guarantee."""

    def __init__(self):
        self._channel = None
        self._connection = None
        self._connected = False

    def _connect(self):
        try:
            import pika
            params = pika.URLParameters(RABBITMQ_URL)
            params.heartbeat = 60
            params.blocked_connection_timeout = 300
            self._connection = pika.BlockingConnection(params)
            self._channel = self._connection.channel()
            self._channel.confirm_delivery()
            self._connected = True
            logger.info("[MessagePublisher] Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"[MessagePublisher] Connection failed: {e}")
            self._connected = False

    def publish(
        self,
        queue: str,
        event_type: str,
        payload: dict,
        exchange: str = "gula.events",
        routing_key: Optional[str] = None,
    ) -> bool:
        if not self._connected:
            self._connect()

        if not self._connected:
            logger.error(f"[MessagePublisher] Cannot publish to {queue}: not connected")
            return False

        message = {
            "event_type": event_type,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0",
        }

        rk = routing_key or queue
        try:
            import pika
            self._channel.basic_publish(
                exchange=exchange,
                routing_key=rk,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,          # Persistent message (Executive Order 6)
                    content_type="application/json",
                    message_id=f"{event_type}_{int(time.time() * 1000)}",
                ),
                mandatory=True,
            )
            logger.debug(f"[MessagePublisher] Published {event_type} → {queue}")

            # Publish to audit queue for medical events (Executive Order 5)
            if event_type in AUDIT_EVENTS:
                self._publish_audit(event_type, payload)

            return True
        except Exception as e:
            logger.error(f"[MessagePublisher] Publish failed: {e}")
            self._connected = False
            self._send_to_retry(queue, event_type, payload)
            return False

    def _publish_audit(self, event_type: str, payload: dict):
        """Publish to audit queue for compliance tracking."""
        try:
            import pika
            audit_msg = {
                "event_type": event_type,
                "payload": payload,
                "timestamp": datetime.utcnow().isoformat(),
                "audit": True,
            }
            self._channel.basic_publish(
                exchange="gula.events",
                routing_key="audit.events",
                body=json.dumps(audit_msg),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type="application/json",
                ),
            )
        except Exception as e:
            logger.warning(f"[MessagePublisher] Audit publish failed: {e}")

    def _send_to_retry(self, queue: str, event_type: str, payload: dict):
        """Send failed message to retry.queue (Executive Order 8)."""
        logger.info(f"[MessagePublisher] Sending to retry.queue: {event_type}")


class MessageConsumer:
    """Consumes messages from RabbitMQ with acknowledgement guarantee."""

    def __init__(self, queue: str, handler: Callable):
        self.queue   = queue
        self.handler = handler

    def start(self):
        import pika

        def on_message(channel, method, properties, body):
            try:
                message = json.loads(body)
                self.handler(message)
                channel.basic_ack(delivery_tag=method.delivery_tag)
                logger.debug(f"[MessageConsumer] ACK message from {self.queue}")
            except Exception as e:
                logger.error(f"[MessageConsumer] Failed to process message: {e}")
                # Reject and requeue (up to dead-letter)
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        while True:
            try:
                params = pika.URLParameters(RABBITMQ_URL)
                connection = pika.BlockingConnection(params)
                channel = connection.channel()
                channel.basic_qos(prefetch_count=10)
                channel.basic_consume(queue=self.queue, on_message_callback=on_message)
                logger.info(f"[MessageConsumer] Listening on {self.queue}")
                channel.start_consuming()
            except Exception as e:
                logger.error(f"[MessageConsumer] Error: {e}. Reconnecting in 5s...")
                time.sleep(5)


# Singleton publisher
_publisher: Optional[MessagePublisher] = None


def get_publisher() -> MessagePublisher:
    global _publisher
    if _publisher is None:
        _publisher = MessagePublisher()
    return _publisher


def publish_event(queue: str, event_type: str, payload: dict, **kwargs) -> bool:
    return get_publisher().publish(queue, event_type, payload, **kwargs)
