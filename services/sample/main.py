"""
GULA Platform - Sample Service
Executive Order 5: Audit on SampleCollected
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
logger = logging.getLogger("sample-service")

DATABASE_URL = os.environ["DATABASE_URL"]  # Required - no hardcoded fallback
RABBITMQ_URL = os.environ["RABBITMQ_URL"]  # Required - no hardcoded fallback

REQUEST_COUNT = Counter("sample_requests_total", "Total requests", ["endpoint", "status"])

app = FastAPI(title="GULA Sample Service", version="1.0.0")
_cors_origins = os.getenv("CORS_ORIGINS", "https://gula-platform.org,http://gula-platform.org").split(",")
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in _cors_origins], allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Authorization", "Content-Type"])

_pool = None


async def get_db():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=20)
    return _pool


def publish_event(event_type: str, payload: dict):
    try:
        import pika
        params = pika.URLParameters(RABBITMQ_URL)
        conn = pika.BlockingConnection(params)
        ch = conn.channel()
        ch.basic_publish(
            exchange="gula.events",
            routing_key="samples.events",
            body=json.dumps({"event_type": event_type, "payload": payload, "timestamp": datetime.utcnow().isoformat()}),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        conn.close()
    except Exception as e:
        logger.error(f"[SampleService] Publish failed: {e}")


class SampleCreate(BaseModel):
    order_id: int
    barcode: Optional[str] = None
    sample_type: str
    collected_by: Optional[int] = None
    notes: Optional[str] = None


class SampleResponse(BaseModel):
    id: int
    sample_uuid: str
    order_id: int
    barcode: Optional[str]
    sample_type: str
    status: str
    collection_time: datetime


@app.on_event("startup")
async def startup():
    await get_db()
    logger.info("[SampleService] Started")


@app.on_event("shutdown")
async def shutdown():
    if _pool:
        await _pool.close()
        logger.info("[SampleService] Database pool closed")


@app.get("/health")
def health():
    return {"status": "healthy", "service": "sample-service"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/samples", response_model=SampleResponse, status_code=201)
async def collect_sample(sample: SampleCreate):
    pool = await get_db()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO samples (order_id, barcode, sample_type, collected_by, notes)
               VALUES ($1, $2, $3, $4, $5)
               RETURNING id, sample_uuid::text, order_id, barcode, sample_type, status, collection_time""",
            sample.order_id, sample.barcode, sample.sample_type, sample.collected_by, sample.notes,
        )
        result = dict(row)

        # Mandatory audit event (Executive Order 5)
        publish_event("SampleCollected", {
            "sample_id": result["id"],
            "order_id": sample.order_id,
            "barcode": sample.barcode,
            "sample_type": sample.sample_type,
        })

        REQUEST_COUNT.labels(endpoint="/samples", status="201").inc()
        return result


@app.put("/samples/{sample_id}/status")
async def update_sample_status(sample_id: int, status: str):
    allowed = {"collected", "in_transit", "received", "processing", "completed", "rejected"}
    if status not in allowed:
        raise HTTPException(status_code=400, detail=f"Invalid status. Allowed: {allowed}")

    pool = await get_db()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "UPDATE samples SET status=$1 WHERE id=$2 RETURNING id, status",
            status, sample_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="Sample not found")

        if status == "rejected":
            publish_event("SampleRejected", {"sample_id": sample_id, "status": status})

        return dict(row)


@app.get("/samples/track/{barcode}")
async def track_by_barcode(barcode: str):
    pool = await get_db()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT id, sample_uuid::text, order_id, barcode, sample_type, status, collection_time
               FROM samples WHERE barcode=$1""",
            barcode
        )
        if not row:
            raise HTTPException(status_code=404, detail="Sample not found")
        return dict(row)
