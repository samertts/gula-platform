"""Create National Blood Bank & Transfusion Platform tables.

Revision ID: 20260716_0006
Revises: 20260716_0005
Create Date: 2026-07-16
"""

from typing import Union
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy import inspect

revision: str = "20260716_0006"
down_revision: str | None = "20260716_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def upgrade() -> None:
    if not _table_exists("blood_bank_donors"):
        op.create_table(
            "blood_bank_donors",
            sa.Column("citizen_id", sa.String()),
            sa.Column("national_id", sa.String()),
            sa.Column("full_name", sa.String(), nullable=False),
            sa.Column("phone", sa.String()),
            sa.Column("email", sa.String()),
            sa.Column("date_of_birth", sa.String()),
            sa.Column("gender", sa.String()),
            sa.Column("blood_group", sa.String(), default="unknown"),
            sa.Column("rh_factor", sa.String(), default="unknown"),
            sa.Column("weight_kg", sa.Float()),
            sa.Column("height_cm", sa.Float()),
            sa.Column("hemoglobin_g_dl", sa.Float()),
            sa.Column("status", sa.String(), default="active"),
            sa.Column("total_donations", sa.Integer(), default=0),
            sa.Column("total_volume_ml", sa.Float(), default=0.0),
            sa.Column("last_donation_date", sa.DateTime(timezone=True)),
            sa.Column("next_eligible_date", sa.DateTime(timezone=True)),
            sa.Column("is_regular_donor", sa.Boolean(), default=False),
            sa.Column("consent_signed", sa.Boolean(), default=False),
            sa.Column("consent_date", sa.DateTime(timezone=True)),
            sa.Column("emergency_contact", sa.String()),
            sa.Column("emergency_phone", sa.String()),
            sa.Column("notes", sa.Text()),
            sa.Column("created_by", sa.String()),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1),
        )
        op.create_index("ix_blood_bank_donors_citizen_id", "blood_bank_donors", ["citizen_id"])
        op.create_index("ix_blood_bank_donors_lab_id", "blood_bank_donors", ["lab_id"])
        op.create_index("ix_blood_bank_donors_fhir_id", "blood_bank_donors", ["fhir_id"])

    if not _table_exists("blood_bank_donor_deferrals"):
        op.create_table(
            "blood_bank_donor_deferrals",
            sa.Column(
                "donor_id", sa.String(), sa.ForeignKey("blood_bank_donors.id"), nullable=False
            ),
            sa.Column("deferral_type", sa.String(), default="temporary"),
            sa.Column("reason", sa.String(), default="other"),
            sa.Column("reason_detail", sa.Text()),
            sa.Column("deferral_days", sa.Integer(), default=0),
            sa.Column("deferred_from", sa.DateTime(timezone=True), nullable=False),
            sa.Column("deferred_until", sa.DateTime(timezone=True)),
            sa.Column("deferred_by", sa.String()),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("notes", sa.Text()),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1),
        )
        op.create_index(
            "ix_blood_bank_donor_deferrals_donor_id", "blood_bank_donor_deferrals", ["donor_id"]
        )
        op.create_index(
            "ix_blood_bank_donor_deferrals_fhir_id", "blood_bank_donor_deferrals", ["fhir_id"]
        )
        op.create_index(
            "ix_blood_bank_donor_deferrals_lab_id", "blood_bank_donor_deferrals", ["lab_id"]
        )

    if not _table_exists("blood_bank_donations"):
        op.create_table(
            "blood_bank_donations",
            sa.Column(
                "donor_id", sa.String(), sa.ForeignKey("blood_bank_donors.id"), nullable=False
            ),
            sa.Column("donation_type", sa.String(), default="whole_blood"),
            sa.Column("collection_method", sa.String(), default="manual"),
            sa.Column("status", sa.String(), default="registered"),
            sa.Column("volume_ml", sa.Float(), default=450.0),
            sa.Column("collection_site", sa.String()),
            sa.Column("collection_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("phlebotomist_id", sa.String()),
            sa.Column("pulse_before", sa.Integer()),
            sa.Column("bp_systolic_before", sa.Integer()),
            sa.Column("bp_diastolic_before", sa.Integer()),
            sa.Column("temperature_before", sa.Float()),
            sa.Column("hemoglobin_pre", sa.Float()),
            sa.Column("pulse_after", sa.Integer()),
            sa.Column("bp_systolic_after", sa.Integer()),
            sa.Column("bp_diastolic_after", sa.Integer()),
            sa.Column("adverse_event", sa.Text()),
            sa.Column("bag_identifier", sa.String(), unique=True),
            sa.Column("isbt_128_code", sa.String(), unique=True),
            sa.Column("barcode", sa.String(), unique=True),
            sa.Column("notes", sa.Text()),
            sa.Column("created_by", sa.String()),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1),
        )
        op.create_index("ix_blood_bank_donations_donor_id", "blood_bank_donations", ["donor_id"])
        op.create_index("ix_blood_bank_donations_lab_id", "blood_bank_donations", ["lab_id"])
        op.create_index("ix_blood_bank_donations_fhir_id", "blood_bank_donations", ["fhir_id"])

    if not _table_exists("blood_bank_screening_results"):
        op.create_table(
            "blood_bank_screening_results",
            sa.Column(
                "donation_id", sa.String(), sa.ForeignKey("blood_bank_donations.id"), nullable=False
            ),
            sa.Column("test", sa.String(), nullable=False),
            sa.Column("result", sa.String(), default="pending"),
            sa.Column("result_value", sa.String()),
            sa.Column("analyzer_id", sa.String()),
            sa.Column("operator_id", sa.String()),
            sa.Column("test_date", sa.DateTime(timezone=True)),
            sa.Column("verified_by", sa.String()),
            sa.Column("verified_at", sa.DateTime(timezone=True)),
            sa.Column("kit_lot_number", sa.String()),
            sa.Column("kit_expiry", sa.String()),
            sa.Column("notes", sa.Text()),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1),
        )
        op.create_index(
            "ix_blood_bank_screening_results_lab_id", "blood_bank_screening_results", ["lab_id"]
        )
        op.create_index(
            "ix_blood_bank_screening_results_donation_id",
            "blood_bank_screening_results",
            ["donation_id"],
        )
        op.create_index(
            "ix_blood_bank_screening_results_fhir_id", "blood_bank_screening_results", ["fhir_id"]
        )

    if not _table_exists("blood_bank_components"):
        op.create_table(
            "blood_bank_components",
            sa.Column(
                "donation_id", sa.String(), sa.ForeignKey("blood_bank_donations.id"), nullable=False
            ),
            sa.Column("component", sa.String(), default="packed_rbc"),
            sa.Column("status", sa.String(), default="pending_processing"),
            sa.Column("volume_ml", sa.Float()),
            sa.Column("parent_component_id", sa.String()),
            sa.Column("bag_identifier", sa.String(), unique=True),
            sa.Column("isbt_128_code", sa.String(), unique=True),
            sa.Column("barcode", sa.String(), unique=True),
            sa.Column("storage_condition", sa.String(), default="refrigerated"),
            sa.Column("expiry_date", sa.DateTime(timezone=True)),
            sa.Column("processing_date", sa.DateTime(timezone=True)),
            sa.Column("processed_by", sa.String()),
            sa.Column("leukocyte_reduced", sa.Boolean(), default=False),
            sa.Column("irradiated", sa.Boolean(), default=False),
            sa.Column("washed", sa.Boolean(), default=False),
            sa.Column("pathogen_reduced", sa.Boolean(), default=False),
            sa.Column("notes", sa.Text()),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1),
        )
        op.create_index("ix_blood_bank_components_fhir_id", "blood_bank_components", ["fhir_id"])
        op.create_index(
            "ix_blood_bank_components_donation_id", "blood_bank_components", ["donation_id"]
        )
        op.create_index("ix_blood_bank_components_lab_id", "blood_bank_components", ["lab_id"])

    if not _table_exists("blood_bank_inventory"):
        op.create_table(
            "blood_bank_inventory",
            sa.Column("facility_id", sa.String(), nullable=False),
            sa.Column("blood_group", sa.String(), nullable=False),
            sa.Column("rh_factor", sa.String(), nullable=False),
            sa.Column("component", sa.String(), nullable=False),
            sa.Column("quantity", sa.Integer(), default=0),
            sa.Column("reserved_quantity", sa.Integer(), default=0),
            sa.Column("minimum_stock", sa.Integer(), default=10),
            sa.Column("critical_threshold", sa.Integer(), default=5),
            sa.Column("storage_location", sa.String()),
            sa.Column("storage_condition", sa.String(), default="refrigerated"),
            sa.Column("last_updated", sa.DateTime(timezone=True)),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1),
        )
        op.create_index("ix_blood_bank_inventory_lab_id", "blood_bank_inventory", ["lab_id"])
        op.create_index("ix_blood_bank_inventory_fhir_id", "blood_bank_inventory", ["fhir_id"])
        op.create_index(
            "ix_blood_bank_inventory_facility_id", "blood_bank_inventory", ["facility_id"]
        )

    if not _table_exists("blood_bank_units"):
        op.create_table(
            "blood_bank_units",
            sa.Column("component_id", sa.String()),
            sa.Column("facility_id", sa.String()),
            sa.Column("blood_group", sa.String(), nullable=False),
            sa.Column("rh_factor", sa.String(), nullable=False),
            sa.Column("component", sa.String(), nullable=False),
            sa.Column("bag_identifier", sa.String(), unique=True),
            sa.Column("isbt_128_code", sa.String(), unique=True),
            sa.Column("barcode", sa.String(), unique=True),
            sa.Column("volume_ml", sa.Float()),
            sa.Column("collection_date", sa.DateTime(timezone=True)),
            sa.Column("expiry_date", sa.DateTime(timezone=True)),
            sa.Column("donor_id", sa.String()),
            sa.Column("donor_name", sa.String()),
            sa.Column("status", sa.String(), default="available"),
            sa.Column("storage_location", sa.String()),
            sa.Column("location_facility_id", sa.String()),
            sa.Column("screening_complete", sa.Boolean(), default=False),
            sa.Column("processing_complete", sa.Boolean(), default=False),
            sa.Column("crossmatch_compatible", sa.String()),
            sa.Column("issued_to", sa.String()),
            sa.Column("issued_at", sa.DateTime(timezone=True)),
            sa.Column("transfused_at", sa.DateTime(timezone=True)),
            sa.Column("discarded_at", sa.DateTime(timezone=True)),
            sa.Column("discard_reason", sa.Text()),
            sa.Column("recalled", sa.Boolean(), default=False),
            sa.Column("recall_reason", sa.Text()),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1),
        )
        op.create_index("ix_blood_bank_units_fhir_id", "blood_bank_units", ["fhir_id"])
        op.create_index("ix_blood_bank_units_expiry_date", "blood_bank_units", ["expiry_date"])
        op.create_index("ix_blood_bank_units_lab_id", "blood_bank_units", ["lab_id"])

    if not _table_exists("blood_bank_crossmatches"):
        op.create_table(
            "blood_bank_crossmatches",
            sa.Column("patient_id", sa.String(), nullable=False),
            sa.Column("patient_name", sa.String()),
            sa.Column("patient_blood_group", sa.String()),
            sa.Column("patient_rh_factor", sa.String()),
            sa.Column("unit_id", sa.String()),
            sa.Column("unit_identifier", sa.String()),
            sa.Column("blood_group", sa.String()),
            sa.Column("crossmatch_type", sa.String(), default="full"),
            sa.Column("status", sa.String(), default="pending"),
            sa.Column("abo_compatible", sa.Boolean(), default=False),
            sa.Column("rh_compatible", sa.Boolean(), default=False),
            sa.Column("crossmatch_result", sa.String()),
            sa.Column("performed_by", sa.String()),
            sa.Column("performed_at", sa.DateTime(timezone=True)),
            sa.Column("verified_by", sa.String()),
            sa.Column("verified_at", sa.DateTime(timezone=True)),
            sa.Column("expires_at", sa.DateTime(timezone=True)),
            sa.Column("notes", sa.Text()),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1),
        )
        op.create_index(
            "ix_blood_bank_crossmatches_fhir_id", "blood_bank_crossmatches", ["fhir_id"]
        )
        op.create_index(
            "ix_blood_bank_crossmatches_patient_id", "blood_bank_crossmatches", ["patient_id"]
        )
        op.create_index("ix_blood_bank_crossmatches_lab_id", "blood_bank_crossmatches", ["lab_id"])

    if not _table_exists("blood_bank_transfusions"):
        op.create_table(
            "blood_bank_transfusions",
            sa.Column("patient_id", sa.String(), nullable=False),
            sa.Column("patient_name", sa.String()),
            sa.Column("patient_blood_group", sa.String()),
            sa.Column("patient_rh_factor", sa.String()),
            sa.Column("medical_record_number", sa.String()),
            sa.Column("unit_id", sa.String()),
            sa.Column("unit_identifier", sa.String()),
            sa.Column("blood_group", sa.String()),
            sa.Column("component", sa.String()),
            sa.Column("volume_ml", sa.Float()),
            sa.Column("crossmatch_id", sa.String()),
            sa.Column("ordered_by", sa.String()),
            sa.Column("order_datetime", sa.DateTime(timezone=True)),
            sa.Column("administered_by", sa.String()),
            sa.Column("start_time", sa.DateTime(timezone=True)),
            sa.Column("end_time", sa.DateTime(timezone=True)),
            sa.Column("pre_vitals", sa.JSON()),
            sa.Column("post_vitals", sa.JSON()),
            sa.Column("status", sa.String(), default="ordered"),
            sa.Column("verification_method", sa.String(), default="manual"),
            sa.Column("verified_by", sa.String()),
            sa.Column("verified_at", sa.DateTime(timezone=True)),
            sa.Column("patient_verified", sa.Boolean(), default=False),
            sa.Column("unit_verified", sa.Boolean(), default=False),
            sa.Column("consent_verified", sa.Boolean(), default=False),
            sa.Column("rate_ml_per_hour", sa.Float()),
            sa.Column("infusion_pump_id", sa.String()),
            sa.Column("bedside_verification_complete", sa.Boolean(), default=False),
            sa.Column("reaction_occurred", sa.Boolean(), default=False),
            sa.Column("reaction_type", sa.String()),
            sa.Column("reaction_severity", sa.String()),
            sa.Column("reaction_time", sa.DateTime(timezone=True)),
            sa.Column("reaction_description", sa.Text()),
            sa.Column("reaction_intervention", sa.Text()),
            sa.Column("outcome", sa.Text()),
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
            sa.Column("version", sa.Integer(), nullable=False, default=1),
        )
        op.create_index(
            "ix_blood_bank_transfusions_fhir_id", "blood_bank_transfusions", ["fhir_id"]
        )
        op.create_index(
            "ix_blood_bank_transfusions_patient_id", "blood_bank_transfusions", ["patient_id"]
        )
        op.create_index("ix_blood_bank_transfusions_lab_id", "blood_bank_transfusions", ["lab_id"])

    if not _table_exists("blood_bank_requests"):
        op.create_table(
            "blood_bank_requests",
            sa.Column("patient_id", sa.String(), nullable=False),
            sa.Column("patient_name", sa.String()),
            sa.Column("medical_record_number", sa.String()),
            sa.Column("facility_id", sa.String()),
            sa.Column("department", sa.String()),
            sa.Column("requested_by", sa.String()),
            sa.Column("physician_name", sa.String()),
            sa.Column("blood_group", sa.String()),
            sa.Column("rh_factor", sa.String()),
            sa.Column("component", sa.String()),
            sa.Column("units_requested", sa.Integer(), default=1),
            sa.Column("urgency", sa.String(), default="routine"),
            sa.Column("indication", sa.Text()),
            sa.Column("crossmatch_required", sa.Boolean(), default=True),
            sa.Column("status", sa.String(), default="pending"),
            sa.Column("approved_by", sa.String()),
            sa.Column("approved_at", sa.DateTime(timezone=True)),
            sa.Column("fulfilled_units", sa.Integer(), default=0),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1),
        )
        op.create_index("ix_blood_bank_requests_fhir_id", "blood_bank_requests", ["fhir_id"])
        op.create_index("ix_blood_bank_requests_lab_id", "blood_bank_requests", ["lab_id"])

    if not _table_exists("blood_bank_inventory_movements"):
        op.create_table(
            "blood_bank_inventory_movements",
            sa.Column("unit_id", sa.String()),
            sa.Column("facility_id", sa.String()),
            sa.Column("from_location", sa.String()),
            sa.Column("to_location", sa.String()),
            sa.Column("movement_type", sa.String(), nullable=False),
            sa.Column("performed_by", sa.String()),
            sa.Column("performed_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("notes", sa.Text()),
            sa.Column("lab_id", sa.Integer(), nullable=False),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("fhir_id", sa.String()),
            sa.Column("fhir_resource_type", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer(), nullable=False, default=1),
        )
        op.create_index(
            "ix_blood_bank_inventory_movements_fhir_id",
            "blood_bank_inventory_movements",
            ["fhir_id"],
        )
        op.create_index(
            "ix_blood_bank_inventory_movements_lab_id", "blood_bank_inventory_movements", ["lab_id"]
        )


def downgrade() -> None:
    if _table_exists("blood_bank_inventory_movements"):
        op.drop_table("blood_bank_inventory_movements")
    if _table_exists("blood_bank_requests"):
        op.drop_table("blood_bank_requests")
    if _table_exists("blood_bank_transfusions"):
        op.drop_table("blood_bank_transfusions")
    if _table_exists("blood_bank_crossmatches"):
        op.drop_table("blood_bank_crossmatches")
    if _table_exists("blood_bank_units"):
        op.drop_table("blood_bank_units")
    if _table_exists("blood_bank_inventory"):
        op.drop_table("blood_bank_inventory")
    if _table_exists("blood_bank_components"):
        op.drop_table("blood_bank_components")
    if _table_exists("blood_bank_screening_results"):
        op.drop_table("blood_bank_screening_results")
    if _table_exists("blood_bank_donations"):
        op.drop_table("blood_bank_donations")
    if _table_exists("blood_bank_donor_deferrals"):
        op.drop_table("blood_bank_donor_deferrals")
    if _table_exists("blood_bank_donors"):
        op.drop_table("blood_bank_donors")
