"""Create surgical safety checklists.

Revision ID: 20260820_0004
Revises: 20260819_0003
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260820_0004"
# IA-054: relinked so 20260820_0003 creates hospital_operation_theaters
# first. This revision has never succeeded anywhere — it is the point at which
# every fresh `alembic upgrade head` dies on an UndefinedTable — so no existing
# database has run it and the usual "never modify an existing migration" rule
# cannot be violated by changing this one line. Its schema is untouched.
down_revision = "20260820_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "hospital_surgical_safety_checklists",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("operation_theater_id", sa.Integer(), nullable=False),
        sa.Column("surgery_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("procedure_name", sa.String(length=300), nullable=False),
        sa.Column("procedure_site", sa.String(length=200), nullable=False),
        sa.Column("planned_laterality", sa.String(length=20), nullable=False, server_default="not_applicable"),
        sa.Column("patient_identity_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("procedure_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("site_marked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("consent_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("anesthesia_assessment_complete", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("allergy_reviewed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("antibiotic_prophylaxis_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("blood_products_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("imaging_reviewed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("team_time_out_completed", sa.Boolean(), nullable=False, server_default=sa.false()),
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
