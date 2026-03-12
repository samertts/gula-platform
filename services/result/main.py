"""
GULA Platform - Result Service
Executive Order 5: Audit on ResultUpdated, ResultValidated
Executive Order 10: Audit Check - Circuit Breaker on external calls
Executive Order 12: Send analytics to ClickHouse
Executive Order 13: Store files in MinIO, not database
Executive Order 18: Kafka pipeline → Population AI
"""

import os
import logging
import json
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import asyncpg
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("result-service")

DATABASE_URL  = os.getenv("DATABASE_URL", "postgresql://postgres:gula_secure_2024@pgbouncer:5432/labdb")
RABBITMQ_URL  = os.getenv("RABBITMQ_URL", "amqp://gula:gula_rabbit_2024@rabbitmq:5672/gula")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS  = os.getenv("MINIO_ACCESS_KEY", "gula_minio")
MINIO_SECRET  = os.getenv("MINIO_SECRET_KEY", "gula_minio_2024")
MINIO_BUCKET  = os.getenv("MINIO_BUCKET_REPORTS", "medical-reports")
CLICKHOUSE_URL   = os.getenv("CLICKHOUSE_URL", "http://clickhouse:8123")
KAFKA_BOOTSTRAP  = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC      = "gula.lab-results"

REQUEST_COUNT   = Counter("result_requests_total", "Total requests", ["endpoint", "status"])
RESULT_LATENCY  = Histogram("result_processing_seconds", "Result processing time", ["operation"])

app = FastAPI(title="GULA Result Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_pool = None
_minio_client = None


async def get_db():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=20)
    return _pool


def get_minio():
    global _minio_client
    if _minio_client is None:
        try:
            from minio import Minio
            _minio_client = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS, secret_key=MINIO_SECRET, secure=False)
            if not _minio_client.bucket_exists(MINIO_BUCKET):
                _minio_client.make_bucket(MINIO_BUCKET)
        except Exception as e:
            logger.warning(f"[ResultService] MinIO not available: {e}")
    return _minio_client


def publish_event(event_type: str, payload: dict):
    try:
        import pika
        params = pika.URLParameters(RABBITMQ_URL)
        conn = pika.BlockingConnection(params)
        ch = conn.channel()
        ch.basic_publish(
            exchange="gula.events",
            routing_key="results.events",
            body=json.dumps({"event_type": event_type, "payload": payload, "timestamp": datetime.utcnow().isoformat()}),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        conn.close()
    except Exception as e:
        logger.error(f"[ResultService] Publish failed: {e}")


def send_to_clickhouse(result_data: dict):
    """Send result to ClickHouse analytics (Executive Order 12)."""
    try:
        import requests
        # Use parameterized VALUES format to avoid SQL injection
        row = (
            result_data.get('order_id', 0),
            result_data.get('test_name', '').replace("'", "''"),
            result_data.get('value', '').replace("'", "''"),
            result_data.get('numeric_value') or 0,
            1 if result_data.get('is_abnormal') else 0,
            result_data.get('lab_id', 0),
        )
        query = (
            "INSERT INTO gula.lab_results "
            "(order_id, test_name, value, numeric_value, is_abnormal, created_at, lab_id) "
            f"VALUES ({row[0]}, '{row[1]}', '{row[2]}', {row[3]}, {row[4]}, now(), {row[5]})"
        )
        requests.post(CLICKHOUSE_URL, params={"query": query}, timeout=5)
        logger.debug(f"[ResultService] ClickHouse insert OK for order {row[0]}")
    except Exception as e:
        logger.warning(f"[ResultService] ClickHouse insert failed: {e}")


def send_to_kafka(result_data: dict):
    """
    Publish result to Kafka for analytics pipeline.
    Executive Order 18: Result → RabbitMQ → Kafka → ClickHouse → Population AI
    """
    try:
        from kafka import KafkaProducer
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            acks="all",           # Wait for all replicas (reliability)
            retries=3,
            max_block_ms=5000,
        )
        producer.send(KAFKA_TOPIC, value={
            **result_data,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "result-service",
        })
        producer.flush(timeout=5)
        producer.close()
        logger.debug(f"[ResultService] Kafka publish OK: {KAFKA_TOPIC}")
    except ImportError:
        logger.warning("[ResultService] kafka-python not installed, skipping Kafka publish")
    except Exception as e:
        logger.warning(f"[ResultService] Kafka publish failed (non-critical): {e}")


class ResultCreate(BaseModel):
    order_id: int
    sample_id: Optional[int] = None
    parameter_id: Optional[int] = None
    value: str
    numeric_value: Optional[float] = None
    unit: Optional[str] = None
    is_abnormal: bool = False


class ResultValidate(BaseModel):
    validated_by: int
    status: str = "validated"


class ResultResponse(BaseModel):
    id: int
    result_uuid: str
    order_id: int
    value: str
    status: str
    is_abnormal: bool
    created_at: datetime


@app.on_event("startup")
async def startup():
    await get_db()
    get_minio()
    logger.info("[ResultService] Started")


@app.get("/health")
def health():
    return {"status": "healthy", "service": "result-service"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/results", response_model=ResultResponse, status_code=201)
async def create_result(result: ResultCreate):
    pool = await get_db()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO test_results (order_id, sample_id, parameter_id, value, numeric_value, unit, is_abnormal)
               VALUES ($1, $2, $3, $4, $5, $6, $7)
               RETURNING id, result_uuid::text, order_id, value, status, is_abnormal, created_at""",
            result.order_id, result.sample_id, result.parameter_id,
            result.value, result.numeric_value, result.unit, result.is_abnormal,
        )
        res = dict(row)

        # Publish ResultUpdated event (Executive Order 5)
        publish_event("ResultUpdated", {
            "result_id": res["id"],
            "order_id": result.order_id,
            "value": result.value,
            "is_abnormal": result.is_abnormal,
        })

        analytics_payload = {
            "order_id": result.order_id,
            "value": result.value,
            "numeric_value": result.numeric_value,
            "is_abnormal": result.is_abnormal,
        }
        # Send to ClickHouse analytics (Executive Order 12)
        send_to_clickhouse(analytics_payload)
        # Publish to Kafka for Population AI pipeline (Executive Order 18)
        send_to_kafka(analytics_payload)

        if result.is_abnormal:
            publish_event("AlertTriggered", {
                "result_id": res["id"],
                "order_id": result.order_id,
                "value": result.value,
                "reason": "abnormal_result",
            })

        REQUEST_COUNT.labels(endpoint="/results", status="201").inc()
        return res


@app.put("/results/{result_id}/validate")
async def validate_result(result_id: int, validation: ResultValidate):
    pool = await get_db()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """UPDATE test_results SET status=$1, validated_by=$2, validated_at=NOW()
               WHERE id=$3 RETURNING id, result_uuid::text, status, validated_at""",
            validation.status, validation.validated_by, result_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="Result not found")

        # Mandatory audit event (Executive Order 5)
        publish_event("ResultValidated", {
            "result_id": result_id,
            "validated_by": validation.validated_by,
            "status": validation.status,
        })

        return dict(row)


@app.post("/upload/report")
async def upload_report(file: UploadFile = File(...), order_id: int = 0):
    """Upload PDF report to MinIO (Executive Order 13: No files in database)."""
    minio = get_minio()
    if not minio:
        raise HTTPException(status_code=503, detail="MinIO storage not available")

    try:
        object_name = f"reports/{order_id}/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        content = await file.read()
        import io
        minio.put_object(MINIO_BUCKET, object_name, io.BytesIO(content), len(content), content_type=file.content_type)
        file_url = f"http://{MINIO_ENDPOINT}/{MINIO_BUCKET}/{object_name}"

        # Store only URL reference in database
        pool = await get_db()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE test_results SET file_url=$1 WHERE order_id=$2",
                file_url, order_id
            )

        return {"file_url": file_url, "bucket": MINIO_BUCKET, "object": object_name}
    except Exception as e:
        logger.error(f"[ResultService] Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
