"""Lab test results referenced by the citizen summary endpoint.

The full LIMS lives in the GULA platform; this mirror table stores only the
minimum projection the NHOP citizen-facing summary needs.
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app._compat import UTC

from ..core.database import Base


class LabTest(Base):
    __tablename__ = "lab_tests"
    __table_args__ = (
        Index("ix_lab_tests_citizen_performed", "citizen_id", "performed_at"),
    )

    id:           Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    citizen_id:   Mapped[int] = mapped_column(Integer, ForeignKey("citizens.id", ondelete="CASCADE"), nullable=False)

    test_name:    Mapped[str] = mapped_column(String(200), nullable=False)
    result_value: Mapped[str | None] = mapped_column(String(200), nullable=True)
    result_unit:  Mapped[str | None] = mapped_column(String(40),  nullable=True)
    status:       Mapped[str] = mapped_column(String(30), nullable=False, default="final")
    lab_name:     Mapped[str | None] = mapped_column(String(200), nullable=True)

    performed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False,
    )
