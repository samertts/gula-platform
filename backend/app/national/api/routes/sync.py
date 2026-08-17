from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.domain.exceptions import ConflictError, NotFoundError
from app.models.lab_user import LabUser
from app.security.dependencies import get_current_user, require_permission
from app.services.audit_service import log_action
from app.services.sync_conflict_service import (
    _assert_device_scope,
    _get_lab_id,
    acquire_record_lock,
    acknowledge_notification,
    create_device_session,
    heartbeat_record_lock,
    ingest_operation,
    list_conflicts,
    list_notifications,
    now_utc,
    resolve_conflict,
)
from app.tasks.queue import task_queue
from app.tasks.schema import TaskPayload
from app.national.sync_models import (
    NationalClinicalNotificationModel,
    NationalRecordLockModel,
    NationalSyncConflictModel,
    NationalSyncOperationModel,
    NationalSyncOutboxModel,
)

router = APIRouter(prefix="/sync", tags=["Offline Sync and Clinical Conflicts"])


class DeviceSessionRequest(BaseModel):
    hospital_id: int = Field(gt=0)
    device_id: str = Field(min_length=2, max_length=128)


class SyncBatchRequest(BaseModel):
    device_id: str = Field(min_length=2, max_length=128)
    operations: list[dict[str, Any]] = Field(min_length=1, max_length=200)


class NotificationEscalationRequest(BaseModel):
    recipient_user_id: int | None = Field(default=None, gt=0)


class ConflictResolutionRequest(BaseModel):
    decision: str = Field(min_length=3, max_length=64)
    reason_code: str = Field(min_length=3, max_length=64)
    reason_note: str = Field(min_length=3, max_length=2000)
    expected_server_version: int | None = Field(default=None, ge=1)


class LockRequest(BaseModel):
    resource_type: str = Field(min_length=2, max_length=64)
    resource_id: str = Field(min_length=1, max_length=128)
    device_id: str = Field(min_length=2, max_length=128)
    hospital_id: int | None = Field(default=None, gt=0)


class LockHeartbeatRequest(BaseModel):
    lock_token: str = Field(min_length=10, max_length=256)


def _error(exc: Exception) -> HTTPException:
    text = str(exc)
    if "not found" in text.lower():
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=text)
    if "locked" in text.lower() or "conflict" in text.lower() or "idempotency" in text.lower() or "version" in text.lower():
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=text)
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=text)


def _select_escalation_recipient(db: Session, current_user: LabUser, requested_user_id: int | None = None) -> str:
    lab_id = _get_lab_id(current_user)
    if requested_user_id is not None:
        recipient = db.query(LabUser).filter(
            LabUser.id == requested_user_id,
            LabUser.lab_id == lab_id,
            LabUser.is_active.is_(True),
        ).first()
        if recipient is None:
            raise ConflictError("Escalation recipient is not active or outside institutional scope")
        return str(recipient.id)
    for role in ("admin", "lab_admin", "supervisor", "department_head", "doctor"):
        recipient = db.query(LabUser).filter(
            LabUser.lab_id == lab_id,
            LabUser.role == role,
            LabUser.is_active.is_(True),
            LabUser.id != current_user.id,
        ).order_by(LabUser.id.asc()).first()
        if recipient is not None:
            return str(recipient.id)
    raise ConflictError("No active escalation recipient is configured for this institution")


def _conflict_view(item: NationalSyncConflictModel) -> dict[str, Any]:
    return {
        "conflict_id": item.id,
        "operation_id": item.operation_id,
        "lab_id": item.lab_id,
        "hospital_id": item.hospital_id,
        "entity_type": item.entity_type,
        "entity_id": item.entity_id,
        "conflict_type": item.conflict_type,
        "severity": item.severity,
        "status": item.status,
        "base_version": item.base_version,
        "server_version": item.server_version,
        "local_payload": item.local_payload,
        "server_snapshot": item.server_snapshot,
        "resolution": item.resolution,
        "resolution_reason": item.resolution_reason,
        "resolved_by": item.resolved_by,
        "resolved_at": item.resolved_at,
        "created_at": item.created_at,
    }


def _notification_view(item: NationalClinicalNotificationModel) -> dict[str, Any]:
    return {
        "notification_id": item.id,
        "event_id": item.event_id,
        "conflict_id": item.conflict_id,
        "severity": item.severity,
        "title": item.title,
        "message": item.message,
        "resource_type": item.resource_type,
        "resource_id": item.resource_id,
        "status": item.status,
        "requires_ack": item.acknowledged_at is None,
        "acknowledged_at": item.acknowledged_at,
        "escalated_at": item.escalated_at,
        "created_at": item.created_at,
        "expires_at": item.expires_at,
    }


@router.post(
    "/devices/session",
    dependencies=[Depends(require_permission("hospital:flow:write"))],
)
def register_device_session(
    payload: DeviceSessionRequest,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    try:
        session, session_token = create_device_session(db, current_user=current_user, device_id=payload.device_id, hospital_id=payload.hospital_id)
        db.commit()
        return {
            "device_session_token": session_token,
            "device_id": session.device_id,
            "hospital_id": session.hospital_id,
            "lab_id": session.lab_id,
            "policy_version": session.policy_version,
            "allowed_operation_types": session.allowed_operation_types,
            "expires_at": session.expires_at,
        }
    except Exception as exc:
        db.rollback()
        raise _error(exc) from exc


@router.get(
    "/status",
    dependencies=[Depends(require_permission("hospital:flow:read"))],
)
def sync_status(
    device_id: str,
    x_device_session: str = Header(min_length=20, alias="X-Device-Session"),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    _assert_device_scope(db, current_user, device_id, x_device_session)
    lab_id = _get_lab_id(current_user)
    pending = db.query(NationalSyncOperationModel).filter(
        NationalSyncOperationModel.lab_id == lab_id,
        NationalSyncOperationModel.device_id == device_id,
        NationalSyncOperationModel.status.in_(["queued", "processing"]),
    ).count()
    conflicts = db.query(NationalSyncConflictModel).filter(
        NationalSyncConflictModel.lab_id == lab_id,
        NationalSyncConflictModel.status == "pending",
    ).count()
    critical = db.query(NationalClinicalNotificationModel).filter(
        NationalClinicalNotificationModel.lab_id == lab_id,
        NationalClinicalNotificationModel.recipient_user_id == str(current_user.id),
        NationalClinicalNotificationModel.status.in_(["delivered", "escalated"]),
        NationalClinicalNotificationModel.severity == "P0_CRITICAL",
    ).count()
    return {
        "device_id": device_id,
        "server_time": now_utc(),
        "pending_count": pending,
        "conflict_count": conflicts,
        "critical_unacknowledged_count": critical,
    }


@router.post(
    "/operations:batch",
    dependencies=[Depends(require_permission("hospital:flow:write"))],
)
def ingest_batch(
    payload: SyncBatchRequest,
    background_tasks: BackgroundTasks,
    x_device_session: str = Header(min_length=20, alias="X-Device-Session"),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    results: list[dict[str, Any]] = []
    accepted = duplicate = conflict = rejected = 0
    try:
        _assert_device_scope(db, current_user, payload.device_id, x_device_session)
        for operation in payload.operations:
            try:
                result = ingest_operation(db, current_user=current_user, device_id=payload.device_id, device_token=x_device_session, operation=operation)
            except Exception as exc:
                result = {
                    "status": "rejected",
                    "operation_id": operation.get("operation_id"),
                    "reason_code": "VALIDATION_FAILED",
                    "message": str(exc),
                }
            results.append(result)
            if result.get("status") == "accepted":
                accepted += 1
            elif result.get("status") == "duplicate":
                duplicate += 1
            elif result.get("status") == "conflict":
                conflict += 1
            else:
                rejected += 1
        db.commit()
        background_tasks.add_task(
            task_queue.enqueue,
            TaskPayload(type="sync_outbox_dispatch", payload={"limit": 100}),
        )
        return {
            "accepted_count": accepted,
            "duplicate_count": duplicate,
            "conflict_count": conflict,
            "rejected_count": rejected,
            "results": results,
        }
    except Exception as exc:
        db.rollback()
        raise _error(exc) from exc


@router.get(
    "/changes",
    dependencies=[Depends(require_permission("hospital:flow:read"))],
)
def changes(
    after: datetime | None = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    query = db.query(NationalSyncOutboxModel).filter(NationalSyncOutboxModel.lab_id == _get_lab_id(current_user))
    if after:
        query = query.filter(NationalSyncOutboxModel.created_at > after)
    items = query.order_by(NationalSyncOutboxModel.created_at.asc()).limit(limit).all()
    return {
        "changes": [
            {"event_id": item.event_id, "event_type": item.event_type, "aggregate_type": item.aggregate_type, "aggregate_id": item.aggregate_id, "payload": item.payload, "created_at": item.created_at}
            for item in items
        ],
    }


@router.get(
    "/conflicts",
    dependencies=[Depends(require_permission("hospital:flow:read"))],
)
def conflicts(
    hospital_id: int | None = None,
    conflict_status: str | None = Query("pending", alias="status"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    return [_conflict_view(item) for item in list_conflicts(db, current_user, hospital_id=hospital_id, status=conflict_status, limit=limit)]


@router.get(
    "/conflicts/{conflict_id}",
    dependencies=[Depends(require_permission("hospital:flow:read"))],
)
def conflict_detail(
    conflict_id: str,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    item = db.query(NationalSyncConflictModel).filter(
        NationalSyncConflictModel.id == conflict_id,
        NationalSyncConflictModel.lab_id == _get_lab_id(current_user),
    ).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Conflict not found")
    return _conflict_view(item)


@router.post(
    "/conflicts/{conflict_id}:resolve",
    dependencies=[Depends(require_permission("hospital:flow:write"))],
)
def conflict_resolve(
    conflict_id: str,
    payload: ConflictResolutionRequest,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    try:
        item = resolve_conflict(db, current_user, conflict_id, decision=payload.decision, reason_code=payload.reason_code, reason_note=payload.reason_note, expected_version=payload.expected_server_version)
        db.commit()
        return _conflict_view(item)
    except Exception as exc:
        db.rollback()
        raise _error(exc) from exc


@router.get(
    "/notifications",
    dependencies=[Depends(require_permission("hospital:flow:read"))],
)
def notifications(
    notification_status: str | None = Query("unread", alias="status"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    items = list_notifications(db, current_user, status=notification_status, limit=limit)
    return {"items": [_notification_view(item) for item in items], "unread_count": len(items)}


@router.post(
    "/notifications/{notification_id}:acknowledge",
    dependencies=[Depends(require_permission("hospital:flow:write"))],
)
def notification_ack(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    try:
        item = acknowledge_notification(db, current_user, notification_id)
        db.commit()
        return _notification_view(item)
    except Exception as exc:
        db.rollback()
        raise _error(exc) from exc


@router.post(
    "/notifications/{notification_id}:escalate",
    dependencies=[Depends(require_permission("hospital:flow:write"))],
)
def notification_escalate(
    notification_id: str,
    payload: NotificationEscalationRequest | None = None,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    item = db.query(NationalClinicalNotificationModel).filter(
        NationalClinicalNotificationModel.id == notification_id,
        NationalClinicalNotificationModel.lab_id == _get_lab_id(current_user),
    ).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    item.status = "escalated"
    item.escalated_at = now_utc()
    item.escalated_to = _select_escalation_recipient(db, current_user, payload.recipient_user_id if payload else None)
    item.updated_at = now_utc()
    log_action(
        db,
        "clinical.notification.escalated",
        resource_type="clinical_notification",
        resource_id=None,
        user_id=current_user.id,
        lab_id=item.lab_id,
        details={"notification_id": item.id, "escalated_to": item.escalated_to, "severity": item.severity},
    )
    db.commit()
    return _notification_view(item)


@router.post(
    "/records/{resource_type}/{resource_id}:lock",
    dependencies=[Depends(require_permission("hospital:flow:write"))],
)
def record_lock(
    resource_type: str,
    resource_id: str,
    payload: LockRequest,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    try:
        lock, token = acquire_record_lock(db, current_user, resource_type=resource_type, resource_id=resource_id, device_id=payload.device_id, hospital_id=payload.hospital_id)
        db.commit()
        return {"resource_type": resource_type, "resource_id": resource_id, "lock_token": token, "expires_at": lock.expires_at, "server_time": now_utc()}
    except Exception as exc:
        db.rollback()
        raise _error(exc) from exc


@router.post(
    "/records/{resource_type}/{resource_id}:lock-heartbeat",
    dependencies=[Depends(require_permission("hospital:flow:write"))],
)
def record_lock_heartbeat(
    resource_type: str,
    resource_id: str,
    payload: LockHeartbeatRequest,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    lock = db.query(NationalRecordLockModel).filter(
        NationalRecordLockModel.resource_type == resource_type,
        NationalRecordLockModel.resource_id == resource_id,
        NationalRecordLockModel.lab_id == _get_lab_id(current_user),
        NationalRecordLockModel.status == "active",
    ).first()
    if lock is None:
        raise HTTPException(status_code=404, detail="Lock not found")
    try:
        heartbeat_record_lock(db, current_user, lock, payload.lock_token)
        db.commit()
        return {"resource_type": resource_type, "resource_id": resource_id, "expires_at": lock.expires_at, "status": lock.status}
    except Exception as exc:
        db.rollback()
        raise _error(exc) from exc


@router.delete(
    "/records/{resource_type}/{resource_id}:lock",
    dependencies=[Depends(require_permission("hospital:flow:write"))],
)
def record_lock_release(
    resource_type: str,
    resource_id: str,
    lock_token: str,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    from hashlib import sha256
    lock = db.query(NationalRecordLockModel).filter(
        NationalRecordLockModel.resource_type == resource_type,
        NationalRecordLockModel.resource_id == resource_id,
        NationalRecordLockModel.lab_id == _get_lab_id(current_user),
        NationalRecordLockModel.owner_user_id == str(current_user.id),
        NationalRecordLockModel.status == "active",
    ).first()
    if lock is None or lock.lock_token_hash != sha256(lock_token.encode()).hexdigest():
        raise HTTPException(status_code=409, detail="Lock token is invalid")
    lock.status = "released"
    lock.released_at = now_utc()
    db.commit()
    return {"released": True, "resource_type": resource_type, "resource_id": resource_id}


@router.get("/notifications/stream")
def notification_stream(
    request: Request,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    user_id = str(current_user.id)
    lab_id = _get_lab_id(current_user)

    async def event_generator():
        last_seen = now_utc()
        while True:
            if await request.is_disconnected():
                break
            session = SessionLocal()
            try:
                rows = session.query(NationalClinicalNotificationModel).filter(
                    NationalClinicalNotificationModel.recipient_user_id == user_id,
                    NationalClinicalNotificationModel.lab_id == lab_id,
                    NationalClinicalNotificationModel.created_at > last_seen,
                    NationalClinicalNotificationModel.status.in_(["delivered", "escalated"]),
                ).order_by(NationalClinicalNotificationModel.created_at.asc()).limit(50).all()
                for row in rows:
                    last_seen = max(last_seen, row.created_at)
                    yield f"id: {row.id}\\nevent: clinical-conflict\\ndata: {json.dumps(_notification_view(row), default=str, ensure_ascii=False)}\\n\\n"
            finally:
                session.close()
            yield ": heartbeat\\n\\n"
            await asyncio.sleep(5)

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
