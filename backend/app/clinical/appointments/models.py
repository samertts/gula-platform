from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    UniqueConstraint,
)

from app._compat import UTC
from app.database import Base


def _core_id() -> str:
    return str(uuid.uuid4()).replace("-", "").upper()[:26]


class CoreAppointmentSlot(Base):  # type: ignore[misc]
    """Canonical slot owned by an explicit workspace/facility context."""

    __tablename__ = "core_appointment_slots"

    id = Column(String(26), primary_key=True, default=_core_id)
    # Cross-domain references are validated by AuthorizationService and enforced
    # by migration-level constraints. Base and IdentityBase use separate
    # SQLAlchemy metadata namespaces, so ORM-level cross-metadata FKs would make
    # mapper configuration fail before the target table is registered.
    organization_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    workspace_id = Column(String(26), nullable=False, index=True)
    provider_account_id = Column(String(26), nullable=False, index=True)
    service_code = Column(String(120), nullable=False)
    starts_at = Column(DateTime(timezone=True), nullable=False, index=True)
    ends_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(24), nullable=False, default="AVAILABLE", index=True)
    version = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "provider_account_id",
            "starts_at",
            "ends_at",
            name="uq_core_appointment_slot_provider_window",
        ),
        CheckConstraint("ends_at > starts_at", name="ck_core_appointment_slot_positive_window"),
        CheckConstraint("status IN ('AVAILABLE','BOOKED','BLOCKED')", name="ck_core_appointment_slot_status"),
        Index("ix_core_appointment_slot_scope_time", "organization_id", "facility_id", "workspace_id", "starts_at"),
    )


class CoreAppointment(Base):  # type: ignore[misc]
    """Canonical request/confirm appointment aggregate.

    Identity-side identifiers are deliberately opaque references. National ID,
    health ID, device fingerprints, and other sensitive identifiers never belong
    in this table or in API payloads.
    """

    __tablename__ = "core_appointments"

    id = Column(String(26), primary_key=True, default=_core_id)
    patient_person_id = Column(String(26), nullable=False, index=True)
    requester_account_id = Column(String(26), nullable=False, index=True)
    provider_account_id = Column(String(26), nullable=False, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    workspace_id = Column(String(26), nullable=False, index=True)
    slot_id = Column(String(26), nullable=False, unique=True, index=True)
    service_code = Column(String(120), nullable=False)
    purpose = Column(String(40), nullable=False, default="TREATMENT")
    starts_at = Column(DateTime(timezone=True), nullable=False)
    ends_at = Column(DateTime(timezone=True), nullable=False)
    state = Column(String(24), nullable=False, default="REQUESTED", index=True)
    version = Column(Integer, nullable=False, default=1)
    requested_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    __table_args__ = (
        CheckConstraint(
            "state IN ('REQUESTED','CONFIRMED','CHECKED_IN','IN_PROGRESS','COMPLETED','CANCELLED','NO_SHOW','RESCHEDULED','EXPIRED')",
            name="ck_core_appointment_state",
        ),
        CheckConstraint("ends_at > starts_at", name="ck_core_appointment_positive_window"),
        Index("ix_core_appointment_patient_scope", "patient_person_id", "organization_id", "workspace_id", "created_at"),
        Index("ix_core_appointment_provider_scope", "provider_account_id", "organization_id", "workspace_id", "created_at"),
    )


class CoreAppointmentIdempotencyReceipt(Base):  # type: ignore[misc]
    """Durable idempotency record for appointment commands."""

    __tablename__ = "core_appointment_idempotency"

    id = Column(Integer, primary_key=True, autoincrement=True)
    actor_account_id = Column(String(26), nullable=False, index=True)
    operation = Column(String(80), nullable=False)
    idempotency_key = Column(String(128), nullable=False)
    request_fingerprint = Column(String(64), nullable=False)
    # The resource may be a slot or an appointment; operation scopes its type.
    # A polymorphic receipt must not pretend that a slot ID is an appointment FK.
    resource_id = Column(String(26), nullable=True, index=True)
    status = Column(String(24), nullable=False, default="CLAIMED", index=True)
    response_body = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("actor_account_id", "operation", "idempotency_key", name="uq_core_appointment_idem_actor_op_key"),
        CheckConstraint("status IN ('CLAIMED','COMPLETED','REJECTED')", name="ck_core_appointment_idem_status"),
        Index("ix_core_appointment_idem_lookup", "actor_account_id", "operation", "created_at"),
    )
