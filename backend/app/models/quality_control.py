"""Quality Control model for lab instrument QC tracking."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app._compat import UTC

from ..database import Base


class QualityControl(Base):
    __tablename__ = "quality_controls"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    test_code = Column(String(50), nullable=False, index=True)  # e.g., glucose, hemoglobin
    instrument_name = Column(String(200), nullable=True)
    lot_number = Column(String(100), nullable=True)

    # QC levels (low, normal, high control)
    level = Column(String(20), nullable=False)  # low, normal, high
    expected_value = Column(Float, nullable=False)
    measured_value = Column(Float, nullable=False)
    sd = Column(Float, nullable=True)  # standard deviation
    unit = Column(String(30), nullable=True)

    # Westgard rule violations
    status = Column(String(20), default="pass")  # pass, warning, fail
    violation = Column(String(50), nullable=True)  # 1-2s, 1-3s, 2-2s, R-4s, 4-1s, 10-x
    notes = Column(Text, nullable=True)

    performed_by = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # passive_deletes=True lets the DB-level CASCADE (ondelete="CASCADE" on the
    # FK above) handle deletion without SQLAlchemy loading records into memory.
    lab = relationship("Lab", passive_deletes=True)
