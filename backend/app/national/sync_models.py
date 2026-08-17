from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Index, Integer, JSON, String, Text, UniqueConstraint

from app._compat import UTC
from app.national.base import NationalBase


def _id() -> str:
    return str(uuid.uuid4()).replace("-", "").upper()[:26]


def _now() -> datetime:
    return datetime.now(UTC)


class NationalSyncOperationModel(NationalBase):
    __tablename__ = "national_sync_operations"

    id = Column(String(26), primary_key=True, default=_id)
    operation_id = Column(String(64), nullable=False, unique=True, index=True)
    idempotency_key = Column(String(128), nullable=False)
    device_id = Column(String(128), nullable=False, index=True)
    user_id = Column(String(64), nullable=False, index=True)
    lab_id = Column(Integer, nullable=False, index=True)
    hospital_id = Column(Integer, nullable=True, index=True)
    client_sequence = Column(Integer, nullable=True)
    operation_type = Column(String(64), nullable=False, index=True)
    entity_type = Column(String(64), nullable=False, index=True)
    entity_id = Column(String(128), nullable=True, index=True)
    base_version = Column(Integer, nullable=True)
    priority = Column(String(16), nullable=False, default="routine", index=True)
    payload = Column(JSON, nullable=False, default=dict)
    payload_hash = Column(String(128), nullable=False)
    signature = Column(String(256), nullable=True)
    status = Column(String(32), nullable=False, default="queued", index=True)
    attempt_count = Column(Integer, nullable=False, default=0)
    next_attempt_at = Column(DateTime(timezone=True), nullable=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    rejection_code = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("lab_id", "device_id", "idempotency_key", name="uq_sync_scope_idempotency"),
        Index("ix_sync_queue_priority_created", "lab_id", "hospital_id", "status", "priority", "created_at"),
    )


class NationalSyncConflictModel(NationalBase):
    __tablename__ = "national_sync_conflicts"

    id = Column(String(26), primary_key=True, default=_id)
    operation_id = Column(String(64), nullable=False, index=True)
    lab_id = Column(Integer, nullable=False, index=True)
    hospital_id = Column(Integer, nullable=True, index=True)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(String(128), nullable=True, index=True)
    conflict_type = Column(String(64), nullable=False, index=True)
    severity = Column(String(16), nullable=False, default="P2_HIGH", index=True)
    status = Column(String(32), nullable=False, default="pending", index=True)
    base_version = Column(Integer, nullable=True)
    server_version = Column(Integer, nullable=True)
    local_payload = Column(JSON, nullable=False, default=dict)
    server_snapshot = Column(JSON, nullable=True)
    resolution = Column(String(64), nullable=True)
    resolution_reason = Column(Text, nullable=True)
    resolved_by = Column(String(64), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    __table_args__ = (
        Index("ix_sync_conflict_queue", "lab_id", "hospital_id", "status", "severity", "created_at"),
    )


class NationalRecordLockModel(NationalBase):
    __tablename__ = "national_record_locks"

    id = Column(String(26), primary_key=True, default=_id)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(String(128), nullable=False)
    lab_id = Column(Integer, nullable=False, index=True)
    hospital_id = Column(Integer, nullable=True, index=True)
    owner_user_id = Column(String(64), nullable=False)
    owner_device_id = Column(String(128), nullable=False)
    lock_token_hash = Column(String(128), nullable=False, unique=True)
    status = Column(String(16), nullable=False, default="active", index=True)
    acquired_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    last_heartbeat_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    released_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_record_lock_resource", "resource_type", "resource_id", "lab_id", "status"),
    )


class NationalSyncOutboxModel(NationalBase):
    __tablename__ = "national_sync_outbox"

    id = Column(String(26), primary_key=True, default=_id)
    event_id = Column(String(64), nullable=False, unique=True, index=True)
    event_type = Column(String(96), nullable=False, index=True)
    aggregate_type = Column(String(64), nullable=False)
    aggregate_id = Column(String(128), nullable=False, index=True)
    lab_id = Column(Integer, nullable=False, index=True)
    hospital_id = Column(Integer, nullable=True, index=True)
    payload = Column(JSON, nullable=False, default=dict)
    status = Column(String(24), nullable=False, default="pending", index=True)
    attempts = Column(Integer, nullable=False, default=0)
    next_attempt_at = Column(DateTime(timezone=True), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)


class NationalClinicalNotificationModel(NationalBase):
    __tablename__ = "national_clinical_notifications"

    id = Column(String(26), primary_key=True, default=_id)
    event_id = Column(String(64), nullable=False, index=True)
    conflict_id = Column(String(26), nullable=False, index=True)
    recipient_user_id = Column(String(64), nullable=False, index=True)
    lab_id = Column(Integer, nullable=False, index=True)
    hospital_id = Column(Integer, nullable=True, index=True)
    severity = Column(String(16), nullable=False, index=True)
    title = Column(String(512), nullable=False)
    message = Column(Text, nullable=False)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(String(128), nullable=True)
    dedupe_key = Column(String(256), nullable=False, unique=True)
    status = Column(String(24), nullable=False, default="delivered", index=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(String(64), nullable=True)
    escalated_at = Column(DateTime(timezone=True), nullable=True)
    escalated_to = Column(String(64), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    __table_args__ = (
        Index("ix_clinical_notification_inbox", "recipient_user_id", "status", "severity", "created_at"),
    )


class NationalDeviceSessionModel(NationalBase):
    __tablename__ = "national_device_sessions"

    id = Column(String(26), primary_key=True, default=_id)
    device_id = Column(String(128), nullable=False, unique=True)
    lab_id = Column(Integer, nullable=False, index=True)
    hospital_id = Column(Integer, nullable=False, index=True)
    user_id = Column(String(64), nullable=False)
    policy_version = Column(String(64), nullable=False, default="offline-emergency-1")
    allowed_operation_types = Column(JSON, nullable=False, default=list)
    session_hash = Column(String(128), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    revoked = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)


_ALL_MODELS = [
    NationalSyncOperationModel,
    NationalSyncConflictModel,
    NationalRecordLockModel,
    NationalSyncOutboxModel,
    NationalClinicalNotificationModel,
    NationalDeviceSessionModel,
]
