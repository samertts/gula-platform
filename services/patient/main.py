"""
GULA Platform - Patient Service
Executive Order 5: Audit on PatientCreated
"""

import os
import logging
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
import asyncpg
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("patient-service")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:gula_secure_2024@pgbouncer:5432/labdb")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://gula:gula_rabbit_2024@rabbitmq:5672/gula")

REQUEST_COUNT = Counter("patient_requests_total", "Total requests", ["endpoint", "status"])

app = FastAPI(title="GULA Patient Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_pool = None


async def get_db():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=20)
    return _pool


def publish_event(event_type: str, payload: dict):
    """Publish event to RabbitMQ."""
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
            routing_key="audit.events" if event_type == "PatientCreated" else "orders.events",
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        connection.close()
    except Exception as e:
        logger.error(f"[PatientService] Event publish failed: {e}")


class PatientCreate(BaseModel):
    lab_id: Optional[int] = None
    national_id: Optional[str] = None
    first_name: str
    last_name: str
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    age: Optional[int] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None


class PatientResponse(BaseModel):
    id: int
    patient_uuid: str
    first_name: str
    last_name: str
    gender: Optional[str]
    age: Optional[int]
    created_at: datetime


@app.on_event("startup")
async def startup():
    await get_db()
    logger.info("[PatientService] Started")


@app.get("/health")
def health():
    return {"status": "healthy", "service": "patient-service"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/patients", response_model=PatientResponse, status_code=201)
async def create_patient(patient: PatientCreate):
    pool = await get_db()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO patients
               (lab_id, national_id, first_name, last_name, gender, date_of_birth, age, phone, email, address)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
               RETURNING id, patient_uuid::text, first_name, last_name, gender, age, created_at""",
            patient.lab_id, patient.national_id, patient.first_name, patient.last_name,
            patient.gender, patient.date_of_birth, patient.age,
            patient.phone, patient.email, patient.address,
        )
        result = dict(row)

        # Mandatory audit event (Executive Order 5)
        publish_event("PatientCreated", {
            "patient_id": result["id"],
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "lab_id": patient.lab_id,
        })

        REQUEST_COUNT.labels(endpoint="/patients", status="201").inc()
        return result


@app.get("/patients", response_model=List[PatientResponse])
async def list_patients(lab_id: Optional[int] = None, skip: int = 0, limit: int = 100):
    pool = await get_db()
    async with pool.acquire() as conn:
        if lab_id:
            rows = await conn.fetch(
                """SELECT id, patient_uuid::text, first_name, last_name, gender, age, created_at
                   FROM patients WHERE lab_id = $1 ORDER BY created_at DESC LIMIT $2 OFFSET $3""",
                lab_id, limit, skip
            )
        else:
            rows = await conn.fetch(
                """SELECT id, patient_uuid::text, first_name, last_name, gender, age, created_at
                   FROM patients ORDER BY created_at DESC LIMIT $1 OFFSET $2""",
                limit, skip
            )
        return [dict(r) for r in rows]


@app.get("/patients/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT id, patient_uuid::text, first_name, last_name, gender, age, created_at
               FROM patients WHERE id = $1""",
            patient_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="Patient not found")
        return dict(row)
