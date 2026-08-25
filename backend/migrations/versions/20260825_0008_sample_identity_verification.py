"""Add versioned human identity verification for samples.

Revision ID: 20260825_0008
Revises: 20260823_0007
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260825_0008"
down_revision = "20260823_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("samples") as batch_op:
        batch_op.add_column(sa.Column("verified_by", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("verification_method", sa.String(length=64), nullable=True))
        batch_op.add_column(
            sa.Column("version", sa.Integer(), nullable=False, server_default="1")
        )
        batch_op.create_foreign_key(
            "fk_samples_verified_by_lab_users",
            "lab_users",
            ["verified_by"],
            ["id"],
            ondelete="SET NULL",
        )
    op.create_index("ix_samples_verified_by", "samples", ["verified_by"])


def downgrade() -> None:
    op.drop_index("ix_samples_verified_by", table_name="samples")
    with op.batch_alter_table("samples") as batch_op:
        batch_op.drop_constraint("fk_samples_verified_by_lab_users", type_="foreignkey")
        batch_op.drop_column("version")
        batch_op.drop_column("verification_method")
        batch_op.drop_column("verified_at")
        batch_op.drop_column("verified_by")
