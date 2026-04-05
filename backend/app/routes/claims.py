"""Claims API — insurance claim submission + fraud detection.

Endpoints:
  POST /claims/                — submit a claim (fraud-scored immediately)
  GET  /claims/                — list claims for current lab
  GET  /claims/{id}            — get claim details
  POST /claims/{id}/review     — mark reviewed (approve/reject) by human
  GET  /claims/patient/{pid}   — patient's claim history
  POST /claims/pre-approve     — lightweight pre-approval check
  GET  /claims/stats           — fraud summary stats for current lab

Security:
  - All claims scoped to current_user.lab_id
  - Patients also scoped to lab_id
  - Fraud score written atomically with claim
  - Full audit log on every mutation
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.claim import Claim, FraudScore, FRAUD_APPROVE_THRESHOLD, FRAUD_REJECT_THRESHOLD
from ..models.lab_user import LabUser
from ..models.patient import Patient
from ..models.lab_order import LabOrder
from ..security.dependencies import get_current_user
from ..services.audit_service import log_action
from ..services.fraud_detection import FraudDetectionEngine, pre_approve_claim

logger = logging.getLogger("gula.claims")

router = APIRouter(prefix="/claims", tags=["claims"])

_VALID_CURRENCIES = {"IQD", "USD", "EUR"}
_VALID_REVIEW_DECISIONS = {"approve", "reject"}


# ── Schemas ───────────────────────────────────────────────────────────────────

class ClaimSubmit(BaseModel):
    patient_id:       int
    order_id:         int
    amount:           float
    currency:         str = "IQD"
    insurance_id:     Optional[str] = None
    diagnosis_codes:  Optional[list[str]] = None
    notes:            Optional[str] = None
    idempotency_key:  Optional[str] = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("amount must be > 0")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if v not in _VALID_CURRENCIES:
            raise ValueError(f"currency must be one of {_VALID_CURRENCIES}")
        return v

    @field_validator("insurance_id")
    @classmethod
    def validate_insurance_id(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > 100:
            raise ValueError("insurance_id too long (max 100 chars)")
        return v


class ReviewDecision(BaseModel):
    decision: str
    notes:    Optional[str] = None

    @field_validator("decision")
    @classmethod
    def validate_decision(cls, v: str) -> str:
        if v not in _VALID_REVIEW_DECISIONS:
            raise ValueError(f"decision must be one of {_VALID_REVIEW_DECISIONS}")
        return v


class PreApproveRequest(BaseModel):
    patient_id: int
    order_id:   int
    amount:     float
    currency:   str = "IQD"


# ── Serialiser ────────────────────────────────────────────────────────────────

def _claim_dict(claim: Claim, score: FraudScore | None = None) -> dict:
    d: dict = {
        "id":             claim.id,
        "patient_id":     claim.patient_id,
        "order_id":       claim.order_id,
        "lab_id":         claim.lab_id,
        "amount":         float(claim.amount),
        "currency":       claim.currency,
        "insurance_id":   claim.insurance_id,
        "diagnosis_codes": json.loads(claim.diagnosis_codes) if claim.diagnosis_codes else None,
        "notes":          claim.notes,
        "status":         claim.status,
        "fraud_score":    float(claim.fraud_score) if claim.fraud_score is not None else None,
        "fraud_decision": claim.fraud_decision,
        "fraud_flags":    json.loads(claim.fraud_flags) if claim.fraud_flags else [],
        "submitted_at":   claim.submitted_at.isoformat() if claim.submitted_at else None,
        "reviewed_at":    claim.reviewed_at.isoformat() if claim.reviewed_at else None,
        "paid_at":        claim.paid_at.isoformat() if claim.paid_at else None,
    }
    if score:
        d["fraud_detail"] = {
            "score_amount":    float(score.score_amount) if score.score_amount else None,
            "score_velocity":  float(score.score_velocity) if score.score_velocity else None,
            "score_duplicate": float(score.score_duplicate) if score.score_duplicate else None,
            "score_ai":        float(score.score_ai) if score.score_ai else None,
            "rules_triggered": json.loads(score.rules_triggered) if score.rules_triggered else [],
            "ai_explanation":  score.ai_explanation,
            "engine_version":  score.engine_version,
        }
    return d


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/", status_code=201)
def submit_claim(
    body: ClaimSubmit,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    """Submit an insurance claim. Fraud score is computed immediately."""
    # Scope check: patient must belong to this lab
    patient = db.query(Patient).filter(
        Patient.id == body.patient_id,
        Patient.lab_id == current_user.lab_id,
    ).first()
    if not patient:
        raise HTTPException(404, "المريض غير موجود أو لا ينتمي لمختبرك")

    # Order check
    order = db.query(LabOrder).filter(
        LabOrder.id == body.order_id,
        LabOrder.lab_id == current_user.lab_id,
    ).first()
    if not order:
        raise HTTPException(404, "الطلب غير موجود أو لا ينتمي لمختبرك")

    # Idempotency: if same idempotency_key exists, return existing
    if body.idempotency_key:
        existing = db.query(Claim).filter(
            Claim.idempotency_key == body.idempotency_key,
            Claim.lab_id == current_user.lab_id,
        ).first()
        if existing:
            score = db.query(FraudScore).filter(FraudScore.claim_id == existing.id).first()
            return _claim_dict(existing, score)

    # Duplicate order check
    dup = db.query(Claim).filter(
        Claim.order_id == body.order_id,
        Claim.lab_id == current_user.lab_id,
    ).first()
    if dup:
        raise HTTPException(409, "مطالبة لهذا الطلب موجودة مسبقاً")

    # Create claim record (status=submitted)
    claim = Claim(
        patient_id      = body.patient_id,
        order_id        = body.order_id,
        lab_id          = current_user.lab_id,
        amount          = Decimal(str(body.amount)),
        currency        = body.currency,
        insurance_id    = body.insurance_id,
        diagnosis_codes = json.dumps(body.diagnosis_codes) if body.diagnosis_codes else None,
        notes           = body.notes,
        status          = "submitted",
        submitted_by    = current_user.id,
        submitted_at    = datetime.now(timezone.utc),
        idempotency_key = body.idempotency_key,
    )
    db.add(claim)
    db.flush()   # get claim.id before scoring

    # Run fraud detection
    engine = FraudDetectionEngine(db)
    fraud_result = engine.score_claim(
        claim_id   = claim.id,
        patient_id = body.patient_id,
        lab_id     = current_user.lab_id,
        amount     = body.amount,
        order_id   = body.order_id,
        currency   = body.currency,
    )

    # Update claim with fraud score
    claim.fraud_score    = Decimal(str(round(fraud_result.score, 3)))
    claim.fraud_decision = fraud_result.decision
    claim.fraud_flags    = json.dumps(fraud_result.rules_triggered, ensure_ascii=False)
    claim.status         = "fraud_scored"

    # Auto-decisions based on fraud score
    if fraud_result.decision == "approve":
        claim.status = "approved"
    elif fraud_result.decision == "reject":
        claim.status = "rejected"
    else:
        claim.status = "pending_review"

    db.commit()
    db.refresh(claim)

    score_record = db.query(FraudScore).filter(FraudScore.claim_id == claim.id).first()

    log_action(
        db, current_user.id, "claim_submitted",
        f"claim_id={claim.id} amount={body.amount} decision={fraud_result.decision} "
        f"score={fraud_result.score:.3f}",
    )

    logger.info(
        "claim submitted id=%d patient=%d amount=%.2f %s decision=%s score=%.3f",
        claim.id, body.patient_id, body.amount, body.currency,
        fraud_result.decision, fraud_result.score,
    )

    return _claim_dict(claim, score_record)


@router.get("/")
def list_claims(
    status: Optional[str] = Query(None),
    patient_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    """List claims for the current lab."""
    q = db.query(Claim).filter(Claim.lab_id == current_user.lab_id)
    if status:
        q = q.filter(Claim.status == status)
    if patient_id:
        q = q.filter(Claim.patient_id == patient_id)
    total = q.count()
    claims = q.order_by(Claim.submitted_at.desc()).offset(offset).limit(limit).all()
    return {
        "total":  total,
        "offset": offset,
        "limit":  limit,
        "items":  [_claim_dict(c) for c in claims],
    }


@router.get("/stats")
def claim_stats(
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    """Fraud + claim statistics for the current lab."""
    base = db.query(Claim).filter(Claim.lab_id == current_user.lab_id)

    by_status = (
        db.query(Claim.status, func.count(Claim.id))
        .filter(Claim.lab_id == current_user.lab_id)
        .group_by(Claim.status)
        .all()
    )
    by_decision = (
        db.query(Claim.fraud_decision, func.count(Claim.id))
        .filter(Claim.lab_id == current_user.lab_id, Claim.fraud_decision.isnot(None))
        .group_by(Claim.fraud_decision)
        .all()
    )
    total_amount = (
        db.query(func.sum(Claim.amount))
        .filter(Claim.lab_id == current_user.lab_id, Claim.status == "approved")
        .scalar()
    ) or 0

    avg_score = (
        db.query(func.avg(Claim.fraud_score))
        .filter(Claim.lab_id == current_user.lab_id, Claim.fraud_score.isnot(None))
        .scalar()
    )

    return {
        "by_status":      {s: c for s, c in by_status},
        "by_fraud_decision": {d: c for d, c in by_decision},
        "total_approved_amount": float(total_amount),
        "avg_fraud_score": float(avg_score) if avg_score else None,
        "thresholds": {
            "approve_below": FRAUD_APPROVE_THRESHOLD,
            "reject_at":     FRAUD_REJECT_THRESHOLD,
        },
    }


@router.get("/patient/{patient_id}")
def patient_claims(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    """Get all claims for a patient (scoped to current lab)."""
    # Scope check
    patient = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.lab_id == current_user.lab_id,
    ).first()
    if not patient:
        raise HTTPException(404, "المريض غير موجود")

    claims = (
        db.query(Claim)
        .filter(Claim.patient_id == patient_id, Claim.lab_id == current_user.lab_id)
        .order_by(Claim.submitted_at.desc())
        .all()
    )
    return {"patient_id": patient_id, "items": [_claim_dict(c) for c in claims]}


@router.get("/{claim_id}")
def get_claim(
    claim_id: int,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    """Get claim details including full fraud scoring breakdown."""
    claim = db.query(Claim).filter(
        Claim.id == claim_id,
        Claim.lab_id == current_user.lab_id,
    ).first()
    if not claim:
        raise HTTPException(404, "المطالبة غير موجودة")

    score = db.query(FraudScore).filter(FraudScore.claim_id == claim_id).first()
    return _claim_dict(claim, score)


@router.post("/{claim_id}/review")
def review_claim(
    claim_id: int,
    body: ReviewDecision,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    """Human review: approve or reject a pending_review claim."""
    claim = db.query(Claim).filter(
        Claim.id == claim_id,
        Claim.lab_id == current_user.lab_id,
    ).first()
    if not claim:
        raise HTTPException(404, "المطالبة غير موجودة")

    if claim.status not in ("pending_review", "submitted", "fraud_scored"):
        raise HTTPException(409, f"لا يمكن مراجعة مطالبة بحالة '{claim.status}'")

    claim.status      = "approved" if body.decision == "approve" else "rejected"
    claim.reviewed_by = current_user.id
    claim.reviewed_at = datetime.now(timezone.utc)
    if body.notes:
        claim.notes = (claim.notes or "") + f"\n[مراجعة]: {body.notes}"

    db.commit()
    db.refresh(claim)

    log_action(
        db, current_user.id, "claim_reviewed",
        f"claim_id={claim_id} decision={body.decision}",
    )

    return _claim_dict(claim)


@router.post("/pre-approve")
def pre_approve(
    body: PreApproveRequest,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    """
    Lightweight pre-approval check. Call this before submit_claim to get
    instant feedback on eligibility and risk level without creating a claim.
    """
    return pre_approve_claim(
        db         = db,
        patient_id = body.patient_id,
        lab_id     = current_user.lab_id,
        amount     = body.amount,
        order_id   = body.order_id,
        currency   = body.currency,
    )
