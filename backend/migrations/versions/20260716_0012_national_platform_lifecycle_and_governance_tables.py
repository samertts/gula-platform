"""Create National Platform Lifecycle & Governance tables.

Revision ID: 20260716_0012
Revises: 20260716_0011
Create Date: 2026-07-16
"""

from typing import Sequence, Union
import sqlalchemy as sa
from alembic import context, op
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy import inspect

revision: str = "20260716_0012"
down_revision: Union[str, None] = "20260716_0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table: str) -> bool:
    if context.is_offline_mode():
        return True
    return inspect(op.get_bind()).has_table(table)


def upgrade() -> None:
    if not _table_exists("lc_component_registry"):
        op.create_table(
            "lc_component_registry",
            sa.Column("name", sa.String(), nullable=False, unique=True),
            sa.Column("component_type", sa.String(), nullable=False),
            sa.Column("current_version", sa.String()),
            sa.Column("latest_version", sa.String()),
            sa.Column("stage", sa.String(), default="development"),
            sa.Column("owner", sa.String()),
            sa.Column("description", sa.Text()),
            sa.Column("repository", sa.String()),
            sa.Column("documentation_url", sa.String()),
            sa.Column("dependencies", sa.JSON()),
            sa.Column("tags", sa.JSON()),
            sa.Column("created_by", sa.Integer()),
            sa.Column("updated_by", sa.Integer()),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_lc_component_registry_fhir_id", "lc_component_registry", ["fhir_id"])

    if not _table_exists("lc_releases"):
        op.create_table(
            "lc_releases",
            sa.Column("component_id", sa.String(), sa.ForeignKey("lc_component_registry.id"), nullable=False),
            sa.Column("version", sa.String(), nullable=False),
            sa.Column("channel", sa.String(), default="stable"),
            sa.Column("status", sa.String(), default="draft"),
            sa.Column("release_notes", sa.Text()),
            sa.Column("changelog", sa.Text()),
            sa.Column("breaking_changes", sa.JSON()),
            sa.Column("certification_level", sa.String()),
            sa.Column("approved_by", sa.String()),
            sa.Column("approved_at", sa.DateTime(timezone=True)),
            sa.Column("deployed_at", sa.DateTime(timezone=True)),
            sa.Column("deployed_by", sa.String()),
            sa.Column("artifact_url", sa.String()),
            sa.Column("checksum", sa.String()),
            sa.Column("sbom_url", sa.String()),
            sa.Column("created_by", sa.Integer()),
            sa.Column("updated_by", sa.Integer()),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True))
        )
        op.create_index("ix_lc_releases_fhir_id", "lc_releases", ["fhir_id"])
        op.create_index("ix_lc_releases_component_id", "lc_releases", ["component_id"])

    if not _table_exists("lc_compatibility_matrix"):
        op.create_table(
            "lc_compatibility_matrix",
            sa.Column("component_a", sa.String(), nullable=False),
            sa.Column("component_b", sa.String(), nullable=False),
            sa.Column("version_a", sa.String(), nullable=False),
            sa.Column("version_b", sa.String(), nullable=False),
            sa.Column("level", sa.String(), default="unknown"),
            sa.Column("tested_at", sa.DateTime(timezone=True)),
            sa.Column("notes", sa.Text()),
            sa.Column("created_by", sa.Integer()),
            sa.Column("updated_by", sa.Integer()),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_lc_compatibility_matrix_fhir_id", "lc_compatibility_matrix", ["fhir_id"])

    if not _table_exists("lc_upgrade_paths"):
        op.create_table(
            "lc_upgrade_paths",
            sa.Column("component", sa.String(), nullable=False),
            sa.Column("from_version", sa.String(), nullable=False),
            sa.Column("to_version", sa.String(), nullable=False),
            sa.Column("severity", sa.String(), default="medium"),
            sa.Column("steps", sa.JSON()),
            sa.Column("prerequisites", sa.JSON()),
            sa.Column("breaking_changes", sa.JSON()),
            sa.Column("estimated_duration_minutes", sa.Integer(), default=0),
            sa.Column("rollback_plan", sa.Text()),
            sa.Column("created_by", sa.Integer()),
            sa.Column("updated_by", sa.Integer()),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_lc_upgrade_paths_fhir_id", "lc_upgrade_paths", ["fhir_id"])

    if not _table_exists("lc_deprecation_notices"):
        op.create_table(
            "lc_deprecation_notices",
            sa.Column("component_id", sa.String(), sa.ForeignKey("lc_component_registry.id"), nullable=False),
            sa.Column("component_name", sa.String()),
            sa.Column("current_version", sa.String()),
            sa.Column("deprecation_policy", sa.String(), default="notice_90_days"),
            sa.Column("sunset_date", sa.DateTime(timezone=True)),
            sa.Column("replacement_component", sa.String()),
            sa.Column("migration_guide", sa.Text()),
            sa.Column("announced_at", sa.DateTime(timezone=True)),
            sa.Column("announced_by", sa.String()),
            sa.Column("rescinded_at", sa.DateTime(timezone=True)),
            sa.Column("created_by", sa.Integer()),
            sa.Column("updated_by", sa.Integer()),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_lc_deprecation_notices_fhir_id", "lc_deprecation_notices", ["fhir_id"])
        op.create_index("ix_lc_deprecation_notices_component_id", "lc_deprecation_notices", ["component_id"])



def downgrade() -> None:
    if _table_exists("lc_deprecation_notices"):
        op.drop_table("lc_deprecation_notices")
    if _table_exists("lc_upgrade_paths"):
        op.drop_table("lc_upgrade_paths")
    if _table_exists("lc_compatibility_matrix"):
        op.drop_table("lc_compatibility_matrix")
    if _table_exists("lc_releases"):
        op.drop_table("lc_releases")
    if _table_exists("lc_component_registry"):
        op.drop_table("lc_component_registry")
