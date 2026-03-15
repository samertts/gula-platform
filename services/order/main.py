"""
GULA Platform - Order Service
Executive Order 5: Audit on OrderCreated, OrderCompleted
"""

import os
import logging
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import asyncpg
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("order-service")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:gula_secure_2024@pgbouncer:5432/labdb")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://gula:gula_rabbit_2024@rabbitmq:5672/gula")

REQUEST_COUNT = Counter("order_requests_total", "Total requests", ["endpoint", "status"])

app = FastAPI(title="GULA Order Service", version="1.0.0")
_cors_origins = os.getenv("CORS_ORIGINS", "https://gula-platform.org,http://gula-platform.org").split(",")
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in _cors_origins], allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Authorization", "Content-Type"])

_pool = None


async def get_db():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=20)
    return _pool


def publish_event(event_type: str, payload: dict, routing_key: str = "orders.events"):
    try:
        import pika
        params = pika.URLParameters(RABBITMQ_URL)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        message = {
            "event_type": event_type,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat(),
        }
        channel.basic_publish(
            exchange="gula.events",
            routing_key=routing_key,
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        connection.close()
    except Exception as e:
        logger.error(f"[OrderService] Event publish failed: {e}")


class OrderCreate(BaseModel):
    lab_id: int
    patient_id: int
    test_id: int
    priority: str = "routine"
    ordered_by: Optional[int] = None


class OrderResponse(BaseModel):
    id: int
    order_uuid: str
    lab_id: int
    patient_id: int
    test_id: int
    priority: str
    status: str
    ordered_at: datetime


@app.on_event("startup")
async def startup():
    await get_db()
    logger.info("[OrderService] Started")


@app.get("/health")
def health():
    return {"status": "healthy", "service": "order-service"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/orders", response_model=OrderResponse, status_code=201)
async def create_order(order: OrderCreate):
    pool = await get_db()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO test_orders (lab_id, patient_id, test_id, priority, ordered_by)
               VALUES ($1, $2, $3, $4, $5)
               RETURNING id, order_uuid::text, lab_id, patient_id, test_id, priority, status, ordered_at""",
            order.lab_id, order.patient_id, order.test_id, order.priority, order.ordered_by,
        )
        result = dict(row)

        # Publish OrderCreated event (Executive Order 5)
        publish_event("OrderCreated", {
            "order_id": result["id"],
            "lab_id": order.lab_id,
            "patient_id": order.patient_id,
            "test_id": order.test_id,
            "priority": order.priority,
        })

        REQUEST_COUNT.labels(endpoint="/orders", status="201").inc()
        return result


@app.put("/orders/{order_id}/complete")
async def complete_order(order_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """UPDATE test_orders SET status='completed', completed_at=NOW(), updated_at=NOW()
               WHERE id=$1 RETURNING id, order_uuid::text, status, completed_at""",
            order_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="Order not found")

        # Mandatory audit event (Executive Order 5)
        publish_event("OrderCompleted", {
            "order_id": order_id,
            "completed_at": row["completed_at"].isoformat(),
        })

        return dict(row)


@app.get("/orders", response_model=List[OrderResponse])
async def list_orders(lab_id: Optional[int] = None, status: Optional[str] = None, skip: int = 0, limit: int = 100):
    pool = await get_db()
    async with pool.acquire() as conn:
        query = """SELECT id, order_uuid::text, lab_id, patient_id, test_id, priority, status, ordered_at
                   FROM test_orders WHERE 1=1"""
        params = []
        idx = 1
        if lab_id:
            query += f" AND lab_id=${idx}"; params.append(lab_id); idx += 1
        if status:
            query += f" AND status=${idx}"; params.append(status); idx += 1
        query += f" ORDER BY ordered_at DESC LIMIT ${idx} OFFSET ${idx+1}"
        params.extend([limit, skip])
        rows = await conn.fetch(query, *params)
        return [dict(r) for r in rows]
