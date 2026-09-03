from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
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


class CoreImagingOrder(Base):  # type: ignore[misc]
    __tablename__ = "core_imaging_orders"

    id = Column(String(26), primary_key=True, default=_core_id)
    order_id = Column(String(26), nullable=False, unique=True, index=True)
    encounter_id = Column(String(26), nullable=False, index=True)
    patient_person_id = Column(String(26), nullable=False, index=True)
    ordering_provider_account_id = Column(String(26), nullable=False, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    workspace_id = Column(String(26), nullable=False, index=True)
    accession_number = Column(String(80), nullable=False, unique=True, index=True)
    modality = Column(String(32), nullable=False)
    body_part = Column(String(120), nullable=True)
    clinical_indication = Column(Text, nullable=True)
    priority = Column(String(16), nullable=False, default="ROUTINE")
    status = Column(String(24), nullable=False, default="DRAFT", index=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    __table_args__ = (
        CheckConstraint("status IN ('DRAFT','PLACED','SCHEDULED','IN_PROGRESS','COMPLETED','CANCELLED')", name="ck_core_imaging_order_status"),
        CheckConstraint("priority IN ('ROUTINE','URGENT','STAT')", name="ck_core_imaging_order_priority"),
        CheckConstraint("version > 0", name="ck_core_imaging_order_version_positive"),
        Index("ix_core_imaging_order_scope_status", "organization_id", "facility_id", "workspace_id", "status", "created_at"),
        Index("ix_core_imaging_order_patient_created", "patient_person_id", "created_at"),
    )


class CoreImagingStudy(Base):  # type: ignore[misc]
    __tablename__ = "core_imaging_studies"

    id = Column(String(26), primary_key=True, default=_core_id)
    study_id = Column(String(26), nullable=False, unique=True, index=True)
    order_id = Column(String(26), ForeignKey("core_imaging_orders.id", ondelete="RESTRICT"), nullable=False, index=True)
    patient_person_id = Column(String(26), nullable=False, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    workspace_id = Column(String(26), nullable=False, index=True)
    study_instance_uid = Column(String(128), nullable=False, unique=True, index=True)
    accession_number = Column(String(80), nullable=False, index=True)
    modality = Column(String(32), nullable=False)
    study_description = Column(String(256), nullable=True)
    status = Column(String(24), nullable=False, default="RECEIVED", index=True)
    provenance_type = Column(String(32), nullable=False, default="SYNTHETIC_ADAPTER")
    source_message_id = Column(String(200), nullable=False, unique=True, index=True)
    quarantine_reason = Column(String(500), nullable=True)
    series_count = Column(Integer, nullable=False, default=0)
    instance_count = Column(Integer, nullable=False, default=0)
    version = Column(Integer, nullable=False, default=1)
    received_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        CheckConstraint("status IN ('RECEIVED','MATCHED','ACQUIRED','COMPLETED','QUARANTINED')", name="ck_core_imaging_study_status"),
        CheckConstraint("provenance_type IN ('SYNTHETIC_ADAPTER','DICOMWEB_ADAPTER','PACS_ADAPTER')", name="ck_core_imaging_study_provenance"),
        CheckConstraint("series_count >= 0", name="ck_core_imaging_study_series_nonnegative"),
        CheckConstraint("instance_count >= 0", name="ck_core_imaging_study_instances_nonnegative"),
        CheckConstraint("version > 0", name="ck_core_imaging_study_version_positive"),
        Index("ix_core_imaging_study_scope_status", "organization_id", "facility_id", "workspace_id", "status", "received_at"),
        Index("ix_core_imaging_study_patient_time", "patient_person_id", "received_at"),
    )


class CoreImagingReport(Base):  # type: ignore[misc]
    """Report version rows; signed/released content is never edited in place."""

    __tablename__ = "core_imaging_reports"

    id = Column(String(26), primary_key=True, default=_core_id)
    report_id = Column(String(26), nullable=False, index=True)
    study_id = Column(String(26), ForeignKey("core_imaging_studies.id", ondelete="RESTRICT"), nullable=False, index=True)
    patient_person_id = Column(String(26), nullable=False, index=True)
    ordering_provider_account_id = Column(String(26), nullable=False, index=True)
    radiologist_account_id = Column(String(26), nullable=False, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    workspace_id = Column(String(26), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    status = Column(String(24), nullable=False, default="DRAFT", index=True)
    findings = Column(Text, nullable=True)
    impression = Column(Text, nullable=True)
    critical = Column(Integer, nullable=False, default=0)
    supersedes_id = Column(String(26), nullable=True, index=True)
    amendment_reason = Column(String(500), nullable=True)
    signed_at = Column(DateTime(timezone=True), nullable=True)
    released_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    __table_args__ = (
        UniqueConstraint("report_id", "version", name="uq_core_imaging_report_version"),
        CheckConstraint("status IN ('DRAFT','SIGNED','RELEASED','AMENDED')", name="ck_core_imaging_report_status"),
        CheckConstraint("critical IN (0,1)", name="ck_core_imaging_report_critical_bool"),
        CheckConstraint("version > 0", name="ck_core_imaging_report_version_positive"),
        Index("ix_core_imaging_report_scope_status", "organization_id", "facility_id", "workspace_id", "status", "created_at"),
        Index("ix_core_imaging_report_patient_time", "patient_person_id", "created_at"),
    )


class CoreImagingInstance(Base):  # type: ignore[misc]
    """DICOM metadata only; object storage/PACS holds the binary outside Postgres."""

    __tablename__ = "core_imaging_instances"

    id = Column(String(26), primary_key=True, default=_core_id)
    study_id = Column(String(26), ForeignKey("core_imaging_studies.id", ondelete="RESTRICT"), nullable=False)
    series_instance_uid = Column(String(128), nullable=False)
    sop_instance_uid = Column(String(128), nullable=False)
    patient_person_id = Column(String(26), nullable=False, index=True)
    provenance_type = Column(String(32), nullable=False)
    source_message_id = Column(String(200), nullable=False)
    object_reference = Column(String(512), nullable=False)
    checksum = Column(String(128), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    __table_args__ = (
        UniqueConstraint("sop_instance_uid", name="uq_core_imaging_instance_sop"),
        UniqueConstraint("source_message_id", name="uq_core_imaging_instance_message"),
        CheckConstraint("file_size_bytes > 0", name="ck_core_imaging_instance_size_positive"),
        CheckConstraint("object_reference NOT LIKE 'http://%' AND object_reference NOT LIKE 'https://%'", name="ck_core_imaging_instance_no_public_url"),
        Index("ix_core_imaging_instance_study_series", "study_id", "series_instance_uid"),
    )


class CoreImagingCriticalEvent(Base):  # type: ignore[misc]
    __tablename__ = "core_imaging_critical_events"

    id = Column(String(26), primary_key=True, default=_core_id)
    report_id = Column(String(26), ForeignKey("core_imaging_reports.id", ondelete="RESTRICT"), nullable=False, unique=True, index=True)
    patient_person_id = Column(String(26), nullable=False, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    workspace_id = Column(String(26), nullable=False, index=True)
    status = Column(String(24), nullable=False, default="DETECTED", index=True)
    severity = Column(String(16), nullable=False, default="CRITICAL")
    required_action = Column(String(500), nullable=False)
    acknowledged_by_account_id = Column(String(26), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    __table_args__ = (
        CheckConstraint("status IN ('DETECTED','NOTIFIED','ACKNOWLEDGED','CLOSED')", name="ck_core_imaging_critical_status"),
        CheckConstraint("severity IN ('HIGH','CRITICAL')", name="ck_core_imaging_critical_severity"),
        CheckConstraint("version > 0", name="ck_core_imaging_critical_version_positive"),
    )
