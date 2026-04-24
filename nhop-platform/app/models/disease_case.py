"""Confirmed disease case records for outbreak detection.

One row per positive lab result mapped to a reportable disease. Written by
the LIMS side (or a future CDC adapter) and consumed read-only by the
outbreak detection service.

We do not carry a DB-level FK to ``labs`` because the Lab model lives on a
separate declarative base (``models.base.Base``) while this table lives on
the registry base (``core.database.Base``); the two run in independent
engines today and a cross-base FK would break fresh-DB bootstrap.
"""
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class DiseaseCase(Base):
    __tablename__ = "disease_cases"
    __table_args__ = (
        Index("ix_disease_cases_code_reported", "disease_code", "reported_at"),
        Index("ix_disease_cases_province_reported", "province", "reported_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    disease_code: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    disease_name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    province: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    district: Mapped[str | None] = mapped_column(String(120), nullable=True)

    citizen_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("citizens.id", ondelete="SET NULL"),
        nullable=True,
    )
    lab_name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    is_positive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
