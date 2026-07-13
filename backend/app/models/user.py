from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app._compat import UTC

from ..database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, nullable=True, index=True)
    phone = Column(String(20), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(200), nullable=False)
    role = Column(
        String(50), nullable=False, default="citizen"
    )  # master_admin, lab_admin, lab_staff, doctor, citizen
    lab_id = Column(
        Integer, ForeignKey("labs.id", ondelete="SET NULL"), nullable=True
    )  # for lab staff/admin
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    national_id_hash = Column(String(255), nullable=True, index=True)
    license_number = Column(String(100), nullable=True)  # for doctors
    specialty = Column(String(200), nullable=True)  # for doctors
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    last_login = Column(DateTime(timezone=True), nullable=True)

    lab = relationship("Lab", backref="staff_users")
