from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from ..database import Base


class Lab(Base):
    __tablename__ = "labs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    license_number = Column(String(100), unique=True, nullable=True)
    city = Column(String(100))
    address = Column(String(500))
    phone = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    users = relationship("LabUser", back_populates="lab", cascade="all, delete-orphan")
    patients = relationship("Patient", back_populates="lab", cascade="all, delete-orphan")
    orders = relationship("LabOrder", back_populates="lab", cascade="all, delete-orphan")
