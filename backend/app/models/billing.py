"""
GULA Platform — Billing, Revenue, Referral & Pricing Models
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Date
from datetime import datetime, timezone
from ..database import Base


class LabWallet(Base):
    __tablename__ = "lab_wallets"
    lab_id      = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), primary_key=True)
    balance_iqd = Column(Integer, default=0, nullable=False)
    updated_at  = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                         onupdate=lambda: datetime.now(timezone.utc))


class UsageEvent(Base):
    __tablename__ = "usage_events"
    id         = Column(Integer, primary_key=True, index=True)
    lab_id     = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id    = Column(Integer, nullable=True, index=True)
    event_type = Column(String(50), nullable=False)   # ai_call | lab_test
    cost_iqd   = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)


class Invoice(Base):
    __tablename__ = "invoices"
    id           = Column(Integer, primary_key=True, index=True)
    lab_id       = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    total_iqd    = Column(Integer, nullable=False)
    period_start = Column(Date, nullable=False)
    period_end   = Column(Date, nullable=False)
    status       = Column(String(20), default="unpaid", nullable=False, index=True)  # unpaid|paid|cancelled
    created_at   = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Payment(Base):
    __tablename__ = "payments"
    id          = Column(Integer, primary_key=True, index=True)
    lab_id      = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_id  = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    provider    = Column(String(20), nullable=False)     # zaincash | qicard | manual
    amount_iqd  = Column(Integer, nullable=False)
    status      = Column(String(20), default="pending")  # pending|paid|failed
    external_id = Column(String(200), nullable=True)
    created_at  = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)


class LabTransaction(Base):
    """Commission split per lab test."""
    __tablename__ = "lab_transactions"
    id               = Column(Integer, primary_key=True, index=True)
    lab_id           = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id          = Column(Integer, nullable=True)
    test_type        = Column(String(100), nullable=True)
    total_price_iqd  = Column(Integer, nullable=False)
    commission_iqd   = Column(Integer, nullable=False)
    lab_share_iqd    = Column(Integer, nullable=False)
    created_at       = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)


class Referral(Base):
    __tablename__ = "referrals"
    id          = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    referred_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, unique=True)
    created_at  = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ReferralEarning(Base):
    __tablename__ = "referral_earnings"
    id          = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    referred_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False)
    amount_iqd  = Column(Integer, nullable=False)
    created_at  = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)


class TestPricing(Base):
    """Dynamic pricing rules per test type."""
    __tablename__ = "test_pricing"
    test_type   = Column(String(100), primary_key=True)
    base_price  = Column(Integer, nullable=False)
    min_price   = Column(Integer, nullable=False)
    max_price   = Column(Integer, nullable=False)
    commission_rate = Column(Float, default=0.10)  # 10% default


class StatsDaily(Base):
    """Pre-aggregated daily stats for fast dashboard queries."""
    __tablename__ = "stats_daily"
    date         = Column(Date, primary_key=True)
    labs_count   = Column(Integer, default=0)
    users_count  = Column(Integer, default=0)
    ai_calls     = Column(Integer, default=0)
    tests_count  = Column(Integer, default=0)
    revenue_iqd  = Column(Integer, default=0)
    commission_iqd = Column(Integer, default=0)
