"""SNDHS-lite Phase 1 — Step B: index patients.national_id (NON-BLOCKING).

Creates a B-tree index on ``patients.national_id`` using
``CREATE INDEX CONCURRENTLY`` so production traffic is not blocked.

Notes
-----
- Uses ``op.get_context().autocommit_block()`` because
  ``CREATE INDEX CONCURRENTLY`` cannot run inside a transaction.
- ``IF NOT EXISTS`` makes the migration idempotent.
- The unique partial index lands later (Phase 1 step F) once data is
  clean — a UNIQUE here would conflict with duplicate / NULL values
  while the backfill runs.

Revision ID : 20260505_0002
Revises     : 20260505_0001
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text


revision = "20260505_0002"
down_revision = "20260505_0001"
branch_labels = None
depends_on = None


def _pg() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def _index_exists(name: str) -> bool:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        # Other dialects: best-effort via inspector
        return name in {ix["name"] for ix in inspect(bind).get_indexes("patients")}
    row = bind.execute(
        text("SELECT 1 FROM pg_indexes WHERE schemaname = current_schema() AND indexname = :n"),
        {"n": name},
    ).first()
    return row is not None


def upgrade() -> None:
    if not _pg():
        # Non-PG dialects (sqlite tests): use a normal index, no concurrency.
        if not _index_exists("ix_patients_national_id"):
            op.create_index("ix_patients_national_id", "patients", ["national_id"])
        return

    if _index_exists("ix_patients_national_id"):
        return

    # CREATE INDEX CONCURRENTLY must NOT run inside a tx.
    with op.get_context().autocommit_block():
        op.execute(
            text(
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_patients_national_id "
                "ON patients (national_id)"
            )
        )


def downgrade() -> None:
    if not _pg():
        if _index_exists("ix_patients_national_id"):
            op.drop_index("ix_patients_national_id", table_name="patients")
        return

    if not _index_exists("ix_patients_national_id"):
        return

    with op.get_context().autocommit_block():
        op.execute(text("DROP INDEX CONCURRENTLY IF EXISTS ix_patients_national_id"))
