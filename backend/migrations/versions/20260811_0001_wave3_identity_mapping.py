"""Wave 3: reversible mapping from legacy accounts to NIAM accounts.

Revision ID: 20260811_0001
Revises: 20260723_0002
"""

from __future__ import annotations

from alembic import context, op
import sqlalchemy as sa


revision = "20260811_0001"
down_revision = "20260723_0002"
branch_labels = None
depends_on = None

_TABLE = "niam_legacy_account_links"


def upgrade() -> None:
    if context.is_offline_mode():
        op.create_table(
            _TABLE,
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("source_kind", sa.String(length=20), nullable=False),
            sa.Column("legacy_account_id", sa.Integer(), nullable=False),
            sa.Column("canonical_account_id", sa.String(length=26), nullable=True),
            sa.Column("source_fingerprint", sa.String(length=128), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
            sa.Column("collision_reason", sa.Text(), nullable=True),
            sa.Column("mapping_version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("rollback_token", sa.String(length=64), nullable=False),
            sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("migrated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("rolled_back_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("source_kind", "legacy_account_id", name="uq_niam_legacy_account_link_source"),
            sa.UniqueConstraint("rollback_token", name="uq_niam_legacy_account_link_rollback"),
        )
        op.create_index("ix_niam_legacy_account_links_status", _TABLE, ["status"])
        op.create_index("ix_niam_legacy_account_links_fingerprint", _TABLE, ["source_fingerprint"])
        op.create_index("ix_niam_legacy_account_links_canonical", _TABLE, ["canonical_account_id"])
        return
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if _TABLE in inspector.get_table_names():
        return

    op.create_table(
        _TABLE,
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column("source_kind", sa.String(length=20), nullable=False),
        sa.Column("legacy_account_id", sa.Integer(), nullable=False),
        sa.Column(
            "canonical_account_id",
            sa.String(length=26),
            sa.ForeignKey("niam_accounts.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("source_fingerprint", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("collision_reason", sa.Text(), nullable=True),
        sa.Column("mapping_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("rollback_token", sa.String(length=64), nullable=False),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("migrated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rolled_back_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_kind", "legacy_account_id", name="uq_niam_legacy_account_link_source"
        ),
        sa.UniqueConstraint("rollback_token", name="uq_niam_legacy_account_link_rollback"),
    )
    op.create_index(
        "ix_niam_legacy_account_links_status",
        _TABLE,
        ["status"],
    )
    op.create_index(
        "ix_niam_legacy_account_links_fingerprint",
        _TABLE,
        ["source_fingerprint"],
    )
    op.create_index(
        "ix_niam_legacy_account_links_canonical",
        _TABLE,
        ["canonical_account_id"],
    )


def downgrade() -> None:
    if context.is_offline_mode():
        op.drop_index("ix_niam_legacy_account_links_canonical", table_name=_TABLE)
        op.drop_index("ix_niam_legacy_account_links_fingerprint", table_name=_TABLE)
        op.drop_index("ix_niam_legacy_account_links_status", table_name=_TABLE)
        op.drop_table(_TABLE)
        return
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if _TABLE not in inspector.get_table_names():
        return
    op.drop_index("ix_niam_legacy_account_links_canonical", table_name=_TABLE)
    op.drop_index("ix_niam_legacy_account_links_fingerprint", table_name=_TABLE)
    op.drop_index("ix_niam_legacy_account_links_status", table_name=_TABLE)
    op.drop_table(_TABLE)
