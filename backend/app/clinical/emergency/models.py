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
    return uuid.uuid4().hex.upper()[:26]


def _now() -> datetime:
    return datetime.now(UTC)


class CoreEmergencyTemporarySubject(Base):  # type: ignore[misc]
    __tablename__ = "core_emergency_temporary_subjects"

    id = Column(String(26), primary_key=True, default=_core_id)
    temporary_subject_id = Column(String(64), nullable=False, unique=True, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    workspace_id = Column(String(26), nullable=False, index=True)
    created_by_account_id = Column(String(26), nullable=False, index=True)
    status = Column(String(24), nullable=False, default="UNVERIFIED", index=True)
    synthetic_label = Column(String(160), nullable=False)
    reconciliation_status = Column(String(24), nullable=False, default="UNMATCHED")
    reconciled_person_id = Column(String(26), nullable=True, index=True)
    reconciliation_reason = Column(Text, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    __table_args__ = (
        CheckConstraint("status IN ('UNVERIFIED','ACTIVE','RECONCILED','RETIRED')", name="ck_core_emergency_temp_status"),
        CheckConstraint("reconciliation_status IN ('UNMATCHED','PENDING_REVIEW','MATCHED','REJECTED')", name="ck_core_emergency_temp_reconciliation"),
        CheckConstraint("version > 0", name="ck_core_emergency_temp_version"),
    )


class CoreEmergencyIncident(Base):  # type: ignore[misc]
    __tablename__ = "core_emergency_incidents"

    id = Column(String(26), primary_key=True, default=_core_id)
    incident_id = Column(String(64), nullable=False, unique=True, index=True)
    subject_kind = Column(String(16), nullable=False)
    patient_person_id = Column(String(26), nullable=True, index=True)
    temporary_subject_id = Column(String(26), nullable=True, index=True)
    encounter_id = Column(String(26), nullable=True, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    workspace_id = Column(String(26), nullable=False, index=True)
    reported_by_account_id = Column(String(26), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="REPORTED", index=True)
    priority = Column(String(16), nullable=False, default="URGENT")
    chief_complaint = Column(Text, nullable=False)
    location_summary = Column(String(500), nullable=True)
    version = Column(Integer, nullable=False, default=1)
    reported_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    __table_args__ = (
        CheckConstraint("subject_kind IN ('KNOWN_PATIENT','TEMPORARY')", name="ck_core_emergency_subject_kind"),
        CheckConstraint("(subject_kind = 'KNOWN_PATIENT' AND patient_person_id IS NOT NULL AND temporary_subject_id IS NULL) OR (subject_kind = 'TEMPORARY' AND patient_person_id IS NULL AND temporary_subject_id IS NOT NULL)", name="ck_core_emergency_subject_exclusive"),
        CheckConstraint("status IN ('REPORTED','TRIAGED','DISPATCHED','EN_ROUTE','ON_SCENE','TRANSPORTING','AT_DESTINATION','HANDOVER_COMPLETE','CLOSED','CANCELLED')", name="ck_core_emergency_incident_status"),
        CheckConstraint("priority IN ('ROUTINE','URGENT','STAT','CRITICAL')", name="ck_core_emergency_priority"),
        CheckConstraint("version > 0", name="ck_core_emergency_incident_version"),
        Index("ix_core_emergency_incident_scope_status", "organization_id", "facility_id", "workspace_id", "status", "reported_at"),
        Index("ix_core_emergency_incident_patient_time", "patient_person_id", "reported_at"),
    )


class CoreEmergencyDispatch(Base):  # type: ignore[misc]
    __tablename__ = "core_emergency_dispatches"

    id = Column(String(26), primary_key=True, default=_core_id)
    dispatch_request_id = Column(String(100), nullable=False, unique=True, index=True)
    incident_id = Column(String(26), nullable=False, index=True)
    ambulance_reference = Column(String(120), nullable=False)
    crew_references = Column(JSON, nullable=False)
    status = Column(String(24), nullable=False, default="ASSIGNED", index=True)
    assigned_by_account_id = Column(String(26), nullable=False, index=True)
    dispatch_notes = Column(Text, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    assigned_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    __table_args__ = (
        CheckConstraint("status IN ('ASSIGNED','EN_ROUTE','ON_SCENE','TRANSPORTING','AT_DESTINATION','COMPLETED','CANCELLED')", name="ck_core_emergency_dispatch_status"),
        CheckConstraint("version > 0", name="ck_core_emergency_dispatch_version"),
    )


class CoreEmergencyTriage(Base):  # type: ignore[misc]
    __tablename__ = "core_emergency_triage_assessments"

    id = Column(String(26), primary_key=True, default=_core_id)
    triage_id = Column(String(64), nullable=False, unique=True, index=True)
    incident_id = Column(String(26), nullable=False, index=True)
    patient_person_id = Column(String(26), nullable=True, index=True)
    temporary_subject_id = Column(String(26), nullable=True, index=True)
    category = Column(String(24), nullable=False)
    clinician_summary = Column(Text, nullable=False)
    vital_snapshot = Column(JSON, nullable=False)
    assessed_by_account_id = Column(String(26), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    assessed_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    __table_args__ = (
        CheckConstraint("category IN ('IMMEDIATE','VERY_URGENT','URGENT','STANDARD','DELAYED','EXPECTANT')", name="ck_core_emergency_triage_category"),
        CheckConstraint("version > 0", name="ck_core_emergency_triage_version"),
    )


class CoreEmergencyTreatment(Base):  # type: ignore[misc]
    __tablename__ = "core_emergency_treatments"

    id = Column(String(26), primary_key=True, default=_core_id)
    treatment_request_id = Column(String(100), nullable=False, unique=True, index=True)
    incident_id = Column(String(26), nullable=False, index=True)
    patient_person_id = Column(String(26), nullable=True, index=True)
    temporary_subject_id = Column(String(26), nullable=True, index=True)
    treatment_type = Column(String(100), nullable=False)
    treatment_details = Column(Text, nullable=False)
    performed_by_account_id = Column(String(26), nullable=False, index=True)
    performed_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)


class CoreEmergencyPrealert(Base):  # type: ignore[misc]
    __tablename__ = "core_emergency_prealerts"

    id = Column(String(26), primary_key=True, default=_core_id)
    prealert_request_id = Column(String(100), nullable=False, unique=True, index=True)
    incident_id = Column(String(26), nullable=False, index=True)
    destination_facility_reference = Column(String(120), nullable=False)
    acuity = Column(String(24), nullable=False)
    estimated_arrival_minutes = Column(Integer, nullable=False)
    minimal_payload = Column(JSON, nullable=False)
    delivery_mode = Column(String(32), nullable=False, default="SYNTHETIC_INTENT")
    status = Column(String(24), nullable=False, default="PENDING", index=True)
    created_by_account_id = Column(String(26), nullable=False, index=True)
    acknowledged_by_account_id = Column(String(26), nullable=True, index=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    __table_args__ = (
        CheckConstraint("estimated_arrival_minutes >= 0 AND estimated_arrival_minutes <= 1440", name="ck_core_prealert_eta_bounds"),
        CheckConstraint("delivery_mode = 'SYNTHETIC_INTENT'", name="ck_core_prealert_synthetic_only"),
        CheckConstraint("status IN ('PENDING','ACKNOWLEDGED','EXPIRED','FAILED')", name="ck_core_prealert_status"),
        CheckConstraint("version > 0", name="ck_core_prealert_version"),
    )


class CoreEmergencyHandover(Base):  # type: ignore[misc]
    __tablename__ = "core_emergency_handovers"

    id = Column(String(26), primary_key=True, default=_core_id)
    handover_request_id = Column(String(100), nullable=False, unique=True, index=True)
    incident_id = Column(String(26), nullable=False, index=True)
    receiving_facility_reference = Column(String(120), nullable=False)
    patient_person_id = Column(String(26), nullable=True, index=True)
    temporary_subject_id = Column(String(26), nullable=True, index=True)
    minimal_summary = Column(JSON, nullable=False)
    submitted_by_account_id = Column(String(26), nullable=False, index=True)
    received_by_account_id = Column(String(26), nullable=True, index=True)
    supersedes_id = Column(String(26), nullable=True, index=True)
    amendment_reason = Column(Text, nullable=True)
    status = Column(String(24), nullable=False, default="SUBMITTED", index=True)
    version = Column(Integer, nullable=False, default=1)
    submitted_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    __table_args__ = (
        CheckConstraint("status IN ('SUBMITTED','ACKNOWLEDGED','AMENDED','CANCELLED')", name="ck_core_emergency_handover_status"),
        CheckConstraint("version > 0", name="ck_core_emergency_handover_version"),
    )


class CoreEmergencyEPCR(Base):  # type: ignore[misc]
    __tablename__ = "core_emergency_epcr"

    id = Column(String(26), primary_key=True, default=_core_id)
    epcr_id = Column(String(64), nullable=False, index=True)
    incident_id = Column(String(26), nullable=False, index=True)
    patient_person_id = Column(String(26), nullable=True, index=True)
    temporary_subject_id = Column(String(26), nullable=True, index=True)
    version = Column(Integer, nullable=False, default=1)
    status = Column(String(24), nullable=False, default="DRAFT", index=True)
    chief_complaint = Column(Text, nullable=False)
    narrative = Column(Text, nullable=False)
    interventions = Column(JSON, nullable=False)
    destination_facility_reference = Column(String(120), nullable=True)
    signature_evidence = Column(JSON, nullable=True)
    authored_by_account_id = Column(String(26), nullable=False, index=True)
    signed_by_account_id = Column(String(26), nullable=True, index=True)
    signed_at = Column(DateTime(timezone=True), nullable=True)
    supersedes_id = Column(String(26), nullable=True, index=True)
    amendment_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    __table_args__ = (
        CheckConstraint("status IN ('DRAFT','SIGNED','AMENDED')", name="ck_core_emergency_epcr_status"),
        CheckConstraint("version > 0", name="ck_core_emergency_epcr_version"),
        UniqueConstraint("epcr_id", "version", name="uq_core_emergency_epcr_version"),
    )


class CoreEmergencyOutbox(Base):  # type: ignore[misc]
    __tablename__ = "core_emergency_outbox"

    id = Column(String(26), primary_key=True, default=_core_id)
    event_key = Column(String(160), nullable=False, unique=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    aggregate_type = Column(String(80), nullable=False)
    aggregate_id = Column(String(26), nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    delivery_mode = Column(String(32), nullable=False, default="SYNTHETIC_INTENT")
    status = Column(String(24), nullable=False, default="PENDING", index=True)
    attempt_count = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)
    next_attempt_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    delivered_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("delivery_mode = 'SYNTHETIC_INTENT'", name="ck_core_emergency_outbox_synthetic_only"),
        CheckConstraint("status IN ('PENDING','CLAIMED','DELIVERED','FAILED')", name="ck_core_emergency_outbox_status"),
        CheckConstraint("attempt_count >= 0", name="ck_core_emergency_outbox_attempts"),
    )


__all__ = [
    "CoreEmergencyDispatch",
    "CoreEmergencyEPCR",
    "CoreEmergencyHandover",
    "CoreEmergencyIncident",
    "CoreEmergencyOutbox",
    "CoreEmergencyPrealert",
    "CoreEmergencyTemporarySubject",
    "CoreEmergencyTreatment",
    "CoreEmergencyTriage",
]
