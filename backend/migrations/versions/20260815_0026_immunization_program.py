"""Create newborn health-record and configurable immunization programme tables.

Revision ID: 20260815_0026
Revises: 20260815_0025

This migration is intentionally idempotent for environments where the legacy
public-health module was created before the national newborn model was tracked
by Alembic. It is not executed by this change set.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260815_0026"
down_revision = "20260815_0025"
branch_labels = None
depends_on = None


def _has_table(table: str) -> bool:
    return bool(sa.inspect(op.get_bind()).has_table(table))


def _columns(table: str) -> set[str]:
    if not _has_table(table):
        return set()
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table)}


def _add_column_if_missing(table: str, column: sa.Column[object]) -> None:
    if column.name not in _columns(table):
        op.add_column(table, column)


def _create_index_if_missing(name: str, table: str, columns: list[str], unique: bool = False) -> None:
    if not _has_table(table):
        return
    existing = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes(table)}
    if name not in existing:
        op.create_index(name, table, columns, unique=unique)


def _audit_columns() -> list[sa.Column[object]]:
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
    if not _has_table("national_newborns"):
        op.create_table(
            "national_newborns",
            sa.Column("id", sa.String(length=26), primary_key=True),
            sa.Column("fhir_id", sa.String(length=64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(length=32), nullable=True),
            * _audit_columns(),
            sa.Column("birth_certificate_number", sa.String(length=50), nullable=False),
            sa.Column("hospital_registration_number", sa.String(length=50), nullable=True),
            sa.Column("temporary_health_number", sa.String(length=20), nullable=True, unique=True),
            sa.Column("first_name", sa.String(length=100), nullable=True),
            sa.Column("father_name", sa.String(length=100), nullable=True),
            sa.Column("last_name", sa.String(length=100), nullable=True),
            sa.Column("date_of_birth", sa.Date(), nullable=False),
            sa.Column("birth_time", sa.DateTime(timezone=True), nullable=True),
            sa.Column("gender", sa.String(length=20), nullable=False),
            sa.Column("birth_weight_grams", sa.SmallInteger(), nullable=True),
            sa.Column("birth_length_cm", sa.SmallInteger(), nullable=True),
            sa.Column("birth_place", sa.String(length=200), nullable=True),
            sa.Column("birth_place_type", sa.String(length=50), nullable=True),
            sa.Column("delivery_method", sa.String(length=50), nullable=True),
            sa.Column("mother_id", sa.String(length=26), nullable=False),
            sa.Column("mother_name", sa.String(length=200), nullable=True),
            sa.Column("father_id", sa.String(length=26), nullable=True),
            sa.Column("guardian_id", sa.String(length=26), nullable=True),
            sa.Column("family_id", sa.String(length=26), nullable=True),
            sa.Column("converted_to_citizen_id", sa.String(length=26), nullable=True),
            sa.Column("converted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_converted", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("registered_by_hospital", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("registration_days_after_birth", sa.SmallInteger(), nullable=True),
            sa.Column("citizen_id", sa.String(length=26), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(["mother_id"], ["national_citizens.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["father_id"], ["national_citizens.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["converted_to_citizen_id"], ["national_citizens.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["citizen_id"], ["national_citizens.id"], ondelete="RESTRICT"),
        )
    for name, columns, unique in (
        ("ix_national_newborns_lab_id", ["lab_id"], False),
        ("ix_national_newborns_fhir_id", ["fhir_id"], False),
        ("ix_national_newborns_birth_cert", ["birth_certificate_number"], False),
        ("ix_national_newborns_temp_health", ["temporary_health_number"], True),
        ("ix_national_newborns_mother", ["mother_id"], False),
        ("ix_national_newborns_father", ["father_id"], False),
        ("ix_national_newborns_converted", ["converted_to_citizen_id"], False),
    ):
        _create_index_if_missing(name, "national_newborns", columns, unique)

    record_columns = (
        sa.Column("health_number", sa.String(length=20), nullable=True),
        sa.Column("newborn_id", sa.String(length=26), nullable=True),
        sa.Column("schedule_id", sa.String(length=26), nullable=True),
        sa.Column("scheduled_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="administered"),
        sa.Column("appointment_id", sa.String(length=100), nullable=True),
        sa.Column("reminder_sent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("reminder_sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    if _has_table("ph_immunization_records"):
        for column in record_columns:
            _add_column_if_missing("ph_immunization_records", column)
        for name, columns, unique in (
            ("ix_ph_immunization_records_health_number", ["health_number"], False),
            ("ix_ph_immunization_records_newborn_id", ["newborn_id"], False),
            ("uq_ph_immunization_records_schedule_id", ["schedule_id"], True),
            ("ix_ph_immunization_records_scheduled_date", ["scheduled_date"], False),
            ("ix_ph_immunization_records_due_date", ["due_date"], False),
            ("ix_ph_immunization_records_status", ["status"], False),
            ("ix_ph_immunization_records_appointment_id", ["appointment_id"], False),
        ):
            _create_index_if_missing(name, "ph_immunization_records", columns, unique)

    if not _has_table("ph_immunization_schedule_definitions"):
        op.create_table(
            "ph_immunization_schedule_definitions",
            sa.Column("id", sa.String(length=26), primary_key=True),
            sa.Column("fhir_id", sa.String(length=64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(length=32), nullable=True),
            * _audit_columns(),
            sa.Column("schedule_version", sa.String(length=40), nullable=False),
            sa.Column("vaccine", sa.String(length=200), nullable=False),
            sa.Column("vaccine_code", sa.String(length=40), nullable=False),
            sa.Column("dose_number", sa.Integer(), nullable=False),
            sa.Column("total_doses", sa.Integer(), nullable=False),
            sa.Column("minimum_age_days", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("recommended_age_days", sa.Integer(), nullable=False),
            sa.Column("grace_period_days", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("route", sa.String(length=50), nullable=True),
            sa.Column("site", sa.String(length=50), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("approved_by", sa.String(length=100), nullable=True),
            sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("source_reference", sa.String(length=500), nullable=True),
            sa.UniqueConstraint("lab_id", "schedule_version", "vaccine_code", "dose_number", name="uq_ph_imm_schedule_definition"),
        )
    for name, columns, unique in (
        ("ix_ph_imm_schedule_definitions_lab_id", ["lab_id"], False),
        ("ix_ph_imm_schedule_definitions_fhir_id", ["fhir_id"], False),
        ("ix_ph_imm_schedule_definitions_version", ["schedule_version"], False),
        ("ix_ph_imm_schedule_definitions_vaccine_code", ["vaccine_code"], False),
    ):
        _create_index_if_missing(name, "ph_immunization_schedule_definitions", columns, unique)

    if not _has_table("ph_immunization_schedules"):
        op.create_table(
            "ph_immunization_schedules",
            sa.Column("id", sa.String(length=26), primary_key=True),
            sa.Column("fhir_id", sa.String(length=64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(length=32), nullable=True),
            * _audit_columns(),
            sa.Column("patient_id", sa.String(length=100), nullable=False),
            sa.Column("health_number", sa.String(length=20), nullable=False),
            sa.Column("newborn_id", sa.String(length=26), nullable=True),
            sa.Column("schedule_definition_id", sa.String(length=26), nullable=False),
            sa.Column("schedule_version", sa.String(length=40), nullable=False),
            sa.Column("vaccine", sa.String(length=200), nullable=False),
            sa.Column("vaccine_code", sa.String(length=40), nullable=False),
            sa.Column("dose_number", sa.Integer(), nullable=False),
            sa.Column("total_doses", sa.Integer(), nullable=False),
            sa.Column("due_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("scheduled_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="scheduled"),
            sa.Column("facility_id", sa.String(length=100), nullable=True),
            sa.Column("appointment_id", sa.String(length=100), nullable=True),
            sa.Column("reminder_sent", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("reminder_sent_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("reminder_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("contraindication_reason", sa.Text(), nullable=True),
            sa.Column("refusal_reason", sa.Text(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.UniqueConstraint("lab_id", "patient_id", "schedule_definition_id", name="uq_ph_imm_patient_schedule"),
        )
    for name, columns, unique in (
        ("ix_ph_imm_schedules_lab_id", ["lab_id"], False),
        ("ix_ph_imm_schedules_fhir_id", ["fhir_id"], False),
        ("ix_ph_imm_schedules_patient_id", ["patient_id"], False),
        ("ix_ph_imm_schedules_health_number", ["health_number"], False),
        ("ix_ph_imm_schedules_newborn_id", ["newborn_id"], False),
        ("ix_ph_imm_schedules_definition_id", ["schedule_definition_id"], False),
        ("ix_ph_imm_schedules_version", ["schedule_version"], False),
        ("ix_ph_imm_schedules_vaccine_code", ["vaccine_code"], False),
        ("ix_ph_imm_schedules_due_date", ["due_date"], False),
        ("ix_ph_imm_schedules_scheduled_date", ["scheduled_date"], False),
        ("ix_ph_imm_schedules_status", ["status"], False),
        ("ix_ph_imm_schedules_appointment_id", ["appointment_id"], False),
        ("ix_ph_imm_schedules_lab_status_due", ["lab_id", "status", "due_date"], False),
    ):
        _create_index_if_missing(name, "ph_immunization_schedules", columns, unique)


def downgrade() -> None:
    # Avoid dropping pre-existing legacy tables. These programme tables are new to
    # this revision and can be safely removed by an intentional downgrade.
    for table in ("ph_immunization_schedules", "ph_immunization_schedule_definitions"):
        if _has_table(table):
            op.drop_table(table)

    if _has_table("ph_immunization_records"):
        existing = _columns("ph_immunization_records")
        indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("ph_immunization_records")}
        for name in (
            "ix_ph_immunization_records_appointment_id",
            "ix_ph_immunization_records_status",
            "ix_ph_immunization_records_due_date",
            "ix_ph_immunization_records_scheduled_date",
            "uq_ph_immunization_records_schedule_id",
            "ix_ph_immunization_records_newborn_id",
            "ix_ph_immunization_records_health_number",
        ):
            if name in indexes:
                op.drop_index(name, table_name="ph_immunization_records")
        for name in (
            "reminder_sent_at", "reminder_sent", "appointment_id", "status", "due_date",
            "scheduled_date", "schedule_id", "newborn_id", "health_number",
        ):
            if name in existing:
                op.drop_column("ph_immunization_records", name)

    # ``national_newborns`` may pre-date Alembic tracking. Preserve it on downgrade
    # rather than risking removal of an existing registry.
