"""Physician-originated test order.

Represents a request from a DOCTOR for one or more tests to be run against a
citizen by a lab. Rows are immutable once created aside from status
transitions; the authoritative test results (``test_results``) reference the
citizen and lab directly, not the order, which keeps the audit boundary
simple: an order states the clinician intent, a result states the lab truth.
"""
from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class TestOrderStatus(enum.StrEnum):
    pending = "pending"
    dispatched = "dispatched"
    fulfilled = "fulfilled"
    cancelled = "cancelled"


def _utcnow() -> datetime:
    return datetime.now(UTC)


class TestOrder(Base):
    __tablename__ = "test_orders"
    __table_args__ = (
        Index("ix_test_orders_citizen_created", "citizen_id", "created_at"),
        Index("ix_test_orders_doctor_created", "doctor_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    citizen_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("citizens.id", ondelete="CASCADE"),
        nullable=False,
    )
    doctor_id: Mapped[str] = mapped_column(String(80), nullable=False)

    lab_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("labs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # JSON list of uppercased test codes as ordered by the physician plus any
    # suggestion-engine additions. Stored verbatim so we can audit exactly
    # what was dispatched.
    tests: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Smart-suggestion additions (subset of ``tests`` that were auto-added).
    suggested_additions: Mapped[list | None] = mapped_column(
        JSON, nullable=True, default=list
    )

    clinical_indication: Mapped[str] = mapped_column(String(500), nullable=False)
    urgent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    status: Mapped[TestOrderStatus] = mapped_column(
        Enum(TestOrderStatus, name="test_order_status"),
        nullable=False,
        default=TestOrderStatus.pending,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
