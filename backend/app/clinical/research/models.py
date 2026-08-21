"""SQLAlchemy models for tenant-scoped clinical research entities."""

from __future__ import annotations

from sqlalchemy import Boolean, Column, ForeignKey, Index, Integer, String, Text

from app.clinical.base import BaseEntity
from app.models.base import TenantMixin


class TenantEntity(TenantMixin, BaseEntity):
    """Base entity for research records owned by one laboratory tenant."""

    __abstract__ = True

    lab_id = Column(Integer, nullable=False, index=True)


class ClinicalRegistry(TenantEntity):
    """A clinical registry definition scoped to a single laboratory."""

    __tablename__ = "clinical_research_registries"
    __table_args__ = (
        Index("ix_research_registry_lab_type", "lab_id", "registry_type"),
        Index("ix_research_registry_lab_deleted", "lab_id", "is_deleted"),
    )

    name = Column(String(256), nullable=False)
    registry_type = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    condition = Column(String(256), nullable=True)
    inclusion_criteria = Column(Text, nullable=True)
    steward = Column(String(256), nullable=True)


class ResearchCohort(TenantEntity):
    """A research cohort definition scoped to a single laboratory."""

    __tablename__ = "clinical_research_cohorts"
    __table_args__ = (
        Index("ix_research_cohort_lab_active", "lab_id", "is_active"),
        Index("ix_research_cohort_lab_deleted", "lab_id", "is_deleted"),
    )

    name = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    inclusion_criteria = Column(Text, nullable=True)
    registry_id = Column(
        String(26),
        ForeignKey("clinical_research_registries.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")


__all__ = ["ClinicalRegistry", "ResearchCohort"]
