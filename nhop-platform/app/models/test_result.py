"""Per-lab test result record.

The canonical source of truth for individual lab test results, distinct from
the lightweight ``lab_tests`` mirror used by the citizen-summary view. Each
row pins a result to both a citizen and the issuing lab, and carries the
metadata needed for smart-analysis, verification, and alerting.
"""
from __future__ import annotations

import enum
import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class ResultStatus(str, enum.Enum):
    pending = "pending"
    final = "final"
    verified = "verified"
    rejected = "rejected"


class ResultCategory(str, enum.Enum):
    hematology = "hematology"
    biochemistry = "biochemistry"
    microbiology = "microbiology"
    immunology = "immunology"
    endocrinology = "endocrinology"
    urinalysis = "urinalysis"
    serology = "serology"
    molecular = "molecular"
    other = "other"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def generate_sample_barcode() -> str:
    """12-char barcode: yymmdd + 6 hex chars (collision probability ≈ 1e-7 per day)."""
    stamp = datetime.now(timezone.utc).strftime("%y%m%d")
    suffix = secrets.token_hex(3).upper()
    return f"{stamp}{suffix}"


class TestResult(Base):
    __tablename__ = "test_results"
    __table_args__ = (
        Index("ix_test_results_citizen_performed", "citizen_id", "performed_at"),
        Index("ix_test_results_lab_performed", "lab_id", "performed_at"),
        Index("ix_test_results_test_code", "test_code"),
        Index("ix_test_results_sample_barcode", "sample_barcode", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    citizen_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("citizens.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lab_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("labs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    sample_barcode: Mapped[str] = mapped_column(
        String(32), nullable=False, default=generate_sample_barcode
    )

    test_code: Mapped[str] = mapped_column(String(60), nullable=False)
    test_name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[ResultCategory] = mapped_column(
        Enum(ResultCategory, name="test_result_category"),
        nullable=False,
        default=ResultCategory.other,
    )

    value_numeric: Mapped[float | None] = mapped_column(Float, nullable=True)
    value_text: Mapped[str | None] = mapped_column(String(400), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(40), nullable=True)

    reference_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    reference_max: Mapped[float | None] = mapped_column(Float, nullable=True)

    is_abnormal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_critical: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    direction: Mapped[str | None] = mapped_column(String(12), nullable=True)  # 'low'|'high'|'normal'

    interpretation_ar: Mapped[str | None] = mapped_column(String(500), nullable=True)
    warnings: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)

    status: Mapped[ResultStatus] = mapped_column(
        Enum(ResultStatus, name="test_result_status"),
        nullable=False,
        default=ResultStatus.final,
        index=True,
    )

    performed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    reported_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    verified_by: Mapped[str | None] = mapped_column(String(80), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    lab: Mapped["Lab"] = relationship(  # noqa: F821
        "Lab", back_populates="test_results"
    )
