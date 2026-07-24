"""Create National Critical Care Platform tables.

Revision ID: 20260716_0007
Revises: 20260716_0006
Create Date: 2026-07-16
"""

from typing import Union
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy import inspect

revision: str = "20260716_0007"
down_revision: str | None = "20260716_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def upgrade() -> None:
    if not _table_exists("critical_care_admissions"):
        op.create_table(
            "critical_care_admissions",
            sa.Column("patient_id", sa.String(), nullable=False),
            sa.Column("patient_name", sa.String()),
            sa.Column("medical_record_number", sa.String()),
            sa.Column("icu_type", sa.String(), default="adult_icu"),
            sa.Column("admission_type", sa.String(), default="emergency"),
            sa.Column("admission_source", sa.String()),
            sa.Column("admission_diagnosis", sa.Text()),
            sa.Column("admitting_physician", sa.String()),
            sa.Column("bed_id", sa.String()),
            sa.Column("room_id", sa.String()),
            sa.Column("unit_id", sa.String()),
            sa.Column("facility_id", sa.String()),
            sa.Column("status", sa.String(), default="stable"),
            sa.Column("isolation_type", sa.String(), default="standard"),
            sa.Column("isolation_reason", sa.Text()),
            sa.Column("admitting_notes", sa.Text()),
            sa.Column("primary_problem_list", sa.JSON()),
            sa.Column("allergies", sa.JSON()),
            sa.Column("code_status", sa.String(), default="full_code"),
            sa.Column("organ_donor_status", sa.Boolean(), default=False),
            sa.Column("expected_discharge_date", sa.DateTime(timezone=True)),
            sa.Column("discharged_at", sa.DateTime(timezone=True)),
            sa.Column("discharge_summary", sa.Text()),
            sa.Column("discharge_destination", sa.String()),
            sa.Column("discharge_reason", sa.String()),
            sa.Column("readmission_within_48h", sa.Boolean(), default=False),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("created_by", sa.Integer()),
            sa.Column("updated_by", sa.Integer()),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_critical_care_admissions_lab_id", "critical_care_admissions", ["lab_id"])
        op.create_index("ix_critical_care_admissions_patient_id", "critical_care_admissions", ["patient_id"])
        op.create_index("ix_critical_care_admissions_fhir_id", "critical_care_admissions", ["fhir_id"])

    if not _table_exists("critical_care_beds"):
        op.create_table(
            "critical_care_beds",
            sa.Column("bed_label", sa.String(), nullable=False),
            sa.Column("room_id", sa.String()),
            sa.Column("unit_id", sa.String()),
            sa.Column("facility_id", sa.String()),
            sa.Column("icu_type", sa.String(), default="adult_icu"),
            sa.Column("is_occupied", sa.Boolean(), default=False),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("current_patient_id", sa.String()),
            sa.Column("current_admission_id", sa.String()),
            sa.Column("has_ventilator", sa.Boolean(), default=False),
            sa.Column("has_monitor", sa.Boolean(), default=False),
            sa.Column("has_infusion_pump", sa.Boolean(), default=False),
            sa.Column("has_dialysis", sa.Boolean(), default=False),
            sa.Column("supported_ventilator_types", sa.JSON()),
            sa.Column("last_cleaned_at", sa.DateTime(timezone=True)),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_critical_care_beds_lab_id", "critical_care_beds", ["lab_id"])
        op.create_index("ix_critical_care_beds_fhir_id", "critical_care_beds", ["fhir_id"])

    if not _table_exists("critical_care_assessments"):
        op.create_table(
            "critical_care_assessments",
            sa.Column("admission_id", sa.String(), sa.ForeignKey("critical_care_admissions.id")),
            sa.Column("patient_id", sa.String()),
            sa.Column("assessment_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("assessed_by", sa.String()),
            sa.Column("clinical_assessment", sa.Text()),
            sa.Column("respiratory_assessment", sa.Text()),
            sa.Column("cardiovascular_assessment", sa.Text()),
            sa.Column("neurological_assessment", sa.Text()),
            sa.Column("renal_assessment", sa.Text()),
            sa.Column("gi_assessment", sa.Text()),
            sa.Column("skin_assessment", sa.Text()),
            sa.Column("pain_assessment", sa.Text()),
            sa.Column("sedation_assessment", sa.Text()),
            sa.Column("delirium_assessment", sa.Text()),
            sa.Column("mobility_assessment", sa.Text()),
            sa.Column("plan", sa.Text()),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("created_by", sa.Integer()),
            sa.Column("updated_by", sa.Integer()),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_critical_care_assessments_fhir_id", "critical_care_assessments", ["fhir_id"])
        op.create_index("ix_critical_care_assessments_lab_id", "critical_care_assessments", ["lab_id"])
        op.create_index("ix_critical_care_assessments_admission_id", "critical_care_assessments", ["admission_id"])

    if not _table_exists("critical_care_vital_signs"):
        op.create_table(
            "critical_care_vital_signs",
            sa.Column("patient_id", sa.String(), nullable=False),
            sa.Column("admission_id", sa.String(), sa.ForeignKey("critical_care_admissions.id")),
            sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("recorded_by", sa.String()),
            sa.Column("heart_rate", sa.Integer()),
            sa.Column("respiratory_rate", sa.Integer()),
            sa.Column("systolic_bp", sa.Integer()),
            sa.Column("diastolic_bp", sa.Integer()),
            sa.Column("mean_arterial_pressure", sa.Float()),
            sa.Column("temperature", sa.Float()),
            sa.Column("oxygen_saturation", sa.Float()),
            sa.Column("fi_o2", sa.Float()),
            sa.Column("pao2", sa.Float()),
            sa.Column("paco2", sa.Float()),
            sa.Column("ph", sa.Float()),
            sa.Column("hco3", sa.Float()),
            sa.Column("lactate", sa.Float()),
            sa.Column("glucose", sa.Float()),
            sa.Column("cvp", sa.Float()),
            sa.Column("cardiac_output", sa.Float()),
            sa.Column("cardiac_index", sa.Float()),
            sa.Column("svr", sa.Float()),
            sa.Column("pvr", sa.Float()),
            sa.Column("sv_o2", sa.Float()),
            sa.Column("gcs_total", sa.Integer()),
            sa.Column("gcs_eye", sa.Integer()),
            sa.Column("gcs_verbal", sa.Integer()),
            sa.Column("gcs_motor", sa.Integer()),
            sa.Column("pupil_right", sa.String()),
            sa.Column("pupil_left", sa.String()),
            sa.Column("pain_score", sa.Integer()),
            sa.Column("sedation_score", sa.Integer()),
            sa.Column("sedation_scale", sa.String(), default="rass"),
            sa.Column("ricam_icu", sa.Boolean()),
            sa.Column("notes", sa.Text()),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_critical_care_vital_signs_patient_id", "critical_care_vital_signs", ["patient_id"])
        op.create_index("ix_critical_care_vital_signs_lab_id", "critical_care_vital_signs", ["lab_id"])
        op.create_index("ix_critical_care_vital_signs_fhir_id", "critical_care_vital_signs", ["fhir_id"])

    if not _table_exists("critical_care_ventilator_settings"):
        op.create_table(
            "critical_care_ventilator_settings",
            sa.Column("patient_id", sa.String(), nullable=False),
            sa.Column("admission_id", sa.String(), sa.ForeignKey("critical_care_admissions.id")),
            sa.Column("setting_time", sa.DateTime(timezone=True), nullable=False),
            sa.Column("set_by", sa.String()),
            sa.Column("mode", sa.String(), default="ac"),
            sa.Column("ventilator_type", sa.String(), default="invasive"),
            sa.Column("tidal_volume_ml", sa.Integer()),
            sa.Column("respiratory_rate_set", sa.Integer()),
            sa.Column("respiratory_rate_total", sa.Integer()),
            sa.Column("peep_cmh2o", sa.Float()),
            sa.Column("pressure_support", sa.Float()),
            sa.Column("peak_inspiratory_pressure", sa.Float()),
            sa.Column("plateau_pressure", sa.Float()),
            sa.Column("mean_airway_pressure", sa.Float()),
            sa.Column("fi_o2", sa.Float()),
            sa.Column("inspiratory_time", sa.Float()),
            sa.Column("ie_ratio", sa.String()),
            sa.Column("minute_ventilation", sa.Float()),
            sa.Column("static_compliance", sa.Float()),
            sa.Column("driving_pressure", sa.Float()),
            sa.Column("rsbi", sa.Float()),
            sa.Column("etco2", sa.Float()),
            sa.Column("spontaneous_breathing_trials", sa.Boolean(), default=False),
            sa.Column("weaning_protocol", sa.String()),
            sa.Column("sedation_hold", sa.Boolean(), default=False),
            sa.Column("notes", sa.Text()),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("created_by", sa.Integer()),
            sa.Column("updated_by", sa.Integer()),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_critical_care_ventilator_settings_patient_id", "critical_care_ventilator_settings", ["patient_id"])
        op.create_index("ix_critical_care_ventilator_settings_fhir_id", "critical_care_ventilator_settings", ["fhir_id"])
        op.create_index("ix_critical_care_ventilator_settings_lab_id", "critical_care_ventilator_settings", ["lab_id"])

    if not _table_exists("critical_care_infusions"):
        op.create_table(
            "critical_care_infusions",
            sa.Column("patient_id", sa.String(), nullable=False),
            sa.Column("admission_id", sa.String(), sa.ForeignKey("critical_care_admissions.id")),
            sa.Column("medication", sa.String(), nullable=False),
            sa.Column("medication_dose", sa.String()),
            sa.Column("rate", sa.String()),
            sa.Column("rate_units", sa.String(), default="ml/hr"),
            sa.Column("route", sa.String(), default="iv"),
            sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
            sa.Column("end_time", sa.DateTime(timezone=True)),
            sa.Column("initiated_by", sa.String()),
            sa.Column("pump_id", sa.String()),
            sa.Column("titrated_to", sa.String()),
            sa.Column("titration_history", sa.JSON()),
            sa.Column("compatible_with", sa.JSON()),
            sa.Column("incompatible_with", sa.JSON()),
            sa.Column("bag_volume_ml", sa.Float()),
            sa.Column("bag_remaining_ml", sa.Float()),
            sa.Column("line_type", sa.String(), default="peripheral"),
            sa.Column("line_site", sa.String()),
            sa.Column("site_assessment", sa.Text()),
            sa.Column("is_pca", sa.Boolean(), default=False),
            sa.Column("notes", sa.Text()),
            sa.Column("status", sa.String(), default="active"),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("created_by", sa.Integer()),
            sa.Column("updated_by", sa.Integer()),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_critical_care_infusions_fhir_id", "critical_care_infusions", ["fhir_id"])
        op.create_index("ix_critical_care_infusions_lab_id", "critical_care_infusions", ["lab_id"])
        op.create_index("ix_critical_care_infusions_patient_id", "critical_care_infusions", ["patient_id"])

    if not _table_exists("critical_care_fluid_balance"):
        op.create_table(
            "critical_care_fluid_balance",
            sa.Column("patient_id", sa.String(), nullable=False),
            sa.Column("admission_id", sa.String(), sa.ForeignKey("critical_care_admissions.id")),
            sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("recorded_by", sa.String()),
            sa.Column("total_intake_ml", sa.Float(), default=0.0),
            sa.Column("total_output_ml", sa.Float(), default=0.0),
            sa.Column("net_balance_ml", sa.Float(), default=0.0),
            sa.Column("cumulative_balance_ml", sa.Float(), default=0.0),
            sa.Column("iv_fluids_ml", sa.Float(), default=0.0),
            sa.Column("enteral_feeding_ml", sa.Float(), default=0.0),
            sa.Column("oral_intake_ml", sa.Float(), default=0.0),
            sa.Column("blood_products_ml", sa.Float(), default=0.0),
            sa.Column("urine_output_ml", sa.Float(), default=0.0),
            sa.Column("stool_output_ml", sa.Float(), default=0.0),
            sa.Column("ng_output_ml", sa.Float(), default=0.0),
            sa.Column("drain_output_ml", sa.Float(), default=0.0),
            sa.Column("estimated_blood_loss_ml", sa.Float(), default=0.0),
            sa.Column("insensible_losses_ml", sa.Float(), default=0.0),
            sa.Column("notes", sa.Text()),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_critical_care_fluid_balance_fhir_id", "critical_care_fluid_balance", ["fhir_id"])
        op.create_index("ix_critical_care_fluid_balance_lab_id", "critical_care_fluid_balance", ["lab_id"])
        op.create_index("ix_critical_care_fluid_balance_patient_id", "critical_care_fluid_balance", ["patient_id"])

    if not _table_exists("critical_care_early_warning_scores"):
        op.create_table(
            "critical_care_early_warning_scores",
            sa.Column("patient_id", sa.String(), nullable=False),
            sa.Column("admission_id", sa.String(), sa.ForeignKey("critical_care_admissions.id")),
            sa.Column("score_time", sa.DateTime(timezone=True), nullable=False),
            sa.Column("score_system", sa.String(), default="news2"),
            sa.Column("score_value", sa.Integer(), default=0),
            sa.Column("heart_rate_score", sa.Integer(), default=0),
            sa.Column("respiratory_rate_score", sa.Integer(), default=0),
            sa.Column("systolic_bp_score", sa.Integer(), default=0),
            sa.Column("temperature_score", sa.Integer(), default=0),
            sa.Column("consciousness_score", sa.Integer(), default=0),
            sa.Column("oxygen_score", sa.Integer(), default=0),
            sa.Column("supplemental_oxygen", sa.Boolean(), default=False),
            sa.Column("risk_category", sa.String(), default="low"),
            sa.Column("recommended_frequency", sa.String(), default="q4h"),
            sa.Column("triggers_escalation", sa.Boolean(), default=False),
            sa.Column("calculated_by", sa.String()),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_critical_care_early_warning_scores_lab_id", "critical_care_early_warning_scores", ["lab_id"])
        op.create_index("ix_critical_care_early_warning_scores_fhir_id", "critical_care_early_warning_scores", ["fhir_id"])
        op.create_index("ix_critical_care_early_warning_scores_patient_id", "critical_care_early_warning_scores", ["patient_id"])

    if not _table_exists("critical_care_scores"):
        op.create_table(
            "critical_care_scores",
            sa.Column("patient_id", sa.String(), nullable=False),
            sa.Column("admission_id", sa.String(), sa.ForeignKey("critical_care_admissions.id")),
            sa.Column("score_time", sa.DateTime(timezone=True), nullable=False),
            sa.Column("score_type", sa.String(), nullable=False),
            sa.Column("score_value", sa.Integer(), nullable=False),
            sa.Column("score_components", sa.JSON()),
            sa.Column("mortality_prediction", sa.Float()),
            sa.Column("calculated_by", sa.String()),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_critical_care_scores_patient_id", "critical_care_scores", ["patient_id"])
        op.create_index("ix_critical_care_scores_lab_id", "critical_care_scores", ["lab_id"])
        op.create_index("ix_critical_care_scores_fhir_id", "critical_care_scores", ["fhir_id"])

    if not _table_exists("critical_care_alerts"):
        op.create_table(
            "critical_care_alerts",
            sa.Column("patient_id", sa.String(), nullable=False),
            sa.Column("admission_id", sa.String(), sa.ForeignKey("critical_care_admissions.id")),
            sa.Column("alert_type", sa.String(), nullable=False),
            sa.Column("severity", sa.String(), default="warning"),
            sa.Column("alert_message", sa.Text()),
            sa.Column("alert_time", sa.DateTime(timezone=True), nullable=False),
            sa.Column("triggered_by", sa.String()),
            sa.Column("parameter", sa.String()),
            sa.Column("value", sa.String()),
            sa.Column("threshold", sa.String()),
            sa.Column("acknowledged_by", sa.String()),
            sa.Column("acknowledged_at", sa.DateTime(timezone=True)),
            sa.Column("resolved_by", sa.String()),
            sa.Column("resolved_at", sa.DateTime(timezone=True)),
            sa.Column("action_taken", sa.Text()),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_critical_care_alerts_patient_id", "critical_care_alerts", ["patient_id"])
        op.create_index("ix_critical_care_alerts_fhir_id", "critical_care_alerts", ["fhir_id"])
        op.create_index("ix_critical_care_alerts_lab_id", "critical_care_alerts", ["lab_id"])

    if not _table_exists("critical_care_device_integrations"):
        op.create_table(
            "critical_care_device_integrations",
            sa.Column("patient_id", sa.String()),
            sa.Column("admission_id", sa.String()),
            sa.Column("device_type", sa.String(), nullable=False),
            sa.Column("device_id", sa.String(), nullable=False),
            sa.Column("device_name", sa.String()),
            sa.Column("vendor", sa.String()),
            sa.Column("model", sa.String()),
            sa.Column("connectivity", sa.String(), default="network"),
            sa.Column("is_connected", sa.Boolean(), default=False),
            sa.Column("last_data_received", sa.DateTime(timezone=True)),
            sa.Column("parameters", sa.JSON()),
            sa.Column("settings", sa.JSON()),
            sa.Column("alerts", sa.JSON()),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_critical_care_device_integrations_lab_id", "critical_care_device_integrations", ["lab_id"])
        op.create_index("ix_critical_care_device_integrations_fhir_id", "critical_care_device_integrations", ["fhir_id"])

    if not _table_exists("critical_care_daily_checklists"):
        op.create_table(
            "critical_care_daily_checklists",
            sa.Column("admission_id", sa.String(), sa.ForeignKey("critical_care_admissions.id")),
            sa.Column("patient_id", sa.String()),
            sa.Column("checklist_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("completed_by", sa.String()),
            sa.Column("ventilator_bundle", sa.Boolean(), default=False),
            sa.Column("central_line_bundle", sa.Boolean(), default=False),
            sa.Column("catheter_bundle", sa.Boolean(), default=False),
            sa.Column("vte_prophylaxis", sa.Boolean(), default=False),
            sa.Column("stress_ulcer_prophylaxis", sa.Boolean(), default=False),
            sa.Column("sedation_vacation", sa.Boolean(), default=False),
            sa.Column("spontaneous_breathing_trial", sa.Boolean(), default=False),
            sa.Column("spontaneous_awakening_trial", sa.Boolean(), default=False),
            sa.Column("glucose_control", sa.Boolean(), default=False),
            sa.Column("nutrition_assessment", sa.Boolean(), default=False),
            sa.Column("mobilization", sa.Boolean(), default=False),
            sa.Column("family_communication", sa.Boolean(), default=False),
            sa.Column("goals_of_care", sa.Boolean(), default=False),
            sa.Column("plan_for_day", sa.Text()),
            sa.Column("issues", sa.Text()),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("created_by", sa.Integer()),
            sa.Column("updated_by", sa.Integer()),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_critical_care_daily_checklists_lab_id", "critical_care_daily_checklists", ["lab_id"])
        op.create_index("ix_critical_care_daily_checklists_fhir_id", "critical_care_daily_checklists", ["fhir_id"])

    if not _table_exists("critical_care_rounds"):
        op.create_table(
            "critical_care_rounds",
            sa.Column("admission_id", sa.String(), sa.ForeignKey("critical_care_admissions.id")),
            sa.Column("patient_id", sa.String()),
            sa.Column("round_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("attending_physician", sa.String()),
            sa.Column("team_members", sa.JSON()),
            sa.Column("overnight_events", sa.Text()),
            sa.Column("review_of_systems", sa.Text()),
            sa.Column("assessment", sa.Text()),
            sa.Column("plan", sa.Text()),
            sa.Column("medications_reviewed", sa.Boolean(), default=False),
            sa.Column("imaging_reviewed", sa.Boolean(), default=False),
            sa.Column("labs_reviewed", sa.Boolean(), default=False),
            sa.Column("microbiology_reviewed", sa.Boolean(), default=False),
            sa.Column("follow_up_items", sa.JSON()),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("created_by", sa.Integer()),
            sa.Column("updated_by", sa.Integer()),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_critical_care_rounds_lab_id", "critical_care_rounds", ["lab_id"])
        op.create_index("ix_critical_care_rounds_fhir_id", "critical_care_rounds", ["fhir_id"])



def downgrade() -> None:
    if _table_exists("critical_care_rounds"):
        op.drop_table("critical_care_rounds")
    if _table_exists("critical_care_daily_checklists"):
        op.drop_table("critical_care_daily_checklists")
    if _table_exists("critical_care_device_integrations"):
        op.drop_table("critical_care_device_integrations")
    if _table_exists("critical_care_alerts"):
        op.drop_table("critical_care_alerts")
    if _table_exists("critical_care_scores"):
        op.drop_table("critical_care_scores")
    if _table_exists("critical_care_early_warning_scores"):
        op.drop_table("critical_care_early_warning_scores")
    if _table_exists("critical_care_fluid_balance"):
        op.drop_table("critical_care_fluid_balance")
    if _table_exists("critical_care_infusions"):
        op.drop_table("critical_care_infusions")
    if _table_exists("critical_care_ventilator_settings"):
        op.drop_table("critical_care_ventilator_settings")
    if _table_exists("critical_care_vital_signs"):
        op.drop_table("critical_care_vital_signs")
    if _table_exists("critical_care_assessments"):
        op.drop_table("critical_care_assessments")
    if _table_exists("critical_care_beds"):
        op.drop_table("critical_care_beds")
    if _table_exists("critical_care_admissions"):
        op.drop_table("critical_care_admissions")
