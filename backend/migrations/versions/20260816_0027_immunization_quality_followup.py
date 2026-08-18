"""Immunization quality, follow-up tasks, and AEFI registry.

Revision ID: 20260816_0027
Revises: 20260815_0026

This migration is prepared locally only. It must be reviewed and applied through
normal staging/change-control procedures after the target schema is verified.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import context, op

revision = "20260816_0027"
down_revision = "20260815_0026"
branch_labels = None
depends_on = None


def _inspect():
    if context.is_offline_mode():
        return None
    return sa.inspect(op.get_bind())


def _has_table(table: str) -> bool:
    if context.is_offline_mode():
        return False
    return bool(_inspect().has_table(table))


def _columns(table: str) -> set[str]:
    if context.is_offline_mode():
        return set()
    return {item["name"] for item in _inspect().get_columns(table)} if _has_table(table) else set()


def _add_column_if_missing(table: str, column: sa.Column) -> None:
    if column.name not in _columns(table):
        op.add_column(table, column)


def _create_index_if_missing(name: str, table: str, columns: list[str]) -> None:
    if context.is_offline_mode():
        op.create_index(name, table, columns)
        return
    if not _has_table(table):
        return
    indexes = {item["name"] for item in _inspect().get_indexes(table)}
    if name not in indexes:
        op.create_index(name, table, columns)


def _audit_columns() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
    ]


def upgrade() -> None:
    if _has_table("ph_immunization_schedule_definitions"):
        for column in (
            sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
            sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
            sa.Column("approval_status", sa.String(length=24), nullable=False, server_default="approved"),
            sa.Column("approval_reference", sa.String(length=200), nullable=True),
        ):
            _add_column_if_missing("ph_immunization_schedule_definitions", column)
        _create_index_if_missing("ix_ph_imm_schedule_definitions_effective_from", "ph_immunization_schedule_definitions", ["effective_from"])

    if _has_table("ph_immunization_schedules"):
        for column in (
            sa.Column("follow_up_status", sa.String(length=24), nullable=False, server_default="not_required"),
            sa.Column("follow_up_priority", sa.String(length=16), nullable=False, server_default="normal"),
            sa.Column("next_follow_up_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("non_administration_reason", sa.String(length=32), nullable=True),
            sa.Column("non_administration_notes", sa.Text(), nullable=True),
        ):
            _add_column_if_missing("ph_immunization_schedules", column)
        _create_index_if_missing("ix_ph_imm_schedules_follow_up_status", "ph_immunization_schedules", ["follow_up_status"])
        _create_index_if_missing("ix_ph_imm_schedules_next_follow_up_date", "ph_immunization_schedules", ["next_follow_up_date"])

    if not _has_table("ph_immunization_follow_up_tasks"):
        op.create_table(
            "ph_immunization_follow_up_tasks",
            sa.Column("id", sa.String(length=26), primary_key=True),
            sa.Column("fhir_id", sa.String(length=64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(length=32), nullable=True),
            *_audit_columns(),
            sa.Column("schedule_id", sa.String(length=26), nullable=False),
            sa.Column("patient_id", sa.String(length=100), nullable=False),
            sa.Column("health_number", sa.String(length=20), nullable=False),
            sa.Column("vaccine", sa.String(length=200), nullable=False),
            sa.Column("due_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("status", sa.String(length=24), nullable=False, server_default="pending"),
            sa.Column("priority", sa.String(length=16), nullable=False, server_default="normal"),
            sa.Column("reason", sa.String(length=32), nullable=True),
            sa.Column("next_action_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("consent_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("preferred_channel", sa.String(length=24), nullable=True),
            sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_by", sa.String(length=100), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
        )
    for name, columns in (
        ("ix_ph_imm_followup_lab_id", ["lab_id"]),
        ("ix_ph_imm_followup_schedule_id", ["schedule_id"]),
        ("ix_ph_imm_followup_patient_id", ["patient_id"]),
        ("ix_ph_imm_followup_status", ["status"]),
        ("ix_ph_imm_followup_due_date", ["due_date"]),
        ("ix_ph_imm_followup_next_action", ["next_action_at"]),
    ):
        _create_index_if_missing(name, "ph_immunization_follow_up_tasks", columns)

    if not _has_table("ph_immunization_adverse_events"):
        op.create_table(
            "ph_immunization_adverse_events",
            sa.Column("id", sa.String(length=26), primary_key=True),
            sa.Column("fhir_id", sa.String(length=64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(length=32), nullable=True),
            *_audit_columns(),
            sa.Column("record_id", sa.String(length=26), nullable=False),
            sa.Column("schedule_id", sa.String(length=26), nullable=True),
            sa.Column("patient_id", sa.String(length=100), nullable=False),
            sa.Column("health_number", sa.String(length=20), nullable=True),
            sa.Column("vaccine", sa.String(length=200), nullable=False),
            sa.Column("onset_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("severity", sa.String(length=24), nullable=False, server_default="unknown"),
            sa.Column("symptoms", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
            sa.Column("treatment", sa.Text(), nullable=True),
            sa.Column("outcome", sa.String(length=32), nullable=True),
            sa.Column("investigation_status", sa.String(length=24), nullable=False, server_default="reported"),
            sa.Column("reported_by", sa.String(length=100), nullable=False),
            sa.Column("reported_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("notes", sa.Text(), nullable=True),
        )
    for name, columns in (
        ("ix_ph_imm_aefi_lab_id", ["lab_id"]),
        ("ix_ph_imm_aefi_record_id", ["record_id"]),
        ("ix_ph_imm_aefi_schedule_id", ["schedule_id"]),
        ("ix_ph_imm_aefi_patient_id", ["patient_id"]),
        ("ix_ph_imm_aefi_status", ["investigation_status"]),
    ):
        _create_index_if_missing(name, "ph_immunization_adverse_events", columns)


def downgrade() -> None:
    for table in ("ph_immunization_adverse_events", "ph_immunization_follow_up_tasks"):
        if _has_table(table):
            op.drop_table(table)

    if _has_table("ph_immunization_schedules"):
        existing = _columns("ph_immunization_schedules")
        for name in ("ix_ph_imm_schedules_next_follow_up_date", "ix_ph_imm_schedules_follow_up_status"):
            if name in {item["name"] for item in _inspect().get_indexes("ph_immunization_schedules")}:
                op.drop_index(name, table_name="ph_immunization_schedules")
        for name in ("non_administration_notes", "non_administration_reason", "next_follow_up_date", "follow_up_priority", "follow_up_status"):
            if name in existing:
                op.drop_column("ph_immunization_schedules", name)

    if _has_table("ph_immunization_schedule_definitions"):
        existing = _columns("ph_immunization_schedule_definitions")
        if "ix_ph_imm_schedule_definitions_effective_from" in {item["name"] for item in _inspect().get_indexes("ph_immunization_schedule_definitions")}:
            op.drop_index("ix_ph_imm_schedule_definitions_effective_from", table_name="ph_immunization_schedule_definitions")
        for name in ("approval_reference", "approval_status", "effective_to", "effective_from"):
            if name in existing:
                op.drop_column("ph_immunization_schedule_definitions", name)
