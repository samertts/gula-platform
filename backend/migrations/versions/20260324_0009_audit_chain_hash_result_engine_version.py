"""Add chain_hash to audit_logs; add clinical_engine_version to lab_results.

audit_logs:
  + chain_hash              VARCHAR(64)  NULL  indexed
    SHA-256 hash chain column — each entry hashes (prev_hash + record).
    Populated by audit_service.log_action().  NULL on legacy rows.

lab_results:
  + clinical_engine_version VARCHAR(20)  NULL
    Records which clinical engine version last evaluated this result,
    so historical evaluations remain interpretable after rule changes.

Revision ID : 20260324_0009
Revises     : 20260324_0008
Create Date : 2026-03-24
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision      = "20260324_0009"
down_revision = "20260324_0008"
branch_labels = None
depends_on    = None


def _col_exists(table: str, col: str) -> bool:
    return col in [c["name"] for c in inspect(op.get_bind()).get_columns(table)]


def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def upgrade() -> None:
    # audit_logs.chain_hash
    if _table_exists("audit_logs") and not _col_exists("audit_logs", "chain_hash"):
        op.add_column("audit_logs", sa.Column("chain_hash", sa.String(64), nullable=True))
        op.create_index("ix_audit_logs_chain_hash", "audit_logs", ["chain_hash"])

    # lab_results.clinical_engine_version
    if _table_exists("lab_results") and not _col_exists("lab_results", "clinical_engine_version"):
        op.add_column(
            "lab_results",
            sa.Column("clinical_engine_version", sa.String(20), nullable=True),
        )


def downgrade() -> None:
    if _table_exists("lab_results") and _col_exists("lab_results", "clinical_engine_version"):
        op.drop_column("lab_results", "clinical_engine_version")

    if _table_exists("audit_logs") and _col_exists("audit_logs", "chain_hash"):
        index_names = {index["name"] for index in inspect(op.get_bind()).get_indexes("audit_logs")}
        if "ix_audit_logs_chain_hash" in index_names:
            op.drop_index("ix_audit_logs_chain_hash", table_name="audit_logs")
        op.drop_column("audit_logs", "chain_hash")
