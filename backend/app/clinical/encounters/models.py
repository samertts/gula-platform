from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
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


class CoreEncounter(Base):  # type: ignore[misc]
    """Canonical clinical visit created from one eligible appointment."""

    __tablename__ = "core_encounters"

    id = Column(String(26), primary_key=True, default=_core_id)
    appointment_id = Column(String(26), nullable=False, unique=True, index=True)
    patient_person_id = Column(String(26), nullable=False, index=True)
    provider_account_id = Column(String(26), nullable=False, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    workspace_id = Column(String(26), nullable=False, index=True)
    status = Column(String(24), nullable=False, default="PLANNED", index=True)
    version = Column(Integer, nullable=False, default=1)
    checked_in_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    __table_args__ = (
        CheckConstraint("status IN ('PLANNED','CHECKED_IN','IN_PROGRESS','COMPLETED','CANCELLED')", name="ck_core_encounter_status"),
        CheckConstraint("version > 0", name="ck_core_encounter_version_positive"),
        Index("ix_core_encounter_patient_scope", "patient_person_id", "organization_id", "workspace_id", "created_at"),
        Index("ix_core_encounter_provider_scope", "provider_account_id", "organization_id", "workspace_id", "created_at"),
    )


class CoreEncounterQueueEntry(Base):  # type: ignore[misc]
    """Server-authoritative queue state created atomically with check-in."""

    __tablename__ = "core_encounter_queue"

    id = Column(String(26), primary_key=True, default=_core_id)
    encounter_id = Column(String(26), nullable=False, unique=True, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    workspace_id = Column(String(26), nullable=False, index=True)
    status = Column(String(24), nullable=False, default="WAITING", index=True)
    position = Column(Integer, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    __table_args__ = (
        CheckConstraint("status IN ('WAITING','CALLED','IN_SERVICE','COMPLETED','NO_SHOW','CANCELLED')", name="ck_core_encounter_queue_status"),
        CheckConstraint("version > 0", name="ck_core_encounter_queue_version_positive"),
        Index("ix_core_encounter_queue_scope_status", "organization_id", "facility_id", "workspace_id", "status"),
    )


class CoreClinicalNote(Base):  # type: ignore[misc]
    """Immutable version row for an extensible clinical note family."""

    __tablename__ = "core_clinical_notes"

    id = Column(String(26), primary_key=True, default=_core_id)
    note_id = Column(String(26), nullable=False, index=True)
    encounter_id = Column(String(26), nullable=False, index=True)
    patient_person_id = Column(String(26), nullable=False, index=True)
    author_account_id = Column(String(26), nullable=False, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    workspace_id = Column(String(26), nullable=False, index=True)
    status = Column(String(24), nullable=False, default="DRAFT", index=True)
    version = Column(Integer, nullable=False, default=1)
    chief_complaint = Column(Text, nullable=True)
    history = Column(Text, nullable=True)
    examination = Column(Text, nullable=True)
    assessment = Column(Text, nullable=True)
    plan = Column(Text, nullable=True)
    amendment_reason = Column(String(500), nullable=True)
    supersedes_id = Column(String(26), nullable=True, index=True)
    signed_by_account_id = Column(String(26), nullable=True)
    signed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    __table_args__ = (
        UniqueConstraint("note_id", "version", name="uq_core_clinical_note_version"),
        CheckConstraint("status IN ('DRAFT','COMPLETED','SIGNED','AMENDED')", name="ck_core_clinical_note_status"),
        CheckConstraint("version > 0", name="ck_core_clinical_note_version_positive"),
        Index("ix_core_note_encounter_scope", "encounter_id", "organization_id", "workspace_id", "created_at"),
    )
