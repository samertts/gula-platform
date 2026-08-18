"""Consent: minimal production consent layer.

Revision ID: 20260417_0001
Revises    : 20260413_0001
Create Date: 2026-04-17

Adds the `consents` table — the governing layer that turns the platform from
technically complete into legally operable. Without it, any cross-lab or
doctor-initiated read of a citizen's record has no lawful basis.

Design rules (from spec):
  - Primary key is a ULID (string), never an autoincrement BigInt
  - gpid   = citizen_ulid (the subject whose data is being shared)
  - grantee_id = actor_id (doctor/lab user) who is being authorized
  - scope  = namespaced permission string (e.g. 'read:lab_results')
  - status = 'active' | 'revoked' | 'expired'
  - expires_at is REQUIRED (no open-ended consent; hard cap 72h at the API)
  - UNIQUE (gpid, grantee_id, scope, status) prevents duplicate active grants

Two indexes cover the two hot paths:
  - idx_consents_lookup  — per-request middleware check (gpid+grantee+status+expiry)
  - idx_consents_expiry  — expiry sweeper / analytics
"""
from alembic import context, op
import sqlalchemy as sa
from sqlalchemy import inspect


revision      = "20260417_0001"
down_revision = "20260413_0001"
branch_labels = None
depends_on    = None


def _has_table(name: str) -> bool:
    if context.is_offline_mode():
        return False
    bind = op.get_bind()
    return inspect(bind).has_table(name)


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


def upgrade() -> None:
    if not _has_table("consents"):
        op.create_table(
            "consents",
            sa.Column("id",          sa.String(26),  primary_key=True),
            sa.Column("gpid",        sa.String(26),  nullable=False),
            sa.Column("grantee_id",  sa.String(64),  nullable=False),
            sa.Column("scope",       sa.String(64),  nullable=False),
            sa.Column("status",      sa.String(16),  nullable=False, server_default="active"),
            sa.Column("expires_at",  sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at",  sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.func.now()),
            sa.Column("revoked_at",  sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_by_user_id", sa.Integer(),
                      sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.UniqueConstraint("gpid", "grantee_id", "scope", "status",
                                name="uq_consents_active_tuple"),
        )

    if not _index_exists("idx_consents_lookup"):
        op.create_index(
            "idx_consents_lookup", "consents",
            ["gpid", "grantee_id", "status", "expires_at"],
        )

    if not _index_exists("idx_consents_expiry"):
        op.create_index("idx_consents_expiry", "consents", ["expires_at"])

    if not _index_exists("idx_consents_gpid"):
        op.create_index("idx_consents_gpid", "consents", ["gpid"])


def downgrade() -> None:
    if _has_table("consents"):
        op.drop_table("consents")
