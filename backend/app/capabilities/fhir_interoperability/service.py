"""Application service for GULA's tenant-scoped FHIR resource boundary."""
from __future__ import annotations

from uuid import uuid4

from sqlalchemy.orm import Session

from .models import FHIRResourceRecord, utc_now
from .schemas import FHIRResourceInput


def _subject_reference(resource: dict) -> str | None:
    for key in ("subject", "patient"):
        value = resource.get(key)
        if isinstance(value, dict) and isinstance(value.get("reference"), str):
            return value["reference"]
    return None


def _profile(resource: dict) -> str | None:
    meta = resource.get("meta")
    if not isinstance(meta, dict):
        return None
    profiles = meta.get("profile")
    if isinstance(profiles, list) and profiles and isinstance(profiles[0], str):
        return profiles[0][:255]
    return None


def _response(record: FHIRResourceRecord) -> dict:
    resource = dict(record.resource or {})
    resource.setdefault("resourceType", record.resource_type)
    resource.setdefault("id", record.resource_id)
    meta = resource.setdefault("meta", {})
    if isinstance(meta, dict):
        meta.setdefault("versionId", str(record.version))
        meta.setdefault("lastUpdated", record.updated_at.isoformat())
    return {
        "resourceType": record.resource_type,
        "id": record.resource_id,
        "meta": resource.get("meta"),
        "resource": resource,
        "version": record.version,
        "lastUpdated": record.updated_at.isoformat(),
    }


def create_resource(
    db: Session,
    *,
    lab_id: int,
    created_by: int,
    payload: FHIRResourceInput,
    source_system: str | None = None,
) -> dict:
    resource = payload.model_dump(exclude_none=True)
    resource_id = payload.id or uuid4().hex
    resource["id"] = resource_id
    now = utc_now()
    record = FHIRResourceRecord(
        lab_id=lab_id,
        resource_type=payload.resourceType,
        resource_id=resource_id,
        version=1,
        profile=_profile(resource),
        subject_reference=_subject_reference(resource),
        resource=resource,
        source_system=source_system[:120] if source_system else None,
        created_by=created_by,
        created_at=now,
        updated_at=now,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _response(record)


def get_resource(
    db: Session,
    *,
    lab_id: int,
    resource_type: str,
    resource_id: str,
) -> dict | None:
    record = (
        db.query(FHIRResourceRecord)
        .filter(
            FHIRResourceRecord.lab_id == lab_id,
            FHIRResourceRecord.resource_type == resource_type,
            FHIRResourceRecord.resource_id == resource_id,
        )
        .first()
    )
    return _response(record) if record else None


def search_resources(
    db: Session,
    *,
    lab_id: int,
    resource_type: str,
    subject: str | None,
    patient: str | None,
    limit: int,
    offset: int,
) -> tuple[int, list[dict]]:
    query = db.query(FHIRResourceRecord).filter(
        FHIRResourceRecord.lab_id == lab_id,
        FHIRResourceRecord.resource_type == resource_type,
    )
    reference = subject or patient
    if reference:
        query = query.filter(FHIRResourceRecord.subject_reference == reference)
    total = query.count()
    records = (
        query.order_by(FHIRResourceRecord.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return total, [_response(record) for record in records]
