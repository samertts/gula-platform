"""Durable clinical command receipts.

A receipt claims an idempotency key before a clinical state transition.  The
unique key is scoped to the laboratory, actor, and operation so a network retry
cannot repeat a clinical side effect.  The receipt belongs to the same database
transaction as the protected write and audit event.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint

from app._compat import UTC
from app.database import Base


class ClinicalCommandReceipt(Base):  # type: ignore[misc, unused-ignore]  # Declarative Base differs by Mypy invocation scope.
    """Append-only claim for a safety-critical clinical command."""

    __tablename__ = "clinical_command_receipts"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_user_id = Column(Integer, ForeignKey("lab_users.id", ondelete="RESTRICT"), nullable=False)
    operation = Column(String(96), nullable=False)
    idempotency_key = Column(String(128), nullable=False)
    request_fingerprint = Column(String(64), nullable=False)
    resource_type = Column(String(64), nullable=False)
    # LIMS uses numeric IDs while pharmacy and radiology use UUID-like strings.
    # A canonical textual resource key permits one durable guard across domains.
    resource_id = Column(String(64), nullable=True)
    status = Column(String(24), nullable=False, default="claimed")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "lab_id",
            "actor_user_id",
            "operation",
            "idempotency_key",
            name="uq_clinical_command_actor_key",
        ),
        Index("ix_clinical_command_receipt_resource", "lab_id", "resource_type", "resource_id"),
    )
