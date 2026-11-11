"""Add the canonical NIAM idempotency key store.

Revision ID: 20260908_0005
Revises: 20260908_0004

One shared table (`niam_idempotency_keys`) for the four Platform
Authority operations proven unsafe to retry blindly:
generate_api_key, issue_certificate, rotate_certificate, rotate_api_key
(docs/security/IDEMPOTENCY_CONTRACT_AND_GAP_REPORT.md). Design rationale,
alternatives considered, and the proven proof-harness semantics are in
docs/security/IDEMPOTENCY_SCHEMA_PROPOSAL.md and
docs/adr/ADR-026-niam-idempotency-key-store.md. No existing table is
touched; this is purely additive. Uniqueness is scoped by
(operation, actor_account_id, key_hash) -- Platform Authority has no
tenant dimension, so the acting identity is the correct security
boundary (a different actor supplying the identical literal key string
must never replay or collide with another actor's result).
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260908_0005"
down_revision = "20260908_0004"
branch_labels = None
depends_on = None

_TABLE = "niam_idempotency_keys"


def _drop_table_indexes(table_name: str) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    unique_constraints = {
        item["name"]
        for item in inspector.get_unique_constraints(table_name)
        if item.get("name")
    }
    for index in inspector.get_indexes(table_name):
        if index["name"] not in unique_constraints:
            op.drop_index(index["name"], table_name=table_name)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if _TABLE in inspector.get_table_names():
        return

    op.create_table(
        _TABLE,
        sa.Column("id", sa.String(length=26), primary_key=True, nullable=False),
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("operation", sa.String(length=50), nullable=False),
        sa.Column("actor_account_id", sa.String(length=26), nullable=False),
        sa.Column("key_hash", sa.String(length=64), nullable=False),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("result_type", sa.String(length=50), nullable=True),
        sa.Column("result_id", sa.String(length=26), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_account_id"], ["niam_accounts.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("uuid", name="uq_niam_idempotency_keys_uuid"),
        sa.UniqueConstraint(
            "operation", "actor_account_id", "key_hash", name="uq_niam_idempotency_scope",
        ),
    )
    for column in ("operation", "actor_account_id", "status", "result_type", "result_id"):
        op.create_index(f"ix_{_TABLE}_{column}", _TABLE, [column])
    op.create_index(f"ix_{_TABLE}_expires_at", _TABLE, ["expires_at"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if _TABLE in inspector.get_table_names():
        _drop_table_indexes(_TABLE)
        op.drop_table(_TABLE)
