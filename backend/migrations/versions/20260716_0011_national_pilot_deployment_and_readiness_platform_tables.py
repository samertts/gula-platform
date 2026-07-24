"""Create National Pilot Deployment & Readiness Platform tables.

Revision ID: 20260716_0011
Revises: 20260716_0010
Create Date: 2026-07-16
"""

from typing import Union
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy import inspect

revision: str = "20260716_0011"
down_revision: str | None = "20260716_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def upgrade() -> None:
    if not _table_exists("pilot_programs"):
        op.create_table(
            "pilot_programs",
            sa.Column("module_name", sa.String(), nullable=False),
            sa.Column("module_path", sa.String()),
            sa.Column("version", sa.String(), nullable=False),
            sa.Column("current_phase", sa.String(), default="planned"),
            sa.Column("status", sa.String(), default="planned"),
            sa.Column("strategy", sa.String(), default="canary"),
            sa.Column("pilot_lead", sa.String()),
            sa.Column("technical_lead", sa.String()),
            sa.Column("clinical_lead", sa.String()),
            sa.Column("start_date", sa.DateTime(timezone=True)),
            sa.Column("target_completion", sa.DateTime(timezone=True)),
            sa.Column("completed_at", sa.DateTime(timezone=True)),
            sa.Column("description", sa.Text()),
            sa.Column("phases", sa.JSON()),
            sa.Column("facilities", sa.JSON()),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True))
        )
        op.create_index("ix_pilot_programs_lab_id", "pilot_programs", ["lab_id"])
        op.create_index("ix_pilot_programs_fhir_id", "pilot_programs", ["fhir_id"])

    if not _table_exists("pilot_facilities"):
        op.create_table(
            "pilot_facilities",
            sa.Column("pilot_id", sa.String(), sa.ForeignKey("pilot_programs.id"), nullable=False),
            sa.Column("facility_id", sa.String(), nullable=False),
            sa.Column("facility_name", sa.String()),
            sa.Column("phase", sa.String()),
            sa.Column("readiness_level", sa.String(), default="not_ready"),
            sa.Column("readiness_score", sa.Float(), default=0.0),
            sa.Column("enrolled_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True)),
            sa.Column("go_no_go_approved", sa.Boolean(), default=False),
            sa.Column("issues", sa.JSON()),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_pilot_facilities_fhir_id", "pilot_facilities", ["fhir_id"])
        op.create_index("ix_pilot_facilities_pilot_id", "pilot_facilities", ["pilot_id"])
        op.create_index("ix_pilot_facilities_lab_id", "pilot_facilities", ["lab_id"])

    if not _table_exists("pilot_readiness_checklists"):
        op.create_table(
            "pilot_readiness_checklists",
            sa.Column("pilot_id", sa.String(), sa.ForeignKey("pilot_programs.id")),
            sa.Column("facility_id", sa.String()),
            sa.Column("items", sa.JSON()),
            sa.Column("overall_score", sa.Float(), default=0.0),
            sa.Column("level", sa.String(), default="not_ready"),
            sa.Column("assessed_by", sa.String()),
            sa.Column("assessed_at", sa.DateTime(timezone=True)),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_pilot_readiness_checklists_fhir_id", "pilot_readiness_checklists", ["fhir_id"])
        op.create_index("ix_pilot_readiness_checklists_lab_id", "pilot_readiness_checklists", ["lab_id"])

    if not _table_exists("pilot_go_no_go_gates"):
        op.create_table(
            "pilot_go_no_go_gates",
            sa.Column("pilot_id", sa.String(), sa.ForeignKey("pilot_programs.id"), nullable=False),
            sa.Column("facility_id", sa.String()),
            sa.Column("gate_name", sa.String(), nullable=False),
            sa.Column("result", sa.String(), default="not_run"),
            sa.Column("certification_level", sa.String()),
            sa.Column("metrics", sa.JSON()),
            sa.Column("approver", sa.String()),
            sa.Column("decided_at", sa.DateTime(timezone=True)),
            sa.Column("comments", sa.Text()),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_pilot_go_no_go_gates_lab_id", "pilot_go_no_go_gates", ["lab_id"])
        op.create_index("ix_pilot_go_no_go_gates_pilot_id", "pilot_go_no_go_gates", ["pilot_id"])
        op.create_index("ix_pilot_go_no_go_gates_fhir_id", "pilot_go_no_go_gates", ["fhir_id"])

    if not _table_exists("pilot_deployment_records"):
        op.create_table(
            "pilot_deployment_records",
            sa.Column("pilot_id", sa.String(), sa.ForeignKey("pilot_programs.id"), nullable=False),
            sa.Column("module", sa.String()),
            sa.Column("version", sa.String()),
            sa.Column("facility_id", sa.String()),
            sa.Column("strategy", sa.String()),
            sa.Column("status", sa.String(), default="pending"),
            sa.Column("deployed_at", sa.DateTime(timezone=True)),
            sa.Column("deployed_by", sa.String()),
            sa.Column("health_check_passed", sa.Boolean(), default=False),
            sa.Column("rollback_at", sa.DateTime(timezone=True)),
            sa.Column("rollback_reason", sa.Text()),
            sa.Column("notes", sa.Text()),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True))
        )
        op.create_index("ix_pilot_deployment_records_lab_id", "pilot_deployment_records", ["lab_id"])
        op.create_index("ix_pilot_deployment_records_pilot_id", "pilot_deployment_records", ["pilot_id"])
        op.create_index("ix_pilot_deployment_records_fhir_id", "pilot_deployment_records", ["fhir_id"])



def downgrade() -> None:
    if _table_exists("pilot_deployment_records"):
        op.drop_table("pilot_deployment_records")
    if _table_exists("pilot_go_no_go_gates"):
        op.drop_table("pilot_go_no_go_gates")
    if _table_exists("pilot_readiness_checklists"):
        op.drop_table("pilot_readiness_checklists")
    if _table_exists("pilot_facilities"):
        op.drop_table("pilot_facilities")
    if _table_exists("pilot_programs"):
        op.drop_table("pilot_programs")
