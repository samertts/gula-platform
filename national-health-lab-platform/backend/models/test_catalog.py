from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.sql import func
from database.db import Base


class TestCatalog(Base):
    __tablename__ = "test_catalog"

    id                = Column(Integer, primary_key=True, index=True)
    code              = Column(String(30), unique=True, nullable=False, index=True)
    name_ar           = Column(String(200), nullable=False)
    name_en           = Column(String(200), nullable=False)
    category          = Column(String(100), nullable=False)
    sample_type       = Column(String(50), default="blood")
    unit              = Column(String(30))
    normal_range_min  = Column(Float)
    normal_range_max  = Column(Float)
    normal_range_text = Column(String(200))
    price             = Column(Float, default=0)
    turnaround_hours  = Column(Integer, default=24)
    is_active         = Column(Boolean, default=True)
    created_at        = Column(DateTime(timezone=True), server_default=func.now())
