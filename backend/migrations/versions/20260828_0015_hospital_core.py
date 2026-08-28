"""Add the canonical Hospital Core slice.

This revision is additive. It does not alter or delete legacy hospital, EMS,
patient, identity, medication, or clinical-record tables.
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "20260828_0015"
down_revision: str | None = "20260828_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _inspector():
    return inspect(op.get_bind())


def _table_exists(table: str) -> bool:
    return _inspector().has_table(table)


def _index_exists(table: str, name: str) -> bool:
    return _table_exists(table) and any(item.get("name") == name for item in _inspector().get_indexes(table))


def _index(name: str, table: str, columns: list[str]) -> None:
    if not _index_exists(table, name):
        op.create_index(name, table, columns, unique=False)


def _scope_fks() -> list[sa.ForeignKeyConstraint]:
    return [
        sa.ForeignKeyConstraint(["organization_id"], ["niam_organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["facility_id"], ["niam_admin_facilities.id"], ondelete="RESTRICT"),
    ]


def upgrade() -> None:
    if not _table_exists("core_hospital_facilities"):
        op.create_table(
            "core_hospital_facilities",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("organization_id", sa.String(26), nullable=False),
            sa.Column("facility_id", sa.String(26), nullable=False),
            sa.Column("name", sa.String(240), nullable=False),
            sa.Column("status", sa.String(24), nullable=False, server_default="ACTIVE"),
            sa.Column("metadata", sa.JSON()),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            *_scope_fks(),
            sa.UniqueConstraint("organization_id", "facility_id", name="uq_core_hospital_facility_scope"),
            sa.CheckConstraint("status IN ('ACTIVE','INACTIVE','SUSPENDED')", name="ck_core_hospital_facility_status"),
            sa.CheckConstraint("version > 0", name="ck_core_hospital_facility_version"),
        )
    _index("ix_core_hospital_facility_org", "core_hospital_facilities", ["organization_id", "facility_id", "status"])

    if not _table_exists("core_hospital_wards"):
        op.create_table(
            "core_hospital_wards",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("facility_id", sa.String(26), nullable=False),
            sa.Column("organization_id", sa.String(26), nullable=False),
            sa.Column("department_id", sa.String(26)),
            sa.Column("code", sa.String(80), nullable=False),
            sa.Column("name", sa.String(240), nullable=False),
            sa.Column("status", sa.String(24), nullable=False, server_default="ACTIVE"),
            sa.Column("capacity", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("metadata", sa.JSON()),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            *_scope_fks(),
            sa.UniqueConstraint("facility_id", "code", name="uq_core_hospital_ward_facility_code"),
            sa.CheckConstraint("capacity >= 0", name="ck_core_hospital_ward_capacity"),
            sa.CheckConstraint("status IN ('ACTIVE','INACTIVE','CLOSED')", name="ck_core_hospital_ward_status"),
            sa.CheckConstraint("version > 0", name="ck_core_hospital_ward_version"),
        )
    _index("ix_core_hospital_ward_scope_status", "core_hospital_wards", ["organization_id", "facility_id", "status"])

    if not _table_exists("core_hospital_rooms"):
        op.create_table(
            "core_hospital_rooms",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("ward_id", sa.String(26), nullable=False),
            sa.Column("facility_id", sa.String(26), nullable=False),
            sa.Column("organization_id", sa.String(26), nullable=False),
            sa.Column("code", sa.String(80), nullable=False),
            sa.Column("name", sa.String(240), nullable=False),
            sa.Column("capacity", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("status", sa.String(24), nullable=False, server_default="ACTIVE"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["ward_id"], ["core_hospital_wards.id"], ondelete="RESTRICT"),
            *_scope_fks(),
            sa.UniqueConstraint("ward_id", "code", name="uq_core_hospital_room_ward_code"),
            sa.CheckConstraint("capacity > 0", name="ck_core_hospital_room_capacity"),
            sa.CheckConstraint("status IN ('ACTIVE','INACTIVE','CLOSED')", name="ck_core_hospital_room_status"),
        )

    if not _table_exists("core_hospital_beds"):
        op.create_table(
            "core_hospital_beds",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("room_id", sa.String(26), nullable=False),
            sa.Column("ward_id", sa.String(26), nullable=False),
            sa.Column("facility_id", sa.String(26), nullable=False),
            sa.Column("organization_id", sa.String(26), nullable=False),
            sa.Column("code", sa.String(80), nullable=False),
            sa.Column("bed_type", sa.String(48), nullable=False, server_default="STANDARD"),
            sa.Column("status", sa.String(24), nullable=False, server_default="AVAILABLE"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("metadata", sa.JSON()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["room_id"], ["core_hospital_rooms.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["ward_id"], ["core_hospital_wards.id"], ondelete="RESTRICT"),
            *_scope_fks(),
            sa.UniqueConstraint("room_id", "code", name="uq_core_hospital_bed_room_code"),
            sa.CheckConstraint("status IN ('AVAILABLE','RESERVED','OCCUPIED','CLEANING','MAINTENANCE','BLOCKED')", name="ck_core_hospital_bed_status"),
            sa.CheckConstraint("version > 0", name="ck_core_hospital_bed_version"),
        )
    _index("ix_core_hospital_bed_board", "core_hospital_beds", ["organization_id", "facility_id", "ward_id", "status"])

    if not _table_exists("core_hospital_admissions"):
        op.create_table(
            "core_hospital_admissions",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("admission_request_id", sa.String(64), nullable=False, unique=True),
            sa.Column("patient_person_id", sa.String(26), nullable=False),
            sa.Column("encounter_id", sa.String(26), nullable=False),
            sa.Column("facility_id", sa.String(26), nullable=False),
            sa.Column("organization_id", sa.String(26), nullable=False),
            sa.Column("ward_id", sa.String(26), nullable=False),
            sa.Column("admitting_provider_account_id", sa.String(26), nullable=False),
            sa.Column("admission_reason", sa.Text(), nullable=False),
            sa.Column("admission_type", sa.String(24), nullable=False, server_default="ELECTIVE"),
            sa.Column("status", sa.String(32), nullable=False, server_default="REQUESTED"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("admitted_at", sa.DateTime(timezone=True)),
            sa.Column("discharged_at", sa.DateTime(timezone=True)),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["encounter_id"], ["core_encounters.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["patient_person_id"], ["niam_persons.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["admitting_provider_account_id"], ["niam_accounts.id"], ondelete="RESTRICT"),
            *_scope_fks(),
            sa.ForeignKeyConstraint(["ward_id"], ["core_hospital_wards.id"], ondelete="RESTRICT"),
            sa.CheckConstraint("admission_type IN ('EMERGENCY','ELECTIVE','TRANSFER','OBSERVATION')", name="ck_core_admission_type"),
            sa.CheckConstraint("status IN ('REQUESTED','ACCEPTED','ADMITTED','IN_CARE','DISCHARGE_PLANNED','DISCHARGED','CANCELLED','REJECTED','TRANSFERRED')", name="ck_core_admission_status"),
            sa.CheckConstraint("version > 0", name="ck_core_admission_version"),
        )
    _index("ix_core_admission_patient_time", "core_hospital_admissions", ["patient_person_id", "created_at"])
    _index("ix_core_admission_scope_status", "core_hospital_admissions", ["organization_id", "facility_id", "ward_id", "status"])

    if not _table_exists("core_hospital_bed_allocations"):
        op.create_table(
            "core_hospital_bed_allocations",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("admission_id", sa.String(26), nullable=False),
            sa.Column("patient_person_id", sa.String(26), nullable=False),
            sa.Column("bed_id", sa.String(26), nullable=False),
            sa.Column("ward_id", sa.String(26), nullable=False),
            sa.Column("facility_id", sa.String(26), nullable=False),
            sa.Column("organization_id", sa.String(26), nullable=False),
            sa.Column("allocated_by_account_id", sa.String(26), nullable=False),
            sa.Column("allocated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("released_at", sa.DateTime(timezone=True)),
            sa.Column("release_reason", sa.String(500)),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["admission_id"], ["core_hospital_admissions.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["bed_id"], ["core_hospital_beds.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["allocated_by_account_id"], ["niam_accounts.id"], ondelete="RESTRICT"),
            *_scope_fks(),
            sa.CheckConstraint("version > 0", name="ck_core_bed_allocation_version"),
        )
    _index("ix_core_bed_allocation_active_bed", "core_hospital_bed_allocations", ["bed_id", "released_at"])
    _index("ix_core_bed_allocation_active_patient", "core_hospital_bed_allocations", ["patient_person_id", "released_at"])

    if not _table_exists("core_hospital_care_team_members"):
        op.create_table(
            "core_hospital_care_team_members",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("admission_id", sa.String(26), nullable=False),
            sa.Column("patient_person_id", sa.String(26), nullable=False),
            sa.Column("account_id", sa.String(26), nullable=False),
            sa.Column("role", sa.String(40), nullable=False),
            sa.Column("scope", sa.String(240), nullable=False),
            sa.Column("purpose", sa.String(120), nullable=False),
            sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("ends_at", sa.DateTime(timezone=True)),
            sa.Column("status", sa.String(24), nullable=False, server_default="ACTIVE"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["admission_id"], ["core_hospital_admissions.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["account_id"], ["niam_accounts.id"], ondelete="RESTRICT"),
            sa.CheckConstraint("status IN ('ACTIVE','ENDED','REVOKED')", name="ck_core_care_team_status"),
            sa.CheckConstraint("version > 0", name="ck_core_care_team_version"),
        )
    _index("ix_core_care_team_patient_active", "core_hospital_care_team_members", ["patient_person_id", "status"])

    if not _table_exists("core_hospital_nursing_tasks"):
        op.create_table(
            "core_hospital_nursing_tasks",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("admission_id", sa.String(26), nullable=False),
            sa.Column("patient_person_id", sa.String(26), nullable=False),
            sa.Column("ward_id", sa.String(26), nullable=False),
            sa.Column("facility_id", sa.String(26), nullable=False),
            sa.Column("organization_id", sa.String(26), nullable=False),
            sa.Column("task_type", sa.String(80), nullable=False),
            sa.Column("instructions", sa.Text()),
            sa.Column("status", sa.String(24), nullable=False, server_default="OPEN"),
            sa.Column("assigned_to_account_id", sa.String(26)),
            sa.Column("claimed_at", sa.DateTime(timezone=True)),
            sa.Column("completed_at", sa.DateTime(timezone=True)),
            sa.Column("completion_note", sa.Text()),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["admission_id"], ["core_hospital_admissions.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["ward_id"], ["core_hospital_wards.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["assigned_to_account_id"], ["niam_accounts.id"], ondelete="SET NULL"),
            *_scope_fks(),
            sa.CheckConstraint("status IN ('OPEN','CLAIMED','IN_PROGRESS','COMPLETED','CANCELLED','DEFERRED')", name="ck_core_nursing_task_status"),
            sa.CheckConstraint("version > 0", name="ck_core_nursing_task_version"),
        )
    _index("ix_core_nursing_task_board", "core_hospital_nursing_tasks", ["organization_id", "facility_id", "ward_id", "status"])

    if not _table_exists("core_hospital_vital_observations"):
        op.create_table(
            "core_hospital_vital_observations",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("patient_person_id", sa.String(26), nullable=False),
            sa.Column("encounter_id", sa.String(26), nullable=False),
            sa.Column("admission_id", sa.String(26)),
            sa.Column("observer_account_id", sa.String(26), nullable=False),
            sa.Column("device_reference", sa.String(160)),
            sa.Column("vital_type", sa.String(64), nullable=False),
            sa.Column("value_numeric", sa.String(64), nullable=False),
            sa.Column("unit", sa.String(40), nullable=False),
            sa.Column("method", sa.String(80), nullable=False),
            sa.Column("source", sa.String(80), nullable=False, server_default="MANUAL"),
            sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("validation_status", sa.String(24), nullable=False, server_default="VALID"),
            sa.Column("warning_code", sa.String(80)),
            sa.Column("metadata", sa.JSON()),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["encounter_id"], ["core_encounters.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["observer_account_id"], ["niam_accounts.id"], ondelete="RESTRICT"),
            sa.CheckConstraint("validation_status IN ('VALID','WARNING','REJECTED')", name="ck_core_vital_validation_status"),
            sa.CheckConstraint("version > 0", name="ck_core_vital_version"),
        )
    _index("ix_core_vital_patient_time", "core_hospital_vital_observations", ["patient_person_id", "observed_at", "id"])

    if not _table_exists("core_hospital_medication_administrations"):
        op.create_table(
            "core_hospital_medication_administrations",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("administration_key", sa.String(120), nullable=False, unique=True),
            sa.Column("admission_id", sa.String(26), nullable=False),
            sa.Column("patient_person_id", sa.String(26), nullable=False),
            sa.Column("encounter_id", sa.String(26), nullable=False),
            sa.Column("prescription_id", sa.String(26), nullable=False),
            sa.Column("prescription_item_id", sa.String(26), nullable=False),
            sa.Column("medication_catalog_id", sa.String(26), nullable=False),
            sa.Column("administrator_account_id", sa.String(26), nullable=False),
            sa.Column("dose_value", sa.String(80), nullable=False),
            sa.Column("dose_unit", sa.String(40), nullable=False),
            sa.Column("route", sa.String(80), nullable=False),
            sa.Column("scheduled_at", sa.DateTime(timezone=True)),
            sa.Column("administered_at", sa.DateTime(timezone=True)),
            sa.Column("status", sa.String(24), nullable=False, server_default="ORDERED"),
            sa.Column("reason", sa.Text()),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["admission_id"], ["core_hospital_admissions.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["prescription_id"], ["core_prescriptions.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["prescription_item_id"], ["core_prescription_items.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["medication_catalog_id"], ["core_medication_catalog.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["administrator_account_id"], ["niam_accounts.id"], ondelete="RESTRICT"),
            sa.CheckConstraint("status IN ('ORDERED','VERIFIED','SCHEDULED','ADMINISTERED','HELD','REFUSED','MISSED','CANCELLED')", name="ck_core_emar_status"),
            sa.CheckConstraint("version > 0", name="ck_core_emar_version"),
        )
    _index("ix_core_emar_patient_time", "core_hospital_medication_administrations", ["patient_person_id", "created_at"])

    if not _table_exists("core_hospital_medication_safety_events"):
        op.create_table(
            "core_hospital_medication_safety_events",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("administration_id", sa.String(26), nullable=False),
            sa.Column("patient_person_id", sa.String(26), nullable=False),
            sa.Column("event_type", sa.String(80), nullable=False),
            sa.Column("severity", sa.String(24), nullable=False, server_default="LOW"),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("reported_by_account_id", sa.String(26), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["administration_id"], ["core_hospital_medication_administrations.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["reported_by_account_id"], ["niam_accounts.id"], ondelete="RESTRICT"),
            sa.CheckConstraint("severity IN ('LOW','MEDIUM','HIGH','CRITICAL')", name="ck_core_med_safety_severity"),
        )

    if not _table_exists("core_hospital_transfers"):
        op.create_table(
            "core_hospital_transfers",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("transfer_request_id", sa.String(100), nullable=False, unique=True),
            sa.Column("admission_id", sa.String(26), nullable=False),
            sa.Column("patient_person_id", sa.String(26), nullable=False),
            sa.Column("from_ward_id", sa.String(26), nullable=False),
            sa.Column("to_ward_id", sa.String(26), nullable=False),
            sa.Column("from_bed_id", sa.String(26)),
            sa.Column("to_bed_id", sa.String(26)),
            sa.Column("facility_id", sa.String(26), nullable=False),
            sa.Column("organization_id", sa.String(26), nullable=False),
            sa.Column("requested_by_account_id", sa.String(26), nullable=False),
            sa.Column("status", sa.String(24), nullable=False, server_default="REQUESTED"),
            sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("completed_at", sa.DateTime(timezone=True)),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["admission_id"], ["core_hospital_admissions.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["from_ward_id"], ["core_hospital_wards.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["to_ward_id"], ["core_hospital_wards.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["from_bed_id"], ["core_hospital_beds.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["to_bed_id"], ["core_hospital_beds.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["requested_by_account_id"], ["niam_accounts.id"], ondelete="RESTRICT"),
            *_scope_fks(),
            sa.CheckConstraint("status IN ('REQUESTED','ACCEPTED','PREPARING','IN_TRANSIT','RECEIVED','COMPLETED','CANCELLED','REJECTED')", name="ck_core_transfer_status"),
            sa.CheckConstraint("version > 0", name="ck_core_transfer_version"),
        )
    _index("ix_core_transfer_patient_status", "core_hospital_transfers", ["patient_person_id", "status"])

    if not _table_exists("core_hospital_handovers"):
        op.create_table(
            "core_hospital_handovers",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("handover_request_id", sa.String(100), nullable=False, unique=True),
            sa.Column("admission_id", sa.String(26), nullable=False),
            sa.Column("patient_person_id", sa.String(26), nullable=False),
            sa.Column("sender_account_id", sa.String(26), nullable=False),
            sa.Column("receiver_account_id", sa.String(26)),
            sa.Column("status", sa.String(24), nullable=False, server_default="SUBMITTED"),
            sa.Column("minimal_summary", sa.JSON(), nullable=False),
            sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("acknowledged_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["admission_id"], ["core_hospital_admissions.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["sender_account_id"], ["niam_accounts.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["receiver_account_id"], ["niam_accounts.id"], ondelete="SET NULL"),
            sa.CheckConstraint("status IN ('SUBMITTED','ACKNOWLEDGED','AMENDED','CANCELLED')", name="ck_core_handover_status"),
            sa.CheckConstraint("version > 0", name="ck_core_handover_version"),
        )

    if not _table_exists("core_hospital_discharges"):
        op.create_table(
            "core_hospital_discharges",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("discharge_request_id", sa.String(100), nullable=False, unique=True),
            sa.Column("admission_id", sa.String(26), nullable=False),
            sa.Column("patient_person_id", sa.String(26), nullable=False),
            sa.Column("facility_id", sa.String(26), nullable=False),
            sa.Column("organization_id", sa.String(26), nullable=False),
            sa.Column("responsible_provider_account_id", sa.String(26), nullable=False),
            sa.Column("disposition", sa.String(32), nullable=False, server_default="HOME"),
            sa.Column("status", sa.String(24), nullable=False, server_default="PLANNED"),
            sa.Column("medication_reconciliation_complete", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("pending_results_reviewed", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("follow_up_plan", sa.Text()),
            sa.Column("instructions", sa.Text()),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("planned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("completed_at", sa.DateTime(timezone=True)),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["admission_id"], ["core_hospital_admissions.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["responsible_provider_account_id"], ["niam_accounts.id"], ondelete="RESTRICT"),
            *_scope_fks(),
            sa.CheckConstraint("disposition IN ('HOME','TRANSFER','OTHER_FACILITY','DEATH')", name="ck_core_discharge_disposition"),
            sa.CheckConstraint("status IN ('PLANNED','APPROVED','COMPLETED','CANCELLED')", name="ck_core_discharge_status"),
            sa.CheckConstraint("medication_reconciliation_complete IN (0,1)", name="ck_core_discharge_med_recon"),
            sa.CheckConstraint("pending_results_reviewed IN (0,1)", name="ck_core_discharge_results_reviewed"),
            sa.CheckConstraint("version > 0", name="ck_core_discharge_version"),
        )

    if not _table_exists("core_hospital_discharge_summaries"):
        op.create_table(
            "core_hospital_discharge_summaries",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("discharge_id", sa.String(26), nullable=False),
            sa.Column("summary_version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("status", sa.String(24), nullable=False, server_default="DRAFT"),
            sa.Column("admission_reason", sa.Text(), nullable=False),
            sa.Column("diagnoses", sa.JSON(), nullable=False),
            sa.Column("procedures", sa.JSON(), nullable=False),
            sa.Column("treatment", sa.Text(), nullable=False),
            sa.Column("medications", sa.JSON(), nullable=False),
            sa.Column("results", sa.JSON(), nullable=False),
            sa.Column("condition", sa.Text(), nullable=False),
            sa.Column("follow_up", sa.Text()),
            sa.Column("authored_by_account_id", sa.String(26), nullable=False),
            sa.Column("signed_at", sa.DateTime(timezone=True)),
            sa.Column("signed_by_account_id", sa.String(26)),
            sa.Column("correction_reason", sa.Text()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["discharge_id"], ["core_hospital_discharges.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["authored_by_account_id"], ["niam_accounts.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["signed_by_account_id"], ["niam_accounts.id"], ondelete="SET NULL"),
            sa.CheckConstraint("status IN ('DRAFT','SIGNED','AMENDED')", name="ck_core_discharge_summary_status"),
            sa.CheckConstraint("summary_version > 0", name="ck_core_discharge_summary_version"),
            sa.UniqueConstraint("discharge_id", "summary_version", name="uq_core_discharge_summary_version"),
        )

    permissions = (
        ("P15HOSPADM000000001", "clinical.hospital.admission.create", "Create hospital admission", "إنشاء قبول مستشفى", "hospital_admission", "create"),
        ("P15HOSPTRANS0000001", "clinical.hospital.admission.transition", "Transition hospital admission", "تغيير حالة قبول المستشفى", "hospital_admission", "transition"),
        ("P15HOSPBED000000001", "clinical.hospital.bed.allocate", "Allocate hospital bed", "تخصيص سرير مستشفى", "hospital_bed", "allocate"),
        ("P15HOSPTASK0000001", "clinical.hospital.task.write", "Manage nursing tasks", "إدارة مهام التمريض", "hospital_task", "write"),
        ("P15HOSPVITAL0000001", "clinical.hospital.vitals.write", "Record hospital vitals", "تسجيل العلامات الحيوية", "hospital_vital", "write"),
        ("P15HOSPemar0000001", "clinical.hospital.emar.write", "Manage medication administration", "إدارة إعطاء الدواء", "hospital_emar", "write"),
        ("P15HOSPTRNS0000001", "clinical.hospital.transfer.write", "Manage patient transfers", "إدارة نقل المريض", "hospital_transfer", "write"),
        ("P15HOSPHAND0000001", "clinical.hospital.handover.write", "Manage clinical handover", "إدارة تسليم الرعاية", "hospital_handover", "write"),
        ("P15HOSPDISC0000001", "clinical.hospital.discharge.write", "Manage discharge", "إدارة الخروج", "hospital_discharge", "write"),
        ("P15HOSPSIGN0000001", "clinical.hospital.discharge.sign", "Sign discharge summary", "توقيع ملخص الخروج", "hospital_discharge_summary", "sign"),
    )
    for index, row in enumerate(permissions):
        exists = op.get_bind().execute(sa.text("SELECT 1 FROM niam_permissions WHERE permission_key = :permission_key"), {"permission_key": row[1]}).scalar()
        if not exists:
            op.get_bind().execute(
                sa.text("INSERT INTO niam_permissions (id, uuid, permission_key, name, name_ar, description, resource, action, sensitivity, status, version, created_at, updated_at) VALUES (:id, :uuid, :permission_key, :name, :name_ar, :description, :resource, :action, 'high', 'active', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"),
                {"id": row[0], "uuid": f"p15-hospital-{index:02d}", "permission_key": row[1], "name": row[2], "name_ar": row[3], "description": row[2], "resource": row[4], "action": row[5]},
            )


def downgrade() -> None:
    for table in (
        "core_hospital_discharge_summaries",
        "core_hospital_discharges",
        "core_hospital_handovers",
        "core_hospital_transfers",
        "core_hospital_medication_safety_events",
        "core_hospital_medication_administrations",
        "core_hospital_vital_observations",
        "core_hospital_nursing_tasks",
        "core_hospital_care_team_members",
        "core_hospital_bed_allocations",
        "core_hospital_admissions",
        "core_hospital_beds",
        "core_hospital_rooms",
        "core_hospital_wards",
        "core_hospital_facilities",
    ):
        if _table_exists(table):
            op.drop_table(table)
