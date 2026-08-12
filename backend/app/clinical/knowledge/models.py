from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app._compat import UTC
from app.clinical.base import BaseEntity
from app.clinical.enums import EvidenceLevel, GuidelineStatus


class ClinicalGuideline(BaseEntity):
    __tablename__ = "clinical_guidelines"
    __table_args__ = (
        Index("ix_guideline_status", "status"),
        Index("ix_guideline_specialty", "specialty"),
    )

    title = Column(String(512), nullable=False)
    identifier = Column(String(64), nullable=True, unique=True)
    version = Column(String(32), nullable=False)
    status = Column(Enum(GuidelineStatus), default=GuidelineStatus.DRAFT, nullable=False)
    specialty = Column(String(128), nullable=True, index=True)
    publisher = Column(String(256), nullable=True)
    authoring_body = Column(String(256), nullable=True)
    description = Column(Text, nullable=True)
    purpose = Column(Text, nullable=True)
    population = Column(Text, nullable=True)
    evidence_level = Column(Enum(EvidenceLevel), nullable=True)
    publication_date = Column(Date, nullable=True)
    effective_date = Column(Date, nullable=True)
    review_date = Column(Date, nullable=True)
    is_derived_from = Column(String(26), ForeignKey("clinical_guidelines.id"), nullable=True)
    body = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    keywords = Column(String(512), nullable=True)
    language = Column(String(8), default="ar", nullable=False)
    source_url = Column(String(1024), nullable=True)
    reference_count = Column(Integer, default=0, nullable=False)

    derived_from = relationship("ClinicalGuideline", remote_side="ClinicalGuideline.id", backref="derived_versions")
    approvals = relationship("GuidelineApproval", back_populates="guideline", cascade="all, delete-orphan")
    recommendations = relationship("ClinicalRecommendation", back_populates="guideline", cascade="all, delete-orphan")


class ClinicalProtocol(BaseEntity):
    __tablename__ = "clinical_protocols"
    __table_args__ = (
        Index("ix_protocol_status", "status"),
    )

    title = Column(String(512), nullable=False)
    protocol_id = Column(String(64), nullable=True, unique=True)
    version = Column(String(32), nullable=False)
    status = Column(Enum(GuidelineStatus), default=GuidelineStatus.DRAFT, nullable=False)
    guideline_id = Column(String(26), ForeignKey("clinical_guidelines.id", ondelete="SET NULL"), nullable=True)
    department = Column(String(128), nullable=True)
    procedure_category = Column(String(128), nullable=True)
    description = Column(Text, nullable=True)
    inclusion_criteria = Column(Text, nullable=True)
    exclusion_criteria = Column(Text, nullable=True)
    prerequisites = Column(Text, nullable=True)
    steps = Column(Text, nullable=True)
    duration_expected = Column(String(32), nullable=True)
    required_equipment = Column(Text, nullable=True)
    required_personnel = Column(Text, nullable=True)
    complications = Column(Text, nullable=True)
    outcome_measures = Column(Text, nullable=True)
    effective_date = Column(Date, nullable=True)
    expiration_date = Column(Date, nullable=True)
    is_emergency = Column(Boolean, default=False, nullable=False)
    is_surgical = Column(Boolean, default=False, nullable=False)

    guideline = relationship("ClinicalGuideline", backref="protocols")


class ClinicalPathway(BaseEntity):
    __tablename__ = "clinical_pathways"
    __table_args__ = (
        Index("ix_pathway_status", "status"),
    )

    name = Column(String(512), nullable=False)
    version = Column(String(32), nullable=False)
    status = Column(Enum(GuidelineStatus), default=GuidelineStatus.DRAFT, nullable=False)
    condition = Column(String(256), nullable=True, index=True)
    description = Column(Text, nullable=True)
    duration_days = Column(Integer, nullable=True)
    phases = Column(Text, nullable=True)
    milestones = Column(Text, nullable=True)
    expected_outcomes = Column(Text, nullable=True)
    inclusion_criteria = Column(Text, nullable=True)
    exclusion_criteria = Column(Text, nullable=True)
    target_population = Column(Text, nullable=True)
    setting = Column(String(64), nullable=True)
    effective_date = Column(Date, nullable=True)
    expiration_date = Column(Date, nullable=True)
    owner = Column(String(128), nullable=True)

    phases_rel = relationship("PathwayPhase", back_populates="pathway", cascade="all, delete-orphan")


class PathwayPhase(BaseEntity):
    __tablename__ = "clinical_pathway_phases"

    pathway_id = Column(String(26), ForeignKey("clinical_pathways.id", ondelete="CASCADE"), nullable=False)
    phase_number = Column(Integer, nullable=False)
    name = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    duration = Column(String(32), nullable=True)
    criteria = Column(Text, nullable=True)
    interventions = Column(Text, nullable=True)
    expected_outcome = Column(Text, nullable=True)
    escalation_triggers = Column(Text, nullable=True)

    pathway = relationship("ClinicalPathway", back_populates="phases_rel")


class StandingOrder(BaseEntity):
    __tablename__ = "clinical_standing_orders"
    __table_args__ = (
        Index("ix_standing_order_department", "department"),
    )

    title = Column(String(512), nullable=False)
    order_id = Column(String(64), nullable=True, unique=True)
    description = Column(Text, nullable=True)
    department = Column(String(128), nullable=True, index=True)
    order_type = Column(String(64), nullable=False)
    order_details = Column(Text, nullable=False)
    indication = Column(Text, nullable=True)
    contraindications = Column(Text, nullable=True)
    frequency = Column(String(64), nullable=True)
    duration = Column(String(32), nullable=True)
    priority = Column(String(16), nullable=True)
    requires_approval = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    effective_start = Column(Date, nullable=True)
    effective_end = Column(Date, nullable=True)
    approver_role = Column(String(64), nullable=True)
    protocol_id = Column(String(26), ForeignKey("clinical_protocols.id", ondelete="SET NULL"), nullable=True)

    protocol = relationship("ClinicalProtocol", backref="standing_orders")


class ClinicalRecommendation(BaseEntity):
    __tablename__ = "clinical_recommendations"
    __table_args__ = (
        Index("ix_recommendation_guideline", "guideline_id"),
        Index("ix_recommendation_level", "evidence_level"),
    )

    guideline_id = Column(String(26), ForeignKey("clinical_guidelines.id", ondelete="CASCADE"), nullable=False)
    recommendation_number = Column(String(16), nullable=True)
    title = Column(String(512), nullable=False)
    text = Column(Text, nullable=False)
    rationale = Column(Text, nullable=True)
    evidence_level = Column(Enum(EvidenceLevel), nullable=True)
    strength = Column(String(32), nullable=True)
    grade = Column(String(8), nullable=True)
    population = Column(Text, nullable=True)
    action = Column(Text, nullable=True)
    condition = Column(Text, nullable=True)
    exceptions = Column(Text, nullable=True)
    references = Column(Text, nullable=True)
    is_conditional = Column(Boolean, default=False, nullable=False)

    guideline = relationship("ClinicalGuideline", back_populates="recommendations")


class GuidelineApproval(BaseEntity):
    __tablename__ = "clinical_guideline_approvals"
    __table_args__ = (
        Index("ix_guideline_approval_guideline", "guideline_id"),
    )

    guideline_id = Column(String(26), ForeignKey("clinical_guidelines.id", ondelete="CASCADE"), nullable=False)
    approver_id = Column(String(26), nullable=False, index=True)
    approver_name = Column(String(256), nullable=False)
    approver_role = Column(String(128), nullable=True)
    organization = Column(String(256), nullable=True)
    decision = Column(String(16), nullable=False)
    comments = Column(Text, nullable=True)
    approved_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    effective_from = Column(Date, nullable=True)
    effective_until = Column(Date, nullable=True)

    guideline = relationship("ClinicalGuideline", back_populates="approvals")
