import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app._compat import UTC

from .base import Base


class LabType(enum.StrEnum):
    governmental = "governmental"
    private = "private"
    academic = "academic"


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Lab(Base):
    __tablename__ = "labs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    license_number: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    lab_type: Mapped[LabType] = mapped_column(
        Enum(LabType, name="lab_type"), nullable=False, index=True
    )
    province: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    quality_rating: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    avg_tat_minutes: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    total_tests: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    test_results: Mapped[list["TestResult"]] = relationship(  # noqa: F821
        "TestResult",
        back_populates="lab",
        cascade="all, delete-orphan",
    )
    devices: Mapped[list["LabDevice"]] = relationship(
        "LabDevice",
        back_populates="lab",
        cascade="all, delete-orphan",
    )


class LabDevice(Base):
    __tablename__ = "lab_devices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    lab_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("labs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    device_name: Mapped[str] = mapped_column(String(200), nullable=False)
    manufacturer: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    serial_number: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    is_calibrated: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    last_calibration: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_calibration: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    lab: Mapped["Lab"] = relationship("Lab", back_populates="devices")
