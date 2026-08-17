from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app._compat import UTC
from app.domain.exceptions import ConflictError, NotFoundError
from app.national.domain.encounter import Encounter
from app.national.services.encounter_service import transition_flow_state
from app.national.sync_models import (
    NationalClinicalNotificationModel,
    NationalDeviceSessionModel,
    NationalRecordLockModel,
    NationalSyncConflictModel,
    NationalSyncOperationModel,
    NationalSyncOutboxModel,
)
from app.services.audit_service import log_action


_ALLOWED_OFFLINE_OPERATIONS = {
    "encounter.arrival",
    "encounter.triage",
    "encounter.transition",
    "encounter.vital_sign",
    "encounter.note",
}
_CRITICAL_PRIORITIES = {"critical", "stat"}
_SEVERITY_ORDER = {"P0_CRITICAL": 0, "P1_URGENT": 1, "P2_HIGH": 2, "P3_ROUTINE": 3}


def now_utc() -> datetime:
    return datetime.now(UTC)


def payload_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _severity(operation: dict[str, Any], conflict_type: str) -> str:
    priority = str(operation.get("priority", "routine")).lower()
    payload = operation.get("payload") or {}
    if priority in _CRITICAL_PRIORITIES or bool(payload.get("is_emergency")):
        return "P0_CRITICAL"
    if priority in {"urgent", "asap"}:
        return "P1_URGENT"
    if conflict_type in {"identity", "clinical_version", "clinical_state"}:
        return "P2_HIGH"
    return "P3_ROUTINE"


def _get_scope_user_id(current_user: Any) -> str:
    return str(getattr(current_user, "id", ""))


def _get_lab_id(current_user: Any) -> int:
    lab_id = getattr(current_user, "lab_id", None)
    if lab_id is None:
        raise ConflictError("Authenticated user has no institutional scope")
    return int(lab_id)


def create_device_session(
    db: Session,
    *,
    current_user: Any,
    device_id: str,
    hospital_id: int,
    expires_minutes: int = 480,
) -> NationalDeviceSessionModel:
    lab_id = _get_lab_id(current_user)
    user_id = _get_scope_user_id(current_user)
    if not device_id.strip():
        raise ConflictError("device_id is required")
    existing = db.query(NationalDeviceSessionModel).filter(
        NationalDeviceSessionModel.device_id == device_id,
    ).first()
    session_hash = hashlib.sha256(secrets.token_urlsafe(32).encode()).hexdigest()
    if existing:
        existing.lab_id = lab_id
        existing.hospital_id = hospital_id
        existing.user_id = user_id
        existing.session_hash = session_hash
        existing.expires_at = now_utc() + timedelta(minutes=expires_minutes)
        existing.revoked = False
        existing.updated_at = now_utc()
        db.flush()
        return existing
    session = NationalDeviceSessionModel(
        device_id=device_id,
        lab_id=lab_id,
        hospital_id=hospital_id,
        user_id=user_id,
        session_hash=session_hash,
        expires_at=now_utc() + timedelta(minutes=expires_minutes),
        allowed_operation_types=sorted(_ALLOWED_OFFLINE_OPERATIONS),
    )
    db.add(session)
    db.flush()
    log_action(db, "sync.device_session.create", session.id, lab_id, user_id, {
        "device_id": device_id,
        "hospital_id": hospital_id,
        "expires_at": session.expires_at.isoformat(),
    })
    return session


def _assert_device_scope(db: Session, current_user: Any, device_id: str, hospital_id: int | None = None) -> NationalDeviceSessionModel:
    lab_id = _get_lab_id(current_user)
    session = db.query(NationalDeviceSessionModel).filter(
        NationalDeviceSessionModel.device_id == device_id,
        NationalDeviceSessionModel.lab_id == lab_id,
        NationalDeviceSessionModel.revoked.is_(False),
        NationalDeviceSessionModel.expires_at > now_utc(),
    ).first()
    if session is None:
        raise ConflictError("Device session is not active or outside institutional scope")
    if hospital_id is not None and session.hospital_id != hospital_id:
        raise ConflictError("Device is not registered for this hospital")
    return session


def create_outbox_event(
    db: Session,
    *,
    event_type: str,
    aggregate_type: str,
    aggregate_id: str,
    lab_id: int,
    hospital_id: int | None,
    payload: dict[str, Any],
) -> NationalSyncOutboxModel:
    event_id = secrets.token_hex(24)
    event = NationalSyncOutboxModel(
        event_id=event_id,
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        lab_id=lab_id,
        hospital_id=hospital_id,
        payload=payload,
    )
    db.add(event)
    db.flush()
    return event


def create_conflict_notification(
    db: Session,
    *,
    conflict: NationalSyncConflictModel,
    event: NationalSyncOutboxModel,
    recipient_user_id: str,
) -> NationalClinicalNotificationModel | None:
    dedupe_key = f"{conflict.id}:{conflict.severity}:{conflict.server_version or 0}:{recipient_user_id}"
    existing = db.query(NationalClinicalNotificationModel).filter(
        NationalClinicalNotificationModel.dedupe_key == dedupe_key,
    ).first()
    if existing:
        return existing
    notification = NationalClinicalNotificationModel(
        event_id=event.event_id,
        conflict_id=conflict.id,
        recipient_user_id=str(recipient_user_id),
        lab_id=conflict.lab_id,
        hospital_id=conflict.hospital_id,
        severity=conflict.severity,
        title="تعارض سريري يتطلب تدخلاً عاجلاً" if conflict.severity == "P0_CRITICAL" else "تعارض سريري يحتاج مراجعة",
        message="تم إيقاف تعديل متعارض ولم تُستبدل بيانات السجل. افتح مركز التعارضات للمراجعة.",
        resource_type=conflict.entity_type,
        resource_id=conflict.entity_id,
        dedupe_key=dedupe_key,
        status="delivered",
        expires_at=now_utc() + timedelta(hours=24),
    )
    db.add(notification)
    db.flush()
    return notification


def ingest_operation(
    db: Session,
    *,
    current_user: Any,
    device_id: str,
    operation: dict[str, Any],
) -> dict[str, Any]:
    lab_id = _get_lab_id(current_user)
    user_id = _get_scope_user_id(current_user)
    operation_id = str(operation.get("operation_id", "")).strip()
    idempotency_key = str(operation.get("idempotency_key", "")).strip()
    if not operation_id or not idempotency_key:
        raise ConflictError("operation_id and idempotency_key are required")
    operation_type = str(operation.get("operation_type", "")).strip()
    if operation_type not in _ALLOWED_OFFLINE_OPERATIONS:
        raise ConflictError("Operation type is not allowed in degraded mode")
    payload = operation.get("payload") or {}
    hospital_id = payload.get("hospital_id")
    if hospital_id is not None:
        hospital_id = int(hospital_id)
    _assert_device_scope(db, current_user, device_id, hospital_id)
    digest = payload_hash(payload)

    existing = db.query(NationalSyncOperationModel).filter(
        NationalSyncOperationModel.operation_id == operation_id,
    ).first()
    if existing:
        if existing.payload_hash != digest or existing.idempotency_key != idempotency_key:
            raise ConflictError("IDEMPOTENCY_KEY_REUSE: operation payload differs")
        return {"status": "duplicate", "operation_id": operation_id, "server_id": existing.entity_id, "server_version": existing.base_version}

    scoped_duplicate = db.query(NationalSyncOperationModel).filter(
        NationalSyncOperationModel.lab_id == lab_id,
        NationalSyncOperationModel.device_id == device_id,
        NationalSyncOperationModel.idempotency_key == idempotency_key,
    ).first()
    if scoped_duplicate:
        if scoped_duplicate.payload_hash != digest:
            raise ConflictError("IDEMPOTENCY_KEY_REUSE: scoped payload differs")
        return {"status": "duplicate", "operation_id": scoped_duplicate.operation_id, "server_id": scoped_duplicate.entity_id, "server_version": scoped_duplicate.base_version}

    record = NationalSyncOperationModel(
        operation_id=operation_id,
        idempotency_key=idempotency_key,
        device_id=device_id,
        user_id=user_id,
        lab_id=lab_id,
        hospital_id=hospital_id,
        client_sequence=operation.get("client_sequence"),
        operation_type=operation_type,
        entity_type=str(operation.get("entity_type", "Encounter")),
        entity_id=operation.get("entity_id") or operation.get("entity_local_id"),
        base_version=operation.get("base_version"),
        priority=str(operation.get("priority", "routine")),
        payload=payload,
        payload_hash=digest,
        signature=operation.get("signature"),
        status="processing",
        attempt_count=1,
    )
    db.add(record)
    db.flush()

    try:
        if operation_type in {"encounter.transition", "encounter.triage"}:
            entity_id = str(operation.get("entity_server_id") or operation.get("entity_id") or "")
            target_state = str(payload.get("target_state") or ("triaged" if operation_type == "encounter.triage" else ""))
            if not entity_id or not target_state:
                raise ConflictError("Encounter transition requires entity_id and target_state")
            expected = operation.get("base_version")
            updated = transition_flow_state(
                db,
                entity_id,
                target_state,
                int(user_id),
                expected_version=int(expected) if expected is not None else None,
                lab_id=lab_id,
            )
            record.entity_id = updated.id
            record.base_version = updated.version
            record.status = "accepted"
            record.accepted_at = now_utc()
            event = create_outbox_event(
                db,
                event_type="clinical.encounter.updated",
                aggregate_type="Encounter",
                aggregate_id=updated.id,
                lab_id=lab_id,
                hospital_id=hospital_id,
                payload={"operation_id": operation_id, "version": updated.version, "flow_state": updated.flow_state},
            )
            db.flush()
            return {"status": "accepted", "operation_id": operation_id, "server_id": updated.id, "server_version": updated.version, "event_id": event.event_id}
        record.status = "accepted"
        record.accepted_at = now_utc()
        event = create_outbox_event(
            db,
            event_type="sync.operation.accepted",
            aggregate_type=record.entity_type,
            aggregate_id=record.entity_id or record.id,
            lab_id=lab_id,
            hospital_id=hospital_id,
            payload={"operation_id": operation_id, "operation_type": operation_type},
        )
        db.flush()
        return {"status": "accepted", "operation_id": operation_id, "server_id": record.entity_id, "event_id": event.event_id}
    except ConflictError as exc:
        record.status = "conflict"
        record.rejection_code = "STALE_VERSION" if "version" in str(exc).lower() else "CLINICAL_CONFLICT"
        conflict = NationalSyncConflictModel(
            operation_id=operation_id,
            lab_id=lab_id,
            hospital_id=hospital_id,
            entity_type=record.entity_type,
            entity_id=record.entity_id,
            conflict_type="clinical_version" if record.rejection_code == "STALE_VERSION" else "clinical_state",
            severity=_severity(operation, "clinical_version"),
            status="pending",
            base_version=record.base_version,
            local_payload=payload,
            server_snapshot=None,
        )
        db.add(conflict)
        db.flush()
        event = create_outbox_event(
            db,
            event_type="clinical.conflict.created",
            aggregate_type="SyncConflict",
            aggregate_id=conflict.id,
            lab_id=lab_id,
            hospital_id=hospital_id,
            payload={"conflict_id": conflict.id, "severity": conflict.severity, "resource_type": conflict.entity_type, "resource_id": conflict.entity_id},
        )
        create_conflict_notification(db, conflict=conflict, event=event, recipient_user_id=user_id)
        log_action(db, "sync.conflict.created", conflict.id, lab_id, user_id, {"operation_id": operation_id, "severity": conflict.severity, "reason": str(exc)})
        db.flush()
        return {"status": "conflict", "operation_id": operation_id, "conflict_id": conflict.id, "reason_code": record.rejection_code, "next_action": "review_required"}


def list_conflicts(db: Session, current_user: Any, *, hospital_id: int | None = None, status: str | None = "pending", limit: int = 50) -> list[NationalSyncConflictModel]:
    query = db.query(NationalSyncConflictModel).filter(NationalSyncConflictModel.lab_id == _get_lab_id(current_user))
    if hospital_id is not None:
        query = query.filter(NationalSyncConflictModel.hospital_id == hospital_id)
    if status:
        query = query.filter(NationalSyncConflictModel.status == status)
    return query.order_by(
        NationalSyncConflictModel.severity.asc(),
        NationalSyncConflictModel.created_at.asc(),
    ).limit(limit).all()


def resolve_conflict(db: Session, current_user: Any, conflict_id: str, *, decision: str, reason_code: str, reason_note: str, expected_version: int | None) -> NationalSyncConflictModel:
    lab_id = _get_lab_id(current_user)
    conflict = db.query(NationalSyncConflictModel).filter(
        NationalSyncConflictModel.id == conflict_id,
        NationalSyncConflictModel.lab_id == lab_id,
    ).first()
    if conflict is None:
        raise NotFoundError("Conflict not found")
    if conflict.status in {"resolved", "rejected"}:
        raise ConflictError("Conflict is already closed")
    if expected_version is not None and conflict.server_version is not None and expected_version != conflict.server_version:
        raise ConflictError("Conflict changed; reload before resolving")
    if decision not in {"accept_server", "accept_local_proposal", "reject_operation"}:
        raise ConflictError("Unsupported conflict decision")
    conflict.status = "resolved" if decision != "reject_operation" else "rejected"
    conflict.resolution = decision
    conflict.resolution_reason = f"{reason_code}: {reason_note}".strip()
    conflict.resolved_by = _get_scope_user_id(current_user)
    conflict.resolved_at = now_utc()
    conflict.updated_at = now_utc()
    log_action(db, "sync.conflict.resolved", conflict.id, lab_id, _get_scope_user_id(current_user), {"decision": decision, "reason_code": reason_code})
    db.flush()
    return conflict


def list_notifications(db: Session, current_user: Any, *, status: str | None = "unread", limit: int = 50) -> list[NationalClinicalNotificationModel]:
    query = db.query(NationalClinicalNotificationModel).filter(
        NationalClinicalNotificationModel.recipient_user_id == _get_scope_user_id(current_user),
        NationalClinicalNotificationModel.lab_id == _get_lab_id(current_user),
    )
    if status:
        query = query.filter(NationalClinicalNotificationModel.status == status)
    return query.order_by(NationalClinicalNotificationModel.severity.asc(), NationalClinicalNotificationModel.created_at.desc()).limit(limit).all()


def acknowledge_notification(db: Session, current_user: Any, notification_id: str) -> NationalClinicalNotificationModel:
    notification = db.query(NationalClinicalNotificationModel).filter(
        NationalClinicalNotificationModel.id == notification_id,
        NationalClinicalNotificationModel.recipient_user_id == _get_scope_user_id(current_user),
        NationalClinicalNotificationModel.lab_id == _get_lab_id(current_user),
    ).first()
    if notification is None:
        raise NotFoundError("Notification not found")
    if notification.acknowledged_at is None:
        notification.acknowledged_at = now_utc()
        notification.acknowledged_by = _get_scope_user_id(current_user)
        notification.status = "acknowledged"
        notification.updated_at = now_utc()
        log_action(db, "clinical.notification.acknowledged", notification.id, notification.lab_id, _get_scope_user_id(current_user), {"conflict_id": notification.conflict_id})
        db.flush()
    return notification


def acquire_record_lock(db: Session, current_user: Any, *, resource_type: str, resource_id: str, device_id: str, hospital_id: int | None, minutes: int = 3) -> tuple[NationalRecordLockModel, str]:
    lab_id = _get_lab_id(current_user)
    now = now_utc()
    active = db.query(NationalRecordLockModel).filter(
        NationalRecordLockModel.resource_type == resource_type,
        NationalRecordLockModel.resource_id == resource_id,
        NationalRecordLockModel.lab_id == lab_id,
        NationalRecordLockModel.status == "active",
        NationalRecordLockModel.expires_at > now,
    ).first()
    if active and active.owner_user_id != _get_scope_user_id(current_user):
        raise ConflictError("Record is locked by another active editor")
    token = secrets.token_urlsafe(32)
    record = active or NationalRecordLockModel(
        resource_type=resource_type,
        resource_id=resource_id,
        lab_id=lab_id,
        hospital_id=hospital_id,
        owner_user_id=_get_scope_user_id(current_user),
        owner_device_id=device_id,
        lock_token_hash=hashlib.sha256(token.encode()).hexdigest(),
        status="active",
    )
    record.owner_user_id = _get_scope_user_id(current_user)
    record.owner_device_id = device_id
    record.expires_at = now + timedelta(minutes=max(1, min(minutes, 5)))
    record.last_heartbeat_at = now
    record.released_at = None
    record.status = "active"
    db.add(record)
    db.flush()
    return record, token


def heartbeat_record_lock(db: Session, current_user: Any, lock: NationalRecordLockModel, token: str, minutes: int = 3) -> NationalRecordLockModel:
    if lock.owner_user_id != _get_scope_user_id(current_user) or lock.lock_token_hash != hashlib.sha256(token.encode()).hexdigest() or lock.status != "active":
        raise ConflictError("Lock token is invalid")
    if lock.expires_at <= now_utc():
        lock.status = "expired"
        db.flush()
        raise ConflictError("Lock expired")
    lock.last_heartbeat_at = now_utc()
    lock.expires_at = now_utc() + timedelta(minutes=max(1, min(minutes, 5)))
    db.flush()
    return lock
