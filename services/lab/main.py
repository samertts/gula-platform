"""
GULA Platform - Lab Service
Manages laboratories, devices, and lab operations
"""

import os
import logging
import sys
sys.path.insert(0, "/app/shared")

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import asyncpg
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lab-service")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:gula_secure_2024@pgbouncer:5432/labdb")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://gula:gula_rabbit_2024@rabbitmq:5672/gula")

REQUEST_COUNT   = Counter("lab_requests_total", "Total requests", ["endpoint", "method", "status"])
REQUEST_LATENCY = Histogram("lab_request_duration_seconds", "Request duration", ["endpoint"])

app = FastAPI(title="GULA Lab Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_pool = None


async def get_db():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=20)
    return _pool


class LaboratoryCreate(BaseModel):
    lab_name: str
    city: Optional[str] = None
    region: Optional[str] = None
    contact_phone: Optional[str] = None
    email: Optional[str] = None


class LaboratoryResponse(BaseModel):
    id: int
    lab_name: str
    city: Optional[str]
    region: Optional[str]
    status: str
    created_at: datetime


@app.on_event("startup")
async def startup():
    await get_db()
    logger.info("[LabService] Started")


@app.get("/health")
def health():
    return {"status": "healthy", "service": "lab-service"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/laboratories", response_model=LaboratoryResponse, status_code=201)
async def create_laboratory(lab: LaboratoryCreate):
    pool = await get_db()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO laboratories (lab_name, city, region, contact_phone, email)
               VALUES ($1, $2, $3, $4, $5)
               RETURNING id, lab_name, city, region, status, created_at""",
            lab.lab_name, lab.city, lab.region, lab.contact_phone, lab.email
        )
        REQUEST_COUNT.labels(endpoint="/laboratories", method="POST", status="201").inc()
        return dict(row)


@app.get("/laboratories", response_model=List[LaboratoryResponse])
async def list_laboratories(skip: int = 0, limit: int = 100):
    pool = await get_db()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, lab_name, city, region, status, created_at FROM laboratories ORDER BY created_at DESC LIMIT $1 OFFSET $2",
            limit, skip
        )
        return [dict(r) for r in rows]


@app.get("/laboratories/{lab_id}", response_model=LaboratoryResponse)
async def get_laboratory(lab_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, lab_name, city, region, status, created_at FROM laboratories WHERE id = $1",
            lab_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="Laboratory not found")
        return dict(row)
