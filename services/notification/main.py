"""
GULA Platform - Notification Service
Handles alerts, notifications via RabbitMQ consumer
"""

import os
import logging
import asyncio
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notification-service")

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://gula:gula_rabbit_2024@rabbitmq:5672/gula")

NOTIFICATIONS_SENT = Counter("notifications_sent_total", "Total notifications sent", ["type"])

app = FastAPI(title="GULA Notification Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def process_alert(message: dict):
    """Process alert notification."""
    event_type = message.get("event_type", "unknown")
    payload = message.get("payload", {})
    logger.warning(f"[ALERT] {event_type}: {payload}")
    NOTIFICATIONS_SENT.labels(type="alert").inc()


def consume_alerts():
    """Consume alerts from RabbitMQ."""
    import pika, time
    while True:
        try:
            params = pika.URLParameters(RABBITMQ_URL)
            conn = pika.BlockingConnection(params)
            ch = conn.channel()
            ch.basic_qos(prefetch_count=10)

            def callback(ch, method, props, body):
                try:
                    msg = json.loads(body)
                    process_alert(msg)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as e:
                    logger.error(f"Alert processing error: {e}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

            ch.basic_consume(queue="alerts.events", on_message_callback=callback)
            logger.info("[NotificationService] Listening for alerts...")
            ch.start_consuming()
        except Exception as e:
            logger.error(f"[NotificationService] RabbitMQ error: {e}. Reconnecting in 5s...")
            time.sleep(5)


@app.on_event("startup")
async def startup():
    import threading
    thread = threading.Thread(target=consume_alerts, daemon=True)
    thread.start()
    logger.info("[NotificationService] Started")


@app.get("/health")
def health():
    return {"status": "healthy", "service": "notification-service"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
