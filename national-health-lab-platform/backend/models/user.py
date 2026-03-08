from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from database.db import Base


class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(200), nullable=False)
    email         = Column(String(200), unique=True, index=True, nullable=False)
    phone         = Column(String(20))
    national_id   = Column(String(20), unique=True)
    password_hash = Column(String(255), nullable=False, default="")
    role          = Column(String(30), nullable=False, default="citizen")
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
