from __future__ import annotations

from sqlalchemy import Column, DateTime, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON

from app.database import Base

# JSONB on PostgreSQL, portable JSON elsewhere (tests use SQLite).
_PayloadJSON = JSONB().with_variant(JSON(), "sqlite")


class CapabilityRecord(Base):
    """Persistence record backing generated capability CRUD routes.

    Records are isolated by `capability` and by owning laboratory. The same
    record ID may exist in different capability namespaces without
    cross-domain leakage, and a lab can never read another lab's rows.
    """

    __tablename__ = "capability_records"
    __table_args__ = (
        Index(
            "ix_capability_records_capability_created_at",
            "capability",
            "created_at",
        ),
        Index(
            "ix_capability_records_lab_capability",
            "lab_id",
            "capability",
            "created_at",
        ),
    )

    capability = Column(String(80), primary_key=True, nullable=False)
    record_id = Column(String(120), primary_key=True, nullable=False)
    lab_id = Column(Integer, nullable=False, index=True)
    owner_user_id = Column(Integer, nullable=False)
    payload = Column(_PayloadJSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
