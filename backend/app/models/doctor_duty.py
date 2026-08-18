"""Duty-bound clinical authorization persistence models.

Design reminder: Authentication is not Duty and Duty is not Clinical Authorization.
Every expanded context is tenant-, organization-, facility-, location-, role-,
patient-scope-, purpose-, and time-bound. Default is deny.
"""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import JSON, Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from app._compat import UTC
from ..database import Base

DUTY_STATES = (
    "SCHEDULED", "CHECKED_IN", "ACTIVE", "PAUSED", "HANDOVER_PENDING",
    "HANDOVER_COMPLETED", "ENDED", "CANCELLED", "REVOKED",
)
ACTIVE_DUTY_STATES = ("ACTIVE", "PAUSED", "HANDOVER_PENDING")


def utcnow() -> datetime:
    return datetime.now(UTC)


class DoctorDuty(Base):
    __tablename__ = "doctor_duties"
    __table_args__ = (
        CheckConstraint("status IN ('SCHEDULED','CHECKED_IN','ACTIVE','PAUSED','HANDOVER_PENDING','HANDOVER_COMPLETED','ENDED','CANCELLED','REVOKED')", name="ck_doctor_duty_status"),
        CheckConstraint("expected_end_at > starts_at", name="ck_doctor_duty_time_order"),
        Index("ix_doctor_duties_user_status_time", "user_id", "status", "starts_at", "expected_end_at"),
        Index("ix_doctor_duties_tenant_org_facility", "tenant_id", "organization_id", "facility_id"),
    )
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id", ondelete="RESTRICT"), nullable=False, index=True)
    department_id = Column(String(100), nullable=True, index=True)
    ward_id = Column(String(100), nullable=True, index=True)
    room_id = Column(String(100), nullable=True)
    role_id = Column(String(100), nullable=False, index=True)
    purpose = Column(String(100), nullable=False)
    starts_at = Column(DateTime(timezone=True), nullable=False)
    expected_end_at = Column(DateTime(timezone=True), nullable=False)
    actual_started_at = Column(DateTime(timezone=True), nullable=True)
    actual_ended_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(30), nullable=False, default="SCHEDULED", index=True)
    assigned_patient_ids = Column(JSON, nullable=True)
    scope = Column(JSON, nullable=True)
    assigned_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    revoked_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    revocation_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    version = Column(Integer, nullable=False, default=1)

    contexts = relationship("DutyContext", back_populates="duty", cascade="all, delete-orphan")


class DutyContext(Base):
    __tablename__ = "duty_contexts"
    __table_args__ = (
        Index("ix_duty_contexts_user_active", "user_id", "status", "expires_at"),
        Index("ix_duty_contexts_scope", "organization_id", "facility_id", "department_id", "ward_id"),
    )
    id = Column(String(64), primary_key=True)
    duty_id = Column(Integer, ForeignKey("doctor_duties.id", ondelete="CASCADE"), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(Integer, nullable=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    facility_id = Column(Integer, nullable=False, index=True)
    department_id = Column(String(100), nullable=True)
    ward_id = Column(String(100), nullable=True)
    role_id = Column(String(100), nullable=False)
    purpose = Column(String(100), nullable=False)
    status = Column(String(30), nullable=False, default="ACTIVE", index=True)
    started_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    authz_version = Column(Integer, nullable=False, default=1)
    assigned_patient_ids = Column(JSON, nullable=True)
    permissions = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    duty = relationship("DoctorDuty", back_populates="contexts")
    shift = relationship("ShiftContext", back_populates="duty_context", uselist=False, cascade="all, delete-orphan")
    clinical_access = relationship("ClinicalAccessContext", back_populates="duty_context", uselist=False, cascade="all, delete-orphan")


class ShiftContext(Base):
    __tablename__ = "shift_contexts"
    id = Column(String(64), primary_key=True)
    duty_context_id = Column(String(64), ForeignKey("duty_contexts.id", ondelete="CASCADE"), nullable=False, unique=True)
    shift_start = Column(DateTime(timezone=True), nullable=False)
    shift_expected_end = Column(DateTime(timezone=True), nullable=False)
    timezone = Column(String(64), nullable=False, default="UTC")
    server_started_at = Column(DateTime(timezone=True), nullable=False)
    server_ended_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(30), nullable=False, default="ACTIVE")

    duty_context = relationship("DutyContext", back_populates="shift")


class ClinicalAccessContext(Base):
    __tablename__ = "clinical_access_contexts"
    id = Column(String(64), primary_key=True)
    duty_context_id = Column(String(64), ForeignKey("duty_contexts.id", ondelete="CASCADE"), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    facility_id = Column(Integer, nullable=False, index=True)
    department_id = Column(String(100), nullable=True)
    ward_id = Column(String(100), nullable=True)
    scope_type = Column(String(30), nullable=False, default="ASSIGNED_LOCATION")
    allowed_resources = Column(JSON, nullable=False, default=list)
    patient_scope = Column(JSON, nullable=False, default=dict)
    purpose = Column(String(100), nullable=False)
    active = Column(Boolean, nullable=False, default=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    version = Column(Integer, nullable=False, default=1)

    duty_context = relationship("DutyContext", back_populates="clinical_access")


class DutyHandover(Base):
    __tablename__ = "duty_handovers"
    id = Column(Integer, primary_key=True)
    outgoing_duty_id = Column(Integer, ForeignKey("doctor_duties.id", ondelete="RESTRICT"), nullable=False, index=True)
    incoming_duty_id = Column(Integer, ForeignKey("doctor_duties.id", ondelete="RESTRICT"), nullable=False, index=True)
    outgoing_user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    incoming_user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    patient_ids = Column(JSON, nullable=False, default=list)
    task_ids = Column(JSON, nullable=False, default=list)
    status = Column(String(30), nullable=False, default="PENDING")
    started_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)


class DutyAuditEvent(Base):
    __tablename__ = "duty_audit_events"
    id = Column(Integer, primary_key=True)
    event_type = Column(String(60), nullable=False, index=True)
    actor_id = Column(Integer, nullable=True, index=True)
    duty_context_id = Column(String(64), nullable=True, index=True)
    organization_id = Column(Integer, nullable=True, index=True)
    facility_id = Column(Integer, nullable=True, index=True)
    location = Column(JSON, nullable=True)
    resource_type = Column(String(80), nullable=True)
    resource_id = Column(String(120), nullable=True)
    patient_id = Column(Integer, nullable=True, index=True)
    purpose = Column(String(100), nullable=True)
    decision = Column(String(20), nullable=False)
    request_id = Column(String(120), nullable=True, index=True)
    correlation_id = Column(String(120), nullable=True, index=True)
    occurred_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    metadata_json = Column(JSON, nullable=True)


class DutyBreakGlass(Base):
    __tablename__ = "duty_break_glass"
    id = Column(String(64), primary_key=True)
    duty_context_id = Column(String(64), ForeignKey("duty_contexts.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="SET NULL"), nullable=True)
    reason = Column(Text, nullable=False)
    scope = Column(JSON, nullable=False)
    started_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="ACTIVE")

__all__ = ["DoctorDuty", "DutyContext", "ShiftContext", "ClinicalAccessContext", "DutyHandover", "DutyAuditEvent", "DutyBreakGlass", "DUTY_STATES", "ACTIVE_DUTY_STATES"]
