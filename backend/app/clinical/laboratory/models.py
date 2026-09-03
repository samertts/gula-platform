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
    String,
    Text,
    UniqueConstraint,
)

from app.database import Base


def _core_id() -> str:
    return str(uuid.uuid4()).replace("-", "").upper()[:26]


def _now() -> datetime:
    return datetime.now(UTC)


class CoreClinicalCommandReceipt(Base):  # type: ignore[misc]
    """Durable idempotency receipt shared by canonical clinical commands."""

    __tablename__ = "core_clinical_command_receipts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    actor_account_id = Column(String(26), nullable=False, index=True)
    operation = Column(String(100), nullable=False)
    idempotency_key = Column(String(128), nullable=False)
    request_fingerprint = Column(String(64), nullable=False)
    resource_id = Column(String(26), nullable=True, index=True)
    status = Column(String(24), nullable=False, default="CLAIMED", index=True)
    response_body = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("actor_account_id", "operation", "idempotency_key", name="uq_core_clinical_command_receipt"),
        CheckConstraint("status IN ('CLAIMED','COMPLETED','REJECTED')", name="ck_core_clinical_command_receipt_status"),
        Index("ix_core_clinical_command_receipt_lookup", "actor_account_id", "operation", "created_at"),
    )


class CoreLabOrder(Base):  # type: ignore[misc]
    """Canonical laboratory order linked to a signed clinical encounter."""

    __tablename__ = "core_lab_orders"

    id = Column(String(26), primary_key=True, default=_core_id)
    encounter_id = Column(String(26), nullable=False, index=True)
    patient_person_id = Column(String(26), nullable=False, index=True)
    ordering_provider_account_id = Column(String(26), nullable=False, index=True)
    laboratory_id = Column(String(26), nullable=False, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    workspace_id = Column(String(26), nullable=False, index=True)
    status = Column(String(24), nullable=False, default="DRAFT", index=True)
    priority = Column(String(16), nullable=False, default="ROUTINE", index=True)
    clinical_indication = Column(Text, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    verified_by_account_id = Column(String(26), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    __table_args__ = (
        CheckConstraint("status IN ('DRAFT','PLACED','VERIFIED','ACCEPTED','IN_PROGRESS','COMPLETED','REJECTED','CANCELLED')", name="ck_core_lab_order_status"),
        CheckConstraint("priority IN ('ROUTINE','URGENT','STAT')", name="ck_core_lab_order_priority"),
        CheckConstraint("version > 0", name="ck_core_lab_order_version_positive"),
        Index("ix_core_lab_order_scope_status", "organization_id", "facility_id", "workspace_id", "status", "created_at"),
        Index("ix_core_lab_order_patient_created", "patient_person_id", "created_at"),
    )


class CoreLabOrderItem(Base):  # type: ignore[misc]
    """One requested test and its specimen requirement."""

    __tablename__ = "core_lab_order_items"

    id = Column(String(26), primary_key=True, default=_core_id)
    lab_order_id = Column(String(26), nullable=False, index=True)
    test_code = Column(String(120), nullable=False)
    test_name = Column(String(240), nullable=False)
    specimen_type = Column(String(80), nullable=False)
    status = Column(String(24), nullable=False, default="ORDERED", index=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    __table_args__ = (
        UniqueConstraint("lab_order_id", "test_code", name="uq_core_lab_order_item_test"),
        CheckConstraint("status IN ('ORDERED','COLLECTED','RECEIVED','PROCESSING','COMPLETED','REJECTED','CANCELLED')", name="ck_core_lab_order_item_status"),
        CheckConstraint("version > 0", name="ck_core_lab_order_item_version_positive"),
        Index("ix_core_lab_order_item_test", "test_code", "created_at"),
    )


class CoreSpecimen(Base):  # type: ignore[misc]
    """Canonical specimen aggregate with server-generated accession/barcode."""

    __tablename__ = "core_specimens"

    id = Column(String(26), primary_key=True, default=_core_id)
    lab_order_id = Column(String(26), nullable=False, index=True)
    order_item_id = Column(String(26), nullable=False, index=True)
    encounter_id = Column(String(26), nullable=False, index=True)
    patient_person_id = Column(String(26), nullable=False, index=True)
    laboratory_id = Column(String(26), nullable=False, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    workspace_id = Column(String(26), nullable=False, index=True)
    specimen_type = Column(String(80), nullable=False)
    accession_number = Column(String(80), nullable=False, unique=True, index=True)
    barcode = Column(String(120), nullable=False, unique=True, index=True)
    status = Column(String(24), nullable=False, default="ORDERED", index=True)
    version = Column(Integer, nullable=False, default=1)
    collector_account_id = Column(String(26), nullable=True)
    receiver_account_id = Column(String(26), nullable=True)
    collected_at = Column(DateTime(timezone=True), nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=True)
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    validated_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    __table_args__ = (
        UniqueConstraint("order_item_id", name="uq_core_specimen_order_item"),
        CheckConstraint("status IN ('ORDERED','COLLECTED','RECEIVED','PROCESSING','ANALYZING','VALIDATED','REJECTED')", name="ck_core_specimen_status"),
        CheckConstraint("version > 0", name="ck_core_specimen_version_positive"),
        Index("ix_core_specimen_scope_status", "organization_id", "facility_id", "workspace_id", "status", "created_at"),
        Index("ix_core_specimen_lab_worklist", "laboratory_id", "status", "created_at"),
    )


class CoreSpecimenEvent(Base):  # type: ignore[misc]
    """Append-only chain-of-custody event for a specimen."""

    __tablename__ = "core_specimen_events"

    id = Column(String(26), primary_key=True, default=_core_id)
    specimen_id = Column(String(26), nullable=False, index=True)
    event_type = Column(String(48), nullable=False, index=True)
    previous_state = Column(String(24), nullable=False)
    new_state = Column(String(24), nullable=False)
    actor_account_id = Column(String(26), nullable=False, index=True)
    laboratory_id = Column(String(26), nullable=False, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    workspace_id = Column(String(26), nullable=False, index=True)
    correlation_id = Column(String(128), nullable=False, index=True)
    event_metadata = Column(JSON, nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=_now, index=True)

    __table_args__ = (
        CheckConstraint("length(trim(event_type)) > 0", name="ck_core_specimen_event_type_nonempty"),
        Index("ix_core_specimen_event_timeline", "specimen_id", "occurred_at", "id"),
    )
