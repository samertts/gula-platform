"""Append-only audit log for citizen registry operations.

Every mutation of a citizen record, plus sensitive reads (summary view),
must produce a row here. Rows are never updated or deleted from application
code.
"""
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = (
        Index("ix_audit_log_target", "target_type", "target_id"),
        Index("ix_audit_log_occurred", "occurred_at"),
    )

    id:          Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action:      Mapped[str] = mapped_column(String(60),  nullable=False)
    target_type: Mapped[str] = mapped_column(String(40),  nullable=False)
    target_id:   Mapped[str] = mapped_column(String(40),  nullable=False)
    actor_id:    Mapped[str | None] = mapped_column(String(40), nullable=True)
    ip_address:  Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
