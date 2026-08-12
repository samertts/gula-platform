"""Financial Engine — Phase A: data-model bootstrap (safe, additive).

Revision ID: 20260506_0001
Revises    : 20260505_0006
Create Date: 2026-05-05

NOTE: This migration was previously authored with revision id ``20260505_0001``
and ``down_revision = 20260503_0001`` — colliding with the SNDHS Phase 1
extend-patients migration that landed in parallel. The duplicate revision
caused alembic to fail on every fresh deploy. This rename re-parents the
migration to the head of the SNDHS chain (``20260505_0006``) and renumbers
to ``20260506_0001`` — restoring a linear single-head history. Schema
behaviour is unchanged: this migration only creates new ``fin_*`` tables
that are independent of any SNDHS object.

Provider-billing / ranking / ads / fraud / clinical-governance / incentive
engine. Phase A is **purely additive**: it creates nine new tables that hold
no data at deploy time. None of them are referenced by any existing code
path, and the runtime engine itself is gated by two feature flags
(`ENABLE_FINANCIAL_ENGINE`, `ENABLE_ADS`) — both default OFF.

Production-safety rules honoured (per spec):
  • All columns are nullable (no NOT NULL constraints) except primary keys.
  • No foreign-key constraints — added in a later phase after backfill.
  • No long locks: every table is brand-new and empty, so CREATE TABLE +
    CREATE INDEX execute instantly with no contention. CREATE INDEX
    CONCURRENTLY is *not* used here because (a) it is illegal inside a
    transactional Alembic step, and (b) it is unnecessary for tables with
    zero rows. When future migrations backfill data and add indexes on
    populated tables, those migrations MUST use op.create_index(..., postgresql_concurrently=True)
    inside an autocommit block.
  • Every operation is idempotent: guarded by _has_table / _index_exists.
  • Downgrade drops the nine tables in reverse dependency-free order.

Naming: every Phase A table is prefixed with `fin_` to namespace the
Financial Engine cleanly. This avoids collision with the existing
`lab_subscriptions` table, the (future) generic `transactions` log, and any
business-domain `providers` concept that may emerge elsewhere.

Tables created:
  1. fin_providers           — billable entity (lab / clinic / doctor / institution)
  2. fin_subscriptions       — provider plan + status + expiry
  3. fin_transactions        — pricing-engine ledger (per-test fees, ad spend, refunds)
  4. fin_ads_campaigns       — sponsored-listing bids and daily caps
  5. fin_ads_clicks          — raw click stream for CPC accounting + fraud scoring
  6. fin_ads_conversions     — attributed orders for CPA accounting
  7. fin_fraud_logs          — provider-level integrity flags
  8. fin_market_benchmarks   — per-test-type market reference (price + TAT)
  9. fin_clinical_behavior   — doctor-level over-testing / deviation profile
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


revision      = "20260506_0001"
down_revision = "20260505_0006"
branch_labels = None
depends_on    = None


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _has_table(name: str) -> bool:
    bind = op.get_bind()
    return inspect(bind).has_table(name)


def _index_exists(index: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    for table in inspector.get_table_names():
        idx_names = [i["name"] for i in inspector.get_indexes(table)]
        if index in idx_names:
            return True
    return False


# ─── Upgrade ─────────────────────────────────────────────────────────────────

def upgrade() -> None:
    UUID = postgresql.UUID(as_uuid=True)

    # ── 1. fin_providers ─────────────────────────────────────────────────────
    # Billable entity. `lab_id` is a soft pointer to the existing `labs.id`
    # (no FK in Phase A); a future migration will add the constraint after
    # backfilling rows for every active lab.
    if not _has_table("fin_providers"):
        op.create_table(
            "fin_providers",
            sa.Column("id",             UUID,                primary_key=True,
                      server_default=sa.text("gen_random_uuid()")),
            sa.Column("lab_id",         sa.Integer(),        nullable=True),
            sa.Column("name",           sa.String(255),      nullable=True),
            sa.Column("plan",           sa.String(50),       nullable=True),
            sa.Column("quality_score",  sa.Numeric(5, 2),    nullable=True),
            sa.Column("rating",         sa.Numeric(3, 2),    nullable=True),
            sa.Column("speed_score",    sa.Numeric(5, 2),    nullable=True),
            sa.Column("price_score",    sa.Numeric(5, 2),    nullable=True),
            sa.Column("reliability",    sa.Numeric(5, 2),    nullable=True),
            sa.Column("created_at",     sa.DateTime(timezone=True),
                      server_default=sa.func.now(), nullable=True),
            sa.Column("updated_at",     sa.DateTime(timezone=True),
                      server_default=sa.func.now(), nullable=True),
        )
        op.create_index("ix_fin_providers_lab_id", "fin_providers", ["lab_id"])
        op.create_index("ix_fin_providers_plan",   "fin_providers", ["plan"])

    # ── 2. fin_subscriptions ─────────────────────────────────────────────────
    if not _has_table("fin_subscriptions"):
        op.create_table(
            "fin_subscriptions",
            sa.Column("id",          UUID, primary_key=True,
                      server_default=sa.text("gen_random_uuid()")),
            sa.Column("provider_id", UUID,            nullable=True),
            sa.Column("plan",        sa.String(50),   nullable=True),
            sa.Column("status",      sa.String(30),   nullable=True),
            sa.Column("expires_at",  sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at",  sa.DateTime(timezone=True),
                      server_default=sa.func.now(), nullable=True),
            sa.Column("updated_at",  sa.DateTime(timezone=True),
                      server_default=sa.func.now(), nullable=True),
        )
        op.create_index("ix_fin_subscriptions_provider_id", "fin_subscriptions", ["provider_id"])
        op.create_index("ix_fin_subscriptions_status",      "fin_subscriptions", ["status"])
        op.create_index("ix_fin_subscriptions_expires_at",  "fin_subscriptions", ["expires_at"])

    # ── 3. fin_transactions ──────────────────────────────────────────────────
    # Append-only ledger. `type` ∈ {'fee', 'ad_spend', 'refund', 'credit', 'penalty', ...}.
    # Currency defaults to IQD (Iraqi Dinar) to match existing claims schema.
    if not _has_table("fin_transactions"):
        meta_col = postgresql.JSONB if op.get_bind().dialect.name == "postgresql" else sa.JSON
        op.create_table(
            "fin_transactions",
            sa.Column("id",          UUID, primary_key=True,
                      server_default=sa.text("gen_random_uuid()")),
            sa.Column("provider_id", UUID,                 nullable=True),
            sa.Column("type",        sa.String(50),        nullable=True),
            sa.Column("amount",      sa.Numeric(14, 2),    nullable=True),
            sa.Column("currency",    sa.String(10),        nullable=True,
                      server_default="IQD"),
            sa.Column("ref_id",      sa.String(64),        nullable=True),
            sa.Column("meta",        meta_col,             nullable=True),
            sa.Column("created_at",  sa.DateTime(timezone=True),
                      server_default=sa.func.now(), nullable=True),
        )
        op.create_index("ix_fin_transactions_provider_id", "fin_transactions", ["provider_id"])
        op.create_index("ix_fin_transactions_type",        "fin_transactions", ["type"])
        op.create_index("ix_fin_transactions_created_at",  "fin_transactions",
                        [sa.text("created_at DESC")])

    # ── 4. fin_ads_campaigns ─────────────────────────────────────────────────
    # `bid` is the ad-boost component clamped 0..0.25 in app code (ranking spec).
    # `spent_today` is reset by a daily worker (Phase D).
    if not _has_table("fin_ads_campaigns"):
        op.create_table(
            "fin_ads_campaigns",
            sa.Column("id",          UUID, primary_key=True,
                      server_default=sa.text("gen_random_uuid()")),
            sa.Column("provider_id", UUID,              nullable=True),
            sa.Column("bid",         sa.Numeric(8, 4),  nullable=True),
            sa.Column("daily_limit", sa.Numeric(14, 2), nullable=True),
            sa.Column("spent_today", sa.Numeric(14, 2), nullable=True,
                      server_default="0"),
            sa.Column("active",      sa.Boolean(),      nullable=True,
                      server_default=sa.text("true")),
            sa.Column("paused_reason", sa.String(255),  nullable=True),
            sa.Column("created_at",  sa.DateTime(timezone=True),
                      server_default=sa.func.now(), nullable=True),
            sa.Column("updated_at",  sa.DateTime(timezone=True),
                      server_default=sa.func.now(), nullable=True),
        )
        op.create_index("ix_fin_ads_campaigns_provider_id", "fin_ads_campaigns", ["provider_id"])
        op.create_index("ix_fin_ads_campaigns_active",      "fin_ads_campaigns", ["active"])

    # ── 5. fin_ads_clicks ────────────────────────────────────────────────────
    # Raw click stream — fed into Phase F fraud detector.
    if not _has_table("fin_ads_clicks"):
        op.create_table(
            "fin_ads_clicks",
            sa.Column("id",                  UUID, primary_key=True,
                      server_default=sa.text("gen_random_uuid()")),
            sa.Column("campaign_id",         UUID,            nullable=True),
            sa.Column("ip",                  sa.String(45),   nullable=True),
            sa.Column("user_id",             sa.String(64),   nullable=True),
            sa.Column("user_agent",          sa.String(500),  nullable=True),
            sa.Column("device_fingerprint",  sa.String(128),  nullable=True),
            sa.Column("referrer",            sa.String(500),  nullable=True),
            sa.Column("fraud_score",         sa.Numeric(5, 2), nullable=True),
            sa.Column("created_at",          sa.DateTime(timezone=True),
                      server_default=sa.func.now(), nullable=True),
        )
        op.create_index("ix_fin_ads_clicks_campaign_id", "fin_ads_clicks", ["campaign_id"])
        op.create_index("ix_fin_ads_clicks_ip",          "fin_ads_clicks", ["ip"])
        op.create_index("ix_fin_ads_clicks_created_at",  "fin_ads_clicks",
                        [sa.text("created_at DESC")])

    # ── 6. fin_ads_conversions ───────────────────────────────────────────────
    # `order_id` is a soft pointer to lab_orders.id (no FK in Phase A).
    if not _has_table("fin_ads_conversions"):
        op.create_table(
            "fin_ads_conversions",
            sa.Column("id",          UUID, primary_key=True,
                      server_default=sa.text("gen_random_uuid()")),
            sa.Column("campaign_id", UUID,              nullable=True),
            sa.Column("order_id",    sa.Integer(),      nullable=True),
            sa.Column("value",       sa.Numeric(14, 2), nullable=True),
            sa.Column("created_at",  sa.DateTime(timezone=True),
                      server_default=sa.func.now(), nullable=True),
        )
        op.create_index("ix_fin_ads_conversions_campaign_id", "fin_ads_conversions", ["campaign_id"])
        op.create_index("ix_fin_ads_conversions_order_id",    "fin_ads_conversions", ["order_id"])

    # ── 7. fin_fraud_logs ────────────────────────────────────────────────────
    # severity ∈ {'info', 'warn', 'high', 'critical'} (validated in app layer).
    if not _has_table("fin_fraud_logs"):
        meta_col = postgresql.JSONB if op.get_bind().dialect.name == "postgresql" else sa.JSON
        op.create_table(
            "fin_fraud_logs",
            sa.Column("id",          UUID, primary_key=True,
                      server_default=sa.text("gen_random_uuid()")),
            sa.Column("provider_id", UUID,             nullable=True),
            sa.Column("campaign_id", UUID,             nullable=True),
            sa.Column("reason",      sa.String(255),   nullable=True),
            sa.Column("severity",    sa.String(20),    nullable=True),
            sa.Column("meta",        meta_col,         nullable=True),
            sa.Column("created_at",  sa.DateTime(timezone=True),
                      server_default=sa.func.now(), nullable=True),
        )
        op.create_index("ix_fin_fraud_logs_provider_id", "fin_fraud_logs", ["provider_id"])
        op.create_index("ix_fin_fraud_logs_severity",    "fin_fraud_logs", ["severity"])
        op.create_index("ix_fin_fraud_logs_created_at",  "fin_fraud_logs",
                        [sa.text("created_at DESC")])

    # ── 8. fin_market_benchmarks ─────────────────────────────────────────────
    # Aggregated reference table refreshed periodically by a Phase B job.
    # `avg_time` is mean turnaround in hours.
    if not _has_table("fin_market_benchmarks"):
        op.create_table(
            "fin_market_benchmarks",
            sa.Column("id",          UUID, primary_key=True,
                      server_default=sa.text("gen_random_uuid()")),
            sa.Column("test_type",   sa.String(100),    nullable=True),
            sa.Column("avg_price",   sa.Numeric(14, 2), nullable=True),
            sa.Column("avg_time",    sa.Numeric(10, 2), nullable=True),
            sa.Column("sample_size", sa.Integer(),      nullable=True),
            sa.Column("computed_at", sa.DateTime(timezone=True),
                      server_default=sa.func.now(), nullable=True),
        )
        op.create_index("ix_fin_market_benchmarks_test_type", "fin_market_benchmarks", ["test_type"])

    # ── 9. fin_clinical_behavior ─────────────────────────────────────────────
    # Doctor-level over-testing profile. `doctor_id` is a soft pointer to
    # lab_users.id; FK added in a later phase after the backfill job runs.
    if not _has_table("fin_clinical_behavior"):
        op.create_table(
            "fin_clinical_behavior",
            sa.Column("id",                  UUID, primary_key=True,
                      server_default=sa.text("gen_random_uuid()")),
            sa.Column("doctor_id",           sa.Integer(),     nullable=True),
            sa.Column("context",             sa.String(100),   nullable=True),
            sa.Column("avg_tests_per_case",  sa.Numeric(8, 2), nullable=True),
            sa.Column("deviation_score",     sa.Numeric(8, 2), nullable=True),
            sa.Column("sample_size",         sa.Integer(),     nullable=True),
            sa.Column("computed_at",         sa.DateTime(timezone=True),
                      server_default=sa.func.now(), nullable=True),
        )
        op.create_index("ix_fin_clinical_behavior_doctor_id",  "fin_clinical_behavior", ["doctor_id"])
        op.create_index("ix_fin_clinical_behavior_context",    "fin_clinical_behavior", ["context"])


# ─── Downgrade ───────────────────────────────────────────────────────────────

def downgrade() -> None:
    # Drop in reverse order. No FKs exist between these tables in Phase A,
    # so order matters only cosmetically. All drops are idempotent.
    for tbl in (
        "fin_clinical_behavior",
        "fin_market_benchmarks",
        "fin_fraud_logs",
        "fin_ads_conversions",
        "fin_ads_clicks",
        "fin_ads_campaigns",
        "fin_transactions",
        "fin_subscriptions",
        "fin_providers",
    ):
        if _has_table(tbl):
            op.drop_table(tbl)
