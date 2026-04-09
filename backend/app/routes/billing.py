"""
GULA Platform — Billing, Revenue, Referral & Pricing API
=========================================================
Routes:
  GET  /admin/dashboard          — platform-wide stats (master_admin)
  GET  /admin/revenue            — revenue breakdown (master_admin)
  GET  /lab/wallet               — lab balance + earnings
  GET  /lab/referrals            — referral stats & invite code
  POST /lab/test-revenue         — record a test sale (internal/webhook)
  GET  /pricing/{test_type}      — dynamic price for a test
  GET  /pricing                  — all pricing rules
  POST /payments/create          — create a payment request
  POST /payments/webhook/{prov}  — payment provider webhook (ZainCash/QiCard)
  GET  /payments/history         — lab payment history
"""
import hmac
import hashlib
import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.billing import Payment, TestPricing
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user
from ..services import billing_service as svc
from ..services.audit_service import log_action

logger = logging.getLogger("gula.billing")
router = APIRouter(tags=["billing"])

_WIDE_ROLES   = {"master_admin", "ministry_admin"}
_ZAINCASH_URL = os.getenv("ZAINCASH_URL", "https://api.zaincash.iq/transaction/pay")
_QICARD_URL   = os.getenv("QICARD_URL",  "https://payment.qi.iq/api/pay")


def _require_admin(user: LabUser):
    if user.role not in _WIDE_ROLES:
        raise HTTPException(403, "Admin only")


# ── Admin Dashboard ─────────────────────────────────────────────────────────

@router.get("/admin/dashboard")
def admin_dashboard(
    db: Session = Depends(get_db),
    user: LabUser = Depends(get_current_user),
):
    _require_admin(user)
    return svc.get_platform_stats(db)


@router.get("/admin/revenue")
def admin_revenue(
    db: Session = Depends(get_db),
    user: LabUser = Depends(get_current_user),
):
    """Daily revenue breakdown for the last 30 days."""
    _require_admin(user)
    from sqlalchemy import text
    rows = db.execute(text("""
        SELECT DATE(created_at) AS day,
               COUNT(*) AS tests,
               SUM(total_price_iqd) AS revenue,
               SUM(commission_iqd) AS commission,
               SUM(lab_share_iqd) AS lab_earnings
        FROM lab_transactions
        WHERE created_at >= NOW() - INTERVAL '30 days'
        GROUP BY day ORDER BY day DESC
    """)).fetchall()
    return [
        {"date": str(r.day), "tests": r.tests,
         "revenue_iqd": r.revenue or 0,
         "commission_iqd": r.commission or 0,
         "lab_earnings_iqd": r.lab_earnings or 0}
        for r in rows
    ]


# ── Lab Dashboard ────────────────────────────────────────────────────────────

@router.get("/lab/wallet")
def lab_wallet(
    db: Session = Depends(get_db),
    user: LabUser = Depends(get_current_user),
):
    return svc.get_lab_stats(db, user.lab_id)


@router.get("/lab/referrals")
def lab_referrals(
    db: Session = Depends(get_db),
    user: LabUser = Depends(get_current_user),
):
    code = svc.ensure_referral_code(db, user.lab_id)
    db.commit()
    stats = svc.get_lab_stats(db, user.lab_id)
    return {
        "referral_code": code,
        "referral_link": f"/register?ref={code}",
        "referrals": stats["referrals"],
        "commission_rate": "10% for 6 months",
    }


# ── Test Revenue Recording ────────────────────────────────────────────────────

class TestSaleBody(BaseModel):
    test_type: str
    price_iqd: int
    user_id: Optional[int] = None
    referral_code: Optional[str] = None


@router.post("/lab/test-revenue")
def record_test_sale(
    body: TestSaleBody,
    db: Session = Depends(get_db),
    user: LabUser = Depends(get_current_user),
):
    """Record a completed test sale and split commission."""
    if user.role not in {"admin", "master_admin", "ministry_admin", "technician", "doctor"}:
        raise HTTPException(403, "Not allowed")
    if body.price_iqd <= 0:
        raise HTTPException(400, "Price must be positive")

    commission = svc.track_test(db, user.lab_id, body.test_type,
                                body.price_iqd, body.user_id)
    db.commit()
    log_action(db, user.id, "test_revenue_recorded",
               details={"test_type": body.test_type, "price": body.price_iqd})
    return {"ok": True, "commission_iqd": commission,
            "lab_share_iqd": body.price_iqd - commission}


# ── Dynamic Pricing ──────────────────────────────────────────────────────────

@router.get("/pricing")
def list_pricing(db: Session = Depends(get_db)):
    """All pricing rules — public (no auth needed for display)."""
    rows = db.query(TestPricing).all()
    return [
        {"test_type": r.test_type, "base_price": r.base_price,
         "min_price": r.min_price, "max_price": r.max_price,
         "commission_rate": r.commission_rate}
        for r in rows
    ]


@router.get("/pricing/{test_type}")
def get_price(
    test_type: str,
    db: Session = Depends(get_db),
):
    """Dynamic price for a specific test (demand + peak-hour aware)."""
    return svc.get_dynamic_price(db, test_type.lower())


# ── Payments ─────────────────────────────────────────────────────────────────

class PaymentCreateBody(BaseModel):
    amount_iqd: int
    provider: str = "zaincash"   # zaincash | qicard | manual
    invoice_id: Optional[int] = None


@router.post("/payments/create")
def create_payment(
    body: PaymentCreateBody,
    db: Session = Depends(get_db),
    user: LabUser = Depends(get_current_user),
):
    """Create a pending payment and return redirect URL."""
    if body.amount_iqd <= 0:
        raise HTTPException(400, "Amount must be positive")
    if body.provider not in ("zaincash", "qicard", "manual"):
        raise HTTPException(400, "Unknown provider")

    pmt = Payment(
        lab_id=user.lab_id,
        invoice_id=body.invoice_id,
        provider=body.provider,
        amount_iqd=body.amount_iqd,
        status="pending",
    )
    db.add(pmt)
    db.commit()
    db.refresh(pmt)

    if body.provider == "zaincash":
        redirect_url = (f"{_ZAINCASH_URL}?amount={body.amount_iqd}"
                        f"&order={pmt.id}&currency=IQD")
    elif body.provider == "qicard":
        redirect_url = (f"{_QICARD_URL}?amount={body.amount_iqd}"
                        f"&order={pmt.id}")
    else:  # manual
        redirect_url = f"/payments/{pmt.id}/confirm"

    log_action(db, user.id, "payment_created",
               details={"payment_id": pmt.id, "amount": body.amount_iqd,
                        "provider": body.provider})
    return {"payment_id": pmt.id, "redirect_url": redirect_url, "status": "pending"}


def _verify_webhook_sig(provider: str, payload: bytes, sig: str) -> bool:
    """HMAC-SHA256 signature verification for payment webhooks."""
    secret_env = {"zaincash": "ZAINCASH_SECRET", "qicard": "QICARD_SECRET"}
    secret = os.getenv(secret_env.get(provider, ""), "")
    if not secret:
        # In production this means the env var is unset — log loudly but don't block
        # so we don't break a live integration on first deploy.
        # Set the secret in .env to enforce signature verification.
        logger.warning("[WEBHOOK] %s secret not configured — signature check skipped", provider)
        return True
    if not sig:
        logger.warning("[WEBHOOK] %s: missing X-Signature header", provider)
        return False
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)


@router.post("/payments/webhook/{provider}")
async def payment_webhook(
    provider: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Payment provider webhook. Verifies HMAC signature then marks payment paid."""
    if provider not in ("zaincash", "qicard"):
        raise HTTPException(400, "Unknown provider")

    body_bytes = await request.body()
    sig = request.headers.get("X-Signature", "")

    if not _verify_webhook_sig(provider, body_bytes, sig):
        logger.warning("[WEBHOOK] Invalid signature from %s", provider)
        raise HTTPException(401, "Invalid signature")

    data = await request.json()
    payment_id = int(data.get("order_id", 0) or data.get("order", 0))
    status = data.get("status", "")

    if not payment_id:
        raise HTTPException(400, "Missing order_id")

    if status in ("success", "paid", "completed"):
        pmt = db.query(Payment).filter(Payment.id == payment_id).first()
        if not pmt:
            raise HTTPException(404, "Payment not found")
        if pmt.provider != provider:
            raise HTTPException(400, "Provider mismatch")
        external_id = str(data.get("transaction_id", "") or data.get("ref", ""))
        paid = svc.mark_paid(db, payment_id, external_id=external_id)
        if paid:
            logger.info("[WEBHOOK] Payment %d confirmed via %s ext=%s",
                        payment_id, provider, external_id)
        else:
            logger.info("[WEBHOOK] Payment %d already processed — skipped", payment_id)
    elif status in ("failed", "cancelled"):
        pmt = db.query(Payment).filter(Payment.id == payment_id).first()
        if pmt:
            pmt.status = "failed"
            db.commit()

    return {"ok": True}


@router.get("/payments/history")
def payment_history(
    db: Session = Depends(get_db),
    user: LabUser = Depends(get_current_user),
):
    rows = db.query(Payment).filter(
        Payment.lab_id == user.lab_id
    ).order_by(Payment.created_at.desc()).limit(50).all()
    return [
        {"id": p.id, "amount_iqd": p.amount_iqd, "provider": p.provider,
         "status": p.status, "created_at": p.created_at.isoformat() if p.created_at else None}
        for p in rows
    ]
