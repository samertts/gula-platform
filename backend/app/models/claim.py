"""Claim and ClaimItem models — Insurance/Billing module.

Status state machine:
    draft → validated → submitted → accepted
                                  ↘ rejected
    accepted → paid

All queries MUST filter by lab_id (security invariant).
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app._compat import UTC

from ..database import Base

# Valid claim status values (ordered by workflow progression)
CLAIM_STATUSES = ("draft", "validated", "submitted", "accepted", "rejected", "paid")


class Claim(Base):
    __tablename__ = "claims"
    __table_args__ = (
        Index("ix_claims_lab_id", "lab_id"),
        Index("ix_claims_patient_id", "patient_id"),
        Index("ix_claims_status", "status"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    order_id = Column(
        Integer, ForeignKey("lab_orders.id", ondelete="SET NULL"), nullable=True, index=True,
    )

    status = Column(String(30), nullable=False, default="draft")
    total_amount = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(10), nullable=False, default="IQD")
    idempotency_key = Column(String(255), nullable=True, unique=True)
    external_ref = Column(String(255), nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    items = relationship("ClaimItem", back_populates="claim", cascade="all, delete-orphan")


class ClaimItem(Base):
    __tablename__ = "claim_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    claim_id = Column(
        Integer, ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    test_code = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(12, 2), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)

    # Relationship
    claim = relationship("Claim", back_populates="items")
