from __future__ import annotations

from datetime import date as date_type
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import DynamicMapped, Mapped, backref, relationship

from app._compat import UTC, StrEnum

from ..database import Base

if TYPE_CHECKING:
    from .lab import Lab
    from .lab_order import LabOrder


class Gender(StrEnum):
    male = "M"
    female = "F"


class Patient(Base):
    __tablename__ = "patients"
    # Composite indexes for multi-tenant queries (lab_id partitions all lookups)
    __table_args__ = (
        Index("ix_patients_lab_id", "lab_id"),
        Index("ix_patients_lab_phone", "lab_id", "phone"),
        Index("ix_patients_lab_nid", "lab_id", "national_id_hash"),
    )

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False)
    health_id = Column(String(20), unique=True, nullable=True, index=True)
    national_id_hash = Column(String(255), nullable=True, index=True)
    # Family ID hash — links all family members by their civil registry family number.
    # Stored as HMAC-SHA256 (prefix "fam:") so the raw number is never persisted.
    family_id_hash = Column(String(255), nullable=True, index=True)
    # Guardian — links a minor to their parent/guardian patient record.
    guardian_id = Column(
        Integer, ForeignKey("patients.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    full_name = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=False, index=True)
    birth_date = Column(Date, nullable=True)
    gender = Column(String(1), nullable=True)
    email = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    lab: Mapped[Lab] = relationship("Lab", back_populates="patients")
    orders: Mapped[list[LabOrder]] = relationship(
        "LabOrder", back_populates="patient", cascade="all, delete-orphan"
    )
    # Guardian relationship — a patient can have many dependents (children)
    dependents: DynamicMapped[Patient] = relationship(
        "Patient",
        foreign_keys=[guardian_id],
        backref=backref("guardian", remote_side=[id]),
        lazy="dynamic",
    )

    @property
    def is_minor(self) -> bool:
        """True if the patient is under 18 years old based on birth_date."""
        if not self.birth_date:
            return False
        today = date_type.today()
        age = (
            today.year
            - self.birth_date.year
            - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        )
        return age < 18
