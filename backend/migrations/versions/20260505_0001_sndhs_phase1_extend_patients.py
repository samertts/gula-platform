"""SNDHS-lite Phase 1 — Step A: extend patients (NON-BLOCKING).

Adds the SNDHS-lite identity / consent columns to ``patients``.
All columns are NULL-able with safe defaults so the migration cannot
take a long lock and cannot break existing rows.

Additions
---------
- ``national_id``      VARCHAR(20)   NULL          (NO unique yet — see step F)
- ``sndhs_health_id``  UUID          DEFAULT gen_random_uuid()  NULL
                       Parallel to the existing ``health_id`` String(20).
                       The original column is preserved untouched.
- ``identity_level``   INT           DEFAULT 1     NOT NULL on default; column
                       added with server_default so existing rows get 1.
- ``consent_flags``    JSONB         DEFAULT '{}'::jsonb

Why a parallel ``sndhs_health_id`` instead of replacing ``health_id``:
the running code in ``backend/app/models/patient.py`` and downstream
queries depend on ``health_id`` (String(20)). Adding a parallel UUID
column lets the new SNDHS endpoints adopt UUIDs without breaking the
LIS surface. We migrate consumers behind ``ENABLE_NATIONAL_ID`` feature
flag (see ``backend/app/core/sndhs_flags.py``).

Operational properties
----------------------
- ``ADD COLUMN`` of a NULLable column with a server_default in PostgreSQL
  ≥ 11 is metadata-only and does NOT rewrite the table.
- No NOT NULL, no UNIQUE here — those land in Phase-1 step F after the
  backfill is verified.
- Idempotent: every change is wrapped in ``_has_column`` guards.

Revision ID : 20260505_0001
Revises     : 20260503_0001
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text
from sqlalchemy.dialects import postgresql


revision = "20260505_0001"
down_revision = "20260503_0001"
branch_labels = None
depends_on = None


# ── Helpers ───────────────────────────────────────────────────────────────────


def _has_column(table: str, column: str) -> bool:
    insp = inspect(op.get_bind())
    return any(c["name"] == column for c in insp.get_columns(table))


def _pg() -> bool:
    return op.get_bind().dialect.name == "postgresql"


# ── Upgrade ───────────────────────────────────────────────────────────────────


def upgrade() -> None:
    if _pg():
        # gen_random_uuid() lives in pgcrypto. uuid-ossp would also work.
        op.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))

    if not _has_column("patients", "national_id"):
        op.add_column(
            "patients",
            sa.Column("national_id", sa.String(20), nullable=True),
        )

    if not _has_column("patients", "sndhs_health_id"):
        # UUID with a DEFAULT — existing rows get a value via server_default
        # without requiring a table rewrite (PG ≥ 11).
        if _pg():
            op.add_column(
                "patients",
                sa.Column(
                    "sndhs_health_id",
                    postgresql.UUID(as_uuid=True),
                    server_default=sa.text("gen_random_uuid()"),
                    nullable=True,
                ),
            )
        else:
            op.add_column(
                "patients",
                sa.Column("sndhs_health_id", sa.String(36), nullable=True),
            )

    if not _has_column("patients", "identity_level"):
        op.add_column(
            "patients",
            sa.Column(
                "identity_level",
                sa.Integer(),
                server_default=sa.text("1"),
                nullable=True,
            ),
        )

    if not _has_column("patients", "consent_flags"):
        if _pg():
            op.add_column(
                "patients",
                sa.Column(
                    "consent_flags",
                    postgresql.JSONB(astext_type=sa.Text()),
                    server_default=sa.text("'{}'::jsonb"),
                    nullable=True,
                ),
            )
        else:
            op.add_column(
                "patients",
                sa.Column(
                    "consent_flags",
                    sa.JSON(),
                    server_default=sa.text("'{}'"),
                    nullable=True,
                ),
            )


# ── Downgrade ─────────────────────────────────────────────────────────────────


def downgrade() -> None:
    """Reverse only the additions made above. Pure metadata DDL — no data
    is touched on existing rows that other migrations care about. Each
    drop is guarded so re-running is safe."""
    for col in ("consent_flags", "identity_level", "sndhs_health_id", "national_id"):
        if _has_column("patients", col):
            op.drop_column("patients", col)
