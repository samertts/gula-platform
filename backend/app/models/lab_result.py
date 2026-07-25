import hashlib
import secrets
from datetime import datetime, timedelta

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app._compat import UTC

from ..database import Base


def generate_token():
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """SHA-256 hash of token for secure storage and lookup."""
    return hashlib.sha256(token.encode()).hexdigest()


def default_expiry():
    return datetime.now(UTC) + timedelta(days=90)


class LabResult(Base):
    __tablename__ = "lab_results"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(
        Integer,
        ForeignKey("lab_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    test_type_id = Column(Integer, ForeignKey("test_types.id", ondelete="SET NULL"), nullable=True)
    test_name = Column(String(200), nullable=False)
    value = Column(Float, nullable=True)
    value_text = Column(String(200), nullable=True)  # for non-numeric results
    unit = Column(String(20), nullable=True)
    normal_range_low = Column(Float, nullable=True)
    normal_range_high = Column(Float, nullable=True)
    flag = Column(String(10), nullable=True, index=True)  # H, L, normal, critical
    token = Column(String(64), unique=True, nullable=False, default=generate_token, index=True)
    token_hash = Column(String(64), unique=True, nullable=True, index=True)
    expires_at = Column(DateTime(timezone=True), default=default_expiry, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # Version of the clinical engine that last evaluated this result.
    # Populated when evaluate_result() / evaluate_order() is called after save.
    # NULL on results created before the clinical engine was introduced.
    clinical_engine_version = Column(String(20), nullable=True)

    # Optimistic locking — increment on every mutation.
    # If the caller's version no longer matches DB, the caller receives HTTP 409.
    version = Column(Integer, nullable=False, default=1)

    order = relationship("LabOrder", back_populates="results")
    test_type = relationship("TestType")
