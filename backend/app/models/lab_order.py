from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from ..database import Base


# Valid order status transitions (state machine):
#   pending → completed  (results entered)
#   completed → validated (doctor/admin validates results — immutable after this)
#   pending → cancelled
ORDER_STATUSES = ("pending", "completed", "validated", "cancelled")


class LabOrder(Base):
    __tablename__ = "lab_orders"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_name = Column(String(200), nullable=True)
    # doctor_user_id links to a LabUser with role='doctor' — enables data isolation
    # so doctors can only query orders associated with them.
    doctor_user_id = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(20), default="pending", index=True)  # see ORDER_STATUSES

    # Validation / locking — added by migration 20250322_0003
    validated_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True, index=True)
    validated_at = Column(DateTime(timezone=True), nullable=True)
    locked_at = Column(DateTime(timezone=True), nullable=True)  # set == validated_at when finalized

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    patient = relationship("Patient", back_populates="orders")
    lab = relationship("Lab", back_populates="orders")
    results = relationship("LabResult", back_populates="order", cascade="all, delete-orphan")
