"""Create the self-contained hospital core schema required by surgical safety.

Revision ID: 20261120_0001
Revises: 20260819_0003
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20261120_0001"
down_revision = "20260819_0003"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    return inspect(op.get_bind()).has_table(table_name)


def _common_columns() -> list[sa.Column]:
    """Columns supplied by ``HospitalBaseEntity`` and its shared mixins."""
    return [
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lab_id", sa.Integer(), nullable=False, index=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    ]


def _create_if_missing(table_name: str, *columns: sa.Column, **kwargs: object) -> None:
    if not _table_exists(table_name):
        op.create_table(table_name, *columns, *(_common_columns()), **kwargs)


def upgrade() -> None:
    _create_if_missing(
        "hospitals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False, index=True),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("name_ar", sa.String(length=300), nullable=True),
        sa.Column("hospital_type", sa.String(length=50), nullable=False, index=True),
        sa.Column("license_number", sa.String(length=100), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("email", sa.String(length=200), nullable=True),
        sa.Column("website", sa.String(length=300), nullable=True),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("province", sa.String(length=100), nullable=True),
        sa.Column("country", sa.String(length=10), nullable=True, server_default="IQ"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_hospitals_code"),
    )

    _create_if_missing(
        "hospital_campuses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "hospital_id",
            sa.Integer(),
            sa.ForeignKey("hospitals.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("code", sa.String(length=50), nullable=False, index=True),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("name_ar", sa.String(length=300), nullable=True),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    _create_if_missing(
        "hospital_buildings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "campus_id",
            sa.Integer(),
            sa.ForeignKey("hospital_campuses.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("code", sa.String(length=50), nullable=False, index=True),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("name_ar", sa.String(length=300), nullable=True),
        sa.Column("floors_count", sa.Integer(), nullable=True, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )

    _create_if_missing(
        "hospital_floors",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "building_id",
            sa.Integer(),
            sa.ForeignKey("hospital_buildings.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("code", sa.String(length=50), nullable=False, index=True),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("name_ar", sa.String(length=300), nullable=True),
        sa.Column("floor_number", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    _create_if_missing(
        "hospital_departments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "hospital_id",
            sa.Integer(),
            sa.ForeignKey("hospitals.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "parent_id",
            sa.Integer(),
            sa.ForeignKey("hospital_departments.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("code", sa.String(length=50), nullable=False, index=True),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("name_ar", sa.String(length=300), nullable=True),
        sa.Column("department_type", sa.String(length=50), nullable=True, index=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    _create_if_missing(
        "hospital_clinics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "hospital_id",
            sa.Integer(),
            sa.ForeignKey("hospitals.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "department_id",
            sa.Integer(),
            sa.ForeignKey("hospital_departments.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("code", sa.String(length=50), nullable=False, index=True),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("name_ar", sa.String(length=300), nullable=True),
        sa.Column("clinic_type", sa.String(length=50), nullable=True, index=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    _create_if_missing(
        "hospital_rooms",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "department_id",
            sa.Integer(),
            sa.ForeignKey("hospital_departments.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "clinic_id",
            sa.Integer(),
            sa.ForeignKey("hospital_clinics.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "floor_id",
            sa.Integer(),
            sa.ForeignKey("hospital_floors.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("code", sa.String(length=50), nullable=False, index=True),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("room_type", sa.String(length=50), nullable=False, index=True),
        sa.Column("capacity", sa.Integer(), nullable=True, server_default="1"),
        sa.PrimaryKeyConstraint("id"),
    )

    _create_if_missing(
        "hospital_beds",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "room_id",
            sa.Integer(),
            sa.ForeignKey("hospital_rooms.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("bed_number", sa.String(length=20), nullable=False),
        sa.Column("bed_type", sa.String(length=30), nullable=False, server_default="standard", index=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="available", index=True),
        sa.Column("current_patient_id", sa.Integer(), nullable=True, index=True),
        sa.PrimaryKeyConstraint("id"),
    )

    _create_if_missing(
        "bed_assignments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "bed_id",
            sa.Integer(),
            sa.ForeignKey("hospital_beds.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("patient_id", sa.Integer(), nullable=False, index=True),
        sa.Column("admission_date", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("discharge_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column("diagnosis", sa.String(length=500), nullable=True),
        sa.Column("doctor_notes", sa.Text(), nullable=True),
        sa.Column("discharge_reason", sa.String(length=500), nullable=True),
        sa.Column("discharged_by", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    _create_if_missing(
        "hospital_units",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "hospital_id",
            sa.Integer(),
            sa.ForeignKey("hospitals.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("code", sa.String(length=50), nullable=False, index=True),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("name_ar", sa.String(length=300), nullable=True),
        sa.Column("unit_type", sa.String(length=50), nullable=False, index=True),
        sa.PrimaryKeyConstraint("id"),
    )

    _create_if_missing(
        "hospital_operation_theaters",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "hospital_id",
            sa.Integer(),
            sa.ForeignKey("hospitals.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "department_id",
            sa.Integer(),
            sa.ForeignKey("hospital_departments.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("code", sa.String(length=50), nullable=False, index=True),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("name_ar", sa.String(length=300), nullable=True),
        sa.Column("theater_type", sa.String(length=50), nullable=False, index=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="available", index=True),
        sa.Column("current_surgery_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    _create_if_missing(
        "hospital_medical_equipment",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "hospital_id",
            sa.Integer(),
            sa.ForeignKey("hospitals.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "department_id",
            sa.Integer(),
            sa.ForeignKey("hospital_departments.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("equipment_code", sa.String(length=50), nullable=False, index=True),
        sa.Column("equipment_name", sa.String(length=300), nullable=False),
        sa.Column("equipment_name_ar", sa.String(length=300), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False, index=True),
        sa.Column("manufacturer", sa.String(length=200), nullable=True),
        sa.Column("model", sa.String(length=200), nullable=True),
        sa.Column("serial_number", sa.String(length=100), nullable=True, unique=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="operational", index=True),
        sa.Column("last_maintenance_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_maintenance_date", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    _create_if_missing(
        "hospital_cost_centers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "hospital_id",
            sa.Integer(),
            sa.ForeignKey("hospitals.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("code", sa.String(length=50), nullable=False, index=True),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("name_ar", sa.String(length=300), nullable=True),
        sa.Column("cost_center_type", sa.String(length=50), nullable=False, index=True),
        sa.Column("budget_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("budget_currency", sa.String(length=3), nullable=True, server_default="IQD"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    for table_name in (
        "hospital_cost_centers",
        "hospital_medical_equipment",
        "hospital_operation_theaters",
        "hospital_units",
        "bed_assignments",
        "hospital_beds",
        "hospital_rooms",
        "hospital_clinics",
        "hospital_departments",
        "hospital_floors",
        "hospital_buildings",
        "hospital_campuses",
        "hospitals",
    ):
        if _table_exists(table_name):
            op.drop_table(table_name)
