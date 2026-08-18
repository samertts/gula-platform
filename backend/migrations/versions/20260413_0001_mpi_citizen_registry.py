"""MPI: canonical citizen registry + identity claims + hash-chained merge audit.

Revision ID: 20260413_0001
Revises    : 20260407_0001
Create Date: 2026-04-13

Adds three national-layer tables:

  1. citizens           — canonical identity, one row per real person
  2. identity_claims    — bridge (lab_id, patient_id) → citizen_id
  3. mpi_merge_audit    — append-only, hash-chained ledger of identity decisions

All three are idempotent (guarded by `_has_table`) so re-running is safe.
Partial unique index on `citizens.nid_hash` (WHERE nid_hash IS NOT NULL)
is created via raw DDL for PostgreSQL portability.
"""
from alembic import context, op
import sqlalchemy as sa
from sqlalchemy import inspect


revision      = "20260413_0001"
down_revision = "20260407_0001"
branch_labels = None
depends_on    = None


# ─── Idempotency helpers (copied from 20260407_0001_claims_tables.py) ─────────

def _has_table(name: str) -> bool:
    if context.is_offline_mode():
        return False
    bind = op.get_bind()
    return inspect(bind).has_table(name)


def _has_column(table: str, column: str) -> bool:
    if context.is_offline_mode():
        return False
    bind = op.get_bind()
    if not inspect(bind).has_table(table):
        return False
    cols = [c["name"] for c in inspect(bind).get_columns(table)]
    return column in cols


def _index_exists(index: str) -> bool:
    if context.is_offline_mode():
        return False
    bind = op.get_bind()
    inspector = inspect(bind)
    for table in inspector.get_table_names():
        idx_names = [i["name"] for i in inspector.get_indexes(table)]
        if index in idx_names:
            return True
    return False


def _is_postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


# ─── Upgrade ─────────────────────────────────────────────────────────────────

def upgrade() -> None:

    # ── 1. citizens ──────────────────────────────────────────────────────────
    if not _has_table("citizens"):
        op.create_table(
            "citizens",
            sa.Column("id",                 sa.BigInteger(),        primary_key=True, autoincrement=True),
            sa.Column("citizen_ulid",       sa.String(26),          nullable=False, unique=True),
            sa.Column("nid_hash",           sa.String(255),         nullable=True),
            sa.Column("nid_verified",       sa.Boolean(),           nullable=False, server_default=sa.false()),
            sa.Column("phone_last10",       sa.String(10),          nullable=True),
            sa.Column("birth_year",         sa.SmallInteger(),      nullable=True),
            sa.Column("birth_month",        sa.SmallInteger(),      nullable=True),
            sa.Column("birth_day",          sa.SmallInteger(),      nullable=True),
            sa.Column("gender",             sa.String(1),           nullable=True),
            sa.Column("name_canonical",     sa.String(255),         nullable=False),
            sa.Column("name_blocking_key",  sa.String(20),          nullable=False),
            sa.Column("family_id_hash",     sa.String(255),         nullable=True),
            sa.Column("merged_into_id",     sa.BigInteger(),
                      sa.ForeignKey("citizens.id", ondelete="RESTRICT"), nullable=True),
            sa.Column("status",             sa.String(20),          nullable=False, server_default="active"),
            sa.Column("version",            sa.Integer(),           nullable=False, server_default="1"),
            sa.Column("created_at",         sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at",         sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    if not _index_exists("ix_citizens_blocking"):
        op.create_index("ix_citizens_blocking", "citizens",
                        ["name_blocking_key", "birth_year", "gender"])
    if not _index_exists("ix_citizens_phone"):
        op.create_index("ix_citizens_phone", "citizens", ["phone_last10"])
    if not _index_exists("ix_citizens_family"):
        op.create_index("ix_citizens_family", "citizens", ["family_id_hash"])
    if not _index_exists("ix_citizens_merged"):
        op.create_index("ix_citizens_merged", "citizens", ["merged_into_id"])
    if not _index_exists("ix_citizens_status"):
        op.create_index("ix_citizens_status", "citizens", ["status"])
    if not _index_exists("ix_citizens_ulid"):
        op.create_index("ix_citizens_ulid", "citizens", ["citizen_ulid"], unique=True)

    # Partial unique index on nid_hash (PostgreSQL only — SQLite gets a plain
    # index as a fallback for dev environments)
    if not _index_exists("uq_citizens_nid_hash"):
        if _is_postgres():
            op.execute(
                "CREATE UNIQUE INDEX uq_citizens_nid_hash "
                "ON citizens (nid_hash) WHERE nid_hash IS NOT NULL"
            )
        else:
            op.create_index("uq_citizens_nid_hash", "citizens", ["nid_hash"])

    # ── 2. identity_claims ───────────────────────────────────────────────────
    if not _has_table("identity_claims"):
        op.create_table(
            "identity_claims",
            sa.Column("id",                 sa.BigInteger(),   primary_key=True, autoincrement=True),
            sa.Column("citizen_id",         sa.BigInteger(),
                      sa.ForeignKey("citizens.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("lab_id",             sa.Integer(),
                      sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("local_patient_id",   sa.Integer(),
                      sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
            sa.Column("match_method",       sa.String(20),     nullable=False),
            sa.Column("match_score",        sa.Numeric(4, 3),  nullable=True),
            sa.Column("match_features",     sa.JSON(),         nullable=True),
            sa.Column("claimed_by_user_id", sa.Integer(),
                      sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("created_at",         sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint("lab_id", "local_patient_id",
                                name="uq_identity_claims_lab_patient"),
        )

    if not _index_exists("ix_identity_claims_citizen"):
        op.create_index("ix_identity_claims_citizen", "identity_claims", ["citizen_id"])
    if not _index_exists("ix_identity_claims_lab_patient"):
        op.create_index("ix_identity_claims_lab_patient", "identity_claims",
                        ["lab_id", "local_patient_id"])
    if not _index_exists("ix_identity_claims_method"):
        op.create_index("ix_identity_claims_method", "identity_claims", ["match_method"])

    # ── 3. mpi_merge_audit ───────────────────────────────────────────────────
    if not _has_table("mpi_merge_audit"):
        op.create_table(
            "mpi_merge_audit",
            sa.Column("id",                   sa.BigInteger(),  primary_key=True, autoincrement=True),
            sa.Column("event_type",           sa.String(20),    nullable=False),
            sa.Column("primary_citizen_id",   sa.BigInteger(),
                      sa.ForeignKey("citizens.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("secondary_citizen_id", sa.BigInteger(),
                      sa.ForeignKey("citizens.id", ondelete="RESTRICT"), nullable=True),
            sa.Column("match_score",          sa.Numeric(4, 3), nullable=True),
            sa.Column("match_features",       sa.JSON(),        nullable=True),
            sa.Column("decision_reason",      sa.String(500),   nullable=True),
            sa.Column("decided_by_user_id",   sa.Integer(),
                      sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("occurred_at",          sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("prev_hash",            sa.String(64),    nullable=False),
            sa.Column("entry_hash",           sa.String(64),    nullable=False, unique=True),
        )

    if not _index_exists("ix_merge_audit_primary"):
        op.create_index("ix_merge_audit_primary", "mpi_merge_audit", ["primary_citizen_id"])
    if not _index_exists("ix_merge_audit_secondary"):
        op.create_index("ix_merge_audit_secondary", "mpi_merge_audit", ["secondary_citizen_id"])
    if not _index_exists("ix_merge_audit_occurred"):
        op.create_index("ix_merge_audit_occurred", "mpi_merge_audit", ["occurred_at"])


# ─── Downgrade ───────────────────────────────────────────────────────────────

def downgrade() -> None:
    """Reverse order to respect foreign-key dependencies."""
    if _has_table("mpi_merge_audit"):
        op.drop_table("mpi_merge_audit")
    if _has_table("identity_claims"):
        op.drop_table("identity_claims")
    if _has_table("citizens"):
        if _is_postgres() and _index_exists("uq_citizens_nid_hash"):
            op.execute("DROP INDEX IF EXISTS uq_citizens_nid_hash")
        op.drop_table("citizens")
