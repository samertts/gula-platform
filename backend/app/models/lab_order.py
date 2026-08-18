from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app._compat import UTC

from ..database import Base

# Optimistic locking: increment `version` on every UPDATE.
# If the version the caller saw no longer matches the DB, the update affects
# 0 rows → caller receives HTTP 409 Conflict and must re-fetch.


# Valid order status transitions (state machine):
#   pending → completed  (results entered)
#   completed → validated (doctor/admin validates results — immutable after this)
#   pending → cancelled
ORDER_STATUSES = ("pending", "completed", "validated", "cancelled")
CLINICAL_ORDER_STATUSES = ("DRAFT", "PLACED", "ACCEPTED", "IN_PROGRESS", "COMPLETED", "CANCELLED", "REJECTED", "FAILED", "EXPIRED")


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
    status = Column(String(20), default="pending", index=True)  # legacy LIMS compatibility status
    clinical_status = Column(String(24), nullable=True, index=True)
    encounter_id = Column(String(80), nullable=True, index=True)
    ordering_practitioner_id = Column(String(80), nullable=True, index=True)
    ordering_account_id = Column(Integer, nullable=True, index=True)
    organization_id = Column(String(80), nullable=True, index=True)
    facility_id = Column(String(80), nullable=True, index=True)
    department_id = Column(String(80), nullable=True, index=True)
    workspace_id = Column(String(80), nullable=True, index=True)
    tenant_id = Column(Integer, nullable=True, index=True)
    service = Column(String(120), nullable=True)
    priority = Column(String(20), nullable=True)
    clinical_indication = Column(Text, nullable=True)
    correlation_id = Column(String(36), nullable=True, index=True)

    # Validation / locking — added by migration 20250322_0003
    validated_by = Column(
        Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    validated_at = Column(DateTime(timezone=True), nullable=True)
    locked_at = Column(DateTime(timezone=True), nullable=True)  # set == validated_at when finalized

    # Optimistic locking — incremented on every mutation (see migration 0004)
    version = Column(Integer, nullable=False, default=1)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=True)

    patient = relationship("Patient", back_populates="orders")
    lab = relationship("Lab", back_populates="orders")
    results = relationship("LabResult", back_populates="order", cascade="all, delete-orphan")
