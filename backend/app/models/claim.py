"""Claim + FraudScore models — GULA Insurance & Fraud Detection.

Lifecycle:
  submitted → fraud_scored → approved | pending_review | rejected

FraudScore:
  Every claim gets a fraud score in [0.0, 1.0] immediately on submission.
  Score is computed by the FraudDetectionEngine (rules + optional AI).
  Decision thresholds:
    < 0.30  → auto-approve   (low risk)
    0.30–0.69 → pending_review (human review required)
    ≥ 0.70  → auto-reject    (high risk — likely fraud)

Rules Engine is the final arbiter. AI score is advisory input.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Column, DateTime, ForeignKey, Index, Integer, Numeric,
    String, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from ..database import Base

# ── Decision thresholds ───────────────────────────────────────────────────────
FRAUD_APPROVE_THRESHOLD = 0.30   # below → auto-approve
FRAUD_REJECT_THRESHOLD  = 0.70   # at or above → auto-reject


class Claim(Base):
    """Insurance claim for a completed lab order."""
    __tablename__ = "claims"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    patient_id       = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    order_id         = Column(Integer, ForeignKey("lab_orders.id"), nullable=False, index=True)
    lab_id           = Column(Integer, ForeignKey("labs.id"), nullable=False, index=True)

    # Financials
    amount           = Column(Numeric(12, 2), nullable=False)
    currency         = Column(String(3),      nullable=False, server_default="IQD")

    # Insurance
    insurance_id     = Column(String(100), nullable=True, index=True)
    diagnosis_codes  = Column(Text,        nullable=True)   # JSON array of ICD-10 codes
    notes            = Column(Text,        nullable=True)

    # Status lifecycle
    status           = Column(String(30), nullable=False, server_default="submitted",
                               index=True)
    # "submitted" | "fraud_scored" | "approved" | "pending_review" | "rejected"
    # | "paid" | "appealed" | "cancelled"

    # Fraud
    fraud_score      = Column(Numeric(4, 3), nullable=True)   # 0.000–1.000
    fraud_decision   = Column(String(20),    nullable=True)   # "approve"|"review"|"reject"
    fraud_flags      = Column(Text,          nullable=True)   # JSON list of triggered rules

    # Audit
    submitted_by     = Column(Integer, ForeignKey("lab_users.id"), nullable=True)
    submitted_at     = Column(DateTime(timezone=True), nullable=False,
                               default=lambda: datetime.now(timezone.utc), index=True)
    reviewed_by      = Column(Integer, ForeignKey("lab_users.id"), nullable=True)
    reviewed_at      = Column(DateTime(timezone=True), nullable=True)
    paid_at          = Column(DateTime(timezone=True), nullable=True)

    # Idempotency
    idempotency_key  = Column(String(64), nullable=True, index=True)

    __table_args__ = (
        UniqueConstraint("order_id", name="uq_claim_order_id"),   # one claim per order
        Index("ix_claims_lab_status", "lab_id", "status"),
        Index("ix_claims_submitted_at", "submitted_at"),
    )


class FraudScore(Base):
    """Detailed fraud scoring record for audit trail."""
    __tablename__ = "fraud_scores"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    claim_id            = Column(Integer, ForeignKey("claims.id"), nullable=False,
                                  unique=True, index=True)

    # Scores per dimension (each 0.0–1.0)
    score_amount        = Column(Numeric(4, 3), nullable=True)   # unusually high amount
    score_velocity      = Column(Numeric(4, 3), nullable=True)   # too many claims recently
    score_duplicate     = Column(Numeric(4, 3), nullable=True)   # same tests, same period
    score_ai            = Column(Numeric(4, 3), nullable=True)   # AI model score
    score_final         = Column(Numeric(4, 3), nullable=False)  # weighted composite

    # Triggered rules
    rules_triggered     = Column(Text, nullable=True)   # JSON list

    # AI advisory
    ai_explanation      = Column(Text, nullable=True)
    ai_confidence       = Column(Numeric(4, 3), nullable=True)

    decision            = Column(String(20), nullable=False)   # "approve"|"review"|"reject"
    scored_at           = Column(DateTime(timezone=True), nullable=False,
                                  default=lambda: datetime.now(timezone.utc))
    engine_version      = Column(String(20), nullable=False, server_default="1.0.0")

    __table_args__ = (
        Index("ix_fraud_scores_scored_at", "scored_at"),
    )
