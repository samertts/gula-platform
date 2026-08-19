"""Create tenant-scoped national search persistence.

Revision ID: 20260819_0004
Revises: 20260819_0003
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260819_0004"
down_revision = "20260819_0003"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    return inspect(op.get_bind()).has_table(table_name)


def _index_names(table_name: str) -> set[str]:
    return {
        index.get("name")
        for index in inspect(op.get_bind()).get_indexes(table_name)
        if index.get("name")
    }


def _ensure_indexes(table_name: str, definitions: list[tuple[str, list[str]]]) -> None:
    existing = _index_names(table_name)
    for name, columns in definitions:
        if name not in existing:
            op.create_index(name, table_name, columns)


def upgrade() -> None:
    if not _table_exists("national_search_saved_searches"):
        op.create_table(
            "national_search_saved_searches",
            sa.Column("id", sa.String(26), nullable=False),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("query", sa.JSON(), nullable=True),
            sa.Column("index_types", sa.JSON(), nullable=True),
            sa.Column("created_by", sa.String(100), nullable=True),
            sa.Column("scheduled", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("schedule_cron", sa.String(100), nullable=True),
            sa.ForeignKeyConstraint(["lab_id"], ["labs.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    elif "lab_id" not in {column["name"] for column in inspect(op.get_bind()).get_columns("national_search_saved_searches")}:
        raise RuntimeError(
            "national_search_saved_searches exists without lab_id; provide an approved tenant backfill before migration"
        )

    _ensure_indexes(
        "national_search_saved_searches",
        [
            ("ix_national_search_saved_searches_fhir_id", ["fhir_id"]),
            ("ix_national_search_saved_searches_lab_id", ["lab_id"]),
            ("ix_nat_search_saved_user", ["lab_id", "created_by", "name"]),
            ("ix_nat_search_saved_lab_deleted", ["lab_id", "is_deleted"]),
        ],
    )

    if not _table_exists("national_search_results"):
        op.create_table(
            "national_search_results",
            sa.Column("id", sa.String(26), nullable=False),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("query_id", sa.String(26), nullable=False),
            sa.Column("index_type", sa.String(50), nullable=False),
            sa.Column("resource_id", sa.String(26), nullable=False),
            sa.Column("resource_type", sa.String(100), nullable=True),
            sa.Column("score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("title", sa.String(500), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("highlights", sa.JSON(), nullable=True),
            sa.Column("matched_fields", sa.JSON(), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.Column("url", sa.String(1000), nullable=True),
            sa.ForeignKeyConstraint(["lab_id"], ["labs.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    elif "lab_id" not in {column["name"] for column in inspect(op.get_bind()).get_columns("national_search_results")}:
        raise RuntimeError(
            "national_search_results exists without lab_id; provide an approved tenant backfill before migration"
        )

    _ensure_indexes(
        "national_search_results",
        [
            ("ix_national_search_results_fhir_id", ["fhir_id"]),
            ("ix_national_search_results_lab_id", ["lab_id"]),
            ("ix_nat_search_result_query", ["lab_id", "query_id", "score"]),
            ("ix_nat_search_result_type_resource", ["lab_id", "index_type", "resource_id"]),
            ("ix_nat_search_result_lab_deleted", ["lab_id", "is_deleted"]),
        ],
    )


def downgrade() -> None:
    if _table_exists("national_search_results"):
        op.drop_table("national_search_results")
    if _table_exists("national_search_saved_searches"):
        op.drop_table("national_search_saved_searches")
