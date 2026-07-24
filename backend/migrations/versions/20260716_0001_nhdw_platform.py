"""Create NHDW (National Health Data Warehouse) platform tables.

Creates all NHDW domain entities:
  - nhdw_admissions, nhdw_discharges, nhdw_transfers
  - nhdw_queue_entries, nhdw_waiting_list_entries
  - nhdw_clinical_tasks, nhdw_ward_rounds, nhdw_care_plans
  - nhdw_hospital_alerts, nhdw_hospital_messages
  - nhdw_telemedicine_sessions, nhdw_resource_schedules
  - nhdw_dashboard_configurations, nhdw_shift_reports

Revision ID: 20260716_0001
Revises: 20260715_0001
Create Date: 2026-07-16
"""

from typing import Union
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import inspect

revision: str = "20260716_0001"
down_revision: str | None = "20260715_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def _index_exists(idx_name: str) -> bool:
    insp = inspect(op.get_bind())
    for table in insp.get_table_names():
        for idx in insp.get_indexes(table):
            if idx["name"] == idx_name:
                return True
    return False


def upgrade() -> None:
    # ── Admissions ────────────────────────────────────────────────────────────
    if not _table_exists("nhdw_admissions"):
        op.create_table(
            "nhdw_admissions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True),
            sa.Column("admission_number", sa.String(30), nullable=False),
            sa.Column("admission_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("admission_type", sa.String(30), nullable=False),
            sa.Column("admitting_doctor", sa.String(200), nullable=True),
            sa.Column("department", sa.String(100), nullable=True),
            sa.Column("ward", sa.String(100), nullable=True),
            sa.Column("bed_number", sa.String(20), nullable=True),
            sa.Column("diagnosis_code", sa.String(20), nullable=True),
            sa.Column("diagnosis_description", sa.Text(), nullable=True),
            sa.Column("referring_physician", sa.String(200), nullable=True),
            sa.Column("insurance_provider", sa.String(200), nullable=True),
            sa.Column("insurance_policy_number", sa.String(100), nullable=True),
            sa.Column("expected_discharge_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="active"),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("lab_id", "admission_number", name="uq_nhdw_admission_number"),
        )
        op.create_index("ix_nhdw_admissions_lab_id", "nhdw_admissions", ["lab_id"])
        op.create_index("ix_nhdw_admissions_patient_id", "nhdw_admissions", ["patient_id"])
        op.create_index("ix_nhdw_adm_lab_status", "nhdw_admissions", ["lab_id", "status"])
        op.create_index("ix_nhdw_admissions_admission_date", "nhdw_admissions", ["admission_date"])

    # ── Discharges ────────────────────────────────────────────────────────────
    if not _table_exists("nhdw_discharges"):
        op.create_table(
            "nhdw_discharges",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("admission_id", sa.Integer(), sa.ForeignKey("nhdw_admissions.id", ondelete="SET NULL"), nullable=True),
            sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True),
            sa.Column("discharge_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("discharge_type", sa.String(30), nullable=False),
            sa.Column("discharge_summary", sa.Text(), nullable=True),
            sa.Column("discharged_by", sa.String(200), nullable=True),
            sa.Column("follow_up_required", sa.Boolean(), default=False),
            sa.Column("follow_up_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("follow_up_notes", sa.Text(), nullable=True),
            sa.Column("discharge_medications", JSON(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_nhdw_discharges_lab_id", "nhdw_discharges", ["lab_id"])
        op.create_index("ix_nhdw_discharges_admission_id", "nhdw_discharges", ["admission_id"])
        op.create_index("ix_nhdw_discharges_patient_id", "nhdw_discharges", ["patient_id"])
        op.create_index("ix_nhdw_discharges_discharge_date", "nhdw_discharges", ["discharge_date"])

    # ── Transfers ─────────────────────────────────────────────────────────────
    if not _table_exists("nhdw_transfers"):
        op.create_table(
            "nhdw_transfers",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("admission_id", sa.Integer(), sa.ForeignKey("nhdw_admissions.id", ondelete="CASCADE"), nullable=False),
            sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True),
            sa.Column("from_ward", sa.String(100), nullable=True),
            sa.Column("from_bed", sa.String(20), nullable=True),
            sa.Column("to_ward", sa.String(100), nullable=False),
            sa.Column("to_bed", sa.String(20), nullable=True),
            sa.Column("transfer_reason", sa.Text(), nullable=True),
            sa.Column("transferred_by", sa.String(200), nullable=True),
            sa.Column("transferred_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("received_by", sa.String(200), nullable=True),
            sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_nhdw_transfers_lab_id", "nhdw_transfers", ["lab_id"])
        op.create_index("ix_nhdw_transfers_admission_id", "nhdw_transfers", ["admission_id"])
        op.create_index("ix_nhdw_transfers_patient_id", "nhdw_transfers", ["patient_id"])
        op.create_index("ix_nhdw_transfers_transferred_at", "nhdw_transfers", ["transferred_at"])

    # ── Queue Entries ─────────────────────────────────────────────────────────
    if not _table_exists("nhdw_queue_entries"):
        op.create_table(
            "nhdw_queue_entries",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True),
            sa.Column("queue_type", sa.String(30), nullable=False),
            sa.Column("queue_number", sa.String(20), nullable=False),
            sa.Column("priority", sa.Integer(), default=0),
            sa.Column("status", sa.String(20), nullable=False, server_default="waiting"),
            sa.Column("called_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("service_point", sa.String(100), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_nhdw_queue_lab_id", "nhdw_queue_entries", ["lab_id"])
        op.create_index("ix_nhdw_queue_patient_id", "nhdw_queue_entries", ["patient_id"])
        op.create_index("ix_nhdw_queue_lab_type_status", "nhdw_queue_entries", ["lab_id", "queue_type", "status"])
        op.create_index("ix_nhdw_queue_number", "nhdw_queue_entries", ["queue_number", "lab_id"], unique=True)

    # ── Waiting List Entries ──────────────────────────────────────────────────
    if not _table_exists("nhdw_waiting_list_entries"):
        op.create_table(
            "nhdw_waiting_list_entries",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True),
            sa.Column("waiting_list_type", sa.String(50), nullable=False),
            sa.Column("priority", sa.Integer(), default=0),
            sa.Column("status", sa.String(20), nullable=False, server_default="active"),
            sa.Column("referral_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("referral_source", sa.String(200), nullable=True),
            sa.Column("referring_physician", sa.String(200), nullable=True),
            sa.Column("clinical_need", sa.Text(), nullable=True),
            sa.Column("target_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("admitted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("cancellation_reason", sa.Text(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_nhdw_waitlist_lab_id", "nhdw_waiting_list_entries", ["lab_id"])
        op.create_index("ix_nhdw_waitlist_patient_id", "nhdw_waiting_list_entries", ["patient_id"])
        op.create_index("ix_nhdw_waitlist_lab_status", "nhdw_waiting_list_entries", ["lab_id", "status"])

    # ── Clinical Tasks ────────────────────────────────────────────────────────
    if not _table_exists("nhdw_clinical_tasks"):
        op.create_table(
            "nhdw_clinical_tasks",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True),
            sa.Column("assigned_to", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("task_type", sa.String(50), nullable=False),
            sa.Column("title", sa.String(300), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("priority", sa.String(20), default="normal"),
            sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
            sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("cancelled_reason", sa.Text(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_nhdw_clinical_tasks_lab_id", "nhdw_clinical_tasks", ["lab_id"])
        op.create_index("ix_nhdw_clinical_tasks_patient_id", "nhdw_clinical_tasks", ["patient_id"])
        op.create_index("ix_nhdw_clinical_tasks_assigned_to", "nhdw_clinical_tasks", ["assigned_to"])
        op.create_index("ix_nhdw_clinical_tasks_lab_status", "nhdw_clinical_tasks", ["lab_id", "status", "due_at"])

    # ── Ward Rounds ────────────────────────────────────────────────────────────
    if not _table_exists("nhdw_ward_rounds"):
        op.create_table(
            "nhdw_ward_rounds",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
            sa.Column("admission_id", sa.Integer(), sa.ForeignKey("nhdw_admissions.id", ondelete="SET NULL"), nullable=True),
            sa.Column("ward", sa.String(100), nullable=True),
            sa.Column("round_type", sa.String(50), nullable=False),
            sa.Column("round_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("conducted_by", sa.String(200), nullable=True),
            sa.Column("findings", sa.Text(), nullable=True),
            sa.Column("assessment", sa.Text(), nullable=True),
            sa.Column("plan", sa.Text(), nullable=True),
            sa.Column("medication_changes", JSON(), nullable=True),
            sa.Column("investigation_orders", JSON(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_nhdw_ward_rounds_lab_id", "nhdw_ward_rounds", ["lab_id"])
        op.create_index("ix_nhdw_ward_rounds_patient_id", "nhdw_ward_rounds", ["patient_id"])
        op.create_index("ix_nhdw_ward_rounds_admission_id", "nhdw_ward_rounds", ["admission_id"])
        op.create_index("ix_nhdw_ward_rounds_date", "nhdw_ward_rounds", ["round_date"])

    # ── Care Plans ────────────────────────────────────────────────────────────
    if not _table_exists("nhdw_care_plans"):
        op.create_table(
            "nhdw_care_plans",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
            sa.Column("admission_id", sa.Integer(), sa.ForeignKey("nhdw_admissions.id", ondelete="SET NULL"), nullable=True),
            sa.Column("care_plan_type", sa.String(50), nullable=False),
            sa.Column("title", sa.String(300), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("goals", JSON(), nullable=True),
            sa.Column("interventions", JSON(), nullable=True),
            sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("target_end_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("actual_end_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="active"),
            sa.Column("outcome", sa.Text(), nullable=True),
            sa.Column("review_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_nhdw_care_plans_lab_id", "nhdw_care_plans", ["lab_id"])
        op.create_index("ix_nhdw_care_plans_patient_id", "nhdw_care_plans", ["patient_id"])
        op.create_index("ix_nhdw_care_plans_admission_id", "nhdw_care_plans", ["admission_id"])
        op.create_index("ix_nhdw_care_plans_lab_status", "nhdw_care_plans", ["lab_id", "status"])

    # ── Hospital Alerts ───────────────────────────────────────────────────────
    if not _table_exists("nhdw_hospital_alerts"):
        op.create_table(
            "nhdw_hospital_alerts",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("alert_type", sa.String(50), nullable=False),
            sa.Column("severity", sa.String(20), nullable=False, server_default="info"),
            sa.Column("title", sa.String(300), nullable=False),
            sa.Column("title_ar", sa.String(300), nullable=True),
            sa.Column("message", sa.Text(), nullable=True),
            sa.Column("source", sa.String(100), nullable=True),
            sa.Column("department", sa.String(100), nullable=True),
            sa.Column("ward", sa.String(100), nullable=True),
            sa.Column("is_read", sa.Boolean(), default=False),
            sa.Column("read_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("action_required", sa.Boolean(), default=False),
            sa.Column("action_taken", sa.Boolean(), default=False),
            sa.Column("action_notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_nhdw_alerts_lab_id", "nhdw_hospital_alerts", ["lab_id"])
        op.create_index("ix_nhdw_alerts_lab_severity", "nhdw_hospital_alerts", ["lab_id", "severity"])
        op.create_index("ix_nhdw_alerts_lab_unread", "nhdw_hospital_alerts", ["lab_id", "is_read"])
        op.create_index("ix_nhdw_alerts_expires_at", "nhdw_hospital_alerts", ["expires_at"])

    # ── Hospital Messages ─────────────────────────────────────────────────────
    if not _table_exists("nhdw_hospital_messages"):
        op.create_table(
            "nhdw_hospital_messages",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("sender_id", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("recipient_id", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("recipient_department", sa.String(100), nullable=True),
            sa.Column("subject", sa.String(300), nullable=False),
            sa.Column("body", sa.Text(), nullable=True),
            sa.Column("priority", sa.String(20), default="normal"),
            sa.Column("is_read", sa.Boolean(), default=False),
            sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("requires_acknowledgment", sa.Boolean(), default=False),
            sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("acknowledged_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("parent_message_id", sa.Integer(), sa.ForeignKey("nhdw_hospital_messages.id", ondelete="SET NULL"), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_nhdw_messages_lab_id", "nhdw_hospital_messages", ["lab_id"])
        op.create_index("ix_nhdw_messages_sender_id", "nhdw_hospital_messages", ["sender_id"])
        op.create_index("ix_nhdw_messages_recipient_id", "nhdw_hospital_messages", ["recipient_id"])
        op.create_index("ix_nhdw_messages_unread", "nhdw_hospital_messages", ["recipient_id", "is_read"])

    # ── Telemedicine Sessions ─────────────────────────────────────────────────
    if not _table_exists("nhdw_telemedicine_sessions"):
        op.create_table(
            "nhdw_telemedicine_sessions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True),
            sa.Column("session_type", sa.String(50), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="scheduled"),
            sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("provider_name", sa.String(200), nullable=True),
            sa.Column("provider_specialty", sa.String(100), nullable=True),
            sa.Column("consultation_notes", sa.Text(), nullable=True),
            sa.Column("diagnosis", sa.Text(), nullable=True),
            sa.Column("prescription", JSON(), nullable=True),
            sa.Column("follow_up_required", sa.Boolean(), default=False),
            sa.Column("follow_up_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("meeting_url", sa.String(500), nullable=True),
            sa.Column("recording_url", sa.String(500), nullable=True),
            sa.Column("duration_minutes", sa.Integer(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_nhdw_telemedicine_lab_id", "nhdw_telemedicine_sessions", ["lab_id"])
        op.create_index("ix_nhdw_telemedicine_patient_id", "nhdw_telemedicine_sessions", ["patient_id"])
        op.create_index("ix_nhdw_telemedicine_scheduled_at", "nhdw_telemedicine_sessions", ["scheduled_at"])
        op.create_index("ix_nhdw_telemedicine_lab_status", "nhdw_telemedicine_sessions", ["lab_id", "status"])

    # ── Resource Schedules ────────────────────────────────────────────────────
    if not _table_exists("nhdw_resource_schedules"):
        op.create_table(
            "nhdw_resource_schedules",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("resource_type", sa.String(50), nullable=False),
            sa.Column("resource_name", sa.String(200), nullable=False),
            sa.Column("resource_id_ref", sa.Integer(), nullable=True),
            sa.Column("scheduled_date", sa.Date(), nullable=False),
            sa.Column("start_time", sa.Time(), nullable=False),
            sa.Column("end_time", sa.Time(), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="available"),
            sa.Column("booked_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("booked_for_patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True),
            sa.Column("purpose", sa.String(300), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_nhdw_resource_sched_lab_id", "nhdw_resource_schedules", ["lab_id"])
        op.create_index("ix_nhdw_resource_sched_date", "nhdw_resource_schedules", ["scheduled_date"])
        op.create_index("ix_nhdw_resource_sched_lab_type_date", "nhdw_resource_schedules", ["lab_id", "resource_type", "scheduled_date"])

    # ── Dashboard Configurations ──────────────────────────────────────────────
    if not _table_exists("nhdw_dashboard_configurations"):
        op.create_table(
            "nhdw_dashboard_configurations",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="CASCADE"), nullable=True),
            sa.Column("dashboard_name", sa.String(200), nullable=False),
            sa.Column("dashboard_type", sa.String(50), nullable=False),
            sa.Column("layout", JSON(), nullable=True),
            sa.Column("widgets", JSON(), nullable=True),
            sa.Column("filters", JSON(), nullable=True),
            sa.Column("refresh_interval_seconds", sa.Integer(), default=60),
            sa.Column("is_default", sa.Boolean(), default=False),
            sa.Column("is_shared", sa.Boolean(), default=False),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_nhdw_dash_config_lab_id", "nhdw_dashboard_configurations", ["lab_id"])
        op.create_index("ix_nhdw_dash_config_user_id", "nhdw_dashboard_configurations", ["user_id"])
        op.create_index("ix_nhdw_dash_config_lab_type", "nhdw_dashboard_configurations", ["lab_id", "dashboard_type"])

    # ── Shift Reports ─────────────────────────────────────────────────────────
    if not _table_exists("nhdw_shift_reports"):
        op.create_table(
            "nhdw_shift_reports",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("shift_type", sa.String(50), nullable=False),
            sa.Column("shift_date", sa.Date(), nullable=False),
            sa.Column("start_time", sa.Time(), nullable=False),
            sa.Column("end_time", sa.Time(), nullable=True),
            sa.Column("reported_by", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("summary", sa.Text(), nullable=True),
            sa.Column("key_events", JSON(), nullable=True),
            sa.Column("patient_count", sa.Integer(), nullable=True),
            sa.Column("admissions_count", sa.Integer(), nullable=True),
            sa.Column("discharges_count", sa.Integer(), nullable=True),
            sa.Column("transfers_count", sa.Integer(), nullable=True),
            sa.Column("incidents", JSON(), nullable=True),
            sa.Column("staff_attendance", JSON(), nullable=True),
            sa.Column("equipment_issues", JSON(), nullable=True),
            sa.Column("pending_tasks", JSON(), nullable=True),
            sa.Column("handover_notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_nhdw_shift_reports_lab_id", "nhdw_shift_reports", ["lab_id"])
        op.create_index("ix_nhdw_shift_reports_reported_by", "nhdw_shift_reports", ["reported_by"])
        op.create_index("ix_nhdw_shift_reports_date", "nhdw_shift_reports", ["shift_date"])


def downgrade() -> None:
    tables = [
        "nhdw_shift_reports",
        "nhdw_dashboard_configurations",
        "nhdw_resource_schedules",
        "nhdw_telemedicine_sessions",
        "nhdw_hospital_messages",
        "nhdw_hospital_alerts",
        "nhdw_care_plans",
        "nhdw_ward_rounds",
        "nhdw_clinical_tasks",
        "nhdw_waiting_list_entries",
        "nhdw_queue_entries",
        "nhdw_transfers",
        "nhdw_discharges",
        "nhdw_admissions",
    ]
    for table in tables:
        if _table_exists(table):
            op.drop_table(table)
