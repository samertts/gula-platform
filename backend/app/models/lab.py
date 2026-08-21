from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import Mapped, relationship

from app._compat import UTC

from ..database import Base

if TYPE_CHECKING:
    from .lab_order import LabOrder
    from .lab_user import LabUser
    from .patient import Patient
    from .subscription import LabSubscription


class Lab(Base):
    __tablename__ = "labs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    license_number = Column(String(100), unique=True, nullable=True)
    # Type: "private" | "government" | "hospital" | "clinic"
    lab_type = Column(String(50), nullable=True, index=True)
    director_name = Column(String(200), nullable=True)  # مدير / مسؤول المختبر
    website = Column(String(300), nullable=True)
    city = Column(String(100))
    address = Column(String(500))
    phone = Column(String(20))
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    users: Mapped[list[LabUser]] = relationship("LabUser", back_populates="lab", cascade="all, delete-orphan")
    patients: Mapped[list[Patient]] = relationship("Patient", back_populates="lab", cascade="all, delete-orphan")
    orders: Mapped[list[LabOrder]] = relationship("LabOrder", back_populates="lab", cascade="all, delete-orphan")
    subscription: Mapped[LabSubscription] = relationship(
        "LabSubscription", back_populates="lab", uselist=False, cascade="all, delete-orphan",
    )
