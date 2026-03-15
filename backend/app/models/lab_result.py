import secrets
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone, timedelta
from ..database import Base


def generate_token():
    return secrets.token_urlsafe(32)


def default_expiry():
    return datetime.now(timezone.utc) + timedelta(days=90)


class LabResult(Base):
    __tablename__ = "lab_results"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("lab_orders.id", ondelete="CASCADE"), nullable=False)
    test_type_id = Column(Integer, ForeignKey("test_types.id"), nullable=True)
    test_name = Column(String(200), nullable=False)
    value = Column(Float, nullable=True)
    value_text = Column(String(200), nullable=True)  # for non-numeric results
    unit = Column(String(20), nullable=True)
    normal_range_low = Column(Float, nullable=True)
    normal_range_high = Column(Float, nullable=True)
    flag = Column(String(10), nullable=True)  # H, L, normal, critical
    token = Column(String(64), unique=True, nullable=False, default=generate_token, index=True)
    expires_at = Column(DateTime(timezone=True), default=default_expiry)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    order = relationship("LabOrder", back_populates="results")
    test_type = relationship("TestType")
