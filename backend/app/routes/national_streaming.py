from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .._compat import UTC
from ..database import get_db
from ..models.lab_user import LabUser
from ..national_data.models.event_store.StoredEvent import StoredEvent
from ..security.dependencies import require_permission
from ..services.data_platform_service import DataPlatformService
from ..services.outbox_service import emit_to_outbox

logger = logging.getLogger("gula.national_streaming")

router = APIRouter(prefix="/national-data/streaming", tags=["national-data-streaming"])


# ── Pydantic Schemas ──────────────────────────────────────────────────────────


class FHIRSubscriptionPayload(BaseModel):
    resource_type: str
    resource_id: str
    event_type: str = "create"
    resource: dict[str, Any] | None = None
    subscription_id: str | None = None
    timestamp: str | None = None


class HL7StreamingPayload(BaseModel):
    message_type: str
    message_control_id: str
    hl7_version: str = "2.5.1"
    raw_message: str | None = None
    parsed_segments: dict[str, Any] | None = None
    source_device: str | None = None
    source_facility: str | None = None
    patient_id: str | None = None
    encounter_id: str | None = None


class EventStreamingPayload(BaseModel):
    event_type: str
    aggregate_type: str
    aggregate_id: str
    event_data: dict[str, Any]
    metadata_: dict[str, Any] | None = None
    partition_key: str | None = None
    correlation_id: str | None = None


class CDCChangeRecord(BaseModel):
    table_name: str
    operation: str = Field(..., pattern="^(insert|update|delete)$")
    primary_key: str
    primary_key_value: str
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    change_timestamp: str | None = None
    transaction_id: str | None = None


# ── FHIR Subscription Endpoint ────────────────────────────────────────────────


@router.post("/fhir", summary="FHIR Subscription endpoint")
def receive_fhir_subscription(
    payload: FHIRSubscriptionPayload,
    request: Request,
    current_user: LabUser = Depends(require_permission("patients:write")),
    db: Session = Depends(get_db),
):
    event_type = f"fhir.{payload.resource_type}.{payload.event_type}"
    event_data = {
        "resource_type": payload.resource_type,
        "resource_id": payload.resource_id,
        "subscription_id": payload.subscription_id,
        "timestamp": payload.timestamp or datetime.now(UTC).isoformat(),
        "resource": payload.resource,
    }

    DataPlatformService.record_event(
        db=db,
        event_type=event_type,
        aggregate_type=f"FHIR::{payload.resource_type}",
        aggregate_id=payload.resource_id,
        event_data=event_data,
        partition_key=payload.resource_type,
    )

    emit_to_outbox(
        db=db,
        event_type=event_type,
        payload=event_data,
        aggregate_type=f"FHIR::{payload.resource_type}",
        aggregate_id=payload.resource_id,
    )

    db.commit()
    logger.info(
        "FHIR subscription event: %s resource=%s/%s",
        payload.event_type,
        payload.resource_type,
        payload.resource_id,
    )
    return {"status": "received", "event_type": event_type}


# ── HL7 Streaming Endpoint ───────────────────────────────────────────────────


@router.post("/hl7", summary="HL7 message streaming endpoint")
def receive_hl7_message(
    payload: HL7StreamingPayload,
    request: Request,
    current_user: LabUser = Depends(require_permission("patients:write")),
    db: Session = Depends(get_db),
):
    event_type = f"hl7.{payload.message_type}"
    event_data = {
        "message_type": payload.message_type,
        "message_control_id": payload.message_control_id,
        "hl7_version": payload.hl7_version,
        "source_device": payload.source_device,
        "source_facility": payload.source_facility,
        "patient_id": payload.patient_id,
        "encounter_id": payload.encounter_id,
        "parsed_segments": payload.parsed_segments,
        "received_at": datetime.now(UTC).isoformat(),
    }

    aggregate_id = payload.message_control_id or f"hl7-{datetime.now(UTC).timestamp()}"

    DataPlatformService.record_event(
        db=db,
        event_type=event_type,
        aggregate_type=f"HL7::{payload.message_type}",
        aggregate_id=aggregate_id,
        event_data=event_data,
        partition_key=payload.message_type,
    )

    emit_to_outbox(
        db=db,
        event_type=event_type,
        payload=event_data,
        aggregate_type=f"HL7::{payload.message_type}",
        aggregate_id=aggregate_id,
    )

    db.commit()
    logger.info(
        "HL7 message: %s control_id=%s device=%s",
        payload.message_type,
        payload.message_control_id,
        payload.source_device,
    )
    return {"status": "received", "event_type": event_type}


# ── Event Streaming Endpoint ─────────────────────────────────────────────────


@router.post("/events", summary="Event streaming endpoint")
def receive_streaming_event(
    payload: EventStreamingPayload,
    request: Request,
    current_user: LabUser = Depends(require_permission("patients:write")),
    db: Session = Depends(get_db),
):
    event = DataPlatformService.record_event(
        db=db,
        event_type=payload.event_type,
        aggregate_type=payload.aggregate_type,
        aggregate_id=payload.aggregate_id,
        event_data=payload.event_data,
        metadata_=payload.metadata_,
        partition_key=payload.partition_key,
        correlation_id=payload.correlation_id,
        recorded_by=str(current_user.id),
    )

    emit_to_outbox(
        db=db,
        event_type=payload.event_type,
        payload=payload.event_data,
        aggregate_type=payload.aggregate_type,
        aggregate_id=payload.aggregate_id,
    )

    db.commit()
    return {
        "status": "received",
        "event_id": event.id,
        "version": event.version,
    }


# ── CDC Feed Endpoint ─────────────────────────────────────────────────────────


@router.get("/cdc", summary="Change Data Capture feed")
def get_cdc_feed(
    table_name: str | None = Query(None),
    event_type: str | None = Query(None),
    since: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    current_user: LabUser = Depends(require_permission("patients:read")),
    db: Session = Depends(get_db),
):
    query = db.query(StoredEvent).filter(~~StoredEvent.is_deleted)

    if table_name:
        query = query.filter(StoredEvent.aggregate_type == table_name)
    if event_type:
        query = query.filter(StoredEvent.event_type == event_type)
    if since:
        try:
            since_dt = datetime.fromisoformat(since)
            query = query.filter(StoredEvent.recorded_at >= since_dt)
        except ValueError as e:
            raise HTTPException(
                status_code=400, detail="Invalid 'since' format. Use ISO 8601."
            ) from e

    events = query.order_by(StoredEvent.recorded_at.desc()).limit(limit).all()

    return [
        {
            "event_id": e.id,
            "event_type": e.event_type,
            "aggregate_type": e.aggregate_type,
            "aggregate_id": e.aggregate_id,
            "event_data": e.event_data,
            "version": e.version,
            "recorded_at": e.recorded_at.isoformat() if e.recorded_at else None,
        }
        for e in events
    ]


@router.post("/cdc", summary="Record CDC change")
def record_cdc_change(
    payload: CDCChangeRecord,
    current_user: LabUser = Depends(require_permission("patients:write")),
    db: Session = Depends(get_db),
):
    event_type = f"cdc.{payload.table_name}.{payload.operation}"
    event_data = {
        "table_name": payload.table_name,
        "operation": payload.operation,
        "primary_key": payload.primary_key,
        "primary_key_value": payload.primary_key_value,
        "before": payload.before,
        "after": payload.after,
        "transaction_id": payload.transaction_id,
        "change_timestamp": payload.change_timestamp or datetime.now(UTC).isoformat(),
    }

    aggregate_id = f"{payload.table_name}:{payload.primary_key_value}:{payload.transaction_id or datetime.now(UTC).timestamp()}"

    event = DataPlatformService.record_event(
        db=db,
        event_type=event_type,
        aggregate_type=f"CDC::{payload.table_name}",
        aggregate_id=aggregate_id,
        event_data=event_data,
        partition_key=payload.table_name,
        recorded_by=str(current_user.id),
    )

    emit_to_outbox(
        db=db,
        event_type=event_type,
        payload=event_data,
        aggregate_type=f"CDC::{payload.table_name}",
        aggregate_id=aggregate_id,
    )

    db.commit()
    return {
        "status": "recorded",
        "event_id": event.id,
        "event_type": event_type,
    }
