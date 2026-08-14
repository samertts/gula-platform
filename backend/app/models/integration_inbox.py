"""Durable inbox records for cross-repository integration events."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, UniqueConstraint

from app._compat import UTC
from ..database import Base


class IntegrationInboxEvent(Base):
    __tablename__ = "integration_inbox_events"
    __table_args__ = (
        UniqueConstraint("event_id", name="uq_integration_inbox_event_id"),
        UniqueConstraint(
            "tenant_id",
            "idempotency_key",
            name="uq_integration_inbox_tenant_idempotency_key",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(120), nullable=False, index=True)
    event_type = Column(String(120), nullable=False, index=True)
    schema_version = Column(Integer, nullable=False)
    source_service = Column(String(80), nullable=False, index=True)
    tenant_id = Column(String(120), nullable=False, index=True)
    entity_id = Column(String(160), nullable=False, index=True)
    correlation_id = Column(String(160), nullable=False, index=True)
    idempotency_key = Column(String(200), nullable=False, index=True)
    actor_id = Column(String(160), nullable=False)
    payload = Column(Text, nullable=False)
    status = Column(String(30), nullable=False, default="pending_review", index=True)
    rejection_reason = Column(Text, nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    processed_at = Column(DateTime(timezone=True), nullable=True)
