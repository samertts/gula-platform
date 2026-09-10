"""Nursing ORM, reconciled to the physical schema (NR-026).

Every model here is generated from the schema migration ``20260716_0002``
builds, then reviewed — not written from intent and hoped to match. Before this
reconciliation the domain could not execute a plain ``SELECT``: all fifteen
models keyed on ``String(26)`` against ``INTEGER`` columns, two named tables no
migration creates, and 137 mapped columns did not exist.

Rules this file follows, and the reasons:

* **The physical schema decides.** Column names, types, nullability, defaults,
  foreign keys and indexes are what PostgreSQL has at head. Where the ORM and
  the database disagreed, the ORM was wrong.
* **No new tables, no new columns.** The reconciliation adds nothing to the
  database; the phantom columns were dropped from the ORM rather than added to
  the schema, because nothing wrote them.
* **No duplicate ownership.** Nursing references ``patients``, ``lab_users``,
  ``labs`` and ``nhdw_admissions`` by their canonical integer keys. It does not
  define its own Patient, Practitioner or User.
* **Cross-base references are plain columns.** Those four tables live on other
  declarative bases, so a ``ForeignKey`` to them cannot resolve and breaks the
  mapper's table sort on every INSERT (NR-023). Pharmacy hit this and solved it
  the same way: declare the column, and let PostgreSQL keep enforcing the
  physical constraint, which it still does. ``nursing_shifts`` is the one target
  inside this MetaData, so its five references keep a real ``ForeignKey``.
* **Identity is not reinvented.** Internal ``INTEGER`` key, portable
  ``sync_id``, both already in the schema. See ``base.py``.

``nursing_shifts`` is the only table other Nursing tables reference; its five
inbound foreign keys are all ``INTEGER``, which is the reason the primary keys
had to move together rather than one model at a time.
"""
from __future__ import annotations

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
)

from app.nursing.base import NursingBaseEntity, NursingFHIREntity

__all__ = [
    "ClinicalChecklist",
    "Delegation",
    "EscalationRecord",
    "FallRiskAssessment",
    "FluidBalance",
    "NursingCarePlan",
    "NursingNote",
    "NursingShift",
    "NursingTask",
    "NutritionAssessment",
    "PainAssessment",
    "PatientAssignment",
    "PressureInjuryAssessment",
    "ShiftHandover",
    "VitalSignsRecord",
]


class NursingShift(NursingBaseEntity):
    __tablename__ = "nursing_shifts"

    nurse_id = Column(Integer, nullable=False)
    shift_type = Column(String(30), nullable=False)
    shift_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=True)
    ward = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False, default="scheduled")
    clocked_in_at = Column(DateTime(timezone=True), nullable=True)
    clocked_out_at = Column(DateTime(timezone=True), nullable=True)
    break_minutes = Column(Integer, nullable=True)
    overtime_minutes = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_nursing_shifts_date", "shift_date"),
        Index("ix_nursing_shifts_lab_date", "lab_id", "shift_date", "shift_type"),
        Index("ix_nursing_shifts_lab_id", "lab_id"),
        Index("ix_nursing_shifts_nurse_id", "nurse_id"),
        {"extend_existing": True},
    )


class PatientAssignment(NursingFHIREntity):
    __tablename__ = "nursing_patient_assignments"

    nurse_id = Column(Integer, nullable=False)
    patient_id = Column(Integer, nullable=False)
    shift_id = Column(Integer, ForeignKey("nursing_shifts.id", ondelete="SET NULL"), nullable=True)
    assignment_type = Column(String(30), nullable=True)
    ward = Column(String(100), nullable=True)
    bed_number = Column(String(20), nullable=True)
    status = Column(String(20), nullable=False, default="active")
    assigned_at = Column(DateTime(timezone=True), nullable=False)
    unassigned_at = Column(DateTime(timezone=True), nullable=True)
    unassigned_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_nursing_patient_assignments_lab_id", "lab_id"),
        Index("ix_nursing_patient_assignments_nurse_id", "nurse_id"),
        Index("ix_nursing_patient_assignments_patient_id", "patient_id"),
        Index("ix_nursing_patient_assignments_shift_id", "shift_id"),
        UniqueConstraint("nurse_id", "patient_id", "shift_id",
                         name="uq_nursing_patient_assignment"),
        {"extend_existing": True},
    )


class NursingTask(NursingFHIREntity):
    __tablename__ = "nursing_tasks"

    patient_id = Column(Integer, nullable=True)
    assigned_by = Column(Integer, nullable=True)
    assigned_to = Column(Integer, nullable=True)
    shift_id = Column(Integer, ForeignKey("nursing_shifts.id", ondelete="SET NULL"), nullable=True)
    task_type = Column(String(50), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String(20), nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    due_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completed_by = Column(Integer, nullable=True)
    cancelled_reason = Column(Text, nullable=True)
    requires_witness = Column(Boolean, nullable=True)
    witnessed_by = Column(Integer, nullable=True)
    witnessed_at = Column(DateTime(timezone=True), nullable=True)
    outcome = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_nursing_tasks_assigned_to", "assigned_to"),
        Index("ix_nursing_tasks_lab_id", "lab_id"),
        Index("ix_nursing_tasks_lab_status", "lab_id", "status", "due_at"),
        Index("ix_nursing_tasks_patient_id", "patient_id"),
        Index("ix_nursing_tasks_shift_id", "shift_id"),
        {"extend_existing": True},
    )


class VitalSignsRecord(NursingFHIREntity):
    __tablename__ = "nursing_vital_signs"

    patient_id = Column(Integer, nullable=False)
    admission_id = Column(Integer, nullable=True)
    recorded_at = Column(DateTime(timezone=True), nullable=False)
    recorded_by = Column(Integer, nullable=True)
    temperature = Column(Float, nullable=True)
    temperature_unit = Column(String(10), nullable=True)
    heart_rate = Column(Integer, nullable=True)
    respiratory_rate = Column(Integer, nullable=True)
    systolic_bp = Column(Integer, nullable=True)
    diastolic_bp = Column(Integer, nullable=True)
    bp_position = Column(String(30), nullable=True)
    bp_cuff_size = Column(String(20), nullable=True)
    oxygen_saturation = Column(Float, nullable=True)
    oxygen_therapy = Column(String(50), nullable=True)
    oxygen_flow_rate = Column(Float, nullable=True)
    blood_glucose = Column(Float, nullable=True)
    blood_glucose_unit = Column(String(20), nullable=True)
    pain_score = Column(Integer, nullable=True)
    consciousness_level = Column(String(50), nullable=True)
    avpu_score = Column(String(10), nullable=True)
    gcs_score = Column(Integer, nullable=True)
    gcs_eye = Column(Integer, nullable=True)
    gcs_verbal = Column(Integer, nullable=True)
    gcs_motor = Column(Integer, nullable=True)
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    bmi = Column(Float, nullable=True)
    head_circumference_cm = Column(Float, nullable=True)
    waist_circumference_cm = Column(Float, nullable=True)
    news2_score = Column(Integer, nullable=True)
    meows_score = Column(Integer, nullable=True)
    clinical_concern = Column(Boolean, nullable=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_nursing_vital_signs_admission_id", "admission_id"),
        Index("ix_nursing_vital_signs_lab_id", "lab_id"),
        Index("ix_nursing_vital_signs_patient_id", "patient_id"),
        Index("ix_nursing_vital_signs_recorded_at", "patient_id", "recorded_at"),
        {"extend_existing": True},
    )


class FluidBalance(NursingFHIREntity):
    __tablename__ = "nursing_fluid_balance"

    patient_id = Column(Integer, nullable=False)
    admission_id = Column(Integer, nullable=True)
    recorded_at = Column(DateTime(timezone=True), nullable=False)
    recorded_by = Column(Integer, nullable=True)
    fluid_type = Column(String(50), nullable=False)
    category = Column(String(20), nullable=False)
    route = Column(String(30), nullable=True)
    solution_name = Column(String(200), nullable=True)
    volume_ml = Column(Float, nullable=False)
    rate_ml_per_hour = Column(Float, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    balance_type = Column(String(20), nullable=False)
    batch_number = Column(String(100), nullable=True)
    witnessed_by = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_nursing_fluid_balance_lab_id", "lab_id"),
        Index("ix_nursing_fluid_balance_patient_id", "patient_id"),
        Index("ix_nursing_fluid_balance_recorded_at", "patient_id", "recorded_at"),
        {"extend_existing": True},
    )


class PainAssessment(NursingFHIREntity):
    __tablename__ = "nursing_pain_assessments"

    patient_id = Column(Integer, nullable=False)
    admission_id = Column(Integer, nullable=True)
    assessed_at = Column(DateTime(timezone=True), nullable=False)
    assessed_by = Column(Integer, nullable=True)
    pain_score = Column(Integer, nullable=False)
    pain_scale = Column(String(30), nullable=True)
    pain_location = Column(String(200), nullable=True)
    pain_type = Column(String(50), nullable=True)
    pain_quality = Column(String(100), nullable=True)
    pain_duration = Column(String(50), nullable=True)
    aggravating_factors = Column(Text, nullable=True)
    relieving_factors = Column(Text, nullable=True)
    interference_with_activity = Column(String(200), nullable=True)
    pain_goal = Column(Integer, nullable=True)
    intervention = Column(Text, nullable=True)
    intervention_response = Column(String(200), nullable=True)
    reassessment_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_nursing_pain_assessments_assessed_at", "patient_id", "assessed_at"),
        Index("ix_nursing_pain_assessments_lab_id", "lab_id"),
        Index("ix_nursing_pain_assessments_patient_id", "patient_id"),
        {"extend_existing": True},
    )


class FallRiskAssessment(NursingFHIREntity):
    __tablename__ = "nursing_fall_risk_assessments"

    patient_id = Column(Integer, nullable=False)
    admission_id = Column(Integer, nullable=True)
    assessed_at = Column(DateTime(timezone=True), nullable=False)
    assessed_by = Column(Integer, nullable=True)
    assessment_tool = Column(String(50), nullable=True)
    total_score = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)
    history_of_falls = Column(Boolean, nullable=True)
    secondary_diagnosis = Column(Boolean, nullable=True)
    ambulatory_aid = Column(Boolean, nullable=True)
    iv_therapy = Column(Boolean, nullable=True)
    gait = Column(String(50), nullable=True)
    mental_status = Column(String(50), nullable=True)
    medication_risk = Column(Boolean, nullable=True)
    environmental_factors = Column(Text, nullable=True)
    prevention_measures = Column(Text, nullable=True)
    reassessment_date = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_nursing_fall_risk_lab_id", "lab_id"),
        Index("ix_nursing_fall_risk_patient_date", "patient_id", "assessed_at"),
        Index("ix_nursing_fall_risk_patient_id", "patient_id"),
        {"extend_existing": True},
    )


class PressureInjuryAssessment(NursingFHIREntity):
    __tablename__ = "nursing_pressure_injury_assessments"

    patient_id = Column(Integer, nullable=False)
    admission_id = Column(Integer, nullable=True)
    assessed_at = Column(DateTime(timezone=True), nullable=False)
    assessed_by = Column(Integer, nullable=True)
    assessment_tool = Column(String(50), nullable=True)
    total_score = Column(Integer, nullable=False)
    risk_level = Column(String(20), nullable=False)
    sensory_perception = Column(Integer, nullable=True)
    moisture = Column(Integer, nullable=True)
    activity = Column(Integer, nullable=True)
    mobility = Column(Integer, nullable=True)
    nutrition = Column(Integer, nullable=True)
    friction_shear = Column(Integer, nullable=True)
    existing_injuries = Column(JSON, nullable=True)
    prevention_measures = Column(Text, nullable=True)
    reassessment_date = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_nursing_pressure_injury_date", "patient_id", "assessed_at"),
        Index("ix_nursing_pressure_injury_lab_id", "lab_id"),
        Index("ix_nursing_pressure_injury_patient_id", "patient_id"),
        {"extend_existing": True},
    )


class NutritionAssessment(NursingFHIREntity):
    __tablename__ = "nursing_nutrition_assessments"

    patient_id = Column(Integer, nullable=False)
    admission_id = Column(Integer, nullable=True)
    assessed_at = Column(DateTime(timezone=True), nullable=False)
    assessed_by = Column(Integer, nullable=True)
    assessment_tool = Column(String(50), nullable=True)
    total_score = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)
    bmi = Column(Float, nullable=True)
    weight_change_percent = Column(Float, nullable=True)
    weight_change_period_days = Column(Integer, nullable=True)
    acute_disease_effect = Column(Boolean, nullable=True)
    food_intake = Column(String(100), nullable=True)
    dietary_requirements = Column(Text, nullable=True)
    swallowing_difficulty = Column(Boolean, nullable=True)
    nutritional_support = Column(String(200), nullable=True)
    dietitian_referral = Column(Boolean, nullable=True)
    reassessment_date = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_nursing_nutrition_date", "patient_id", "assessed_at"),
        Index("ix_nursing_nutrition_lab_id", "lab_id"),
        Index("ix_nursing_nutrition_patient_id", "patient_id"),
        {"extend_existing": True},
    )


class NursingCarePlan(NursingFHIREntity):
    __tablename__ = "nursing_care_plans"

    patient_id = Column(Integer, nullable=False)
    admission_id = Column(Integer, nullable=True)
    care_plan_type = Column(String(50), nullable=False)
    title = Column(String(300), nullable=False)
    nursing_diagnosis = Column(Text, nullable=True)
    goals = Column(JSON, nullable=True)
    interventions = Column(JSON, nullable=True)
    expected_outcomes = Column(JSON, nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=False)
    review_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="active")
    outcome = Column(Text, nullable=True)
    reviewed_by = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_nursing_care_plans_admission_id", "admission_id"),
        Index("ix_nursing_care_plans_lab_id", "lab_id"),
        Index("ix_nursing_care_plans_lab_status", "lab_id", "status"),
        Index("ix_nursing_care_plans_patient_id", "patient_id"),
        {"extend_existing": True},
    )


class NursingNote(NursingFHIREntity):
    __tablename__ = "nursing_notes"

    patient_id = Column(Integer, nullable=False)
    admission_id = Column(Integer, nullable=True)
    note_type = Column(String(50), nullable=False)
    title = Column(String(300), nullable=True)
    content = Column(Text, nullable=False)
    written_by = Column(Integer, nullable=True)
    written_at = Column(DateTime(timezone=True), nullable=False)
    is_signed = Column(Boolean, nullable=True)
    signed_by = Column(Integer, nullable=True)
    signed_at = Column(DateTime(timezone=True), nullable=True)
    is_confidential = Column(Boolean, nullable=True)
    tags = Column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_nursing_notes_admission_id", "admission_id"),
        Index("ix_nursing_notes_lab_id", "lab_id"),
        Index("ix_nursing_notes_patient_date", "patient_id", "written_at"),
        Index("ix_nursing_notes_patient_id", "patient_id"),
        Index("ix_nursing_notes_written_by", "written_by"),
        {"extend_existing": True},
    )


class ShiftHandover(NursingBaseEntity):
    __tablename__ = "nursing_shift_handovers"

    from_shift_id = Column(Integer, ForeignKey("nursing_shifts.id", ondelete="CASCADE"), nullable=False)
    to_shift_id = Column(Integer, ForeignKey("nursing_shifts.id", ondelete="SET NULL"), nullable=True)
    from_nurse_id = Column(Integer, nullable=True)
    to_nurse_id = Column(Integer, nullable=True)
    handover_at = Column(DateTime(timezone=True), nullable=False)
    patient_summary = Column(Text, nullable=True)
    critical_events = Column(JSON, nullable=True)
    pending_tasks = Column(JSON, nullable=True)
    medication_changes = Column(JSON, nullable=True)
    equipment_issues = Column(JSON, nullable=True)
    follow_up_required = Column(Text, nullable=True)
    is_completed = Column(Boolean, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_nursing_shift_handovers_date", "handover_at"),
        Index("ix_nursing_shift_handovers_from_shift", "from_shift_id"),
        Index("ix_nursing_shift_handovers_lab_id", "lab_id"),
        Index("ix_nursing_shift_handovers_to_shift", "to_shift_id"),
        {"extend_existing": True},
    )


class ClinicalChecklist(NursingFHIREntity):
    __tablename__ = "nursing_clinical_checklists"

    patient_id = Column(Integer, nullable=True)
    shift_id = Column(Integer, ForeignKey("nursing_shifts.id", ondelete="SET NULL"), nullable=True)
    checklist_type = Column(String(50), nullable=False)
    title = Column(String(300), nullable=False)
    items = Column(JSON, nullable=False)
    completed_items = Column(JSON, nullable=True)
    total_items = Column(Integer, nullable=False)
    completed_count = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False, default="in_progress")
    assigned_to = Column(Integer, nullable=True)
    completed_by = Column(Integer, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(Integer, nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_nursing_checklists_lab_id", "lab_id"),
        Index("ix_nursing_checklists_lab_type_status", "lab_id", "checklist_type", "status"),
        Index("ix_nursing_checklists_patient_id", "patient_id"),
        Index("ix_nursing_checklists_shift_id", "shift_id"),
        {"extend_existing": True},
    )


class Delegation(NursingBaseEntity):
    __tablename__ = "nursing_delegations"

    patient_id = Column(Integer, nullable=True)
    delegated_by = Column(Integer, nullable=False)
    delegated_to = Column(Integer, nullable=False)
    task_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    delegated_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    requires_supervision = Column(Boolean, nullable=True)
    supervised_by = Column(Integer, nullable=True)
    outcome = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_nursing_delegations_delegated_by", "delegated_by"),
        Index("ix_nursing_delegations_delegated_to", "delegated_to"),
        Index("ix_nursing_delegations_lab_id", "lab_id"),
        Index("ix_nursing_delegations_status", "delegated_to", "status"),
        {"extend_existing": True},
    )


class EscalationRecord(NursingFHIREntity):
    __tablename__ = "nursing_escalation_records"

    patient_id = Column(Integer, nullable=False)
    admission_id = Column(Integer, nullable=True)
    escalated_by = Column(Integer, nullable=False)
    escalated_to = Column(Integer, nullable=True)
    escalation_level = Column(String(30), nullable=False)
    reason = Column(Text, nullable=False)
    clinical_context = Column(Text, nullable=True)
    vital_signs_summary = Column(JSON, nullable=True)
    ews_score = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False, default="active")
    escalated_at = Column(DateTime(timezone=True), nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    outcome = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_nursing_escalation_escalated_by", "escalated_by"),
        Index("ix_nursing_escalation_escalated_to", "escalated_to"),
        Index("ix_nursing_escalation_lab_id", "lab_id"),
        Index("ix_nursing_escalation_lab_status", "lab_id", "status", "escalated_at"),
        Index("ix_nursing_escalation_patient_id", "patient_id"),
        {"extend_existing": True},
    )

