"""Create surgical safety checklists.

Revision ID: 20260820_0007
Revises: 20260820_0006
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260820_0007"
down_revision = "20260820_0006"
branch_labels = None
depends_on = None


def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def upgrade() -> None:
    # These Hospital resources are referenced by later domain tables but were
    # absent from the historical migration chain. Create only when missing;
    # existing production tables remain untouched.
    if not _table_exists("hospitals"):
        op.create_table(
            "hospitals",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("code", sa.String(50), nullable=False),
            sa.Column("name", sa.String(300), nullable=False),
            sa.Column("name_ar", sa.String(300), nullable=True),
            sa.Column("hospital_type", sa.String(50), nullable=False, server_default="hospital"),
            sa.Column("license_number", sa.String(100), nullable=True),
            sa.Column("phone", sa.String(20), nullable=True),
            sa.Column("email", sa.String(200), nullable=True),
            sa.Column("website", sa.String(300), nullable=True),
            sa.Column("address", sa.String(500), nullable=True),
            sa.Column("city", sa.String(100), nullable=True),
            sa.Column("province", sa.String(100), nullable=True),
            sa.Column("country", sa.String(10), nullable=False, server_default="IQ"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("code", name="uq_hospitals_code"),
        )
        op.create_index("ix_hospitals_id", "hospitals", ["id"])
        op.create_index("ix_hospitals_code", "hospitals", ["code"])
        op.create_index("ix_hospitals_hospital_type", "hospitals", ["hospital_type"])

    if not _table_exists("hospital_departments"):
        op.create_table(
            "hospital_departments",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("hospital_id", sa.Integer(), sa.ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False),
            sa.Column("parent_id", sa.Integer(), sa.ForeignKey("hospital_departments.id", ondelete="SET NULL"), nullable=True),
            sa.Column("code", sa.String(50), nullable=False),
            sa.Column("name", sa.String(300), nullable=False),
            sa.Column("name_ar", sa.String(300), nullable=True),
            sa.Column("department_type", sa.String(50), nullable=True),
            sa.Column("phone", sa.String(20), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        for column in ("id", "hospital_id", "parent_id", "code", "department_type"):
            op.create_index(f"ix_hospital_departments_{column}", "hospital_departments", [column])

    # OperationTheater is the owning Hospital resource referenced by the
    # checklist. Older history had the ORM model but omitted its DDL.
    if not _table_exists("hospital_operation_theaters"):
        op.create_table(
            "hospital_operation_theaters",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("hospital_id", sa.Integer(), sa.ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False),
            sa.Column("department_id", sa.Integer(), sa.ForeignKey("hospital_departments.id", ondelete="SET NULL"), nullable=True),
            sa.Column("code", sa.String(50), nullable=False),
            sa.Column("name", sa.String(300), nullable=False),
            sa.Column("name_ar", sa.String(300), nullable=True),
            sa.Column("theater_type", sa.String(50), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="available"),
            sa.Column("current_surgery_id", sa.Integer(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        for column in ("id", "hospital_id", "department_id", "code", "theater_type", "status"):
            op.create_index(f"ix_hospital_operation_theaters_{column}", "hospital_operation_theaters", [column])

    op.create_table(
        "hospital_surgical_safety_checklists",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("operation_theater_id", sa.Integer(), nullable=False),
        sa.Column("surgery_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("procedure_name", sa.String(length=300), nullable=False),
        sa.Column("procedure_site", sa.String(length=200), nullable=False),
        sa.Column(
            "planned_laterality",
            sa.String(length=20),
            nullable=False,
            server_default="not_applicable",
        ),
        sa.Column(
            "patient_identity_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("procedure_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("site_marked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("consent_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "anesthesia_assessment_complete",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("allergy_reviewed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "antibiotic_prophylaxis_confirmed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "blood_products_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("imaging_reviewed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "team_time_out_completed", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_by", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(
            ["operation_theater_id"],
            ["hospital_operation_theaters.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "lab_id",
            "operation_theater_id",
            "surgery_id",
            name="uq_surgical_checklist_per_theater_case",
        ),
    )
    op.create_index(
        "ix_surgical_checklist_theater_surgery",
        "hospital_surgical_safety_checklists",
        ["lab_id", "operation_theater_id", "surgery_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_surgical_checklist_theater_surgery",
        table_name="hospital_surgical_safety_checklists",
    )
    op.drop_table("hospital_surgical_safety_checklists")
    # The OperationTheater resource is owned by Hospital and is retained to
    # avoid deleting pre-existing operational data during checklist rollback.
