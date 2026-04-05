"""GULA Fraud Detection Engine v1.0.

Architecture:
  1. Rules Engine     — deterministic, fast, auditable (primary decision maker)
  2. AI Layer         — advisory score (Ollama/OpenRouter if configured)
  3. Composite Score  — weighted blend of rule signals + AI advisory
  4. Decision         — Rules Engine is the FINAL arbiter

Score range: 0.0 (no risk) to 1.0 (definitely fraudulent).

Decision thresholds (configurable):
  < 0.30  → approve          (auto-approve, low risk)
  0.30–0.69 → review         (human review required)
  ≥ 0.70  → reject           (auto-reject, high risk)

Rules are NEVER overridden by AI. The AI score is one input to the
weighted composite — it cannot, by itself, approve or reject a claim.

Usage::

    from app.services.fraud_detection import FraudDetectionEngine

    engine = FraudDetectionEngine(db)
    result = engine.score_claim(
        claim_id=claim.id,
        patient_id=claim.patient_id,
        lab_id=claim.lab_id,
        amount=float(claim.amount),
        order_id=claim.order_id,
    )
    # result.decision in ("approve", "review", "reject")
    # result.score in [0.0, 1.0]
    # result.rules_triggered — list of rule names that fired
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.claim import (
    Claim, FraudScore,
    FRAUD_APPROVE_THRESHOLD, FRAUD_REJECT_THRESHOLD,
)

logger = logging.getLogger("gula.fraud")

# ── Rule weights (must sum to 1.0) ────────────────────────────────────────────
_WEIGHT_AMOUNT    = 0.30
_WEIGHT_VELOCITY  = 0.30
_WEIGHT_DUPLICATE = 0.25
_WEIGHT_AI        = 0.15

# ── Amount thresholds (IQD) ───────────────────────────────────────────────────
_AMOUNT_HIGH_IQD  = 500_000   # above → elevated risk
_AMOUNT_EXTREME   = 2_000_000 # above → critical risk

# ── Velocity window ───────────────────────────────────────────────────────────
_VELOCITY_WINDOW_DAYS = 30
_VELOCITY_MAX_CLAIMS  = 5     # >5 claims in 30 days → suspicious


@dataclass
class FraudResult:
    """Output of the fraud detection engine."""
    claim_id:        int
    score:           float            # 0.0–1.0 composite
    decision:        str              # "approve" | "review" | "reject"
    rules_triggered: list[str] = field(default_factory=list)
    score_amount:    float     = 0.0
    score_velocity:  float     = 0.0
    score_duplicate: float     = 0.0
    score_ai:        float     = 0.0
    ai_explanation:  str       = ""
    ai_confidence:   float     = 0.0


class FraudDetectionEngine:
    """
    Hybrid rule + AI fraud detection.

    Rules Engine is always executed first and is the final arbiter.
    AI layer is optional: if unavailable, AI weight is redistributed
    to the rules proportionally.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Public API ────────────────────────────────────────────────────────────

    def score_claim(
        self,
        claim_id: int,
        patient_id: int,
        lab_id: int,
        amount: float,
        order_id: int,
        currency: str = "IQD",
    ) -> FraudResult:
        """
        Score a claim and return a FraudResult.

        Does NOT commit to DB — caller handles persistence.
        Persists FraudScore record to the DB for the audit trail (flush only).
        """
        rules_triggered: list[str] = []

        # ── Rule 1: Amount anomaly ──────────────────────────────────────────
        score_amount = self._score_amount(amount, currency, rules_triggered)

        # ── Rule 2: Velocity (claims in window) ────────────────────────────
        score_velocity = self._score_velocity(patient_id, rules_triggered)

        # ── Rule 3: Duplicate detection ────────────────────────────────────
        score_duplicate = self._score_duplicate(patient_id, order_id, rules_triggered)

        # ── Rule 4: AI advisory (optional) ────────────────────────────────
        score_ai, ai_explanation, ai_confidence = self._score_ai(
            claim_id, patient_id, amount, order_id,
        )

        # ── Composite weighted score ───────────────────────────────────────
        if score_ai is None:
            # AI unavailable — redistribute AI weight to amount + velocity
            w_amount    = _WEIGHT_AMOUNT    + _WEIGHT_AI * 0.5
            w_velocity  = _WEIGHT_VELOCITY  + _WEIGHT_AI * 0.3
            w_duplicate = _WEIGHT_DUPLICATE + _WEIGHT_AI * 0.2
            composite = (
                score_amount    * w_amount +
                score_velocity  * w_velocity +
                score_duplicate * w_duplicate
            )
            score_ai = 0.0
        else:
            composite = (
                score_amount    * _WEIGHT_AMOUNT +
                score_velocity  * _WEIGHT_VELOCITY +
                score_duplicate * _WEIGHT_DUPLICATE +
                score_ai        * _WEIGHT_AI
            )

        composite = min(1.0, max(0.0, composite))

        # ── Hard override rules (Rules Engine is final arbiter) ────────────
        # A claim with extreme amount is ALWAYS flagged for review regardless of score
        if amount > _AMOUNT_EXTREME and currency == "IQD":
            if composite < FRAUD_APPROVE_THRESHOLD:
                composite = FRAUD_APPROVE_THRESHOLD  # force to review band
            if "extreme_amount" not in rules_triggered:
                rules_triggered.append("extreme_amount")

        # ── Decision ───────────────────────────────────────────────────────
        decision = self._decide(composite)

        logger.info(
            "fraud_score claim_id=%d score=%.3f decision=%s rules=%s",
            claim_id, composite, decision, rules_triggered,
        )

        result = FraudResult(
            claim_id        = claim_id,
            score           = composite,
            decision        = decision,
            rules_triggered = rules_triggered,
            score_amount    = score_amount,
            score_velocity  = score_velocity,
            score_duplicate = score_duplicate,
            score_ai        = score_ai,
            ai_explanation  = ai_explanation,
            ai_confidence   = ai_confidence,
        )

        # Persist audit record
        self._persist(result)
        return result

    # ── Rules ─────────────────────────────────────────────────────────────────

    def _score_amount(
        self,
        amount: float,
        currency: str,
        triggered: list[str],
    ) -> float:
        """Score based on claim amount relative to thresholds."""
        if currency != "IQD":
            return 0.10   # minimal penalty — non-IQD is unusual but not suspicious alone

        if amount <= 0:
            triggered.append("zero_or_negative_amount")
            return 0.95   # invalid amount — very suspicious

        if amount > _AMOUNT_EXTREME:
            triggered.append("extreme_amount")
            return 0.90

        if amount > _AMOUNT_HIGH_IQD:
            triggered.append("high_amount")
            return 0.60

        return 0.05   # normal range

    def _score_velocity(self, patient_id: int, triggered: list[str]) -> float:
        """Score based on how many claims this patient has made recently."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=_VELOCITY_WINDOW_DAYS)
        recent_count = (
            self.db.query(func.count(Claim.id))
            .filter(
                Claim.patient_id == patient_id,
                Claim.submitted_at >= cutoff,
                Claim.status.notin_(["rejected", "cancelled"]),
            )
            .scalar()
        ) or 0

        if recent_count >= _VELOCITY_MAX_CLAIMS * 2:
            triggered.append(f"very_high_velocity:{recent_count}_in_{_VELOCITY_WINDOW_DAYS}d")
            return 0.85
        if recent_count >= _VELOCITY_MAX_CLAIMS:
            triggered.append(f"high_velocity:{recent_count}_in_{_VELOCITY_WINDOW_DAYS}d")
            return 0.50
        return max(0.0, recent_count / _VELOCITY_MAX_CLAIMS * 0.30)

    def _score_duplicate(
        self,
        patient_id: int,
        order_id: int,
        triggered: list[str],
    ) -> float:
        """Detect if a claim for this order already exists (duplicate submission)."""
        existing = (
            self.db.query(Claim.id)
            .filter(
                Claim.patient_id == patient_id,
                Claim.order_id   == order_id,
                Claim.status.notin_(["rejected", "cancelled"]),
            )
            .first()
        )
        if existing:
            triggered.append(f"duplicate_order_claim:order_id={order_id}")
            return 0.95   # same order claimed twice — very suspicious

        return 0.0

    def _score_ai(
        self,
        claim_id: int,
        patient_id: int,
        amount: float,
        order_id: int,
    ) -> tuple[float | None, str, float]:
        """
        Advisory AI score. Returns (score, explanation, confidence).
        Returns (None, "", 0.0) if AI is unavailable — caller redistributes weight.

        In v1.0 this is a no-op placeholder.
        Replace with actual Ollama/OpenRouter call in v1.1.
        """
        # Placeholder: return None to skip AI weighting
        return None, "", 0.0

    # ── Decision ──────────────────────────────────────────────────────────────

    @staticmethod
    def _decide(score: float) -> str:
        if score < FRAUD_APPROVE_THRESHOLD:
            return "approve"
        if score < FRAUD_REJECT_THRESHOLD:
            return "review"
        return "reject"

    # ── Persistence ───────────────────────────────────────────────────────────

    def _persist(self, result: FraudResult) -> None:
        """Flush FraudScore record. Caller commits."""
        record = FraudScore(
            claim_id         = result.claim_id,
            score_amount     = Decimal(str(round(result.score_amount, 3))),
            score_velocity   = Decimal(str(round(result.score_velocity, 3))),
            score_duplicate  = Decimal(str(round(result.score_duplicate, 3))),
            score_ai         = Decimal(str(round(result.score_ai, 3))),
            score_final      = Decimal(str(round(result.score, 3))),
            rules_triggered  = json.dumps(result.rules_triggered, ensure_ascii=False),
            ai_explanation   = result.ai_explanation or None,
            ai_confidence    = Decimal(str(round(result.ai_confidence, 3))) if result.ai_confidence else None,
            decision         = result.decision,
            engine_version   = "1.0.0",
        )
        self.db.add(record)
        self.db.flush()


# ── Pre-approval check ────────────────────────────────────────────────────────

def pre_approve_claim(
    db: Session,
    patient_id: int,
    lab_id: int,
    amount: float,
    order_id: int,
    currency: str = "IQD",
) -> dict:
    """
    Lightweight pre-approval check before creating a claim.

    Returns dict with:
      - eligible: bool — whether to proceed with the full claim
      - reason:   str  — human-readable explanation
      - risk:     str  — "low" | "medium" | "high"

    Use this at the API boundary to give immediate feedback
    before doing the full FraudDetectionEngine.score_claim().
    """
    # Quick duplicate check
    existing = (
        db.query(Claim.id)
        .filter(
            Claim.order_id == order_id,
            Claim.status.notin_(["rejected", "cancelled"]),
        )
        .first()
    )
    if existing:
        return {
            "eligible": False,
            "reason":   "مطالبة لهذا الطلب موجودة مسبقاً",
            "risk":     "high",
        }

    if amount <= 0:
        return {
            "eligible": False,
            "reason":   "المبلغ يجب أن يكون أكبر من صفر",
            "risk":     "high",
        }

    risk = "low"
    if amount > _AMOUNT_EXTREME:
        risk = "high"
    elif amount > _AMOUNT_HIGH_IQD:
        risk = "medium"

    # Velocity quick check
    cutoff = datetime.now(timezone.utc) - timedelta(days=_VELOCITY_WINDOW_DAYS)
    recent = (
        db.query(func.count(Claim.id))
        .filter(
            Claim.patient_id == patient_id,
            Claim.submitted_at >= cutoff,
            Claim.status.notin_(["rejected", "cancelled"]),
        )
        .scalar()
    ) or 0

    if recent >= _VELOCITY_MAX_CLAIMS:
        risk = "high" if risk != "high" else risk

    return {
        "eligible": True,
        "reason":   "مؤهل للمطالبة",
        "risk":     risk,
        "recent_claims_30d": recent,
    }
