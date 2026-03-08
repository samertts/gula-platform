from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from database.db import Base


class TestResult(Base):
    __tablename__ = "test_results"

    id              = Column(Integer, primary_key=True, index=True)
    sample_id       = Column(Integer, ForeignKey("samples.id"))
    order_item_id   = Column(Integer, ForeignKey("lab_order_items.id"))
    test_catalog_id = Column(Integer, ForeignKey("test_catalog.id"), nullable=False)
    patient_id      = Column(Integer, ForeignKey("patients.id"), nullable=False)
    value           = Column(String(200))
    value_numeric   = Column(Float)
    unit            = Column(String(30))
    status          = Column(String(30), default="draft")
    is_abnormal     = Column(Boolean, default=False)
    abnormal_flag   = Column(String(10))
    tech_id         = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by     = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at     = Column(DateTime(timezone=True))
    notes           = Column(Text)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
