"""Create Nursing Platform tables.

Creates all Nursing domain entities:
  - nursing_shifts, nursing_patient_assignments, nursing_tasks
  - nursing_vital_signs, nursing_fluid_balance
  - nursing_pain_assessments, nursing_fall_risk_assessments
  - nursing_pressure_injury_assessments, nursing_nutrition_assessments
  - nursing_care_plans, nursing_notes, nursing_shift_handovers
  - nursing_clinical_checklists, nursing_delegations
  - nursing_escalation_records

Revision ID: 20260716_0002
Revises: 20260716_0001
Create Date: 2026-07-16
"""

from typing import Union
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import inspect

revision: str = "20260716_0002"
down_revision: str | None = "20260716_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def _index_exists(idx_name: str) -> bool:
    insp = inspect(op.get_bind())
    for table in insp.get_table_names():
        for idx in insp.get_indexes(table):
            if idx["name"] == idx_name:
                return True
    return False


def upgrade() -> None:
    # ── Nursing Shifts ────────────────────────────────────────────────────────
    if not _table_exists("nursing_shifts"):
        op.create_table(
            "nursing_shifts",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column(
                "lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False
            ),
            sa.Column(
                "nurse_id",
                sa.Integer(),
                sa.ForeignKey("lab_users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("shift_type", sa.String(30), nullable=False),
            sa.Column("shift_date", sa.Date(), nullable=False),
            sa.Column("start_time", sa.Time(), nullable=False),
            sa.Column("end_time", sa.Time(), nullable=True),
            sa.Column("ward", sa.String(100), nullable=True),
            sa.Column("department", sa.String(100), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="scheduled"),
            sa.Column("clocked_in_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("clocked_out_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("break_minutes", sa.Integer(), nullable=True),
            sa.Column("overtime_minutes", sa.Integer(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_nursing_shifts_lab_id", "nursing_shifts", ["lab_id"])
        op.create_index("ix_nursing_shifts_nurse_id", "nursing_shifts", ["nurse_id"])
        op.create_index("ix_nursing_shifts_date", "nursing_shifts", ["shift_date"])
        op.create_index(
            "ix_nursing_shifts_lab_date", "nursing_shifts", ["lab_id", "shift_date", "shift_type"]
        )

    # ── Patient Assignments ───────────────────────────────────────────────────
    if not _table_exists("nursing_patient_assignments"):
        op.create_table(
            "nursing_patient_assignments",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column(
                "lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False
            ),
            sa.Column(
                "nurse_id",
                sa.Integer(),
                sa.ForeignKey("lab_users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "patient_id",
                sa.Integer(),
                sa.ForeignKey("patients.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "shift_id",
                sa.Integer(),
                sa.ForeignKey("nursing_shifts.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("assignment_type", sa.String(30), default="primary"),
            sa.Column("ward", sa.String(100), nullable=True),
            sa.Column("bed_number", sa.String(20), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="active"),
            sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("unassigned_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("unassigned_reason", sa.Text(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "nurse_id", "patient_id", "shift_id", name="uq_nursing_patient_assignment"
            ),
        )
        op.create_index(
            "ix_nursing_patient_assignments_lab_id", "nursing_patient_assignments", ["lab_id"]
        )
        op.create_index(
            "ix_nursing_patient_assignments_nurse_id", "nursing_patient_assignments", ["nurse_id"]
        )
        op.create_index(
            "ix_nursing_patient_assignments_patient_id",
            "nursing_patient_assignments",
            ["patient_id"],
        )
        op.create_index(
            "ix_nursing_patient_assignments_shift_id", "nursing_patient_assignments", ["shift_id"]
        )

    # ── Nursing Tasks ─────────────────────────────────────────────────────────
    if not _table_exists("nursing_tasks"):
        op.create_table(
            "nursing_tasks",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column(
                "lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False
            ),
            sa.Column(
                "patient_id",
                sa.Integer(),
                sa.ForeignKey("patients.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column(
                "assigned_by",
                sa.Integer(),
                sa.ForeignKey("lab_users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column(
                "assigned_to",
                sa.Integer(),
                sa.ForeignKey("lab_users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column(
                "shift_id",
                sa.Integer(),
                sa.ForeignKey("nursing_shifts.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("task_type", sa.String(50), nullable=False),
            sa.Column("title", sa.String(300), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("priority", sa.String(20), default="normal"),
            sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
            sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "completed_by",
                sa.Integer(),
                sa.ForeignKey("lab_users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("cancelled_reason", sa.Text(), nullable=True),
            sa.Column("requires_witness", sa.Boolean(), default=False),
            sa.Column(
                "witnessed_by",
                sa.Integer(),
                sa.ForeignKey("lab_users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("witnessed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("outcome", sa.Text(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_nursing_tasks_lab_id", "nursing_tasks", ["lab_id"])
        op.create_index("ix_nursing_tasks_patient_id", "nursing_tasks", ["patient_id"])
        op.create_index("ix_nursing_tasks_assigned_to", "nursing_tasks", ["assigned_to"])
        op.create_index("ix_nursing_tasks_shift_id", "nursing_tasks", ["shift_id"])
        op.create_index(
            "ix_nursing_tasks_lab_status", "nursing_tasks", ["lab_id", "status", "due_at"]
        )

    # ── Vital Signs ───────────────────────────────────────────────────────────
    if not _table_exists("nursing_vital_signs"):
        op.create_table(
            "nursing_vital_signs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column(
                "lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False
            ),
            sa.Column(
                "patient_id",
                sa.Integer(),
                sa.ForeignKey("patients.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "admission_id",
                sa.Integer(),
                sa.ForeignKey("nhdw_admissions.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column(
                "recorded_by",
                sa.Integer(),
                sa.ForeignKey("lab_users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("temperature", sa.Float(), nullable=True),
            sa.Column("temperature_unit", sa.String(10), default="celsius"),
            sa.Column("heart_rate", sa.Integer(), nullable=True),
            sa.Column("respiratory_rate", sa.Integer(), nullable=True),
            sa.Column("systolic_bp", sa.Integer(), nullable=True),
            sa.Column("diastolic_bp", sa.Integer(), nullable=True),
            sa.Column("bp_position", sa.String(30), nullable=True),
            sa.Column("bp_cuff_size", sa.String(20), nullable=True),
            sa.Column("oxygen_saturation", sa.Float(), nullable=True),
            sa.Column("oxygen_therapy", sa.String(50), nullable=True),
            sa.Column("oxygen_flow_rate", sa.Float(), nullable=True),
            sa.Column("blood_glucose", sa.Float(), nullable=True),
            sa.Column("blood_glucose_unit", sa.String(20), nullable=True),
            sa.Column("pain_score", sa.Integer(), nullable=True),
            sa.Column("consciousness_level", sa.String(50), nullable=True),
            sa.Column("avpu_score", sa.String(10), nullable=True),
            sa.Column("gcs_score", sa.Integer(), nullable=True),
            sa.Column("gcs_eye", sa.Integer(), nullable=True),
            sa.Column("gcs_verbal", sa.Integer(), nullable=True),
            sa.Column("gcs_motor", sa.Integer(), nullable=True),
            sa.Column("height_cm", sa.Float(), nullable=True),
            sa.Column("weight_kg", sa.Float(), nullable=True),
            sa.Column("bmi", sa.Float(), nullable=True),
            sa.Column("head_circumference_cm", sa.Float(), nullable=True),
            sa.Column("waist_circumference_cm", sa.Float(), nullable=True),
            sa.Column("news2_score", sa.Integer(), nullable=True),
            sa.Column("meows_score", sa.Integer(), nullable=True),
            sa.Column("clinical_concern", sa.Boolean(), default=False),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_nursing_vital_signs_lab_id", "nursing_vital_signs", ["lab_id"])
        op.create_index("ix_nursing_vital_signs_patient_id", "nursing_vital_signs", ["patient_id"])
        op.create_index(
            "ix_nursing_vital_signs_admission_id", "nursing_vital_signs", ["admission_id"]
        )
        op.create_index(
            "ix_nursing_vital_signs_recorded_at",
            "nursing_vital_signs",
            ["patient_id", "recorded_at"],
        )

    # ── Fluid Balance ─────────────────────────────────────────────────────────
    if not _table_exists("nursing_fluid_balance"):
        op.create_table(
            "nursing_fluid_balance",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column(
                "lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False
            ),
            sa.Column(
                "patient_id",
                sa.Integer(),
                sa.ForeignKey("patients.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "admission_id",
                sa.Integer(),
                sa.ForeignKey("nhdw_admissions.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column(
                "recorded_by",
                sa.Integer(),
                sa.ForeignKey("lab_users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("fluid_type", sa.String(50), nullable=False),
            sa.Column("category", sa.String(20), nullable=False),
            sa.Column("route", sa.String(30), nullable=True),
            sa.Column("solution_name", sa.String(200), nullable=True),
            sa.Column("volume_ml", sa.Float(), nullable=False),
            sa.Column("rate_ml_per_hour", sa.Float(), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("balance_type", sa.String(20), nullable=False),
            sa.Column("batch_number", sa.String(100), nullable=True),
            sa.Column(
                "witnessed_by",
                sa.Integer(),
                sa.ForeignKey("lab_users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_nursing_fluid_balance_lab_id", "nursing_fluid_balance", ["lab_id"])
        op.create_index(
            "ix_nursing_fluid_balance_patient_id", "nursing_fluid_balance", ["patient_id"]
        )
        op.create_index(
            "ix_nursing_fluid_balance_recorded_at",
            "nursing_fluid_balance",
            ["patient_id", "recorded_at"],
        )

    # ── Pain Assessments ──────────────────────────────────────────────────────
    if not _table_exists("nursing_pain_assessments"):
        op.create_table(
            "nursing_pain_assessments",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column(
                "lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False
            ),
            sa.Column(
                "patient_id",
                sa.Integer(),
                sa.ForeignKey("patients.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "admission_id",
                sa.Integer(),
                sa.ForeignKey("nhdw_admissions.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column(
                "assessed_by",
                sa.Integer(),
                sa.ForeignKey("lab_users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("pain_score", sa.Integer(), nullable=False),
            sa.Column("pain_scale", sa.String(30), default="numeric"),
            sa.Column("pain_location", sa.String(200), nullable=True),
            sa.Column("pain_type", sa.String(50), nullable=True),
            sa.Column("pain_quality", sa.String(100), nullable=True),
            sa.Column("pain_duration", sa.String(50), nullable=True),
            sa.Column("aggravating_factors", sa.Text(), nullable=True),
            sa.Column("relieving_factors", sa.Text(), nullable=True),
            sa.Column("interference_with_activity", sa.String(200), nullable=True),
            sa.Column("pain_goal", sa.Integer(), nullable=True),
            sa.Column("intervention", sa.Text(), nullable=True),
            sa.Column("intervention_response", sa.String(200), nullable=True),
            sa.Column("reassessment_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_nursing_pain_assessments_lab_id", "nursing_pain_assessments", ["lab_id"]
        )
        op.create_index(
            "ix_nursing_pain_assessments_patient_id", "nursing_pain_assessments", ["patient_id"]
        )
        op.create_index(
            "ix_nursing_pain_assessments_assessed_at",
            "nursing_pain_assessments",
            ["patient_id", "assessed_at"],
        )

    # ── Fall Risk Assessments ─────────────────────────────────────────────────
    if not _table_exists("nursing_fall_risk_assessments"):
        op.create_table(
            "nursing_fall_risk_assessments",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column(
                "lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False
            ),
            sa.Column(
                "patient_id",
                sa.Integer(),
                sa.ForeignKey("patients.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "admission_id",
                sa.Integer(),
                sa.ForeignKey("nhdw_admissions.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column(
                "assessed_by",
                sa.Integer(),
                sa.ForeignKey("lab_users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("assessment_tool", sa.String(50), default="morse"),
            sa.Column("total_score", sa.Float(), nullable=False),
            sa.Column("risk_level", sa.String(20), nullable=False),
            sa.Column("history_of_falls", sa.Boolean(), default=False),
            sa.Column("secondary_diagnosis", sa.Boolean(), default=False),
            sa.Column("ambulatory_aid", sa.Boolean(), default=False),
            sa.Column("iv_therapy", sa.Boolean(), default=False),
            sa.Column("gait", sa.String(50), nullable=True),
            sa.Column("mental_status", sa.String(50), nullable=True),
            sa.Column("medication_risk", sa.Boolean(), default=False),
            sa.Column("environmental_factors", sa.Text(), nullable=True),
            sa.Column("prevention_measures", sa.Text(), nullable=True),
            sa.Column("reassessment_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_nursing_fall_risk_lab_id", "nursing_fall_risk_assessments", ["lab_id"])
        op.create_index(
            "ix_nursing_fall_risk_patient_id", "nursing_fall_risk_assessments", ["patient_id"]
        )
        op.create_index(
            "ix_nursing_fall_risk_patient_date",
            "nursing_fall_risk_assessments",
            ["patient_id", "assessed_at"],
        )

    # ── Pressure Injury Assessments ───────────────────────────────────────────
    if not _table_exists("nursing_pressure_injury_assessments"):
        op.create_table(
            "nursing_pressure_injury_assessments",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column(
                "lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False
            ),
            sa.Column(
                "patient_id",
                sa.Integer(),
                sa.ForeignKey("patients.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "admission_id",
                sa.Integer(),
                sa.ForeignKey("nhdw_admissions.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column(
                "assessed_by",
                sa.Integer(),
                sa.ForeignKey("lab_users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("assessment_tool", sa.String(50), default="braden"),
            sa.Column("total_score", sa.Integer(), nullable=False),
            sa.Column("risk_level", sa.String(20), nullable=False),
            sa.Column("sensory_perception", sa.Integer(), nullable=True),
            sa.Column("moisture", sa.Integer(), nullable=True),
            sa.Column("activity", sa.Integer(), nullable=True),
            sa.Column("mobility", sa.Integer(), nullable=True),
            sa.Column("nutrition", sa.Integer(), nullable=True),
            sa.Column("friction_shear", sa.Integer(), nullable=True),
            sa.Column("existing_injuries", JSON(), nullable=True),
            sa.Column("prevention_measures", sa.Text(), nullable=True),
            sa.Column("reassessment_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_nursing_pressure_injury_lab_id", "nursing_pressure_injury_assessments", ["lab_id"]
        )
        op.create_index(
            "ix_nursing_pressure_injury_patient_id",
            "nursing_pressure_injury_assessments",
            ["patient_id"],
        )
        op.create_index(
            "ix_nursing_pressure_injury_date",
            "nursing_pressure_injury_assessments",
            ["patient_id", "assessed_at"],
        )

    # ── Nutrition Assessments ─────────────────────────────────────────────────
    if not _table_exists("nursing_nutrition_assessments"):
        op.create_table(
            "nursing_nutrition_assessments",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column(
                "lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False
            ),
            sa.Column(
                "patient_id",
                sa.Integer(),
                sa.ForeignKey("patients.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "admission_id",
                sa.Integer(),
                sa.ForeignKey("nhdw_admissions.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column(
                "assessed_by",
                sa.Integer(),
                sa.ForeignKey("lab_users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("assessment_tool", sa.String(50), default="must"),
            sa.Column("total_score", sa.Float(), nullable=False),
            sa.Column("risk_level", sa.String(20), nullable=False),
            sa.Column("bmi", sa.Float(), nullable=True),
            sa.Column("weight_change_percent", sa.Float(), nullable=True),
            sa.Column("weight_change_period_days", sa.Integer(), nullable=True),
            sa.Column("acute_disease_effect", sa.Boolean(), default=False),
            sa.Column("food_intake", sa.String(100), nullable=True),
            sa.Column("dietary_requirements", sa.Text(), nullable=True),
            sa.Column("swallowing_difficulty", sa.Boolean(), default=False),
            sa.Column("nutritional_support", sa.String(200), nullable=True),
            sa.Column("dietitian_referral", sa.Boolean(), default=False),
            sa.Column("reassessment_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_nursing_nutrition_lab_id", "nursing_nutrition_assessments", ["lab_id"])
        op.create_index(
            "ix_nursing_nutrition_patient_id", "nursing_nutrition_assessments", ["patient_id"]
        )
        op.create_index(
            "ix_nursing_nutrition_date",
            "nursing_nutrition_assessments",
            ["patient_id", "assessed_at"],
        )

    # ── Care Plans (Nursing) ──────────────────────────────────────────────────
    if not _table_exists("nursing_care_plans"):
        op.create_table(
            "nursing_care_plans",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column(
                "lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False
            ),
            sa.Column(
                "patient_id",
                sa.Integer(),
                sa.ForeignKey("patients.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "admission_id",
                sa.Integer(),
                sa.ForeignKey("nhdw_admissions.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("care_plan_type", sa.String(50), nullable=False),
            sa.Column("title", sa.String(300), nullable=False),
            sa.Column("nursing_diagnosis", sa.Text(), nullable=True),
            sa.Column("goals", JSON(), nullable=True),
            sa.Column("interventions", JSON(), nullable=True),
            sa.Column("expected_outcomes", JSON(), nullable=True),
            sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("review_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="active"),
            sa.Column("outcome", sa.Text(), nullable=True),
            sa.Column(
                "reviewed_by",
                sa.Integer(),
                sa.ForeignKey("lab_users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_nursing_care_plans_lab_id", "nursing_care_plans", ["lab_id"])
        op.create_index("ix_nursing_care_plans_patient_id", "nursing_care_plans", ["patient_id"])
        op.create_index(
            "ix_nursing_care_plans_admission_id", "nursing_care_plans", ["admission_id"]
        )
        op.create_index(
            "ix_nursing_care_plans_lab_status", "nursing_care_plans", ["lab_id", "status"]
        )

    # ── Nursing Notes ─────────────────────────────────────────────────────────
    if not _table_exists("nursing_notes"):
        op.create_table(
            "nursing_notes",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column(
                "lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False
            ),
            sa.Column(
                "patient_id",
                sa.Integer(),
                sa.ForeignKey("patients.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "admission_id",
                sa.Integer(),
                sa.ForeignKey("nhdw_admissions.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("note_type", sa.String(50), nullable=False),
            sa.Column("title", sa.String(300), nullable=True),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column(
                "written_by",
                sa.Integer(),
                sa.ForeignKey("lab_users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("written_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_signed", sa.Boolean(), default=False),
            sa.Column(
                "signed_by",
                sa.Integer(),
                sa.ForeignKey("lab_users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_confidential", sa.Boolean(), default=False),
            sa.Column("tags", JSON(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_nursing_notes_lab_id", "nursing_notes", ["lab_id"])
        op.create_index("ix_nursing_notes_patient_id", "nursing_notes", ["patient_id"])
        op.create_index("ix_nursing_notes_admission_id", "nursing_notes", ["admission_id"])
        op.create_index("ix_nursing_notes_written_by", "nursing_notes", ["written_by"])
        op.create_index(
            "ix_nursing_notes_patient_date", "nursing_notes", ["patient_id", "written_at"]
        )

    # ── Shift Handovers ───────────────────────────────────────────────────────
    if not _table_exists("nursing_shift_handovers"):
        op.create_table(
            "nursing_shift_handovers",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column(
                "lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False
            ),
            sa.Column(
                "from_shift_id",
                sa.Integer(),
                sa.ForeignKey("nursing_shifts.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "to_shift_id",
                sa.Integer(),
                sa.ForeignKey("nursing_shifts.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column(
                "from_nurse_id",
                sa.Integer(),
                sa.ForeignKey("lab_users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column(
                "to_nurse_id",
                sa.Integer(),
                sa.ForeignKey("lab_users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("handover_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("patient_summary", sa.Text(), nullable=True),
            sa.Column("critical_events", JSON(), nullable=True),
            sa.Column("pending_tasks", JSON(), nullable=True),
            sa.Column("medication_changes", JSON(), nullable=True),
            sa.Column("equipment_issues", JSON(), nullable=True),
            sa.Column("follow_up_required", sa.Text(), nullable=True),
            sa.Column("is_completed", sa.Boolean(), default=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_nursing_shift_handovers_lab_id", "nursing_shift_handovers", ["lab_id"])
        op.create_index(
            "ix_nursing_shift_handovers_from_shift", "nursing_shift_handovers", ["from_shift_id"]
        )
        op.create_index(
            "ix_nursing_shift_handovers_to_shift", "nursing_shift_handovers", ["to_shift_id"]
        )
        op.create_index(
            "ix_nursing_shift_handovers_date", "nursing_shift_handovers", ["handover_at"]
        )

    # ── Clinical Checklists ───────────────────────────────────────────────────
    if not _table_exists("nursing_clinical_checklists"):
        op.create_table(
            "nursing_clinical_checklists",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column(
                "lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False
            ),
            sa.Column(
                "patient_id",
                sa.Integer(),
                sa.ForeignKey("patients.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column(
                "shift_id",
                sa.Integer(),
                sa.ForeignKey("nursing_shifts.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("checklist_type", sa.String(50), nullable=False),
            sa.Column("title", sa.String(300), nullable=False),
            sa.Column("items", JSON(), nullable=False),
            sa.Column("completed_items", JSON(), nullable=True),
            sa.Column("total_items", sa.Integer(), nullable=False),
            sa.Column("completed_count", sa.Integer(), default=0),
            sa.Column("status", sa.String(20), nullable=False, server_default="in_progress"),
            sa.Column(
                "assigned_to",
                sa.Integer(),
                sa.ForeignKey("lab_users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column(
                "completed_by",
                sa.Integer(),
                sa.ForeignKey("lab_users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "verified_by",
                sa.Integer(),
                sa.ForeignKey("lab_users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_nursing_checklists_lab_id", "nursing_clinical_checklists", ["lab_id"])
        op.create_index(
            "ix_nursing_checklists_patient_id", "nursing_clinical_checklists", ["patient_id"]
        )
        op.create_index(
            "ix_nursing_checklists_shift_id", "nursing_clinical_checklists", ["shift_id"]
        )
        op.create_index(
            "ix_nursing_checklists_lab_type_status",
            "nursing_clinical_checklists",
            ["lab_id", "checklist_type", "status"],
        )

    # ── Delegations ───────────────────────────────────────────────────────────
    if not _table_exists("nursing_delegations"):
        op.create_table(
            "nursing_delegations",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column(
                "lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False
            ),
            sa.Column(
                "patient_id",
                sa.Integer(),
                sa.ForeignKey("patients.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column(
                "delegated_by",
                sa.Integer(),
                sa.ForeignKey("lab_users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "delegated_to",
                sa.Integer(),
                sa.ForeignKey("lab_users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("task_type", sa.String(50), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
            sa.Column("delegated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("cancellation_reason", sa.Text(), nullable=True),
            sa.Column("requires_supervision", sa.Boolean(), default=False),
            sa.Column(
                "supervised_by",
                sa.Integer(),
                sa.ForeignKey("lab_users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("outcome", sa.Text(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_nursing_delegations_lab_id", "nursing_delegations", ["lab_id"])
        op.create_index(
            "ix_nursing_delegations_delegated_by", "nursing_delegations", ["delegated_by"]
        )
        op.create_index(
            "ix_nursing_delegations_delegated_to", "nursing_delegations", ["delegated_to"]
        )
        op.create_index(
            "ix_nursing_delegations_status", "nursing_delegations", ["delegated_to", "status"]
        )

    # ── Escalation Records ────────────────────────────────────────────────────
    if not _table_exists("nursing_escalation_records"):
        op.create_table(
            "nursing_escalation_records",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column(
                "lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False
            ),
            sa.Column(
                "patient_id",
                sa.Integer(),
                sa.ForeignKey("patients.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "admission_id",
                sa.Integer(),
                sa.ForeignKey("nhdw_admissions.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column(
                "escalated_by",
                sa.Integer(),
                sa.ForeignKey("lab_users.id", ondelete="SET NULL"),
                nullable=False,
            ),
            sa.Column(
                "escalated_to",
                sa.Integer(),
                sa.ForeignKey("lab_users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("escalation_level", sa.String(30), nullable=False),
            sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("clinical_context", sa.Text(), nullable=True),
            sa.Column("vital_signs_summary", JSON(), nullable=True),
            sa.Column("ews_score", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="active"),
            sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("resolution_notes", sa.Text(), nullable=True),
            sa.Column("outcome", sa.Text(), nullable=True),
            sa.Column("sync_id", sa.String(26), unique=True),
            sa.Column("fhir_id", sa.String(64), nullable=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), default=1, nullable=False),
            sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_nursing_escalation_lab_id", "nursing_escalation_records", ["lab_id"])
        op.create_index(
            "ix_nursing_escalation_patient_id", "nursing_escalation_records", ["patient_id"]
        )
        op.create_index(
            "ix_nursing_escalation_escalated_by", "nursing_escalation_records", ["escalated_by"]
        )
        op.create_index(
            "ix_nursing_escalation_escalated_to", "nursing_escalation_records", ["escalated_to"]
        )
        op.create_index(
            "ix_nursing_escalation_lab_status",
            "nursing_escalation_records",
            ["lab_id", "status", "escalated_at"],
        )


def downgrade() -> None:
    tables = [
        "nursing_escalation_records",
        "nursing_delegations",
        "nursing_clinical_checklists",
        "nursing_shift_handovers",
        "nursing_notes",
        "nursing_care_plans",
        "nursing_nutrition_assessments",
        "nursing_pressure_injury_assessments",
        "nursing_fall_risk_assessments",
        "nursing_pain_assessments",
        "nursing_fluid_balance",
        "nursing_vital_signs",
        "nursing_tasks",
        "nursing_patient_assignments",
        "nursing_shifts",
    ]
    for table in tables:
        if _table_exists(table):
            op.drop_table(table)
