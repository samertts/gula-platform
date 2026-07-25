"""GULA Platform — Subscription & Tier Models
===========================================
Multi-tier SaaS model with 3 orthogonal dimensions:

  1. Subscription Tier: starter | growth | enterprise
  2. Deployment Mode:   single | multi_branch | government
  3. Security Level:    standard | high_security | air_gapped

Labs start at 'starter / single / standard'.
Upgrades are self-service (admin panel) or demand-driven (citizen pressure).
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app._compat import UTC

from ..database import Base


class LabSubscription(Base):
    """Active subscription for a lab — the authoritative source for
    tier, deployment mode and security level.

    One subscription per lab (UNIQUE on lab_id).
    """

    __tablename__ = "lab_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(
        Integer,
        ForeignKey("labs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # ── Dimension 1: Subscription Tier ──────────────────────────────────────
    # starter | growth | enterprise
    tier = Column(String(30), nullable=False, default="starter", index=True)

    # ── Dimension 2: Deployment Mode ────────────────────────────────────────
    # single | multi_branch | government
    deployment_mode = Column(String(30), nullable=False, default="single")

    # ── Dimension 3: Security Level ─────────────────────────────────────────
    # standard | high_security | air_gapped
    security_level = Column(String(30), nullable=False, default="standard")

    # ── Billing & Validity ──────────────────────────────────────────────────
    is_active = Column(Boolean, default=True, nullable=False)
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    billing_cycle = Column(String(20), default="monthly")  # monthly | yearly
    monthly_price_usd = Column(Float, default=0.0)

    # ── Limits (enforced at API layer) ──────────────────────────────────────
    max_patients = Column(Integer, default=500)
    max_staff = Column(Integer, default=5)
    max_branches = Column(Integer, default=1)
    max_orders_per_day = Column(Integer, default=100)
    max_ai_calls_per_day = Column(Integer, default=0)

    # ── Metadata ────────────────────────────────────────────────────────────
    notes = Column(Text, nullable=True)
    activated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    lab = relationship("Lab", back_populates="subscription", uselist=False)


class UpgradeRequest(Base):
    """Demand-driven upgrade requests.
    Citizens can request that a lab be upgraded to a higher tier.
    A weighted score drives upgrade recommendations to platform admins.
    """

    __tablename__ = "upgrade_requests"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    requester_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )  # citizen who requested

    # What they're asking for
    target_tier = Column(String(30), nullable=False)  # growth | enterprise | ai_enabled
    target_deployment_mode = Column(String(30), nullable=True)  # multi_branch | government
    target_security_level = Column(String(30), nullable=True)  # high_security | air_gapped

    reason = Column(Text, nullable=True)  # free-text reason from citizen
    status = Column(
        String(20),
        default="pending",
        index=True,
    )  # pending | approved | rejected | fulfilled
    weight = Column(Float, default=1.0)  # weighted demand contribution (1.0 = verified patient)

    reviewed_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_note = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)

    lab = relationship("Lab")
    requester = relationship("User", foreign_keys=[requester_id])

    __table_args__ = (Index("ix_upgrade_requests_lab_status", "lab_id", "status"),)


class UpgradeDemandScore(Base):
    """Aggregated demand score per lab — updated whenever an UpgradeRequest is created.
    Weighted formula:
        score = Σ(request.weight) for pending + approved requests
        normalised by: unique verified requesters
    Platform admins see labs sorted by demand score to prioritise outreach.
    """

    __tablename__ = "upgrade_demand_scores"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(
        Integer,
        ForeignKey("labs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    raw_score = Column(Float, default=0.0)
    unique_requesters = Column(Integer, default=0)
    weighted_score = Column(Float, default=0.0)  # raw_score * log(unique_requesters+1)
    last_request_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    lab = relationship("Lab")


class FeatureFlag(Base):
    """Feature flags for granular feature control per lab.
    Overrides the tier defaults — allows per-lab customisation without
    changing the billing tier.

    Examples:
      - enable AI for a specific starter lab during a trial
      - disable batch export for a compromised lab
      - enable government reporting for a single clinic

    """

    __tablename__ = "feature_flags"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    feature_key = Column(String(100), nullable=False)  # e.g. "ai_interpretation"
    is_enabled = Column(Boolean, default=True, nullable=False)
    reason = Column(String(300), nullable=True)
    set_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # None = permanent
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    __table_args__ = (Index("ix_feature_flags_lab_key", "lab_id", "feature_key", unique=True),)
