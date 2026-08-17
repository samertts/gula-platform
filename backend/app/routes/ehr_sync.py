from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.integration.healthcare.ehr_sync import assess_readiness, mark_acknowledged, upsert_connector_config
from app.services.outbox_service import outbox_metrics, replay_outbox_event
from app.services.cache_service import cache_key, delete as cache_delete, get_or_set as cache_get_or_set
from app.models.ehr_integration import EHRConnectorConfig, EHRSyncRecord
from app.security.dependencies import require_permission

router = APIRouter(prefix="/integrations/ehr", tags=["ehr-integration"])


class EHRConnectorRequest(BaseModel):
    endpoint: str = Field(min_length=1, max_length=500)
    protocol: str = Field(default="fhir_r4", pattern="^fhir_r4$")
    contract_version: str = Field(min_length=1, max_length=80)
    trust_material_ref: str = Field(min_length=1, max_length=200)
    auto_activate: bool = True


class EHRAcknowledgementRequest(BaseModel):
    external_id: str | None = Field(default=None, max_length=200)
    rejected_reason: str | None = Field(default=None, max_length=2000)


def _lab_id(user: Any) -> int:
    value = getattr(user, "lab_id", None)
    if not isinstance(value, int) or value <= 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Facility context is required")
    return value


def _config_dict(config: EHRConnectorConfig, readiness: dict[str, Any]) -> dict[str, Any]:
    return {
        "connector": "ehr",
        "protocol": config.protocol,
        "contract_version": config.contract_version,
        "enabled": config.enabled,
        "health_status": config.last_health_status,
        "readiness": readiness,
        "last_health_checked_at": config.last_health_checked_at,
        "last_error": config.last_error,
    }


@router.get("/outbox/metrics")
def ehr_outbox_metrics(
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_permission("integration:read")),
) -> dict[str, Any]:
    lab_id = _lab_id(current_user)
    key = cache_key("outbox_metrics", lab_id, version="ehr")
    return cache_get_or_set(key, lambda: outbox_metrics(db, event_type_prefix="ehr.", lab_id=lab_id), ttl_seconds=15)


@router.post("/outbox/{event_id}/replay")
def replay_ehr_outbox(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_permission("integration:manage")),
) -> dict[str, Any]:
    try:
        lab_id = _lab_id(current_user)
        event = replay_outbox_event(db, event_id, str(getattr(current_user, "id", "")), lab_id=lab_id)
        cache_delete(cache_key("outbox_metrics", lab_id, version="ehr"))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Outbox event not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return {"id": event.id, "status": event.status, "attempts": event.attempts, "replayed_by": event.replayed_by}


@router.get("/status")
def ehr_status(
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_permission("integration:read")),
) -> dict[str, Any]:
    lab_id = _lab_id(current_user)
    config = db.query(EHRConnectorConfig).filter(EHRConnectorConfig.lab_id == lab_id, EHRConnectorConfig.connector_name == "ehr").first()
    if not config:
        return {"connector": "ehr", "enabled": False, "health_status": "not_configured", "readiness": assess_readiness(db, lab_id)}
    return _config_dict(config, assess_readiness(db, lab_id))


@router.put("/config")
def configure_ehr(
    body: EHRConnectorRequest,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_permission("integration:manage")),
) -> dict[str, Any]:
    lab_id = _lab_id(current_user)
    config = upsert_connector_config(db, lab_id, body.model_dump(), approved_by=str(getattr(current_user, "id", "")))
    return _config_dict(config, assess_readiness(db, lab_id))


@router.post("/sync/{sync_key}/ack")
def acknowledge_ehr_sync(
    sync_key: str,
    body: EHRAcknowledgementRequest,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_permission("integration:manage")),
) -> dict[str, Any]:
    try:
        sync = mark_acknowledged(db, sync_key, _lab_id(current_user), body.external_id, body.rejected_reason)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Synchronization record not found") from exc
    return {"id": sync.id, "status": sync.status, "external_id": sync.external_id, "acknowledged_at": sync.acknowledged_at}


@router.get("/sync")
def list_ehr_sync(
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_permission("integration:read")),
) -> list[dict[str, Any]]:
    rows = db.query(EHRSyncRecord).filter(EHRSyncRecord.lab_id == _lab_id(current_user)).order_by(EHRSyncRecord.created_at.desc()).limit(100).all()
    return [{"id": row.id, "event_type": row.event_type, "entity_type": row.entity_type, "status": row.status, "created_at": row.created_at, "acknowledged_at": row.acknowledged_at} for row in rows]
