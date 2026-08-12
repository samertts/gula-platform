"""SNDHS-lite Phase 1 — Step C: create ``visits`` table.

Visit-based architecture: every clinical action is anchored to a visit.
Phase 1 only creates the table and indexes; no consumer is mandatory yet
(the ``ENABLE_VISITS`` feature flag gates all writes/reads).

Schema
------
- id          UUID PK    DEFAULT gen_random_uuid()
- patient_id  INT FK → patients.id  ON DELETE CASCADE
- visit_type  VARCHAR(40) NOT NULL DEFAULT 'lab'
- status      VARCHAR(20) NOT NULL DEFAULT 'open'
- created_at  TIMESTAMPTZ DEFAULT now()
- closed_at   TIMESTAMPTZ NULL  (added now to avoid a second migration)

Why ``patient_id`` is INT, not UUID:
the existing ``patients`` table uses an auto-increment INT PK. Phase 1
must preserve compatibility; a UUID-keyed visits table referencing
INT-keyed patients is the safe interim shape. Phase 2 may introduce a
UUID surrogate on patients without breaking the column added here.

Idempotency
-----------
- Table creation guarded by ``_table_exists``.
- ``IF NOT EXISTS`` on indexes.

Revision ID : 20260505_0003
Revises     : 20260505_0002
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text
from sqlalchemy.dialects import postgresql


revision      = "20260505_0003"
down_revision = "20260505_0002"
branch_labels = None
depends_on    = None


def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def _pg() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if _table_exists("visits"):
        return

    if _pg():
        op.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))

    pk_default = sa.text("gen_random_uuid()") if _pg() else None

    op.create_table(
        "visits",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True) if _pg() else sa.String(36),
            primary_key=True,
            server_default=pk_default,
            nullable=False,
        ),
        sa.Column(
            "patient_id",
            sa.Integer(),
            sa.ForeignKey("patients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("visit_type", sa.String(40), nullable=False, server_default="lab"),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Indexes — non-CONCURRENT here because the table is brand new and empty.
    op.create_index("ix_visits_patient_id", "visits", ["patient_id"])
    op.create_index("ix_visits_status",     "visits", ["status"])
    op.create_index("ix_visits_created_at", "visits", ["created_at"])


def downgrade() -> None:
    if not _table_exists("visits"):
        return
    op.drop_index("ix_visits_created_at", table_name="visits")
    op.drop_index("ix_visits_status",     table_name="visits")
    op.drop_index("ix_visits_patient_id", table_name="visits")
    op.drop_table("visits")
