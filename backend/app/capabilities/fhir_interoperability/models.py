"""Tenant-scoped storage for normalized FHIR R4 resources.

This is an original GULA contract layer inspired by the resource-oriented
approach used by public FHIR platforms. It is not copied from any external
repository and deliberately stores only the validated resource envelope plus
an audit-safe tenant boundary.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, JSON, String, UniqueConstraint

from ..._compat import UTC
from ...database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class FHIRResourceRecord(Base):
    __tablename__ = "fhir_resource_records"
    __table_args__ = (
        UniqueConstraint(
            "lab_id",
            "resource_type",
            "resource_id",
            "version",
            name="uq_fhir_resource_lab_type_id_version",
        ),
        Index("ix_fhir_resource_lab_type", "lab_id", "resource_type"),
        Index("ix_fhir_resource_lab_subject", "lab_id", "subject_reference"),
        Index("ix_fhir_resource_lab_created", "lab_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(String(128), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    profile = Column(String(255), nullable=True)
    subject_reference = Column(String(255), nullable=True)
    resource = Column(JSON, nullable=False)
    source_system = Column(String(120), nullable=True)
    created_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)
