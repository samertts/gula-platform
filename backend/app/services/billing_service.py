"""
GULA Platform — Billing, Commission, Referral & Pricing Service
===============================================================
All financial logic lives here. API routes are thin wrappers.
"""
from __future__ import annotations

import secrets
import logging
from datetime import datetime, timezone, date
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, text

from ..models.billing import (
    LabWallet, UsageEvent, Invoice, Payment,
    LabTransaction, Referral, ReferralEarning, TestPricing,
)
from ..models.lab import Lab

logger = logging.getLogger("gula.billing")

# ── Constants ─────────────────────────────────────────────────────────────────

AI_COST_PER_CALL_IQD = 50          # per AI interpretation call
REFERRAL_COMMISSION_RATE = 0.10    # 10% of referred lab payment
REFERRAL_MONTHS = 6                # earning window
AI_DAILY_LIMIT_PER_LAB = int(__import__("os").getenv("AI_MAX_CALLS_PER_LAB_DAILY", "200"))


# ── Wallet ────────────────────────────────────────────────────────────────────

def get_or_create_wallet(db: Session, lab_id: int) -> LabWallet:
    w = db.query(LabWallet).filter(LabWallet.lab_id == lab_id).first()
    if not w:
        w = LabWallet(lab_id=lab_id, balance_iqd=0)
        db.add(w)
        db.flush()
    return w


def credit_wallet(db: Session, lab_id: int, amount: int) -> None:
    """Atomic wallet credit — safe under concurrent requests."""
    # Ensure wallet row exists first
    get_or_create_wallet(db, lab_id)
    # Single atomic UPDATE — no read-modify-write race condition
    db.execute(text("""
        UPDATE lab_wallets
        SET balance_iqd = balance_iqd + :amount,
            updated_at  = NOW()
        WHERE lab_id = :lab_id
    """), {"amount": amount, "lab_id": lab_id})


# ── Usage tracking ─────────────────────────────────────────────────────────────

def track_ai_call(db: Session, lab_id: int, user_id: Optional[int] = None) -> bool:
    """
    Record one AI call usage event.
    Returns False and does nothing if lab has hit its daily limit.
    """
    today = date.today()
    today_count = db.query(func.count(UsageEvent.id)).filter(
        UsageEvent.lab_id == lab_id,
        UsageEvent.event_type == "ai_call",
        func.date(UsageEvent.created_at) == today,
    ).scalar() or 0

    if today_count >= AI_DAILY_LIMIT_PER_LAB:
        logger.warning("[BILLING] lab=%d hit AI daily limit (%d)", lab_id, AI_DAILY_LIMIT_PER_LAB)
        return False

    db.add(UsageEvent(
        lab_id=lab_id, user_id=user_id,
        event_type="ai_call", cost_iqd=AI_COST_PER_CALL_IQD,
    ))
    return True


def track_test(db: Session, lab_id: int, test_type: str, price_iqd: int,
               user_id: Optional[int] = None) -> int:
    """
    Record a lab test, split revenue, credit lab wallet.
    Returns commission amount.
    """
    pricing = db.query(TestPricing).filter(TestPricing.test_type == test_type).first()
    rate = pricing.commission_rate if pricing else 0.10

    commission = int(price_iqd * rate)
    lab_share = price_iqd - commission

    db.add(LabTransaction(
        lab_id=lab_id, user_id=user_id, test_type=test_type,
        total_price_iqd=price_iqd, commission_iqd=commission, lab_share_iqd=lab_share,
    ))
    db.add(UsageEvent(lab_id=lab_id, user_id=user_id,
                      event_type="lab_test", cost_iqd=commission))
    credit_wallet(db, lab_id, lab_share)
    return commission


# ── Dynamic pricing ────────────────────────────────────────────────────────────
# In-process EMA (Exponential Moving Average) cache: test_type → last smoothed price
_price_ema: dict[str, float] = {}


def get_dynamic_price(db: Session, test_type: str, lab_id: Optional[int] = None) -> dict:
    """
    Returns recommended price based on demand signals.
    Keeps math simple — no heavy ML, just weighted rules.
    """
    pricing = db.query(TestPricing).filter(TestPricing.test_type == test_type).first()
    if not pricing:
        pricing = db.query(TestPricing).filter(TestPricing.test_type == "other").first()
    if not pricing:
        return {"price": 10000, "test_type": test_type, "signal": "default"}

    # Demand signal: tests of this type in last 24h across platform
    day_count = db.execute(text("""
        SELECT COUNT(*) FROM usage_events
        WHERE event_type = 'lab_test' AND created_at > NOW() - INTERVAL '24 hours'
    """)).scalar() or 0

    # Demand factor: 0% → +20% based on volume (cap at 1,000 events/day)
    demand_boost = min(day_count / 1000, 0.20)

    # Peak hour bonus (+10% between 8–11am)
    hour = datetime.now(timezone.utc).hour
    peak_boost = 0.10 if 8 <= hour <= 11 else 0.0

    raw_price = pricing.base_price * (1 + demand_boost + peak_boost)

    # EMA smoothing — prevents sudden price jumps (α=0.3 new, 0.7 old)
    prev = _price_ema.get(test_type, raw_price)
    smoothed = prev * 0.7 + raw_price * 0.3
    _price_ema[test_type] = smoothed
    price = int(max(pricing.min_price, min(pricing.max_price, smoothed)))

    signal = "high" if demand_boost > 0.10 else ("medium" if demand_boost > 0.03 else "low")
    return {
        "test_type": test_type,
        "price": price,
        "base_price": pricing.base_price,
        "commission_rate": pricing.commission_rate,
        "demand": signal,
        "peak_hour": bool(peak_boost),
    }


# ── Referral ──────────────────────────────────────────────────────────────────

def generate_referral_code() -> str:
    return secrets.token_hex(4).upper()


def ensure_referral_code(db: Session, lab_id: int) -> str:
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        return ""
    if not lab.referral_code:
        lab.referral_code = generate_referral_code()
        db.flush()
    return lab.referral_code


def link_referral(db: Session, referred_lab_id: int, referral_code: str) -> bool:
    """Link a newly registered lab to its referrer. Idempotent."""
    referrer = db.query(Lab).filter(Lab.referral_code == referral_code).first()
    if not referrer or referrer.id == referred_lab_id:
        return False

    existing = db.query(Referral).filter(Referral.referred_id == referred_lab_id).first()
    if existing:
        return False

    db.add(Referral(referrer_id=referrer.id, referred_id=referred_lab_id))
    return True


def pay_referral_commission(db: Session, referred_lab_id: int, payment_amount: int) -> None:
    """Pay referrer their cut when referred lab makes a payment (within 6 months)."""
    referral = db.query(Referral).filter(Referral.referred_id == referred_lab_id).first()
    if not referral:
        return

    # Only pay within REFERRAL_MONTHS of referral creation
    months_since = (datetime.now(timezone.utc) - referral.created_at).days / 30
    if months_since > REFERRAL_MONTHS:
        return

    commission = int(payment_amount * REFERRAL_COMMISSION_RATE)
    if commission <= 0:
        return

    db.add(ReferralEarning(
        referrer_id=referral.referrer_id,
        referred_id=referred_lab_id,
        amount_iqd=commission,
    ))
    credit_wallet(db, referral.referrer_id, commission)
    logger.info("[REFERRAL] lab=%d earns %d IQD from lab=%d",
                referral.referrer_id, commission, referred_lab_id)


# ── Invoicing ────────────────────────────────────────────────────────────────

def create_invoice(db: Session, lab_id: int, total_iqd: int,
                   period_start: date, period_end: date) -> Invoice:
    inv = Invoice(lab_id=lab_id, total_iqd=total_iqd,
                  period_start=period_start, period_end=period_end, status="unpaid")
    db.add(inv)
    db.flush()
    return inv


def mark_paid(db: Session, payment_id: int, external_id: str = "") -> bool:
    """
    Mark a payment as paid. Idempotent — safe if webhook fires twice.
    Uses SELECT FOR UPDATE to prevent concurrent double-processing.
    """
    # Lock row to prevent concurrent webhook race
    pmt = (
        db.query(Payment)
        .filter(Payment.id == payment_id)
        .with_for_update()
        .first()
    )
    if not pmt or pmt.status == "paid":
        return False  # already processed — do nothing

    # If provider sent an external_id, verify no duplicate transaction
    if external_id:
        dup = (
            db.query(Payment)
            .filter(Payment.external_id == external_id, Payment.status == "paid")
            .first()
        )
        if dup:
            logger.warning("[PAYMENT] Duplicate external_id=%s blocked", external_id)
            return False
        pmt.external_id = external_id

    pmt.status = "paid"
    if pmt.invoice_id:
        inv = db.query(Invoice).filter(Invoice.id == pmt.invoice_id).first()
        if inv:
            inv.status = "paid"
    # Credit lab wallet with payment amount
    credit_wallet(db, pmt.lab_id, pmt.amount_iqd)
    # Pay referral commission
    pay_referral_commission(db, pmt.lab_id, pmt.amount_iqd)
    db.commit()
    logger.info("[PAYMENT] paid lab=%d amount=%d provider=%s",
                pmt.lab_id, pmt.amount_iqd, pmt.provider)
    return True


# ── Dashboard stats ───────────────────────────────────────────────────────────

def get_platform_stats(db: Session) -> dict:
    """Fast platform-wide stats. Used by /admin/dashboard."""
    from ..models.lab_user import LabUser

    today = date.today()

    labs   = db.query(func.count(Lab.id)).scalar() or 0
    users  = db.query(func.count(LabUser.id)).scalar() or 0
    ai_today = db.query(func.count(UsageEvent.id)).filter(
        UsageEvent.event_type == "ai_call",
        func.date(UsageEvent.created_at) == today,
    ).scalar() or 0
    revenue_today = db.query(func.coalesce(func.sum(LabTransaction.total_price_iqd), 0)).filter(
        func.date(LabTransaction.created_at) == today,
    ).scalar() or 0
    commission_today = db.query(func.coalesce(func.sum(LabTransaction.commission_iqd), 0)).filter(
        func.date(LabTransaction.created_at) == today,
    ).scalar() or 0

    total_revenue = db.query(func.coalesce(func.sum(LabTransaction.total_price_iqd), 0)).scalar() or 0
    total_commission = db.query(func.coalesce(func.sum(LabTransaction.commission_iqd), 0)).scalar() or 0
    total_ai = db.query(func.count(UsageEvent.id)).filter(
        UsageEvent.event_type == "ai_call"
    ).scalar() or 0

    return {
        "labs": labs,
        "users": users,
        "today": {
            "ai_calls": ai_today,
            "revenue_iqd": revenue_today,
            "commission_iqd": commission_today,
        },
        "total": {
            "ai_calls": total_ai,
            "revenue_iqd": total_revenue,
            "commission_iqd": total_commission,
        },
    }


def get_lab_stats(db: Session, lab_id: int) -> dict:
    """Per-lab stats for the lab's own dashboard."""
    today = date.today()
    wallet = db.query(LabWallet).filter(LabWallet.lab_id == lab_id).first()

    income_today = db.query(func.coalesce(func.sum(LabTransaction.lab_share_iqd), 0)).filter(
        LabTransaction.lab_id == lab_id,
        func.date(LabTransaction.created_at) == today,
    ).scalar() or 0

    total_income = db.query(func.coalesce(func.sum(LabTransaction.lab_share_iqd), 0)).filter(
        LabTransaction.lab_id == lab_id,
    ).scalar() or 0

    tests_today = db.query(func.count(LabTransaction.id)).filter(
        LabTransaction.lab_id == lab_id,
        func.date(LabTransaction.created_at) == today,
    ).scalar() or 0

    referral_earnings = db.query(func.coalesce(func.sum(ReferralEarning.amount_iqd), 0)).filter(
        ReferralEarning.referrer_id == lab_id,
    ).scalar() or 0

    referral_count = db.query(func.count(Referral.id)).filter(
        Referral.referrer_id == lab_id,
    ).scalar() or 0

    return {
        "balance_iqd": wallet.balance_iqd if wallet else 0,
        "income_today_iqd": income_today,
        "total_income_iqd": total_income,
        "tests_today": tests_today,
        "referrals": {"count": referral_count, "earnings_iqd": referral_earnings},
    }
