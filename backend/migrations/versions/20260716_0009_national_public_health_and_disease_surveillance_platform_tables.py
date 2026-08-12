"""Create National Public Health & Disease Surveillance Platform tables.

Revision ID: 20260716_0009
Revises: 20260716_0008
Create Date: 2026-07-16
"""

from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy import inspect

revision: str = "20260716_0009"
down_revision: Union[str, None] = "20260716_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def upgrade() -> None:
    if not _table_exists("ph_disease_cases"):
        op.create_table(
            "ph_disease_cases",
            sa.Column("disease_code", sa.String(), nullable=False),
            sa.Column("disease_name", sa.String()),
            sa.Column("category", sa.String(), default="reportable"),
            sa.Column("region", sa.String(), nullable=False),
            sa.Column("district", sa.String()),
            sa.Column("location_lat", sa.Float()),
            sa.Column("location_lng", sa.Float()),
            sa.Column("patient_age", sa.Integer()),
            sa.Column("patient_gender", sa.String()),
            sa.Column("patient_national_id", sa.String()),
            sa.Column("is_confirmed", sa.Boolean(), default=False),
            sa.Column("confirmation_method", sa.String()),
            sa.Column("confirmation_date", sa.DateTime(timezone=True)),
            sa.Column("source", sa.String(), default="laboratory"),
            sa.Column("reported_by", sa.String()),
            sa.Column("reported_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("outcome", sa.String()),
            sa.Column("severity", sa.String(), default="moderate"),
            sa.Column("symptoms", sa.JSON()),
            sa.Column("risk_factors", sa.JSON()),
            sa.Column("exposure_history", sa.Text()),
            sa.Column("travel_history", sa.Text()),
            sa.Column("contact_tracing_completed", sa.Boolean(), default=False),
            sa.Column("contact_count", sa.Integer(), default=0),
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
        op.create_index("ix_ph_disease_cases_lab_id", "ph_disease_cases", ["lab_id"])
        op.create_index("ix_ph_disease_cases_region", "ph_disease_cases", ["region"])
        op.create_index("ix_ph_disease_cases_disease_code", "ph_disease_cases", ["disease_code"])
        op.create_index("ix_ph_disease_cases_fhir_id", "ph_disease_cases", ["fhir_id"])

    if not _table_exists("ph_outbreak_alerts"):
        op.create_table(
            "ph_outbreak_alerts",
            sa.Column("disease", sa.String(), nullable=False),
            sa.Column("disease_code", sa.String()),
            sa.Column("region", sa.String(), nullable=False),
            sa.Column("district", sa.String()),
            sa.Column("confirmed_cases", sa.Integer(), default=0),
            sa.Column("suspected_cases", sa.Integer(), default=0),
            sa.Column("recovered_cases", sa.Integer(), default=0),
            sa.Column("fatalities", sa.Integer(), default=0),
            sa.Column("attack_rate", sa.Float(), default=0.0),
            sa.Column("transmission_type", sa.String(), default="unknown"),
            sa.Column("alert_level", sa.String(), default="information"),
            sa.Column("status", sa.String(), default="monitoring"),
            sa.Column("first_detected", sa.DateTime(timezone=True), nullable=False),
            sa.Column("last_updated", sa.DateTime(timezone=True)),
            sa.Column("investigation_notes", sa.Text()),
            sa.Column("recommendations", sa.Text()),
            sa.Column("control_measures", sa.JSON()),
            sa.Column("declared_by", sa.String()),
            sa.Column("declared_over_at", sa.DateTime(timezone=True)),
            sa.Column("lab_confirmed", sa.Boolean(), default=False),
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
        op.create_index("ix_ph_outbreak_alerts_region", "ph_outbreak_alerts", ["region"])
        op.create_index("ix_ph_outbreak_alerts_lab_id", "ph_outbreak_alerts", ["lab_id"])
        op.create_index("ix_ph_outbreak_alerts_fhir_id", "ph_outbreak_alerts", ["fhir_id"])

    if not _table_exists("ph_immunization_records"):
        op.create_table(
            "ph_immunization_records",
            sa.Column("patient_id", sa.String(), nullable=False),
            sa.Column("patient_name", sa.String()),
            sa.Column("vaccine", sa.String(), nullable=False),
            sa.Column("vaccine_code", sa.String()),
            sa.Column("dose_number", sa.Integer(), default=1),
            sa.Column("total_doses", sa.Integer(), default=1),
            sa.Column("administration_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("administered_by", sa.String()),
            sa.Column("facility_id", sa.String()),
            sa.Column("lot_number", sa.String()),
            sa.Column("expiry_date", sa.DateTime(timezone=True)),
            sa.Column("route", sa.String(), default="intramuscular"),
            sa.Column("site", sa.String(), default="deltoid"),
            sa.Column("batch_number", sa.String()),
            sa.Column("manufacturer", sa.String()),
            sa.Column("is_boosted", sa.Boolean(), default=False),
            sa.Column("adverse_event", sa.Text()),
            sa.Column("consent_obtained", sa.Boolean(), default=True),
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
        op.create_index("ix_ph_immunization_records_lab_id", "ph_immunization_records", ["lab_id"])
        op.create_index("ix_ph_immunization_records_patient_id", "ph_immunization_records", ["patient_id"])
        op.create_index("ix_ph_immunization_records_fhir_id", "ph_immunization_records", ["fhir_id"])

    if not _table_exists("ph_reports"):
        op.create_table(
            "ph_reports",
            sa.Column("report_type", sa.String(), default="weekly"),
            sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
            sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
            sa.Column("region", sa.String()),
            sa.Column("total_cases", sa.Integer(), default=0),
            sa.Column("total_deaths", sa.Integer(), default=0),
            sa.Column("diseases_reported", sa.JSON()),
            sa.Column("outbreaks_active", sa.Integer(), default=0),
            sa.Column("alerts_raised", sa.Integer(), default=0),
            sa.Column("vaccination_coverage_pct", sa.Float(), default=0.0),
            sa.Column("key_findings", sa.Text()),
            sa.Column("recommendations", sa.Text()),
            sa.Column("published_by", sa.String()),
            sa.Column("published_at", sa.DateTime(timezone=True)),
            sa.Column("status", sa.String(), default="draft"),
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
        op.create_index("ix_ph_reports_lab_id", "ph_reports", ["lab_id"])
        op.create_index("ix_ph_reports_fhir_id", "ph_reports", ["fhir_id"])

    if not _table_exists("ph_surveillance_signals"):
        op.create_table(
            "ph_surveillance_signals",
            sa.Column("disease", sa.String(), nullable=False),
            sa.Column("disease_code", sa.String()),
            sa.Column("region", sa.String(), nullable=False),
            sa.Column("case_count", sa.Integer(), default=0),
            sa.Column("expected_count", sa.Integer(), default=0),
            sa.Column("baseline_period_days", sa.Integer(), default=30),
            sa.Column("z_score", sa.Float(), default=0.0),
            sa.Column("alert_level", sa.String(), default="information"),
            sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("recommendation", sa.Text()),
            sa.Column("acknowledged_by", sa.String()),
            sa.Column("acknowledged_at", sa.DateTime(timezone=True)),
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
        op.create_index("ix_ph_surveillance_signals_region", "ph_surveillance_signals", ["region"])
        op.create_index("ix_ph_surveillance_signals_fhir_id", "ph_surveillance_signals", ["fhir_id"])
        op.create_index("ix_ph_surveillance_signals_lab_id", "ph_surveillance_signals", ["lab_id"])

    if not _table_exists("ph_environmental_health"):
        op.create_table(
            "ph_environmental_health",
            sa.Column("sample_type", sa.String(), nullable=False),
            sa.Column("location_lat", sa.Float()),
            sa.Column("location_lng", sa.Float()),
            sa.Column("region", sa.String()),
            sa.Column("district", sa.String()),
            sa.Column("collection_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("tested_for", sa.String()),
            sa.Column("result", sa.String()),
            sa.Column("value", sa.Float()),
            sa.Column("unit", sa.String()),
            sa.Column("laboratory", sa.String()),
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
        op.create_index("ix_ph_environmental_health_lab_id", "ph_environmental_health", ["lab_id"])
        op.create_index("ix_ph_environmental_health_fhir_id", "ph_environmental_health", ["fhir_id"])
        op.create_index("ix_ph_environmental_health_region", "ph_environmental_health", ["region"])



def downgrade() -> None:
    if _table_exists("ph_environmental_health"):
        op.drop_table("ph_environmental_health")
    if _table_exists("ph_surveillance_signals"):
        op.drop_table("ph_surveillance_signals")
    if _table_exists("ph_reports"):
        op.drop_table("ph_reports")
    if _table_exists("ph_immunization_records"):
        op.drop_table("ph_immunization_records")
    if _table_exists("ph_outbreak_alerts"):
        op.drop_table("ph_outbreak_alerts")
    if _table_exists("ph_disease_cases"):
        op.drop_table("ph_disease_cases")
