from datetime import datetime

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
)
from sqlalchemy import Enum as SAEnum

from app._compat import UTC
from app.nursing.base import NursingBaseEntity
from app.nursing.enums import (
    AssignmentType,
    DelegationStatus,
    FallRiskLevel,
    FluidCategory,
    HandoverType,
    NursingTaskType,
    NutritionStatus,
    PainLevel,
    PressureInjuryStage,
    ShiftType,
    TaskPriority,
)


class NursingShift(NursingBaseEntity):
    __tablename__ = "nursing_shifts"

    nurse_id = Column(String(26), ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=False, index=True)
    clinician_user_id = Column(String(26), ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("hospital_departments.id", ondelete="SET NULL"), nullable=True, index=True)
    shift_type = Column(SAEnum(ShiftType), nullable=False)
    shift_date = Column(Date, nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    patient_count = Column(Integer, default=0)
    assigned_patients = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_nursing_shifts_nurse_date", "nurse_id", "shift_date"),
        {"extend_existing": True},
    )


class PatientAssignment(NursingBaseEntity):
    __tablename__ = "nursing_patient_assignments"

    nurse_id = Column(String(26), ForeignKey("lab_users.id", ondelete="CASCADE"), nullable=False, index=True)
    clinician_user_id = Column(String(26), ForeignKey("lab_users.id", ondelete="CASCADE"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("hospital_departments.id", ondelete="SET NULL"), nullable=True, index=True)
    assignment_type = Column(SAEnum(AssignmentType), nullable=False, default=AssignmentType.PRIMARY)
    start_date = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_nursing_pat_assign_nurse_active", "nurse_id", "is_active"),
        Index("ix_nursing_pat_assign_patient", "patient_id", "is_active"),
        {"extend_existing": True},
    )


class NursingTask(NursingBaseEntity):
    __tablename__ = "nursing_tasks"

    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_by = Column(String(26), ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_to = Column(String(26), ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True, index=True)
    task_type = Column(SAEnum(NursingTaskType), nullable=False, index=True)
    description = Column(Text, nullable=False)
    priority = Column(SAEnum(TaskPriority), nullable=False, default=TaskPriority.MEDIUM)
    status = Column(String(50), default="pending", index=True)
    scheduled_time = Column(DateTime(timezone=True), nullable=True)
    due_time = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completed_by = Column(String(26), ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    is_recurring = Column(Boolean, default=False)
    recurrence_rule = Column(JSON, nullable=True)
    clinical_instruction = Column(Text, nullable=True)
    patient_response = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_nursing_tasks_patient", "patient_id", "status"),
        Index("ix_nursing_tasks_assigned_to", "assigned_to", "status"),
        Index("ix_nursing_tasks_due", "due_time"),
        {"extend_existing": True},
    )


class VitalSignsRecord(NursingBaseEntity):
    __tablename__ = "nursing_vital_signs"

    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)
    recorded_by = Column(String(26), ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True, index=True)
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)
    bp_systolic = Column(Integer, nullable=True)
    bp_diastolic = Column(Integer, nullable=True)
    heart_rate = Column(Integer, nullable=True)
    respiratory_rate = Column(Integer, nullable=True)
    temperature = Column(Float, nullable=True)
    temperature_site = Column(String(50), nullable=True)
    oxygen_saturation = Column(Float, nullable=True)
    oxygen_device = Column(String(50), nullable=True)
    oxygen_flow_rate = Column(Float, nullable=True)
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    bmi = Column(Float, nullable=True)
    head_circumference_cm = Column(Float, nullable=True)
    pain_score = Column(Integer, nullable=True)
    consciousness_level = Column(String(50), nullable=True)
    gcs_eye = Column(Integer, nullable=True)
    gcs_verbal = Column(Integer, nullable=True)
    gcs_motor = Column(Integer, nullable=True)
    gcs_total = Column(Integer, nullable=True)
    pupil_left_size = Column(Float, nullable=True)
    pupil_left_reaction = Column(String(50), nullable=True)
    pupil_right_size = Column(Float, nullable=True)
    pupil_right_reaction = Column(String(50), nullable=True)
    blood_glucose = Column(Float, nullable=True)
    glucose_context = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_nursing_vs_patient_time", "patient_id", "recorded_at"),
        {"extend_existing": True},
    )


class FluidBalance(NursingBaseEntity):
    __tablename__ = "nursing_fluid_balance"

    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)
    recorded_by = Column(String(26), ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True, index=True)
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    balance_type = Column(String(20), nullable=False)
    category = Column(SAEnum(FluidCategory), nullable=False)
    fluid_name = Column(String(200), nullable=True)
    amount_ml = Column(Float, nullable=False)
    route = Column(String(50), nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    infusion_rate = Column(Float, nullable=True)
    bag_volume = Column(Float, nullable=True)
    bag_number = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_nursing_fb_patient_date", "patient_id", "recorded_at"),
        {"extend_existing": True},
    )


class PainAssessment(NursingBaseEntity):
    __tablename__ = "nursing_pain_assessments"

    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)
    assessed_by = Column(String(26), ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True, index=True)
    assessed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    pain_score = Column(Integer, nullable=False)
    pain_level = Column(SAEnum(PainLevel), nullable=True)
    pain_location = Column(Text, nullable=True)
    pain_quality = Column(String(50), nullable=True)
    pain_pattern = Column(String(50), nullable=True)
    onset = Column(Text, nullable=True)
    duration = Column(Text, nullable=True)
    aggravating_factors = Column(Text, nullable=True)
    relieving_factors = Column(Text, nullable=True)
    pain_goal = Column(Integer, nullable=True)
    interventions_tried = Column(Text, nullable=True)
    effectiveness = Column(String(50), nullable=True)
    non_verbal_indicators = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_nursing_pain_patient_time", "patient_id", "assessed_at"),
        {"extend_existing": True},
    )


class FallRiskAssessment(NursingBaseEntity):
    __tablename__ = "nursing_fall_risk_assessments"

    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)
    assessed_by = Column(String(26), ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True, index=True)
    assessed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    total_score = Column(Integer, nullable=False)
    risk_level = Column(SAEnum(FallRiskLevel), nullable=False)
    age_ge_65 = Column(Boolean, default=False)
    fall_history_12mo = Column(Boolean, default=False)
    secondary_condition = Column(Boolean, default=False)
    assistive_device = Column(Boolean, default=False)
    iv_or_heparin_lock = Column(Boolean, default=False)
    gait_impaired = Column(Boolean, default=False)
    mental_status = Column(String(50), nullable=True)
    elimination = Column(String(50), nullable=True)
    medications = Column(String(100), nullable=True)
    interventions_ordered = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_nursing_fall_patient_time", "patient_id", "assessed_at"),
        {"extend_existing": True},
    )


class PressureInjuryAssessment(NursingBaseEntity):
    __tablename__ = "nursing_pressure_injury_assessments"

    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)
    assessed_by = Column(String(26), ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True, index=True)
    assessed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    stage = Column(SAEnum(PressureInjuryStage), nullable=False)
    anatomical_location = Column(String(200), nullable=True)
    length_cm = Column(Float, nullable=True)
    width_cm = Column(Float, nullable=True)
    depth_cm = Column(Float, nullable=True)
    wound_bed = Column(String(50), nullable=True)
    exudate_type = Column(String(50), nullable=True)
    exudate_amount = Column(String(50), nullable=True)
    wound_edges = Column(String(50), nullable=True)
    periwound_skin = Column(String(50), nullable=True)
    infection_signs = Column(JSON, nullable=True)
    wound_culture = Column(String(100), nullable=True)
    dressing_type = Column(String(100), nullable=True)
    dressing_frequency = Column(String(100), nullable=True)
    treatment_plan = Column(Text, nullable=True)
    photographs = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_nursing_pi_patient_time", "patient_id", "assessed_at"),
        {"extend_existing": True},
    )


class NutritionAssessment(NursingBaseEntity):
    __tablename__ = "nursing_nutrition_assessments"

    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)
    assessed_by = Column(String(26), ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True, index=True)
    assessed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    nutrition_status = Column(SAEnum(NutritionStatus), nullable=False)
    weight_kg = Column(Float, nullable=True)
    height_cm = Column(Float, nullable=True)
    bmi = Column(Float, nullable=True)
    usual_weight_kg = Column(Float, nullable=True)
    weight_change_1mo_kg = Column(Float, nullable=True)
    appetite = Column(String(50), nullable=True)
    dietary_restrictions = Column(JSON, nullable=True)
    chewing_difficulty = Column(Boolean, default=False)
    swallowing_difficulty = Column(Boolean, default=False)
    dysphagia_risk = Column(Boolean, default=False)
    fluid_restriction_ml = Column(Float, nullable=True)
    calorie_target_kcal = Column(Float, nullable=True)
    protein_target_g = Column(Float, nullable=True)
    feeding_method = Column(String(50), nullable=True)
    supplements = Column(JSON, nullable=True)
    diet_type = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_nursing_nutrition_patient_time", "patient_id", "assessed_at"),
        {"extend_existing": True},
    )


class NursingCarePlan(NursingBaseEntity):
    __tablename__ = "nursing_care_plans"

    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)
    nursing_diagnosis = Column(Text, nullable=False)
    goals = Column(JSON, nullable=True)
    interventions = Column(JSON, nullable=True)
    evaluation = Column(Text, nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=False)
    review_date = Column(DateTime(timezone=True), nullable=True)
    next_review = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="active", index=True)
    created_by = Column(String(26), ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    approved_by = Column(String(26), ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_nursing_cp_patient", "patient_id", "status"),
        {"extend_existing": True},
    )


class NursingNote(NursingBaseEntity):
    __tablename__ = "nursing_notes"

    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)
    shift_id = Column(String(26), ForeignKey("nursing_shifts.id", ondelete="SET NULL"), nullable=True, index=True)
    documented_by = Column(String(26), ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True, index=True)
    documentation_time = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    note_type = Column(String(50), nullable=False, index=True)
    subjective = Column(Text, nullable=True)
    objective = Column(Text, nullable=True)
    assessment = Column(Text, nullable=True)
    intervention = Column(Text, nullable=True)
    response = Column(Text, nullable=True)
    evaluation = Column(Text, nullable=True)
    plan = Column(Text, nullable=True)
    attachments = Column(JSON, nullable=True)
    patient_education = Column(Text, nullable=True)
    is_confidential = Column(Boolean, default=False)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_nursing_notes_patient_type", "patient_id", "note_type"),
        Index("ix_nursing_notes_shift", "shift_id"),
        {"extend_existing": True},
    )


class ShiftHandover(NursingBaseEntity):
    __tablename__ = "nursing_shift_handovers"

    from_shift_id = Column(String(26), ForeignKey("nursing_shifts.id", ondelete="SET NULL"), nullable=True, index=True)
    to_shift_id = Column(String(26), ForeignKey("nursing_shifts.id", ondelete="SET NULL"), nullable=True, index=True)
    from_nurse_id = Column(String(26), ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True, index=True)
    to_nurse_id = Column(String(26), ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True, index=True)
    handover_type = Column(SAEnum(HandoverType), nullable=False)
    shift_date = Column(Date, nullable=False, index=True)
    patient_summaries = Column(JSON, nullable=True)
    pending_tasks = Column(JSON, nullable=True)
    critical_alerts = Column(JSON, nullable=True)
    medication_changes = Column(JSON, nullable=True)
    equipment_issues = Column(JSON, nullable=True)
    staffing_issues = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_nursing_ho_date_type", "shift_date", "handover_type"),
        {"extend_existing": True},
    )


class ClinicalChecklist(NursingBaseEntity):
    __tablename__ = "nursing_checklists"

    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)
    checklist_type = Column(String(50), nullable=False, index=True)
    items = Column(JSON, nullable=True)
    status = Column(String(50), default="draft", index=True)
    created_by = Column(String(26), ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    verified_by = Column(String(26), ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_nursing_cl_patient_type", "patient_id", "checklist_type"),
        {"extend_existing": True},
    )


class Delegation(NursingBaseEntity):
    __tablename__ = "nursing_delegations"

    task_id = Column(String(26), ForeignKey("nursing_tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    delegated_by = Column(String(26), ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=False, index=True)
    delegated_to = Column(String(26), ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=False, index=True)
    delegation_time = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(SAEnum(DelegationStatus), nullable=False, default=DelegationStatus.PENDING)
    reason = Column(Text, nullable=True)
    scope_notes = Column(Text, nullable=True)
    supervising_instructions = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_nursing_del_to_status", "delegated_to", "status"),
        Index("ix_nursing_del_from_status", "delegated_by", "status"),
        {"extend_existing": True},
    )


class EscalationRecord(NursingBaseEntity):
    __tablename__ = "nursing_escalations"

    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)
    escalated_by = Column(String(26), ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=False, index=True)
    escalated_to = Column(String(26), ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True, index=True)
    escalation_time = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    reason = Column(Text, nullable=False)
    severity = Column(String(50), nullable=False)
    category = Column(String(50), nullable=False)
    status = Column(String(50), default="open", index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(26), ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    resolution = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_nursing_esc_patient", "patient_id", "status"),
        Index("ix_nursing_esc_to_status", "escalated_to", "status"),
        {"extend_existing": True},
    )
