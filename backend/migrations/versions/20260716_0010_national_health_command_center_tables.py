"""Create National Health Command Center tables.

Revision ID: 20260716_0010
Revises: 20260716_0009
Create Date: 2026-07-16
"""

from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy import inspect

revision: str = "20260716_0010"
down_revision: Union[str, None] = "20260716_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def upgrade() -> None:
    if not _table_exists("cc_emergency_declarations"):
        op.create_table(
            "cc_emergency_declarations",
            sa.Column("emergency_type", sa.String(), nullable=False),
            sa.Column("level", sa.String(), default="level_1_minor"),
            sa.Column("status", sa.String(), default="standby"),
            sa.Column("region", sa.String(), nullable=False),
            sa.Column("district", sa.String()),
            sa.Column("description", sa.Text()),
            sa.Column("affected_population", sa.Integer(), default=0),
            sa.Column("declared_by", sa.String()),
            sa.Column("declared_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("resolved_at", sa.DateTime(timezone=True)),
            sa.Column("resolved_by", sa.String()),
            sa.Column("activation_protocol", sa.String()),
            sa.Column("ic_name", sa.String()),
            sa.Column("ic_title", sa.String()),
            sa.Column("ic_phone", sa.String()),
            sa.Column("command_post_location", sa.Text()),
            sa.Column("operational_period", sa.String(), default="continuous"),
            sa.Column("objectives", sa.JSON()),
            sa.Column("situation_summary", sa.Text()),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=false),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_cc_emergency_declarations_lab_id", "cc_emergency_declarations", ["lab_id"])
        op.create_index("ix_cc_emergency_declarations_region", "cc_emergency_declarations", ["region"])
        op.create_index("ix_cc_emergency_declarations_fhir_id", "cc_emergency_declarations", ["fhir_id"])

    if not _table_exists("cc_resource_requests"):
        op.create_table(
            "cc_resource_requests",
            sa.Column("emergency_id", sa.String(), sa.ForeignKey("cc_emergency_declarations.id")),
            sa.Column("resource_type", sa.String(), nullable=False),
            sa.Column("quantity", sa.Integer(), default=1),
            sa.Column("priority", sa.String(), default="medium"),
            sa.Column("status", sa.String(), default="pending"),
            sa.Column("requesting_facility", sa.String()),
            sa.Column("destination_location", sa.Text()),
            sa.Column("requested_by", sa.String()),
            sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("fulfilled_quantity", sa.Integer(), default=0),
            sa.Column("fulfilled_by", sa.String()),
            sa.Column("fulfilled_at", sa.DateTime(timezone=True)),
            sa.Column("source", sa.String()),
            sa.Column("notes", sa.Text()),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=false),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_cc_resource_requests_fhir_id", "cc_resource_requests", ["fhir_id"])
        op.create_index("ix_cc_resource_requests_emergency_id", "cc_resource_requests", ["emergency_id"])
        op.create_index("ix_cc_resource_requests_lab_id", "cc_resource_requests", ["lab_id"])

    if not _table_exists("cc_situation_reports"):
        op.create_table(
            "cc_situation_reports",
            sa.Column("emergency_id", sa.String(), sa.ForeignKey("cc_emergency_declarations.id")),
            sa.Column("report_number", sa.Integer(), default=1),
            sa.Column("operational_period", sa.String()),
            sa.Column("summary", sa.Text()),
            sa.Column("key_actions", sa.JSON()),
            sa.Column("resources_deployed", sa.JSON()),
            sa.Column("casualties", sa.JSON()),
            sa.Column("challenges", sa.JSON()),
            sa.Column("next_steps", sa.JSON()),
            sa.Column("published_by", sa.String()),
            sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=false),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_cc_situation_reports_emergency_id", "cc_situation_reports", ["emergency_id"])
        op.create_index("ix_cc_situation_reports_fhir_id", "cc_situation_reports", ["fhir_id"])
        op.create_index("ix_cc_situation_reports_lab_id", "cc_situation_reports", ["lab_id"])

    if not _table_exists("cc_after_action_reports"):
        op.create_table(
            "cc_after_action_reports",
            sa.Column("emergency_id", sa.String(), sa.ForeignKey("cc_emergency_declarations.id")),
            sa.Column("emergency_type", sa.String()),
            sa.Column("region", sa.String()),
            sa.Column("incident_duration_hours", sa.Integer(), default=0),
            sa.Column("overall_rating", sa.String(), default="satisfactory"),
            sa.Column("strengths", sa.JSON()),
            sa.Column("weaknesses", sa.JSON()),
            sa.Column("recommendations", sa.JSON()),
            sa.Column("response_time_minutes", sa.Integer(), default=0),
            sa.Column("lives_saved", sa.Integer(), default=0),
            sa.Column("resources_used", sa.JSON()),
            sa.Column("completed_by", sa.String()),
            sa.Column("completed_at", sa.DateTime(timezone=True)),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=false),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_cc_after_action_reports_lab_id", "cc_after_action_reports", ["lab_id"])
        op.create_index("ix_cc_after_action_reports_fhir_id", "cc_after_action_reports", ["fhir_id"])



def downgrade() -> None:
    if _table_exists("cc_after_action_reports"):
        op.drop_table("cc_after_action_reports")
    if _table_exists("cc_situation_reports"):
        op.drop_table("cc_situation_reports")
    if _table_exists("cc_resource_requests"):
        op.drop_table("cc_resource_requests")
    if _table_exists("cc_emergency_declarations"):
        op.drop_table("cc_emergency_declarations")
