from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, relationship

from app._compat import UTC

from ..database import Base

if TYPE_CHECKING:
    from .lab import Lab
    from .lab_result import LabResult
    from .patient import Patient

# Optimistic locking: increment `version` on every UPDATE.
# If the version the caller saw no longer matches the DB, the update affects
# 0 rows → caller receives HTTP 409 Conflict and must re-fetch.


# Valid order status transitions (state machine):
#   pending → completed  (results entered)
#   completed → validated (doctor/admin validates results — immutable after this)
#   pending → cancelled
ORDER_STATUSES = ("pending", "completed", "validated", "cancelled")


class LabOrder(Base):
    __tablename__ = "lab_orders"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(
        Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_name = Column(String(200), nullable=True)
    # doctor_user_id links to a LabUser with role='doctor' — enables data isolation
    # so doctors can only query orders associated with them.
    doctor_user_id = Column(
        Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    status = Column(String(20), default="pending", index=True)  # see ORDER_STATUSES

    # Validation / locking — added by migration 20250322_0003
    validated_by = Column(
        Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    validated_at = Column(DateTime(timezone=True), nullable=True)
    locked_at = Column(DateTime(timezone=True), nullable=True)  # set == validated_at when finalized

    # Optimistic locking — incremented on every mutation (see migration 0004)
    version = Column(Integer, nullable=False, default=1)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)

    patient: Mapped[Patient] = relationship("Patient", back_populates="orders")
    lab: Mapped[Lab] = relationship("Lab", back_populates="orders")
    results: Mapped[list[LabResult]] = relationship(
        "LabResult", back_populates="order", cascade="all, delete-orphan"
    )
