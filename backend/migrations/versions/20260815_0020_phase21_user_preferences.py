"""Add privacy-separated user accessibility and health preferences.

Revision ID: 20260815_0020
Revises: 20260815_0019
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260815_0020"
down_revision = "20260815_0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "accessibility_profiles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("preferences", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["lab_users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lab_id"], ["labs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_accessibility_profiles_user"),
    )
    op.create_index(
        "ix_accessibility_profiles_user_lab",
        "accessibility_profiles",
        ["user_id", "lab_id"],
    )

    op.create_table(
        "health_preferences",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("encrypted_payload", sa.Text(), nullable=True),
        sa.Column("consent_granted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("consent_version", sa.String(length=32), nullable=True),
        sa.Column("consented_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["lab_users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lab_id"], ["labs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_health_preferences_user"),
    )
    op.create_index(
        "ix_health_preferences_user_lab",
        "health_preferences",
        ["user_id", "lab_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_health_preferences_user_lab", table_name="health_preferences")
    op.drop_table("health_preferences")
    op.drop_index("ix_accessibility_profiles_user_lab", table_name="accessibility_profiles")
    op.drop_table("accessibility_profiles")
