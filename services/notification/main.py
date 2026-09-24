"""
GULA Platform - Notification Service
Handles alerts, notifications via RabbitMQ consumer
"""

import json
import logging
import os

from fail_closed import FailClosedMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
from starlette.responses import Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notification-service")

RABBITMQ_URL = os.environ["RABBITMQ_URL"]  # Required - no hardcoded fallback

NOTIFICATIONS_SENT = Counter("notifications_sent_total", "Total notifications sent", ["type"])

app = FastAPI(title="GULA Notification Service", version="1.0.0")
_cors_origins = os.getenv("CORS_ORIGINS", "https://gula-platform.org,http://gula-platform.org").split(",")
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in _cors_origins], allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Authorization", "Content-Type"])
# NR-142: refuse every request this service cannot attribute to a caller.
# Added last, so Starlette runs it outermost -- before CORS and before any
# handler touches labdb. See services/fail_closed.py.
app.add_middleware(FailClosedMiddleware)


def process_alert(message: dict):
    """Process alert notification."""
    event_type = message.get("event_type", "unknown")
    payload = message.get("payload", {})
    logger.warning(f"[ALERT] {event_type}: {payload}")
    NOTIFICATIONS_SENT.labels(type="alert").inc()


def consume_alerts():
    """Consume alerts from RabbitMQ."""
    import time

    import pika
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
