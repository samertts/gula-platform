from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from database.db import Base


class LabOrder(Base):
    __tablename__ = "lab_orders"

    id             = Column(Integer, primary_key=True, index=True)
    patient_id     = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id      = Column(Integer, ForeignKey("users.id"), nullable=True)
    status         = Column(String(30), default="pending")
    priority       = Column(String(20), default="normal")
    clinical_notes = Column(Text)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    updated_at     = Column(DateTime(timezone=True), onupdate=func.now())


class LabOrderItem(Base):
    __tablename__ = "lab_order_items"

    id              = Column(Integer, primary_key=True, index=True)
    order_id        = Column(Integer, ForeignKey("lab_orders.id"), nullable=False)
    test_catalog_id = Column(Integer, ForeignKey("test_catalog.id"), nullable=False)
    status          = Column(String(30), default="pending")
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
