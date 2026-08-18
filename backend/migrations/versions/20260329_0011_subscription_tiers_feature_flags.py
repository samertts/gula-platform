"""Add subscription tiers, upgrade requests, demand scores, and feature flags.

Multi-tier SaaS architecture:
  - lab_subscriptions      : tier + deployment mode + security level per lab
  - upgrade_requests       : citizen/admin demand signals
  - upgrade_demand_scores  : aggregated weighted demand per lab
  - feature_flags          : per-lab feature overrides

Revision ID: 20260329_0011
Revises    : 20260324_0010
Create Date: 2026-03-29
"""
from alembic import context, op
import sqlalchemy as sa
from sqlalchemy import inspect

revision    = "20260329_0011"
down_revision = "20260324_0010"
branch_labels = None
depends_on    = None


def _has_table(name: str) -> bool:
    if context.is_offline_mode():
        return False
    bind = op.get_bind()
    return inspect(bind).has_table(name)


def _has_column(table: str, column: str) -> bool:
    if context.is_offline_mode():
        return False
    bind = op.get_bind()
    cols = [c["name"] for c in inspect(bind).get_columns(table)]
    return column in cols


def upgrade() -> None:
    # ── lab_subscriptions ─────────────────────────────────────────────────────
    if not _has_table("lab_subscriptions"):
        op.create_table(
            "lab_subscriptions",
            sa.Column("id",                   sa.Integer(),    primary_key=True),
            sa.Column("lab_id",               sa.Integer(),    sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("tier",                 sa.String(30),   nullable=False, server_default="starter"),
            sa.Column("deployment_mode",      sa.String(30),   nullable=False, server_default="single"),
            sa.Column("security_level",       sa.String(30),   nullable=False, server_default="standard"),
            sa.Column("is_active",            sa.Boolean(),    nullable=False, server_default="true"),
            sa.Column("trial_ends_at",        sa.DateTime(timezone=True), nullable=True),
            sa.Column("billing_cycle",        sa.String(20),   server_default="monthly"),
            sa.Column("monthly_price_usd",    sa.Float(),      server_default="0"),
            sa.Column("max_patients",         sa.Integer(),    server_default="500"),
            sa.Column("max_staff",            sa.Integer(),    server_default="5"),
            sa.Column("max_branches",         sa.Integer(),    server_default="1"),
            sa.Column("max_orders_per_day",   sa.Integer(),    server_default="100"),
            sa.Column("max_ai_calls_per_day", sa.Integer(),    server_default="0"),
            sa.Column("notes",                sa.Text(),       nullable=True),
            sa.Column("activated_at",         sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("expires_at",           sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at",           sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at",           sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_lab_subscriptions_lab_id", "lab_subscriptions", ["lab_id"], unique=True)
        op.create_index("ix_lab_subscriptions_tier",   "lab_subscriptions", ["tier"])

    # ── upgrade_requests ──────────────────────────────────────────────────────
    if not _has_table("upgrade_requests"):
        op.create_table(
            "upgrade_requests",
            sa.Column("id",                      sa.Integer(),   primary_key=True),
            sa.Column("lab_id",                  sa.Integer(),   sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("requester_id",            sa.Integer(),   sa.ForeignKey("users.id",  ondelete="SET NULL"), nullable=True),
            sa.Column("target_tier",             sa.String(30),  nullable=False),
            sa.Column("target_deployment_mode",  sa.String(30),  nullable=True),
            sa.Column("target_security_level",   sa.String(30),  nullable=True),
            sa.Column("reason",                  sa.Text(),      nullable=True),
            sa.Column("status",                  sa.String(20),  server_default="pending"),
            sa.Column("weight",                  sa.Float(),     server_default="1.0"),
            sa.Column("reviewed_by",             sa.Integer(),   sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("reviewed_at",             sa.DateTime(timezone=True), nullable=True),
            sa.Column("review_note",             sa.Text(),      nullable=True),
            sa.Column("created_at",              sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_upgrade_requests_lab_id",     "upgrade_requests", ["lab_id"])
        op.create_index("ix_upgrade_requests_status",     "upgrade_requests", ["status"])
        op.create_index("ix_upgrade_requests_lab_status", "upgrade_requests", ["lab_id", "status"])
        op.create_index("ix_upgrade_requests_created_at", "upgrade_requests", ["created_at"])

    # ── upgrade_demand_scores ─────────────────────────────────────────────────
    if not _has_table("upgrade_demand_scores"):
        op.create_table(
            "upgrade_demand_scores",
            sa.Column("id",               sa.Integer(), primary_key=True),
            sa.Column("lab_id",           sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("raw_score",        sa.Float(),   server_default="0"),
            sa.Column("unique_requesters",sa.Integer(), server_default="0"),
            sa.Column("weighted_score",   sa.Float(),   server_default="0"),
            sa.Column("last_request_at",  sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at",       sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_upgrade_demand_scores_lab_id",      "upgrade_demand_scores", ["lab_id"], unique=True)
        op.create_index("ix_upgrade_demand_scores_weighted",    "upgrade_demand_scores", ["weighted_score"])

    # ── feature_flags ─────────────────────────────────────────────────────────
    if not _has_table("feature_flags"):
        op.create_table(
            "feature_flags",
            sa.Column("id",          sa.Integer(),     primary_key=True),
            sa.Column("lab_id",      sa.Integer(),     sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("feature_key", sa.String(100),   nullable=False),
            sa.Column("is_enabled",  sa.Boolean(),     nullable=False, server_default="true"),
            sa.Column("reason",      sa.String(300),   nullable=True),
            sa.Column("set_by",      sa.Integer(),     sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("expires_at",  sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at",  sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_feature_flags_lab_id",  "feature_flags", ["lab_id"])
        op.create_index("ix_feature_flags_lab_key", "feature_flags", ["lab_id", "feature_key"], unique=True)

    # ── Seed all existing active labs with default starter subscription ────────
    op.execute("""
        INSERT INTO lab_subscriptions (lab_id, tier, deployment_mode, security_level,
            is_active, billing_cycle, monthly_price_usd,
            max_patients, max_staff, max_branches, max_orders_per_day, max_ai_calls_per_day)
        SELECT l.id, 'starter', 'single', 'standard',
               true, 'monthly', 0,
               500, 5, 1, 100, 0
        FROM labs l
        WHERE l.is_active = true
          AND NOT EXISTS (
              SELECT 1 FROM lab_subscriptions s WHERE s.lab_id = l.id
          )
    """)


def downgrade() -> None:
    for tbl in ["feature_flags", "upgrade_demand_scores", "upgrade_requests", "lab_subscriptions"]:
        if _has_table(tbl):
            op.drop_table(tbl)
