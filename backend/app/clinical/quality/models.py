from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.clinical.base import BaseEntity
from app.clinical.enums import QualityIndicatorType


class QualityIndicator(BaseEntity):
    __tablename__ = "clinical_quality_indicators"
    __table_args__ = (
        Index("ix_quality_indicator_type", "indicator_type"),
        Index("ix_quality_indicator_dept", "department"),
    )

    name = Column(String(256), nullable=False)
    code = Column(String(64), nullable=True, unique=True)
    indicator_type = Column(Enum(QualityIndicatorType), nullable=False)
    description = Column(Text, nullable=True)
    department = Column(String(128), nullable=True, index=True)
    numerator = Column(String(512), nullable=False)
    denominator = Column(String(512), nullable=False)
    target_value = Column(Float, nullable=True)
    benchmark_value = Column(Float, nullable=True)
    unit = Column(String(32), nullable=True)
    frequency = Column(String(32), nullable=True)
    direction = Column(String(8), nullable=True)
    is_national = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    steward = Column(String(128), nullable=True)
    source = Column(String(128), nullable=True)
    effective_start = Column(Date, nullable=True)
    effective_end = Column(Date, nullable=True)

    measurements = relationship("IndicatorMeasurement", back_populates="indicator", cascade="all, delete-orphan")


class IndicatorMeasurement(BaseEntity):
    __tablename__ = "clinical_indicator_measurements"
    __table_args__ = (
        Index("ix_indicator_measurement_date", "indicator_id", "measurement_date"),
    )

    indicator_id = Column(String(26), ForeignKey("clinical_quality_indicators.id", ondelete="CASCADE"), nullable=False)
    measurement_date = Column(Date, nullable=False)
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    numerator_value = Column(Float, nullable=False)
    denominator_value = Column(Float, nullable=True)
    result_value = Column(Float, nullable=True)
    percentage = Column(Float, nullable=True)
    met_target = Column(Boolean, nullable=True)
    notes = Column(Text, nullable=True)
    measured_by = Column(String(26), nullable=True)

    indicator = relationship("QualityIndicator", back_populates="measurements")


class ClinicalAuditRecord(BaseEntity):
    __tablename__ = "clinical_audit_records"
    __table_args__ = (
        Index("ix_audit_record_patient", "patient_id"),
        Index("ix_audit_record_date", "audit_date"),
    )

    audit_type = Column(String(64), nullable=False)
    patient_id = Column(String(26), nullable=True, index=True)
    encounter_id = Column(String(26), nullable=True)
    provider_id = Column(String(26), nullable=True)
    department = Column(String(128), nullable=True)
    audit_date = Column(Date, nullable=False, index=True)
    criteria = Column(Text, nullable=True)
    finding = Column(Text, nullable=True)
    compliance = Column(String(16), nullable=False)
    score = Column(Float, nullable=True)
    severity = Column(String(16), nullable=True)
    recommendations = Column(Text, nullable=True)
    corrective_action = Column(Text, nullable=True)
    corrective_deadline = Column(Date, nullable=True)
    corrective_completed = Column(Boolean, default=False, nullable=False)
    corrective_completed_at = Column(DateTime(timezone=True), nullable=True)
    audited_by = Column(String(26), nullable=False)
    reviewed_by = Column(String(26), nullable=True)


class ComplianceCheck(BaseEntity):
    __tablename__ = "clinical_compliance_checks"
    __table_args__ = (
        Index("ix_compliance_check_date", "check_date"),
        Index("ix_compliance_check_standard", "standard"),
    )

    check_type = Column(String(64), nullable=False)
    standard = Column(String(256), nullable=True, index=True)
    department = Column(String(128), nullable=True)
    check_date = Column(Date, nullable=False)
    result = Column(String(16), nullable=False)
    score = Column(Float, nullable=True)
    findings = Column(Text, nullable=True)
    non_conformities = Column(Text, nullable=True)
    observations = Column(Text, nullable=True)
    opportunities = Column(Text, nullable=True)
    action_plan = Column(Text, nullable=True)
    deadline = Column(Date, nullable=True)
    status = Column(String(16), default="open", nullable=False)
    checked_by = Column(String(26), nullable=False)
    approved_by = Column(String(26), nullable=True)


class BenchmarkValue(BaseEntity):
    __tablename__ = "clinical_benchmark_values"
    __table_args__ = (
        Index("ix_benchmark_indicator", "indicator_id"),
    )

    indicator_id = Column(String(26), ForeignKey("clinical_quality_indicators.id", ondelete="CASCADE"), nullable=False)
    benchmark_name = Column(String(128), nullable=False)
    source = Column(String(256), nullable=True)
    value = Column(Float, nullable=False)
    percentile = Column(Integer, nullable=True)
    year = Column(Integer, nullable=True)
    region = Column(String(64), nullable=True)
    setting = Column(String(64), nullable=True)
    population = Column(String(128), nullable=True)
    is_national = Column(Boolean, default=False, nullable=False)

    indicator = relationship("QualityIndicator", backref="benchmarks")


class MortalityReview(BaseEntity):
    __tablename__ = "clinical_mortality_reviews"
    __table_args__ = (
        Index("ix_mortality_patient", "patient_id"),
        Index("ix_mortality_date", "review_date"),
    )

    patient_id = Column(String(26), nullable=False, index=True)
    encounter_id = Column(String(26), nullable=True)
    date_of_death = Column(Date, nullable=False)
    cause_of_death = Column(String(256), nullable=True)
    cause_code = Column(String(16), nullable=True)
    cause_system = Column(String(32), nullable=True)
    location = Column(String(128), nullable=True)
    department = Column(String(128), nullable=True)
    review_date = Column(Date, nullable=False)
    reviewer = Column(String(26), nullable=False)
    classification = Column(String(32), nullable=True)
    preventability = Column(String(16), nullable=True)
    contributing_factors = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    is_autopsy_performed = Column(Boolean, default=False, nullable=False)
    autopsy_findings = Column(Text, nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False)


class IncidentReport(BaseEntity):
    __tablename__ = "clinical_incident_reports"
    __table_args__ = (
        Index("ix_incident_type", "incident_type"),
        Index("ix_incident_date", "incident_date"),
    )

    incident_type = Column(String(64), nullable=False, index=True)
    incident_date = Column(DateTime(timezone=True), nullable=False)
    severity = Column(String(16), nullable=False)
    location = Column(String(128), nullable=True)
    department = Column(String(128), nullable=True)
    patient_id = Column(String(26), nullable=True)
    encounter_id = Column(String(26), nullable=True)
    reporter_id = Column(String(26), nullable=False)
    description = Column(Text, nullable=True)
    immediate_action = Column(Text, nullable=True)
    contributing_factors = Column(Text, nullable=True)
    root_cause = Column(Text, nullable=True)
    outcome = Column(Text, nullable=True)
    actions_taken = Column(Text, nullable=True)
    status = Column(String(16), default="open", nullable=False)
    reviewed_by = Column(String(26), nullable=True)
    review_comments = Column(Text, nullable=True)
    is_notifiable = Column(Boolean, default=False, nullable=False)
    notified_authority = Column(String(128), nullable=True)
    notified_at = Column(DateTime(timezone=True), nullable=True)


class PatientSafetyEvent(BaseEntity):
    __tablename__ = "clinical_patient_safety_events"
    __table_args__ = (
        Index("ix_safety_event_category", "category"),
        Index("ix_safety_event_patient", "patient_id"),
    )

    category = Column(String(64), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)
    patient_id = Column(String(26), nullable=True, index=True)
    encounter_id = Column(String(26), nullable=True)
    provider_id = Column(String(26), nullable=True)
    event_date = Column(DateTime(timezone=True), nullable=False)
    severity = Column(String(16), nullable=False)
    description = Column(Text, nullable=True)
    harm_level = Column(String(16), nullable=True)
    preventability = Column(String(16), nullable=True)
    contributing_factors = Column(Text, nullable=True)
    mitigating_factors = Column(Text, nullable=True)
    actions_taken = Column(Text, nullable=True)
    outcome = Column(Text, nullable=True)
    reported_by = Column(String(26), nullable=False)
    reviewed_by = Column(String(26), nullable=True)
    review_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(16), default="open", nullable=False)
    is_sentinel = Column(Boolean, default=False, nullable=False)
    sentinel_review_completed = Column(Boolean, default=False, nullable=False)
