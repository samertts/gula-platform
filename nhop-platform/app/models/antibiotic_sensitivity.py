"""Antibiotic sensitivity test results for resistance surveillance.

Each row represents a single bacterium/antibiotic pair tested in one lab.
Aggregating across rows yields the national resistance report.
"""
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class AntibioticSensitivity(Base):
    __tablename__ = "antibiotic_sensitivities"
    __table_args__ = (
        Index("ix_abx_sens_bug_drug", "bacterium", "antibiotic"),
        Index("ix_abx_sens_province", "province"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    bacterium:  Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    antibiotic: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    is_resistant: Mapped[bool] = mapped_column(Boolean, nullable=False)

    province: Mapped[str | None] = mapped_column(String(80),  nullable=True, index=True)
    district: Mapped[str | None] = mapped_column(String(120), nullable=True)
    lab_name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    citizen_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("citizens.id", ondelete="SET NULL"),
        nullable=True,
    )

    tested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )
