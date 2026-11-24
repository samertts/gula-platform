"""Unify foundation: patient identifier widening, organization/facility columns,
claims per-lab idempotency, and the identity-authorities registry.

Revision ID: 20261114_0001
Revises: 20260908_0001
Create Date: 2026-11-14

Forward-only reconciliation of local-lineage schema additions onto the
origin/main migration head. Every statement is additive or widening and is
guarded by runtime inspection, so it is safe on an existing database and on a
fresh one.

Carried forward from local revisions:
  * 20260802_0001_widen_patient_health_id  (health_id varchar(20)->32,
    gender varchar(1)->10, organization/facility bootstrap columns)
  * 20260805_0001_claims_lab_idempotency   (global unique -> composite
    (lab_id, idempotency_key))

The `niam_identity_authorities` table (local 20260723_0002 addition) is created
here because the preserved professional registry references it and origin/main
does not otherwise define it.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "20261114_0001"
down_revision = "20260908_0001"
branch_labels = None
depends_on = None


def _inspector():
    return inspect(op.get_bind())


def _has_table(name: str) -> bool:
    return name in _inspector().get_table_names()


def _columns(table: str) -> set[str]:
    return {c["name"] for c in _inspector().get_columns(table)}


def _widen(table: str, column: str, length: int, existing_length: int) -> None:
    if not _has_table(table):
        return
    if column not in _columns(table):
        return
    op.alter_column(
        table,
        column,
        type_=sa.String(length),
        existing_type=sa.String(existing_length),
    )


def _add_column(table: str, column: str, ddl_type: str) -> None:
    if not _has_table(table):
        return
    op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {ddl_type}")


def _drop_not_null(table: str, column: str) -> None:
    if not _has_table(table):
        return
    if column in _columns(table):
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} DROP NOT NULL")


def upgrade() -> None:
    # ── Widened patient identifiers (GULA- + 16 hex = 21 chars) ───────────────
    _widen("patients", "health_id", 32, 20)
    _widen("canonical_patients", "health_id", 32, 20)
    _widen("patients", "gender", 10, 1)
    _widen("canonical_patients", "gender", 10, 1)
    _widen("citizens", "gender", 10, 1)

    # ── Organization / facility bootstrap columns ────────────────────────────
    _drop_not_null("organizations", "name")
    for column, ddl in (
        ("org_id", "varchar(100)"),
        ("name_en", "varchar(200)"),
        ("name_ar", "varchar(200)"),
        ("parent_org_id", "varchar(100)"),
        ("contact_email", "varchar(200)"),
        ("contact_phone", "varchar(30)"),
        ("address", "text"),
        ("created_at", "timestamptz"),
        ("updated_at", "timestamptz"),
    ):
        _add_column("organizations", column, ddl)

    _drop_not_null("facilities", "name")
    for column, ddl in (
        ("facility_id", "varchar(100)"),
        ("name_en", "varchar(200)"),
        ("name_ar", "varchar(200)"),
        ("created_at", "timestamptz"),
    ):
        _add_column("facilities", column, ddl)

    # ── Claims idempotency scoped per lab ────────────────────────────────────
    if _has_table("claims"):
        if op.get_bind().dialect.name == "postgresql":
            op.execute(
                "ALTER TABLE claims DROP CONSTRAINT IF EXISTS claims_idempotency_key_key"
            )
        if "uq_claims_lab_idempotency" not in {
            i["name"] for i in _inspector().get_indexes("claims")
        }:
            op.create_index(
                "uq_claims_lab_idempotency",
                "claims",
                ["lab_id", "idempotency_key"],
                unique=True,
            )

    # ── Identity authorities (referenced by the professional registry) ──────
    if not _has_table("niam_identity_authorities"):
        op.create_table(
            "niam_identity_authorities",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False),
            sa.Column("authority_id", sa.String(length=100), nullable=False),
            sa.Column("name_en", sa.String(length=300), nullable=False),
            sa.Column("name_ar", sa.String(length=300), nullable=True),
            sa.Column("authority_type", sa.String(length=50), nullable=False),
            sa.Column("jurisdiction", sa.String(length=30), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("authority_id"),
        )
        op.create_index(
            "ix_niam_identity_authorities_uuid",
            "niam_identity_authorities",
            ["uuid"],
        )
        op.create_index(
            "ix_niam_identity_authorities_authority_id",
            "niam_identity_authorities",
            ["authority_id"],
        )
        op.create_index(
            "ix_niam_identity_authorities_authority_type",
            "niam_identity_authorities",
            ["authority_type"],
        )
        op.create_index(
            "ix_niam_identity_authorities_status",
            "niam_identity_authorities",
            ["status"],
        )


def downgrade() -> None:
    if _has_table("niam_identity_authorities"):
        op.drop_table("niam_identity_authorities")

    if _has_table("claims"):
        try:
            op.drop_index("uq_claims_lab_idempotency", table_name="claims")
        except Exception:  # noqa: BLE001 - index may not exist
            pass
        if op.get_bind().dialect.name == "postgresql":
            op.execute(
                "ALTER TABLE claims ADD CONSTRAINT claims_idempotency_key_key "
                "UNIQUE (idempotency_key)"
            )

    # Widening is intentionally not reversed: narrowing columns could truncate
    # production data. The organization/facility columns are left in place for
    # the same reason (additive, nullable).
