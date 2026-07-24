import secrets
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app._compat import UTC

from ..database import Base


def generate_barcode():
    return f"SMP-{secrets.token_hex(6).upper()}"


class Sample(Base):
    __tablename__ = "samples"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(
        Integer, ForeignKey("lab_orders.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    barcode = Column(String(20), unique=True, nullable=False, default=generate_barcode, index=True)
    sample_type = Column(String(50), nullable=False)  # blood, urine, stool, swab, serum, plasma
    collection_time = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    collected_by = Column(String(200), nullable=True)
    status = Column(
        String(30), default="collected", index=True,
    )  # collected, received, processing, analyzed, rejected
    rejection_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    storage_location = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    order = relationship("LabOrder", back_populates="samples")
