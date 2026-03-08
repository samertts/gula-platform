from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from database.db import Base


class Patient(Base):
    __tablename__ = "patients"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=True)
    full_name   = Column(String(200), nullable=False)
    gender      = Column(String(10))
    birth_date  = Column(Date)
    phone       = Column(String(20))
    national_id = Column(String(20), unique=True, index=True)
    address     = Column(Text)
    blood_type  = Column(String(5))
    notes       = Column(Text)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
