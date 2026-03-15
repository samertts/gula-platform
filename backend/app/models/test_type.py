from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime, timezone
from ..database import Base


class TestType(Base):
    __tablename__ = "test_types"

    id = Column(Integer, primary_key=True, index=True)
    test_code = Column(String(50), unique=True, nullable=False)
    test_name = Column(String(200), nullable=False)
    test_name_ar = Column(String(200), nullable=True)
    category = Column(String(50), nullable=True)  # CBC, Chemistry, Lipid, etc.
    unit = Column(String(20), nullable=True)
    normal_range_low = Column(Float, nullable=True)
    normal_range_high = Column(Float, nullable=True)
    interpretation_low = Column(String(500), nullable=True)
    interpretation_normal = Column(String(500), nullable=True)
    interpretation_high = Column(String(500), nullable=True)
    interpretation_low_ar = Column(String(500), nullable=True)
    interpretation_normal_ar = Column(String(500), nullable=True)
    interpretation_high_ar = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
