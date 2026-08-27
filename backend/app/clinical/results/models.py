from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)

from app.database import Base


def _core_id() -> str:
    return str(uuid.uuid4()).replace("-", "").upper()[:26]


def _now() -> datetime:
    return datetime.now(UTC)


class CoreLabResult(Base):  # type: ignore[misc]
    """Canonical result version; released rows are never overwritten."""

    __tablename__ = "core_lab_results"

    id = Column(String(26), primary_key=True, default=_core_id)
    result_id = Column(String(26), nullable=False, index=True)
    specimen_id = Column(String(26), nullable=False, index=True)
    lab_order_id = Column(String(26), nullable=False, index=True)
    order_item_id = Column(String(26), nullable=False, index=True)
    encounter_id = Column(String(26), nullable=False, index=True)
    patient_person_id = Column(String(26), nullable=False, index=True)
    laboratory_id = Column(String(26), nullable=False, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    workspace_id = Column(String(26), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="DRAFT", index=True)
    version = Column(Integer, nullable=False, default=1)
    value_numeric = Column(Numeric(20, 6), nullable=True)
    value_text = Column(Text, nullable=True)
    unit = Column(String(40), nullable=True)
    reference_low = Column(Numeric(20, 6), nullable=True)
    reference_high = Column(Numeric(20, 6), nullable=True)
    abnormal_flag = Column(String(24), nullable=True)
    test_code = Column(String(120), nullable=False)
    test_name = Column(String(240), nullable=False)
    provenance_type = Column(String(32), nullable=False, default="MANUAL")
    source_message_id = Column(String(200), nullable=True, unique=True, index=True)
    analyzer_code = Column(String(120), nullable=True)
    technical_validated_by = Column(String(26), nullable=True)
    technical_validated_at = Column(DateTime(timezone=True), nullable=True)
    clinically_validated_by = Column(String(26), nullable=True)
    clinically_validated_at = Column(DateTime(timezone=True), nullable=True)
    released_at = Column(DateTime(timezone=True), nullable=True)
    supersedes_id = Column(String(26), nullable=True, index=True)
    amendment_reason = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    __table_args__ = (
        UniqueConstraint("result_id", "version", name="uq_core_lab_result_version"),
        CheckConstraint("status IN ('DRAFT','TECHNICALLY_VALIDATED','CLINICALLY_VALIDATED','RELEASED','CORRECTED','AMENDED')", name="ck_core_lab_result_status"),
        CheckConstraint("provenance_type IN ('MANUAL','ANALYZER','IMPORTED_SYNTHETIC')", name="ck_core_lab_result_provenance"),
        CheckConstraint("version > 0", name="ck_core_lab_result_version_positive"),
        CheckConstraint("reference_high IS NULL OR reference_low IS NULL OR reference_high >= reference_low", name="ck_core_lab_result_reference_range"),
        Index("ix_core_lab_result_patient_status", "patient_person_id", "status", "created_at"),
        Index("ix_core_lab_result_scope_status", "organization_id", "facility_id", "workspace_id", "status", "created_at"),
    )


class CoreCriticalResultEvent(Base):  # type: ignore[misc]
    """Critical-result workflow separated from the result value itself."""

    __tablename__ = "core_critical_result_events"

    id = Column(String(26), primary_key=True, default=_core_id)
    result_id = Column(String(26), nullable=False, index=True)
    patient_person_id = Column(String(26), nullable=False, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    workspace_id = Column(String(26), nullable=False, index=True)
    severity = Column(String(16), nullable=False)
    status = Column(String(24), nullable=False, default="DETECTED", index=True)
    required_action = Column(String(500), nullable=False)
    acknowledged_by = Column(String(26), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    closed_by = Column(String(26), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    resolution_reason = Column(String(500), nullable=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    __table_args__ = (
        UniqueConstraint("result_id", name="uq_core_critical_result_result"),
        CheckConstraint("severity IN ('HIGH','CRITICAL')", name="ck_core_critical_result_severity"),
        CheckConstraint("status IN ('DETECTED','NOTIFIED','ACKNOWLEDGED','ACTIONED','ESCALATED','CLOSED')", name="ck_core_critical_result_status"),
        CheckConstraint("version > 0", name="ck_core_critical_result_version_positive"),
        Index("ix_core_critical_result_scope_status", "organization_id", "facility_id", "workspace_id", "status", "created_at"),
    )


class CoreClinicalNotification(Base):  # type: ignore[misc]
    """Synthetic/provider-neutral notification intent, not a Telegram/SMS adapter."""

    __tablename__ = "core_clinical_notifications"

    id = Column(String(26), primary_key=True, default=_core_id)
    event_key = Column(String(200), nullable=False, unique=True, index=True)
    recipient_account_id = Column(String(26), nullable=False, index=True)
    event_type = Column(String(80), nullable=False)
    channel = Column(String(32), nullable=False, default="SYNTHETIC")
    status = Column(String(24), nullable=False, default="PENDING", index=True)
    payload = Column(JSON, nullable=False)
    attempt_count = Column(Integer, nullable=False, default=0)
    last_error = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    delivered_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("channel IN ('SYNTHETIC','INTERNAL')", name="ck_core_notification_channel"),
        CheckConstraint("status IN ('PENDING','DELIVERED','FAILED','ACKNOWLEDGED','ESCALATED')", name="ck_core_notification_status"),
        CheckConstraint("attempt_count >= 0", name="ck_core_notification_attempts"),
        Index("ix_core_notification_recipient_status", "recipient_account_id", "status", "created_at"),
    )
