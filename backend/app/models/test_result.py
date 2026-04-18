"""CMD-008 — TestResult model + Pydantic schemas.

نموذج نتيجة التحليل: links a lab test outcome to a canonical citizen
(via the MPI `citizens` table), the issuing `labs` row, and optionally
the `lab_devices` instrument that produced it.

NOTE: this module is intentionally NOT yet re-exported from
``app/models/__init__.py``.  The FK to ``lab_devices`` points at a table
that is not present in the current schema — wiring the model into
``Base.metadata`` before a migration adds that table would break
``create_all`` on fresh deployments.  Add the import once the matching
Alembic revision lands.
"""
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)

from ..database import Base


TEST_RESULT_STATUSES = ("pending", "completed", "verified", "rejected")
ABNORMALITY_DIRECTIONS = ("high", "low", "normal")


class TestResult(Base):
    __tablename__ = "test_results"

    __table_args__ = (
        Index("ix_test_results_citizen_lab", "citizen_id", "lab_id"),
        Index("ix_test_results_lab_status", "lab_id", "status"),
        Index("ix_test_results_lab_collected", "lab_id", "sample_collected_at"),
        Index("ix_test_results_test_code", "test_code"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # ── Foreign keys ────────────────────────────────────────────────────────
    citizen_id = Column(
        BigInteger,
        ForeignKey("citizens.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    lab_id = Column(
        Integer,
        ForeignKey("labs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    device_id = Column(
        Integer,
        ForeignKey("lab_devices.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Test identification (LOINC) ─────────────────────────────────────────
    test_code    = Column(String(30),  nullable=False)
    test_name_en = Column(String(200), nullable=False)
    test_name_ar = Column(String(200), nullable=False)
    category     = Column(String(50),  nullable=True)  # hematology, chemistry, hormones…

    # ── Result ──────────────────────────────────────────────────────────────
    result_value  = Column(Float,       nullable=True)
    result_text   = Column(String(200), nullable=True)   # positive / negative / …
    unit          = Column(String(20),  nullable=True)
    reference_min = Column(Float,       nullable=True)
    reference_max = Column(Float,       nullable=True)

    # ── Status ──────────────────────────────────────────────────────────────
    status                = Column(String(20), nullable=False, default="pending")
    is_critical           = Column(Boolean,    nullable=False, default=False)
    is_abnormal           = Column(Boolean,    nullable=False, default=False)
    abnormality_direction = Column(String(10), nullable=True)  # high / low / normal

    # ── Timing ──────────────────────────────────────────────────────────────
    sample_collected_at = Column(DateTime(timezone=True), nullable=False)
    result_completed_at = Column(DateTime(timezone=True), nullable=True)
    verified_at         = Column(DateTime(timezone=True), nullable=True)
    verified_by         = Column(String(200), nullable=True)

    # ── Tracking ────────────────────────────────────────────────────────────
    sample_barcode     = Column(String(64),  nullable=False, unique=True, index=True)
    ordering_physician = Column(String(200), nullable=True)
    clinical_notes     = Column(Text,        nullable=True)

    # ── Audit timestamps ────────────────────────────────────────────────────
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


# ───────────────────────── Pydantic v2 schemas ─────────────────────────────


class TestResultCreate(BaseModel):
    """Payload accepted by ``POST /test-results``."""

    citizen_id:   int = Field(..., ge=1)
    lab_id:       int = Field(..., ge=1)
    device_id:    Optional[int] = Field(default=None, ge=1)

    test_code:    str = Field(..., min_length=1, max_length=30)
    test_name_en: str = Field(..., min_length=1, max_length=200)
    test_name_ar: str = Field(..., min_length=1, max_length=200)
    category:     Optional[str] = Field(default=None, max_length=50)

    result_value:  Optional[float] = None
    result_text:   Optional[str]   = Field(default=None, max_length=200)
    unit:          Optional[str]   = Field(default=None, max_length=20)
    reference_min: Optional[float] = None
    reference_max: Optional[float] = None

    status:                str  = Field(default="pending")
    is_critical:           bool = False
    is_abnormal:           bool = False
    abnormality_direction: Optional[str] = None

    sample_collected_at: datetime
    sample_barcode:      str = Field(..., min_length=1, max_length=64)
    ordering_physician:  Optional[str] = Field(default=None, max_length=200)
    clinical_notes:      Optional[str] = None

    @field_validator("status")
    @classmethod
    def _check_status(cls, v: str) -> str:
        if v not in TEST_RESULT_STATUSES:
            raise ValueError(f"status must be one of {TEST_RESULT_STATUSES}")
        return v

    @field_validator("abnormality_direction")
    @classmethod
    def _check_direction(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ABNORMALITY_DIRECTIONS:
            raise ValueError(
                f"abnormality_direction must be one of {ABNORMALITY_DIRECTIONS}"
            )
        return v


class TestResultRead(BaseModel):
    """Full server representation — used by staff / API consumers."""

    model_config = ConfigDict(from_attributes=True)

    id:           int
    citizen_id:   int
    lab_id:       int
    device_id:    Optional[int] = None

    test_code:    str
    test_name_en: str
    test_name_ar: str
    category:     Optional[str] = None

    result_value:  Optional[float] = None
    result_text:   Optional[str]   = None
    unit:          Optional[str]   = None
    reference_min: Optional[float] = None
    reference_max: Optional[float] = None

    status:                str
    is_critical:           bool
    is_abnormal:           bool
    abnormality_direction: Optional[str] = None

    sample_collected_at: datetime
    result_completed_at: Optional[datetime] = None
    verified_at:         Optional[datetime] = None
    verified_by:         Optional[str] = None

    sample_barcode:     str
    ordering_physician: Optional[str] = None
    clinical_notes:     Optional[str] = None

    created_at: datetime
    updated_at: datetime


class TestResultBrief(BaseModel):
    """Compact view for list endpoints and search results."""

    model_config = ConfigDict(from_attributes=True)

    id:           int
    test_code:    str
    test_name_en: str
    test_name_ar: str
    result_value: Optional[float] = None
    result_text:  Optional[str]   = None
    unit:         Optional[str]   = None
    status:       str
    is_abnormal:  bool
    is_critical:  bool
    sample_collected_at: datetime


class TestResultForCitizen(BaseModel):
    """نسخة مبسّطة للمريض — بالعربي فقط، بدون حقول فنية أو إدارية.

    Exposes Arabic-only field names via ``serialization_alias`` so the
    citizen-facing JSON is consumable without client-side translation.
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int = Field(..., serialization_alias="المعرف")
    test_name_ar: str = Field(..., serialization_alias="اسم_التحليل")
    result_value: Optional[float] = Field(default=None, serialization_alias="القيمة")
    result_text:  Optional[str]   = Field(default=None, serialization_alias="النتيجة")
    unit:         Optional[str]   = Field(default=None, serialization_alias="الوحدة")
    reference_min: Optional[float] = Field(default=None, serialization_alias="الحد_الأدنى")
    reference_max: Optional[float] = Field(default=None, serialization_alias="الحد_الأعلى")
    status:      str  = Field(..., serialization_alias="الحالة")
    is_abnormal: bool = Field(..., serialization_alias="غير_طبيعي")
    is_critical: bool = Field(..., serialization_alias="حرج")
    abnormality_direction: Optional[str] = Field(
        default=None, serialization_alias="اتجاه_الانحراف"
    )
    sample_collected_at: datetime = Field(..., serialization_alias="تاريخ_العينة")
    result_completed_at: Optional[datetime] = Field(
        default=None, serialization_alias="تاريخ_النتيجة"
    )
