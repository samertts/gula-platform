from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)

from app.database import Base


def _id() -> str:
    return uuid.uuid4().hex.upper()[:26]


class CoreMedicationRecall(Base):
    """Append-only recall event; batch quarantine remains the operational gate."""

    __tablename__ = "core_medication_recalls"

    id = Column(String(26), primary_key=True, default=_id)
    batch_id = Column(String(26), ForeignKey("core_medication_batches.id", ondelete="RESTRICT"), nullable=False, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    workspace_id = Column(String(26), nullable=False, index=True)
    recall_reference = Column(String(120), nullable=False, unique=True)
    reason = Column(Text, nullable=False)
    status = Column(String(24), nullable=False, default="OPEN")
    # NIAM account ownership is enforced by the database migration; IdentityBase has separate metadata.
    created_by_account_id = Column(String(26), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    __table_args__ = (
        UniqueConstraint("batch_id", "status", name="uq_core_medication_recall_batch_status"),
        CheckConstraint("status IN ('OPEN','CLEARED')", name="ck_core_medication_recall_status"),
        Index("ix_core_medication_recall_scope_status", "organization_id", "facility_id", "workspace_id", "status", "created_at"),
    )
