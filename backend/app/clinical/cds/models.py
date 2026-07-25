from __future__ import annotations

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

from app.clinical.base import BaseEntity
from app.clinical.enums import EvidenceLevel


class OrderSet(BaseEntity):
    __tablename__ = "clinical_order_sets"
    __table_args__ = (
        Index("ix_order_set_department", "department"),
        Index("ix_order_set_condition", "condition"),
    )

    name = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    department = Column(String(128), nullable=True, index=True)
    condition = Column(String(256), nullable=True)
    version = Column(String(32), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_emergency = Column(Boolean, default=False, nullable=False)
    priority = Column(Integer, default=0, nullable=False)
    required_justification = Column(Boolean, default=False, nullable=False)
    guideline_id = Column(
        String(26), ForeignKey("clinical_guidelines.id", ondelete="SET NULL"), nullable=True,
    )
    effective_start = Column(Date, nullable=True)
    effective_end = Column(Date, nullable=True)

    items = relationship("OrderSetItem", back_populates="order_set", cascade="all, delete-orphan")


class OrderSetItem(BaseEntity):
    __tablename__ = "clinical_order_set_items"

    order_set_id = Column(
        String(26), ForeignKey("clinical_order_sets.id", ondelete="CASCADE"), nullable=False,
    )
    item_type = Column(String(32), nullable=False)
    item_code = Column(String(64), nullable=True)
    item_display = Column(String(256), nullable=True)
    sequence = Column(Integer, default=0, nullable=False)
    is_optional = Column(Boolean, default=False, nullable=False)
    is_required = Column(Boolean, default=True, nullable=False)
    default_value = Column(String(256), nullable=True)
    instructions = Column(Text, nullable=True)
    frequency = Column(String(64), nullable=True)

    order_set = relationship("OrderSet", back_populates="items")


class CareBundle(BaseEntity):
    __tablename__ = "clinical_care_bundles"
    __table_args__ = (Index("ix_care_bundle_condition", "condition"),)

    name = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    condition = Column(String(256), nullable=True, index=True)
    version = Column(String(32), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    evidence_level = Column(Enum(EvidenceLevel), nullable=True)
    compliance_threshold = Column(Integer, default=80, nullable=False)
    elements_summary = Column(Text, nullable=True)
    rationale = Column(Text, nullable=True)
    guideline_id = Column(
        String(26), ForeignKey("clinical_guidelines.id", ondelete="SET NULL"), nullable=True,
    )

    elements = relationship(
        "CareBundleElement", back_populates="care_bundle", cascade="all, delete-orphan",
    )


class CareBundleElement(BaseEntity):
    __tablename__ = "clinical_care_bundle_elements"

    care_bundle_id = Column(
        String(26), ForeignKey("clinical_care_bundles.id", ondelete="CASCADE"), nullable=False,
    )
    element_code = Column(String(64), nullable=False)
    element_name = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    sequence = Column(Integer, default=0, nullable=False)
    is_all_or_none = Column(Boolean, default=True, nullable=False)
    time_window = Column(String(32), nullable=True)
    numerator = Column(String(256), nullable=True)
    denominator = Column(String(256), nullable=True)

    care_bundle = relationship("CareBundle", back_populates="elements")


class ClinicalAlert(BaseEntity):
    __tablename__ = "clinical_alerts"
    __table_args__ = (
        Index("ix_clinical_alert_severity", "severity"),
        Index("ix_clinical_alert_patient", "patient_id"),
    )

    alert_type = Column(String(64), nullable=False, index=True)
    severity = Column(String(16), nullable=False)
    patient_id = Column(String(26), nullable=True, index=True)
    encounter_id = Column(String(26), nullable=True)
    provider_id = Column(String(26), nullable=True)
    title = Column(String(256), nullable=False)
    message = Column(Text, nullable=False)
    detail = Column(Text, nullable=True)
    trigger_code = Column(String(64), nullable=True)
    trigger_system = Column(String(32), nullable=True)
    trigger_value = Column(String(256), nullable=True)
    is_actionable = Column(Boolean, default=True, nullable=False)
    acknowledged = Column(Boolean, default=False, nullable=False)
    acknowledged_by = Column(String(26), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved = Column(Boolean, default=False, nullable=False)
    resolved_by = Column(String(26), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    source_rule_id = Column(String(26), nullable=True)

    actions = relationship(
        "ClinicalAlertAction", back_populates="alert", cascade="all, delete-orphan",
    )


class ClinicalAlertAction(BaseEntity):
    __tablename__ = "clinical_alert_actions"

    alert_id = Column(
        String(26), ForeignKey("clinical_alerts.id", ondelete="CASCADE"), nullable=False,
    )
    action = Column(String(32), nullable=False)
    description = Column(Text, nullable=True)
    parameters = Column(Text, nullable=True)
    executed = Column(Boolean, default=False, nullable=False)
    executed_by = Column(String(26), nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    outcome = Column(String(64), nullable=True)

    alert = relationship("ClinicalAlert", back_populates="actions")


class Contraindication(BaseEntity):
    __tablename__ = "clinical_contraindications"
    __table_args__ = (
        Index("ix_contraindication_subject", "subject_code", "subject_system"),
        Index("ix_contraindication_contra", "contraindicated_code", "contraindicated_system"),
    )

    subject_code = Column(String(64), nullable=False)
    subject_system = Column(String(32), nullable=False)
    subject_display = Column(String(256), nullable=True)
    contraindicated_code = Column(String(64), nullable=False)
    contraindicated_system = Column(String(32), nullable=False)
    contraindicated_display = Column(String(256), nullable=True)
    relationship_type = Column(String(32), nullable=False)
    severity = Column(String(16), nullable=False)
    evidence = Column(Text, nullable=True)
    mechanism = Column(String(256), nullable=True)
    management = Column(Text, nullable=True)
    alternative = Column(Text, nullable=True)
    is_absolute = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    source = Column(String(64), nullable=True)


class DuplicateOrderRule(BaseEntity):
    __tablename__ = "clinical_duplicate_order_rules"
    __table_args__ = (Index("ix_duplicate_order_code", "order_code"),)

    order_code = Column(String(64), nullable=False, index=True)
    order_system = Column(String(32), nullable=True)
    rule_name = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    time_window_hours = Column(Integer, nullable=False)
    same_encounter_only = Column(Boolean, default=True, nullable=False)
    same_provider_only = Column(Boolean, default=False, nullable=False)
    action = Column(String(32), nullable=False)
    severity = Column(String(16), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    notification_message = Column(Text, nullable=True)
    override_requires_approval = Column(Boolean, default=False, nullable=False)
    override_reason_required = Column(Boolean, default=True, nullable=False)


class ReminderRule(BaseEntity):
    __tablename__ = "clinical_reminder_rules"
    __table_args__ = (Index("ix_reminder_rule_trigger", "trigger_event"),)

    name = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    trigger_event = Column(String(64), nullable=False, index=True)
    condition_expression = Column(Text, nullable=True)
    action_type = Column(String(32), nullable=False)
    action_config = Column(Text, nullable=True)
    priority = Column(Integer, default=0, nullable=False)
    frequency = Column(String(32), nullable=True)
    max_reminders = Column(Integer, default=3, nullable=False)
    escalation_after_hours = Column(Integer, nullable=True)
    escalation_action = Column(String(32), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    effective_start = Column(Date, nullable=True)
    effective_end = Column(Date, nullable=True)
    target_role = Column(String(64), nullable=True)


class PreventiveRecommendation(BaseEntity):
    __tablename__ = "clinical_preventive_recommendations"
    __table_args__ = (
        Index("ix_preventive_condition", "condition"),
        Index("ix_preventive_age_range", "age_min", "age_max"),
    )

    title = Column(String(256), nullable=False)
    condition = Column(String(256), nullable=True, index=True)
    description = Column(Text, nullable=True)
    recommendation_type = Column(String(32), nullable=False)
    intervention = Column(Text, nullable=True)
    intervention_code = Column(String(64), nullable=True)
    intervention_system = Column(String(32), nullable=True)
    frequency = Column(String(64), nullable=True)
    age_min = Column(Integer, nullable=True)
    age_max = Column(Integer, nullable=True)
    gender = Column(String(1), nullable=True)
    risk_factors = Column(Text, nullable=True)
    evidence_level = Column(Enum(EvidenceLevel), nullable=True)
    guideline_id = Column(
        String(26), ForeignKey("clinical_guidelines.id", ondelete="SET NULL"), nullable=True,
    )
    is_active = Column(Boolean, default=True, nullable=False)
    effective_start = Column(Date, nullable=True)
    effective_end = Column(Date, nullable=True)
    priority = Column(String(16), nullable=True)
    source = Column(String(128), nullable=True)
