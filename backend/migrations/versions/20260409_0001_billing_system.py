"""Add billing, revenue, referral, and pricing tables.

Revision ID: 20260409_0001
Revises    : 20260407_0001
Create Date: 2026-04-09

Tables created:
  1. lab_wallets        — per-lab balance ledger
  2. usage_events       — AI call and test usage tracking
  3. invoices           — monthly billing invoices
  4. payments           — payment provider records
  5. lab_transactions   — commission split per test
  6. referrals          — referral linkage
  7. referral_earnings  — commission earned from referrals
  8. test_pricing       — dynamic pricing rules
  9. stats_daily        — pre-aggregated daily dashboard stats

Column added:
  - labs.referral_code  — unique invite code per lab
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20260409_0001"
down_revision = "20260407_0001"
branch_labels = None
depends_on = None


def _table_exists(name: str) -> bool:
    return inspect(op.get_bind()).has_table(name)


def _column_exists(table: str, col: str) -> bool:
    cols = [c["name"] for c in inspect(op.get_bind()).get_columns(table)]
    return col in cols


def upgrade():
    bind = op.get_bind()

    if not _table_exists("lab_wallets"):
        op.create_table(
            "lab_wallets",
            sa.Column("lab_id", sa.Integer, sa.ForeignKey("labs.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("balance_iqd", sa.Integer, nullable=False, server_default="0"),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )

    if not _table_exists("usage_events"):
        op.create_table(
            "usage_events",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("lab_id", sa.Integer, sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", sa.Integer, nullable=True),
            sa.Column("event_type", sa.String(50), nullable=False),
            sa.Column("cost_iqd", sa.Integer, nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        )
        op.create_index("ix_usage_events_lab_id", "usage_events", ["lab_id"])
        op.create_index("ix_usage_events_created_at", "usage_events", ["created_at"])

    if not _table_exists("invoices"):
        op.create_table(
            "invoices",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("lab_id", sa.Integer, sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("total_iqd", sa.Integer, nullable=False),
            sa.Column("period_start", sa.Date, nullable=False),
            sa.Column("period_end", sa.Date, nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="unpaid"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        )
        op.create_index("ix_invoices_lab_id", "invoices", ["lab_id"])
        op.create_index("ix_invoices_status", "invoices", ["status"])

    if not _table_exists("payments"):
        op.create_table(
            "payments",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("lab_id", sa.Integer, sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("invoice_id", sa.Integer, sa.ForeignKey("invoices.id"), nullable=True),
            sa.Column("provider", sa.String(20), nullable=False),
            sa.Column("amount_iqd", sa.Integer, nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
            sa.Column("external_id", sa.String(200), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        )
        op.create_index("ix_payments_lab_id", "payments", ["lab_id"])

    if not _table_exists("lab_transactions"):
        op.create_table(
            "lab_transactions",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("lab_id", sa.Integer, sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", sa.Integer, nullable=True),
            sa.Column("test_type", sa.String(100), nullable=True),
            sa.Column("total_price_iqd", sa.Integer, nullable=False),
            sa.Column("commission_iqd", sa.Integer, nullable=False),
            sa.Column("lab_share_iqd", sa.Integer, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        )
        op.create_index("ix_lab_transactions_lab_id", "lab_transactions", ["lab_id"])

    if not _table_exists("referrals"):
        op.create_table(
            "referrals",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("referrer_id", sa.Integer, sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("referred_id", sa.Integer, sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
            sa.UniqueConstraint("referred_id", name="uq_referral_referred"),
        )
        op.create_index("ix_referrals_referrer_id", "referrals", ["referrer_id"])

    if not _table_exists("referral_earnings"):
        op.create_table(
            "referral_earnings",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("referrer_id", sa.Integer, sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("referred_id", sa.Integer, sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("amount_iqd", sa.Integer, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        )
        op.create_index("ix_referral_earnings_referrer", "referral_earnings", ["referrer_id"])

    if not _table_exists("test_pricing"):
        op.create_table(
            "test_pricing",
            sa.Column("test_type", sa.String(100), primary_key=True),
            sa.Column("base_price", sa.Integer, nullable=False),
            sa.Column("min_price", sa.Integer, nullable=False),
            sa.Column("max_price", sa.Integer, nullable=False),
            sa.Column("commission_rate", sa.Float, nullable=False, server_default="0.10"),
        )
        # Seed default pricing for common tests
        bind.execute(sa.text("""
            INSERT INTO test_pricing (test_type, base_price, min_price, max_price, commission_rate)
            VALUES
              ('cbc',         10000,  8000, 15000, 0.10),
              ('vitamin_d',   25000, 20000, 35000, 0.15),
              ('hba1c',       20000, 15000, 28000, 0.12),
              ('lipid',       15000, 12000, 22000, 0.10),
              ('tsh',         18000, 14000, 25000, 0.12),
              ('glucose',      8000,  6000, 12000, 0.10),
              ('liver',       22000, 18000, 30000, 0.12),
              ('kidney',      22000, 18000, 30000, 0.12),
              ('urine',        7000,  5000, 10000, 0.10),
              ('other',       10000,  5000, 20000, 0.10)
            ON CONFLICT DO NOTHING
        """))

    if not _table_exists("stats_daily"):
        op.create_table(
            "stats_daily",
            sa.Column("date", sa.Date, primary_key=True),
            sa.Column("labs_count", sa.Integer, nullable=False, server_default="0"),
            sa.Column("users_count", sa.Integer, nullable=False, server_default="0"),
            sa.Column("ai_calls", sa.Integer, nullable=False, server_default="0"),
            sa.Column("tests_count", sa.Integer, nullable=False, server_default="0"),
            sa.Column("revenue_iqd", sa.Integer, nullable=False, server_default="0"),
            sa.Column("commission_iqd", sa.Integer, nullable=False, server_default="0"),
        )

    # Add referral_code to labs if missing
    if not _column_exists("labs", "referral_code"):
        op.add_column("labs", sa.Column("referral_code", sa.String(20), nullable=True))
        op.create_index("ix_labs_referral_code", "labs", ["referral_code"], unique=True)
        # Generate codes for existing labs
        bind.execute(sa.text("""
            UPDATE labs
            SET referral_code = UPPER(SUBSTRING(MD5(RANDOM()::TEXT), 1, 8))
            WHERE referral_code IS NULL
        """))


def downgrade():
    for idx in [
        "ix_labs_referral_code",
        "ix_referral_earnings_referrer",
        "ix_referrals_referrer_id",
        "ix_lab_transactions_lab_id",
        "ix_payments_lab_id",
        "ix_invoices_status",
        "ix_invoices_lab_id",
        "ix_usage_events_created_at",
        "ix_usage_events_lab_id",
    ]:
        try:
            op.drop_index(idx)
        except Exception:
            pass

    for tbl in ["stats_daily", "test_pricing", "referral_earnings", "referrals",
                "lab_transactions", "payments", "invoices", "usage_events", "lab_wallets"]:
        try:
            op.drop_table(tbl)
        except Exception:
            pass

    try:
        op.drop_column("labs", "referral_code")
    except Exception:
        pass
