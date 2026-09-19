"""Canonical citizen record for the national health registry.

One row per real person. Externally identified by `health_id` (never by
primary key, never by raw national_id). `national_id` is unique when present
but nullable for edge cases (e.g. newborns awaiting civil registration).
"""
from datetime import UTC, date, datetime

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class Citizen(Base):
    __tablename__ = "citizens"
    __table_args__ = (
        Index("ix_citizens_name", "full_name"),
        Index("ix_citizens_province", "province"),
        Index("ix_citizens_birth", "birth_date"),
    )

    id:            Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    health_id:     Mapped[str]      = mapped_column(String(20),  unique=True, nullable=False, index=True)
    national_id:   Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True, index=True)

    full_name:     Mapped[str]      = mapped_column(String(200), nullable=False)
    mother_name:   Mapped[str | None] = mapped_column(String(200), nullable=True)
    birth_date:    Mapped[date | None] = mapped_column(Date, nullable=True)
    gender:        Mapped[str | None] = mapped_column(String(1), nullable=True)   # 'M' | 'F'
    phone:         Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    email:         Mapped[str | None] = mapped_column(String(120), nullable=True)

    province:      Mapped[str | None] = mapped_column(String(80),  nullable=True)
    district:      Mapped[str | None] = mapped_column(String(120), nullable=True)
    address:       Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Clinical summary fields (denormalized for fast /summary responses).
    # Detailed history lives elsewhere (lab_tests, encounters).
    chronic_diseases: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    allergies:        Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    blood_type:       Mapped[str | None]  = mapped_column(String(5), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
