from __future__ import annotations

import enum
import secrets
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class Gender(str, enum.Enum):
    male = "male"
    female = "female"


def _generate_health_id() -> str:
    return "HID-" + secrets.token_hex(8).upper()


class Citizen(Base):
    __tablename__ = "citizens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    national_id = Column(String(20), unique=True, nullable=False, index=True)
    health_id = Column(String(32), unique=True, nullable=False, index=True, default=_generate_health_id)
    first_name = Column(String(100), nullable=False)
    father_name = Column(String(100), nullable=True)
    grandfather_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=False)
    mother_name = Column(String(100), nullable=True)
    birth_date = Column(Date, nullable=False)
    gender = Column(Enum(Gender, name="citizen_gender"), nullable=True)
    blood_type = Column(String(5), nullable=True)
    phone = Column(String(20), nullable=True)
    province = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    is_alive = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.utcnow(),
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
        server_default=func.now(),
    )

    health_records = relationship(
        "HealthRecord",
        back_populates="citizen",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    test_results = relationship(
        "TestResult",
        back_populates="citizen",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Citizen id={self.id} health_id={self.health_id}>"
