from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from database.db import Base


class Sample(Base):
    __tablename__ = "samples"

    id               = Column(Integer, primary_key=True, index=True)
    order_id         = Column(Integer, ForeignKey("lab_orders.id"), nullable=False)
    patient_id       = Column(Integer, ForeignKey("patients.id"), nullable=False)
    barcode          = Column(String(50), unique=True, index=True)
    sample_type      = Column(String(50), nullable=False)
    status           = Column(String(30), default="ordered")
    collected_at     = Column(DateTime(timezone=True))
    received_at      = Column(DateTime(timezone=True))
    collector_id     = Column(Integer, ForeignKey("users.id"), nullable=True)
    rejection_reason = Column(String(255))
    notes            = Column(Text)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())
