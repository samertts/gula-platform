from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    Date,
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


class CoreMedicationCatalog(Base):  # type: ignore[misc]
    """Canonical medication identity; not a prescription or a stock record."""

    __tablename__ = "core_medication_catalog"

    id = Column(String(26), primary_key=True, default=_core_id)
    code = Column(String(120), nullable=False, unique=True)
    code_system = Column(String(80), nullable=False, default="SYNTHETIC")
    generic_name = Column(String(300), nullable=False)
    brand_name = Column(String(300), nullable=True)
    strength_value = Column(String(80), nullable=True)
    strength_unit = Column(String(40), nullable=True)
    dosage_form = Column(String(80), nullable=True)
    route = Column(String(80), nullable=True)
    is_controlled = Column(Integer, nullable=False, default=0)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    __table_args__ = (
        CheckConstraint("is_controlled IN (0,1)", name="ck_core_medication_controlled_bool"),
        CheckConstraint("is_active IN (0,1)", name="ck_core_medication_active_bool"),
        Index("ix_core_medication_active_name", "is_active", "generic_name"),
    )


class CorePrescription(Base):  # type: ignore[misc]
    """Versioned prescription aggregate. Signed rows are immutable."""

    __tablename__ = "core_prescriptions"

    id = Column(String(26), primary_key=True, default=_core_id)
    prescription_id = Column(String(26), nullable=False, index=True)
    prescription_number = Column(String(80), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    encounter_id = Column(String(26), nullable=False, index=True)
    patient_person_id = Column(String(26), nullable=False, index=True)
    prescriber_account_id = Column(String(26), nullable=False, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    workspace_id = Column(String(26), nullable=False, index=True)
    status = Column(String(24), nullable=False, default="DRAFT", index=True)
    purpose = Column(String(40), nullable=False, default="treatment")
    controlled_policy_status = Column(String(32), nullable=False, default="NOT_CONTROLLED")
    # Identity tables use a separate SQLAlchemy metadata; the database migration owns this FK.
    controlled_policy_approved_by_account_id = Column(String(26), nullable=True)
    controlled_policy_approved_at = Column(DateTime(timezone=True), nullable=True)
    controlled_policy_reason = Column(String(500), nullable=True)
    controlled_policy_evidence = Column(JSON, nullable=True)
    signed_by_account_id = Column(String(26), nullable=True)
    signed_at = Column(DateTime(timezone=True), nullable=True)
    supersedes_id = Column(String(26), nullable=True, index=True)
    amendment_reason = Column(String(500), nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    __table_args__ = (
        UniqueConstraint("prescription_id", "version", name="uq_core_prescription_version"),
        UniqueConstraint("prescription_number", "version", name="uq_core_prescription_number_version"),
        CheckConstraint("version > 0", name="ck_core_prescription_version_positive"),
        CheckConstraint("status IN ('DRAFT','SIGNED','AMENDED','CANCELLED','COMPLETED')", name="ck_core_prescription_status"),
        CheckConstraint("controlled_policy_status IN ('NOT_CONTROLLED','PENDING_POLICY_REVIEW','APPROVED_BY_POLICY','REJECTED_BY_POLICY')", name="ck_core_prescription_controlled_policy"),
        Index("ix_core_prescription_scope_status", "organization_id", "facility_id", "workspace_id", "status", "created_at"),
        Index("ix_core_prescription_patient_created", "patient_person_id", "created_at"),
    )


class CorePrescriptionItem(Base):  # type: ignore[misc]
    """Snapshot of the medication identity and directions for one prescription version."""

    __tablename__ = "core_prescription_items"

    id = Column(String(26), primary_key=True, default=_core_id)
    prescription_row_id = Column(String(26), ForeignKey("core_prescriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    medication_catalog_id = Column(String(26), ForeignKey("core_medication_catalog.id", ondelete="RESTRICT"), nullable=False, index=True)
    medication_code = Column(String(120), nullable=False)
    medication_name = Column(String(300), nullable=False)
    dose_value = Column(String(80), nullable=False)
    dose_unit = Column(String(40), nullable=False)
    frequency = Column(String(120), nullable=False)
    route = Column(String(80), nullable=False)
    duration_days = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    quantity_unit = Column(String(40), nullable=False)
    substitution_allowed = Column(Integer, nullable=False, default=0)
    instructions = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    __table_args__ = (
        CheckConstraint("duration_days > 0", name="ck_core_prescription_item_duration_positive"),
        CheckConstraint("quantity > 0", name="ck_core_prescription_item_quantity_positive"),
        CheckConstraint("substitution_allowed = 0", name="ck_core_prescription_item_no_auto_substitution"),
        Index("ix_core_prescription_item_row", "prescription_row_id", "created_at"),
    )


class CoreMedicationBatch(Base):  # type: ignore[misc]
    """Facility-scoped batch balance; quantity is changed only with a ledger entry."""

    __tablename__ = "core_medication_batches"

    id = Column(String(26), primary_key=True, default=_core_id)
    medication_catalog_id = Column(String(26), ForeignKey("core_medication_catalog.id", ondelete="RESTRICT"), nullable=False, index=True)
    batch_number = Column(String(120), nullable=False)
    organization_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    workspace_id = Column(String(26), nullable=False, index=True)
    expiry_date = Column(Date, nullable=False, index=True)
    quantity_received = Column(Integer, nullable=False)
    quantity_available = Column(Integer, nullable=False)
    quarantined = Column(Integer, nullable=False, default=0)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    __table_args__ = (
        UniqueConstraint("facility_id", "medication_catalog_id", "batch_number", name="uq_core_medication_batch_facility"),
        CheckConstraint("quantity_received >= 0", name="ck_core_medication_batch_received_nonnegative"),
        CheckConstraint("quantity_available >= 0", name="ck_core_medication_batch_available_nonnegative"),
        CheckConstraint("quantity_available <= quantity_received", name="ck_core_medication_batch_available_lte_received"),
        CheckConstraint("quarantined IN (0,1)", name="ck_core_medication_batch_quarantine_bool"),
        CheckConstraint("version > 0", name="ck_core_medication_batch_version_positive"),
        Index("ix_core_medication_batch_scope_expiry", "organization_id", "facility_id", "workspace_id", "expiry_date"),
    )


class CoreMedicationStockLedger(Base):  # type: ignore[misc]
    """Append-only stock movement ledger; no update/delete API exists."""

    __tablename__ = "core_medication_stock_ledger"

    id = Column(String(26), primary_key=True, default=_core_id)
    batch_id = Column(String(26), ForeignKey("core_medication_batches.id", ondelete="RESTRICT"), nullable=False, index=True)
    medication_catalog_id = Column(String(26), ForeignKey("core_medication_catalog.id", ondelete="RESTRICT"), nullable=False, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    workspace_id = Column(String(26), nullable=False, index=True)
    movement_type = Column(String(32), nullable=False)
    quantity_delta = Column(Integer, nullable=False)
    reference_type = Column(String(64), nullable=False)
    reference_id = Column(String(26), nullable=False, index=True)
    actor_account_id = Column(String(26), nullable=False, index=True)
    correlation_id = Column(String(128), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now, index=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        CheckConstraint("quantity_delta <> 0", name="ck_core_stock_ledger_delta_nonzero"),
        CheckConstraint("movement_type IN ('RECEIPT','DISPENSE','ADJUSTMENT_REVERSAL')", name="ck_core_stock_ledger_movement"),
        Index("ix_core_stock_ledger_batch_time", "batch_id", "created_at", "id"),
    )


class CoreDispense(Base):  # type: ignore[misc]
    """A completed or partially completed dispense linked to one signed item."""

    __tablename__ = "core_medication_dispenses"

    id = Column(String(26), primary_key=True, default=_core_id)
    prescription_row_id = Column(String(26), ForeignKey("core_prescriptions.id", ondelete="RESTRICT"), nullable=False, index=True)
    prescription_item_id = Column(String(26), ForeignKey("core_prescription_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    patient_person_id = Column(String(26), nullable=False, index=True)
    medication_catalog_id = Column(String(26), ForeignKey("core_medication_catalog.id", ondelete="RESTRICT"), nullable=False, index=True)
    batch_id = Column(String(26), ForeignKey("core_medication_batches.id", ondelete="RESTRICT"), nullable=False, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    workspace_id = Column(String(26), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    status = Column(String(24), nullable=False, default="PREPARED", index=True)
    prepared_by_account_id = Column(String(26), nullable=False, index=True)
    dispensed_by_account_id = Column(String(26), nullable=True, index=True)
    verified_by_account_id = Column(String(26), nullable=True, index=True)
    version = Column(Integer, nullable=False, default=1)
    correlation_id = Column(String(128), nullable=False, index=True)
    dispensed_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_core_dispense_quantity_positive"),
        CheckConstraint("status IN ('PREPARED','PARTIAL','COMPLETED','REVERSED')", name="ck_core_dispense_status"),
        CheckConstraint("version > 0", name="ck_core_dispense_version_positive"),
        Index("ix_core_dispense_patient_time", "patient_person_id", "dispensed_at"),
        Index("ix_core_dispense_scope_time", "organization_id", "facility_id", "workspace_id", "dispensed_at"),
    )
