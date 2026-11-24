from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app._compat import UTC
from app.services import audit_service

from .models import CapabilityRecord

MAX_PAYLOAD_BYTES = 64 * 1024
_RESERVED_KEYS = frozenset(
    {"id", "capability", "created_at", "updated_at", "lab_id", "owner_user_id"}
)
_MANAGER_ROLES = frozenset(
    {"master_admin", "ministry_admin", "province_admin", "admin", "lab_admin"}
)


def _validate_payload(payload: Any) -> dict[str, Any]:
    """Fail closed on malformed, reserved or oversized capability payloads."""
    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="payload must be a JSON object")
    if not payload:
        raise HTTPException(status_code=422, detail="payload must not be empty")
    reserved = _RESERVED_KEYS.intersection(payload)
    if reserved:
        raise HTTPException(
            status_code=422,
            detail=f"payload contains reserved field(s): {', '.join(sorted(reserved))}",
        )
    encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    if len(encoded) > MAX_PAYLOAD_BYTES:
        raise HTTPException(status_code=413, detail="payload exceeds 64 KiB limit")
    return dict(payload)


def _serialize(record: CapabilityRecord) -> dict[str, Any]:
    return {
        "id": record.record_id,
        "capability": record.capability,
        "lab_id": record.lab_id,
        "owner_user_id": record.owner_user_id,
        **record.payload,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
    }


def _scoped(
    query,
    capability: str,
    actor: dict[str, Any],
):
    return query.where(
        CapabilityRecord.capability == capability,
        CapabilityRecord.lab_id == int(actor["lab_id"]),
    )


def _assert_writer(actor: dict[str, Any], record: CapabilityRecord) -> None:
    """Institutional lab scope is mandatory; non-managers may write only own rows."""
    if actor.get("role") in _MANAGER_ROLES:
        return
    if record.owner_user_id != int(actor["user_id"]):
        raise HTTPException(status_code=403, detail="record is owned by another user")


def _audit(
    db: Session,
    action: str,
    capability: str,
    actor: dict[str, Any],
    record_id: str,
) -> None:
    audit_service.log_action(
        db,
        action=f"capability_record.{action}",
        resource_type=capability,
        resource_id=None,
        user_id=int(actor["user_id"]),
        user_role=str(actor.get("role") or "unknown")[:50],
        lab_id=int(actor["lab_id"]),
        details=json.dumps(
            {"capability": capability, "record_id": record_id, "operation": action},
            sort_keys=True,
        ),
    )


def list_records(
    db: Session,
    capability: str,
    actor: dict[str, Any],
    skip: int = 0,
    limit: int = 100,
) -> dict[str, Any]:
    total = db.scalar(
        select(func.count())
        .select_from(CapabilityRecord)
        .where(
            CapabilityRecord.capability == capability,
            CapabilityRecord.lab_id == int(actor["lab_id"]),
        ),
    ) or 0
    records = db.scalars(
        _scoped(
            select(CapabilityRecord),
            capability,
            actor,
        )
        .order_by(CapabilityRecord.created_at, CapabilityRecord.record_id)
        .offset(skip)
        .limit(limit),
    ).all()
    return {
        "items": [_serialize(record) for record in records],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


def get_record(
    db: Session,
    capability: str,
    record_id: str,
    actor: dict[str, Any],
) -> dict[str, Any]:
    record = db.get(CapabilityRecord, (capability, record_id))
    if record is None or record.lab_id != int(actor["lab_id"]):
        raise HTTPException(status_code=404, detail="record not found")
    return _serialize(record)


def create_record(
    db: Session,
    capability: str,
    payload: Any,
    actor: dict[str, Any],
) -> dict[str, Any]:
    clean_payload = _validate_payload(payload)
    now = datetime.now(UTC)
    record_id = str(uuid.uuid4())
    record = CapabilityRecord(
        capability=capability,
        record_id=record_id,
        lab_id=int(actor["lab_id"]),
        owner_user_id=int(actor["user_id"]),
        payload=clean_payload,
        created_at=now,
        updated_at=now,
    )
    db.add(record)
    _audit(db, "create", capability, actor, record_id)
    db.commit()
    db.refresh(record)
    return _serialize(record)


def update_record(
    db: Session,
    capability: str,
    record_id: str,
    payload: Any,
    actor: dict[str, Any],
) -> dict[str, Any]:
    clean_payload = _validate_payload(payload)
    record = db.get(CapabilityRecord, (capability, record_id))
    if record is None or record.lab_id != int(actor["lab_id"]):
        raise HTTPException(status_code=404, detail="record not found")
    _assert_writer(actor, record)
    record.payload = clean_payload
    record.updated_at = datetime.now(UTC)
    _audit(db, "update", capability, actor, record_id)
    db.commit()
    db.refresh(record)
    return _serialize(record)


def delete_record(
    db: Session,
    capability: str,
    record_id: str,
    actor: dict[str, Any],
) -> dict[str, Any]:
    record = db.get(CapabilityRecord, (capability, record_id))
    if record is None or record.lab_id != int(actor["lab_id"]):
        raise HTTPException(status_code=404, detail="record not found")
    _assert_writer(actor, record)
    _audit(db, "delete", capability, actor, record_id)
    db.delete(record)
    db.commit()
    return {"success": True, "id": record_id, "capability": capability}
