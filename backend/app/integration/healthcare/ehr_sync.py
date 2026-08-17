"""Fail-closed EHR synchronization for immunization events.

This module only queues validated FHIR R4 payloads. Delivery is delegated to the
existing outbox worker and remains disabled until a tenant-scoped connector has
an approved contract and trust reference.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.models.ehr_integration import EHRConnectorConfig, EHRSyncRecord
from app.services.outbox_service import emit_to_outbox


class EHRNotReadyError(RuntimeError):
    """Raised when automatic synchronization is not safe to activate."""


def _safe_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:32]


def build_immunization_fhir(record: Any, lab_id: int) -> dict[str, Any]:
    """Build a minimal, de-identified-safe Immunization resource.

    National identifiers and contact details are intentionally excluded. The
    health number is represented only as a locally scoped identifier reference.
    """
    health_number = str(getattr(record, "health_number", ""))
    patient_ref = f"gula-health-{_safe_hash(health_number)}" if health_number else f"gula-record-{record.id}"
    resource: dict[str, Any] = {
        "resourceType": "Immunization",
        "id": f"gula-immunization-{record.id}",
        "status": "completed",
        "vaccineCode": {"coding": [{"system": "urn:gula:vaccine", "code": record.vaccine_code, "display": record.vaccine}]},
        "patient": {"reference": f"Patient/{patient_ref}"},
        "occurrenceDateTime": record.administration_date.isoformat() if record.administration_date else datetime.now(UTC).isoformat(),
        "primarySource": True,
        "protocolApplied": [{"doseNumberPositiveInt": record.dose_number, "seriesDosesPositiveInt": record.total_doses}],
        "extension": [{"url": "urn:gula:facility-id", "valueInteger": lab_id}],
    }
    for field, path in (("lot_number", "lotNumber"), ("manufacturer", "manufacturer"), ("route", "route"), ("site", "site")):
        value = getattr(record, field, None)
        if value:
            resource[path] = {"text": str(value)} if path in {"route", "site"} else str(value)
    return resource


def assess_readiness(db: Session, lab_id: int) -> dict[str, Any]:
    config = db.query(EHRConnectorConfig).filter(EHRConnectorConfig.lab_id == lab_id, EHRConnectorConfig.connector_name == "ehr").first()
    if not config:
        return {"ready": False, "status": "not_configured", "reason": "No approved EHR connector configuration"}
    parsed = urlparse(config.endpoint or "")
    checks = {
        "approved": bool(config.approved_at and config.approved_by),
        "contract": bool(config.contract_version),
        "endpoint": parsed.scheme in {"https", "http"} and bool(parsed.netloc),
        "trust_material": bool(config.trust_material_ref),
        "runtime_credential": bool(os.getenv("GULA_EHR_BEARER_TOKEN")),
        "protocol": config.protocol == "fhir_r4",
    }
    ready = all(checks.values())
    return {"ready": ready, "status": "ready" if ready else "blocked", "checks": checks, "contract_version": config.contract_version}


def queue_immunization_sync(db: Session, record: Any, lab_id: int) -> EHRSyncRecord:
    readiness = assess_readiness(db, lab_id)
    key = f"immunization:{lab_id}:{record.id}"
    existing = db.query(EHRSyncRecord).filter(EHRSyncRecord.lab_id == lab_id, EHRSyncRecord.idempotency_key == key).first()
    if existing:
        return existing
    if not readiness["ready"]:
        sync = EHRSyncRecord(lab_id=lab_id, event_type="immunization.completed", entity_type="Immunization", entity_id=str(record.id), idempotency_key=key, status="blocked")
        db.add(sync)
        db.flush()
        return sync
    payload = build_immunization_fhir(record, lab_id)
    outbox = emit_to_outbox(db, event_type="ehr.immunization.completed", aggregate_type="immunization", aggregate_id=int(record.id), payload={"lab_id": lab_id, "sync_key": key, "resource": payload})
    sync = EHRSyncRecord(lab_id=lab_id, event_type="immunization.completed", entity_type="Immunization", entity_id=str(record.id), idempotency_key=key, status="queued", outbox_event_id=outbox.id)
    db.add(sync)
    db.flush()
    return sync


def upsert_connector_config(db: Session, lab_id: int, data: dict[str, Any], approved_by: str | None = None) -> EHRConnectorConfig:
    config = db.query(EHRConnectorConfig).filter(EHRConnectorConfig.lab_id == lab_id, EHRConnectorConfig.connector_name == "ehr").first()
    if not config:
        config = EHRConnectorConfig(lab_id=lab_id, connector_name="ehr")
        db.add(config)
    config.protocol = str(data.get("protocol", "fhir_r4"))
    config.endpoint = str(data.get("endpoint", "")).strip()
    config.contract_version = str(data.get("contract_version", "")).strip()
    config.trust_material_ref = str(data.get("trust_material_ref", "")).strip() or None
    config.approved_by = approved_by or config.approved_by
    config.approved_at = datetime.now(UTC) if config.approved_by else config.approved_at
    db.flush()
    readiness = assess_readiness(db, lab_id)
    config.enabled = bool(data.get("auto_activate", True)) and readiness["ready"]
    config.last_health_status = "ready" if config.enabled else readiness["status"]
    config.last_health_checked_at = datetime.now(UTC)
    config.last_error = None if config.enabled else str(readiness.get("reason", "Connector readiness checks incomplete"))
    db.commit()
    db.refresh(config)
    return config


def dispatch_ehr_event(payload: dict[str, Any]) -> None:
    """Deliver one queued FHIR event synchronously from the outbox worker.

    The bearer token is resolved from the runtime secret store and never persisted.
    Any missing readiness condition raises so the outbox retains retry semantics.
    """
    import httpx
    from app.database import SessionLocal

    lab_id = int(payload.get("lab_id", 0))
    sync_key = str(payload.get("sync_key", ""))
    db = SessionLocal()
    try:
        config = db.query(EHRConnectorConfig).filter(EHRConnectorConfig.lab_id == lab_id, EHRConnectorConfig.connector_name == "ehr").first()
        readiness = assess_readiness(db, lab_id)
        if not config or not readiness["ready"]:
            raise EHRNotReadyError("EHR connector is not ready")
        resource = payload.get("resource")
        token = os.getenv("GULA_EHR_BEARER_TOKEN")
        headers = {"Accept": "application/fhir+json", "Content-Type": "application/fhir+json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        response = httpx.post(f"{config.endpoint.rstrip('/')}/{resource['resourceType']}", json=resource, headers=headers, timeout=15.0)
        if response.status_code >= 400:
            raise EHRNotReadyError(f"EHR rejected resource with status {response.status_code}")
        sync = db.query(EHRSyncRecord).filter(EHRSyncRecord.lab_id == lab_id, EHRSyncRecord.idempotency_key == sync_key).first()
        if sync:
            sync.status = "sent"
            sync.external_id = str(response.json().get("id", ""))[:200] or None
            sync.acknowledged_at = datetime.now(UTC)
            db.commit()
    finally:
        db.close()


from shared.events import events as _events
_events.subscribe("ehr.immunization.completed", dispatch_ehr_event)


def mark_acknowledged(db: Session, sync_key: str, lab_id: int, external_id: str | None = None, rejected_reason: str | None = None) -> EHRSyncRecord:
    sync = db.query(EHRSyncRecord).filter(EHRSyncRecord.lab_id == lab_id, EHRSyncRecord.idempotency_key == sync_key).first()
    if not sync:
        raise EHRNotReadyError("Unknown EHR synchronization record")
    sync.status = "rejected" if rejected_reason else "acknowledged"
    sync.external_id = external_id
    sync.rejection_reason = rejected_reason
    sync.acknowledged_at = datetime.now(UTC)
    db.commit()
    db.refresh(sync)
    return sync
