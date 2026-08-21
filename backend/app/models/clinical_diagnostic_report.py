from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text, UniqueConstraint

from app._compat import UTC

from ..database import Base


def _ulid() -> str:
    return str(uuid.uuid4()).replace("-", "").upper()[:26]


class ClinicalDiagnosticReport(Base):
    __tablename__ = "clinical_diagnostic_reports"
    __table_args__ = (
        UniqueConstraint("source_type", "source_id", name="uq_clinical_diag_report_source"),
    )

    id = Column(String(26), primary_key=True, default=_ulid)
    source_type = Column(String(32), nullable=False, index=True)
    source_id = Column(String(80), nullable=False, index=True)
    patient_id = Column(String(80), nullable=False, index=True)
    encounter_id = Column(String(80), nullable=True, index=True)
    report_code = Column(String(80), nullable=True, index=True)
    report_name = Column(String(255), nullable=False)
    status = Column(String(24), nullable=False, default="PRELIMINARY", index=True)
    conclusion = Column(Text, nullable=True)
    result_refs = Column(JSON, nullable=False, default=list)
    source_metadata = Column(JSON, nullable=True, default=dict)

    organization_id = Column(String(80), nullable=False, index=True)
    facility_id = Column(String(80), nullable=False, index=True)
    department_id = Column(String(80), nullable=True, index=True)
    workspace_id = Column(String(80), nullable=False, index=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    legacy_lab_id = Column(Integer, nullable=False, index=True)

    version = Column(Integer, nullable=False, default=1)
    issued_at = Column(DateTime(timezone=True), nullable=True)
    released_at = Column(DateTime(timezone=True), nullable=True)
    released_by = Column(String(80), nullable=True)
    amended_at = Column(DateTime(timezone=True), nullable=True)
    amendment_reason = Column(String(1000), nullable=True)
    correlation_id = Column(String(36), nullable=True, index=True)
    created_by = Column(String(80), nullable=False)
    updated_by = Column(String(80), nullable=True)
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=lambda: datetime.now(UTC))
