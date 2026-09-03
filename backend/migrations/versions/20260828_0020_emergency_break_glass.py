"""Add canonical emergency break-glass sessions and immutable events.

Synthetic-only, additive migration. No external emergency provider is connected.
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "20260828_0020"
down_revision: str | None = "20260828_0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def upgrade() -> None:
    if not _exists("core_emergency_break_glass"):
        op.create_table(
            "core_emergency_break_glass",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("request_id", sa.String(100), nullable=False),
            sa.Column("patient_person_id", sa.String(26), nullable=False),
            sa.Column("organization_id", sa.String(26), nullable=False),
            sa.Column("facility_id", sa.String(26), nullable=False),
            sa.Column("workspace_id", sa.String(26), nullable=False),
            sa.Column("requested_by_account_id", sa.String(26), nullable=False),
            sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("purpose", sa.String(160), nullable=False),
            sa.Column("resource_scope", sa.JSON(), nullable=False),
            sa.Column("status", sa.String(24), nullable=False, server_default="REQUESTED"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("request_id", name="uq_core_break_glass_request"),
            sa.CheckConstraint("status IN ('REQUESTED','ACTIVE','EXPIRED','REVOKED','DENIED')", name="ck_core_break_glass_status"),
            sa.CheckConstraint("version > 0", name="ck_core_break_glass_version"),
            sa.CheckConstraint("expires_at > requested_at", name="ck_core_break_glass_expiry"),
        )
        op.create_index("ix_core_break_glass_active_scope", "core_emergency_break_glass", ["organization_id", "facility_id", "workspace_id", "patient_person_id", "status"])

    if not _exists("core_emergency_break_glass_events"):
        op.create_table(
            "core_emergency_break_glass_events",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("break_glass_id", sa.String(26), nullable=False),
            sa.Column("event_key", sa.String(160), nullable=False),
            sa.Column("event_type", sa.String(48), nullable=False),
            sa.Column("actor_account_id", sa.String(26), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("event_key", name="uq_core_break_glass_event_key"),
            sa.CheckConstraint("event_type IN ('ATTEMPTED','ACTIVATED','EXPIRED','REVOKED','DENIED','REVIEWED')", name="ck_core_break_glass_event_type"),
        )
        op.create_index("ix_core_break_glass_event_session", "core_emergency_break_glass_events", ["break_glass_id", "created_at"])


def downgrade() -> None:
    if _exists("core_emergency_break_glass_events"):
        op.drop_index("ix_core_break_glass_event_session", table_name="core_emergency_break_glass_events")
        op.drop_table("core_emergency_break_glass_events")
    if _exists("core_emergency_break_glass"):
        op.drop_index("ix_core_break_glass_active_scope", table_name="core_emergency_break_glass")
        op.drop_table("core_emergency_break_glass")
