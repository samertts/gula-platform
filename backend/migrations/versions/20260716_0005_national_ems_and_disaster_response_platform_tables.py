"""Create National EMS & Disaster Response Platform tables.

Revision ID: 20260716_0005
Revises: 20260716_0004
Create Date: 2026-07-16
"""

from typing import Sequence, Union
import sqlalchemy as sa
from alembic import context, op
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy import inspect

revision: str = "20260716_0005"
down_revision: Union[str, None] = "20260716_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table: str) -> bool:
    if context.is_offline_mode():
        return True
    return inspect(op.get_bind()).has_table(table)


def upgrade() -> None:
    if not _table_exists("ems_incidents"):
        op.create_table(
            "ems_incidents",
            sa.Column("caller_name", sa.String()),
            sa.Column("caller_phone", sa.String()),
            sa.Column("caller_relationship", sa.String()),
            sa.Column("location_lat", sa.Float()),
            sa.Column("location_lng", sa.Float()),
            sa.Column("location_address", sa.Text()),
            sa.Column("location_description", sa.Text()),
            sa.Column("category", sa.String(), default="medical"),
            sa.Column("priority", sa.String(), default="bravo"),
            sa.Column("status", sa.String(), default="pending"),
            sa.Column("description", sa.Text()),
            sa.Column("symptoms", sa.Text()),
            sa.Column("patient_count", sa.Integer(), default=1),
            sa.Column("patient_age", sa.Integer()),
            sa.Column("patient_gender", sa.String()),
            sa.Column("patient_name", sa.String()),
            sa.Column("patient_phone", sa.String()),
            sa.Column("patient_condition", sa.Text()),
            sa.Column("is_conscious", sa.Boolean(), default=True),
            sa.Column("is_breathing", sa.Boolean(), default=True),
            sa.Column("has_pulse", sa.Boolean(), default=True),
            sa.Column("has_allergies", sa.Boolean(), default=False),
            sa.Column("has_bleeding", sa.Boolean(), default=False),
            sa.Column("has_chest_pain", sa.Boolean(), default=False),
            sa.Column("has_difficulty_breathing", sa.Boolean(), default=False),
            sa.Column("is_pregnant", sa.Boolean(), default=False),
            sa.Column("is_diabetic", sa.Boolean(), default=False),
            sa.Column("has_seizure", sa.Boolean(), default=False),
            sa.Column("dispatcher_notes", sa.Text()),
            sa.Column("dispatch_time", sa.DateTime(timezone=True)),
            sa.Column("scene_arrival_time", sa.DateTime(timezone=True)),
            sa.Column("scene_departure_time", sa.DateTime(timezone=True)),
            sa.Column("destination_arrival_time", sa.DateTime(timezone=True)),
            sa.Column("completion_time", sa.DateTime(timezone=True)),
            sa.Column("destination_facility_id", sa.String()),
            sa.Column("destination_facility_name", sa.String()),
            sa.Column("destination_type", sa.String(), default="emergency_department"),
            sa.Column("incident_command_id", sa.String()),
            sa.Column("disaster_event_id", sa.String()),
            sa.Column("mass_casualty_id", sa.String()),
            sa.Column("created_by", sa.String()),
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
        op.create_index("ix_ems_incidents_fhir_id", "ems_incidents", ["fhir_id"])
        op.create_index("ix_ems_incidents_lab_id", "ems_incidents", ["lab_id"])

    if not _table_exists("ems_ambulances"):
        op.create_table(
            "ems_ambulances",
            sa.Column("vehicle_id", sa.String()),
            sa.Column("registration_number", sa.String(), unique=True),
            sa.Column("call_sign", sa.String(), unique=True),
            sa.Column("type", sa.String(), default="bls"),
            sa.Column("status", sa.String(), default="available"),
            sa.Column("status_reason", sa.Text()),
            sa.Column("current_location_lat", sa.Float()),
            sa.Column("current_location_lng", sa.Float()),
            sa.Column("current_location_updated", sa.DateTime(timezone=True)),
            sa.Column("station_id", sa.String()),
            sa.Column("station_name", sa.String()),
            sa.Column("facility_id", sa.String()),
            sa.Column("is_gps_enabled", sa.Boolean(), default=True),
            sa.Column("fuel_level", sa.Float(), default=100.0),
            sa.Column("mileage_km", sa.Float(), default=0.0),
            sa.Column("last_maintenance_date", sa.DateTime(timezone=True)),
            sa.Column("next_maintenance_due", sa.DateTime(timezone=True)),
            sa.Column("vehicle_status", sa.String(), default="active"),
            sa.Column("equipment_inventory", sa.JSON()),
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
        op.create_index("ix_ems_ambulances_lab_id", "ems_ambulances", ["lab_id"])
        op.create_index("ix_ems_ambulances_vehicle_id", "ems_ambulances", ["vehicle_id"])
        op.create_index("ix_ems_ambulances_fhir_id", "ems_ambulances", ["fhir_id"])

    if not _table_exists("ems_ambulance_crew"):
        op.create_table(
            "ems_ambulance_crew",
            sa.Column("user_id", sa.String()),
            sa.Column("full_name", sa.String(), nullable=False),
            sa.Column("role", sa.String(), default="emt"),
            sa.Column("is_available", sa.Boolean(), default=True),
            sa.Column("station_id", sa.String()),
            sa.Column("facility_id", sa.String()),
            sa.Column("certifications", sa.JSON()),
            sa.Column("phone", sa.String()),
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
        op.create_index("ix_ems_ambulance_crew_lab_id", "ems_ambulance_crew", ["lab_id"])
        op.create_index("ix_ems_ambulance_crew_fhir_id", "ems_ambulance_crew", ["fhir_id"])

    if not _table_exists("ems_crew_shifts"):
        op.create_table(
            "ems_crew_shifts",
            sa.Column("crew_id", sa.String(), sa.ForeignKey("ems_ambulance_crew.id"), nullable=False),
            sa.Column("start_time", sa.DateTime(timezone=True)),
            sa.Column("end_time", sa.DateTime(timezone=True)),
            sa.Column("status", sa.String(), default="scheduled"),
            sa.Column("station_id", sa.String()),
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
        op.create_index("ix_ems_crew_shifts_crew_id", "ems_crew_shifts", ["crew_id"])
        op.create_index("ix_ems_crew_shifts_lab_id", "ems_crew_shifts", ["lab_id"])
        op.create_index("ix_ems_crew_shifts_fhir_id", "ems_crew_shifts", ["fhir_id"])

    if not _table_exists("ems_dispatch_assignments"):
        op.create_table(
            "ems_dispatch_assignments",
            sa.Column("incident_id", sa.String(), sa.ForeignKey("ems_incidents.id"), nullable=False),
            sa.Column("ambulance_id", sa.String(), sa.ForeignKey("ems_ambulances.id")),
            sa.Column("status", sa.String(), default="pending"),
            sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("acknowledged_at", sa.DateTime(timezone=True)),
            sa.Column("en_route_at", sa.DateTime(timezone=True)),
            sa.Column("on_scene_at", sa.DateTime(timezone=True)),
            sa.Column("transporting_at", sa.DateTime(timezone=True)),
            sa.Column("completed_at", sa.DateTime(timezone=True)),
            sa.Column("cancelled_at", sa.DateTime(timezone=True)),
            sa.Column("cancellation_reason", sa.Text()),
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
            sa.Column("version", sa.Integer(), nullable=False, default=1)
        )
        op.create_index("ix_ems_dispatch_assignments_fhir_id", "ems_dispatch_assignments", ["fhir_id"])
        op.create_index("ix_ems_dispatch_assignments_incident_id", "ems_dispatch_assignments", ["incident_id"])
        op.create_index("ix_ems_dispatch_assignments_lab_id", "ems_dispatch_assignments", ["lab_id"])

    if not _table_exists("ems_triage_assessments"):
        op.create_table(
            "ems_triage_assessments",
            sa.Column("incident_id", sa.String(), sa.ForeignKey("ems_incidents.id")),
            sa.Column("patient_id", sa.String()),
            sa.Column("patient_name", sa.String()),
            sa.Column("patient_age", sa.Integer()),
            sa.Column("patient_gender", sa.String()),
            sa.Column("category", sa.String(), default="minor"),
            sa.Column("system", sa.String(), default="start"),
            sa.Column("respiratory_rate", sa.Integer()),
            sa.Column("capillary_refill", sa.Float()),
            sa.Column("heart_rate", sa.Integer()),
            sa.Column("systolic_bp", sa.Integer()),
            sa.Column("mental_status", sa.String()),
            sa.Column("ambulatory", sa.Boolean(), default=True),
            sa.Column("external_bleeding", sa.Boolean(), default=False),
            sa.Column("burns_percentage", sa.Float()),
            sa.Column("trauma_score", sa.Integer()),
            sa.Column("glasgow_coma_scale", sa.Integer()),
            sa.Column("priority_score", sa.Integer(), default=0),
            sa.Column("assessed_by", sa.String()),
            sa.Column("assessed_at", sa.DateTime(timezone=True)),
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
        op.create_index("ix_ems_triage_assessments_fhir_id", "ems_triage_assessments", ["fhir_id"])
        op.create_index("ix_ems_triage_assessments_lab_id", "ems_triage_assessments", ["lab_id"])
        op.create_index("ix_ems_triage_assessments_incident_id", "ems_triage_assessments", ["incident_id"])

    if not _table_exists("ems_epcr"):
        op.create_table(
            "ems_epcr",
            sa.Column("incident_id", sa.String(), sa.ForeignKey("ems_incidents.id"), nullable=False),
            sa.Column("patient_id", sa.String()),
            sa.Column("patient_name", sa.String()),
            sa.Column("patient_dob", sa.String()),
            sa.Column("patient_gender", sa.String()),
            sa.Column("patient_address", sa.Text()),
            sa.Column("patient_phone", sa.String()),
            sa.Column("patient_blood_group", sa.String()),
            sa.Column("patient_allergies", sa.JSON()),
            sa.Column("patient_medications", sa.JSON()),
            sa.Column("patient_medical_history", sa.JSON()),
            sa.Column("dispatch_call_time", sa.DateTime(timezone=True)),
            sa.Column("scene_arrival_time", sa.DateTime(timezone=True)),
            sa.Column("patient_assessment_time", sa.DateTime(timezone=True)),
            sa.Column("scene_departure_time", sa.DateTime(timezone=True)),
            sa.Column("destination_arrival_time", sa.DateTime(timezone=True)),
            sa.Column("transfer_of_care_time", sa.DateTime(timezone=True)),
            sa.Column("incident_description", sa.Text()),
            sa.Column("chief_complaint", sa.Text()),
            sa.Column("history_of_present_illness", sa.Text()),
            sa.Column("mechanism_of_injury", sa.Text()),
            sa.Column("injury_type", sa.String()),
            sa.Column("injury_location", sa.String()),
            sa.Column("initial_vital_signs", sa.JSON()),
            sa.Column("serial_vitals", sa.JSON()),
            sa.Column("physical_exam_findings", sa.Text()),
            sa.Column("neurological_assessment", sa.Text()),
            sa.Column("pain_assessment", sa.Text()),
            sa.Column("pain_scale", sa.Integer()),
            sa.Column("interventions", sa.JSON()),
            sa.Column("medications_administered", sa.JSON()),
            sa.Column("procedures_performed", sa.JSON()),
            sa.Column("ecg_interpretation", sa.Text()),
            sa.Column("cardiac_rhythm", sa.String()),
            sa.Column("oxygen_saturation", sa.Float()),
            sa.Column("end_tidal_co2", sa.Float()),
            sa.Column("blood_glucose", sa.Float()),
            sa.Column("etco2", sa.Float()),
            sa.Column("stroke_scale", sa.String()),
            sa.Column("trauma_score", sa.Integer()),
            sa.Column("glasgow_coma_scale", sa.Integer()),
            sa.Column("revised_trauma_score", sa.Integer()),
            sa.Column("prehospital_index", sa.Integer()),
            sa.Column("destination_facility", sa.String()),
            sa.Column("destination_reason", sa.Text()),
            sa.Column("transport_mode", sa.String(), default="ground"),
            sa.Column("crew_members", sa.JSON()),
            sa.Column("submitting_crew_member", sa.String()),
            sa.Column("signatures", sa.JSON()),
            sa.Column("narrative", sa.Text()),
            sa.Column("notes", sa.Text()),
            sa.Column("status", sa.String(), default="draft"),
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
        op.create_index("ix_ems_epcr_fhir_id", "ems_epcr", ["fhir_id"])
        op.create_index("ix_ems_epcr_incident_id", "ems_epcr", ["incident_id"])
        op.create_index("ix_ems_epcr_lab_id", "ems_epcr", ["lab_id"])

    if not _table_exists("ems_disaster_events"):
        op.create_table(
            "ems_disaster_events",
            sa.Column("event_name", sa.String(), nullable=False),
            sa.Column("disaster_type", sa.String(), default="other"),
            sa.Column("phase", sa.String(), default="response"),
            sa.Column("severity_level", sa.Integer(), default=3),
            sa.Column("location_lat", sa.Float()),
            sa.Column("location_lng", sa.Float()),
            sa.Column("location_address", sa.Text()),
            sa.Column("region", sa.String()),
            sa.Column("governorate", sa.String()),
            sa.Column("description", sa.Text()),
            sa.Column("casualties_count", sa.Integer(), default=0),
            sa.Column("fatalities_count", sa.Integer(), default=0),
            sa.Column("missing_count", sa.Integer(), default=0),
            sa.Column("displaced_count", sa.Integer(), default=0),
            sa.Column("affected_population", sa.Integer(), default=0),
            sa.Column("incident_command_id", sa.String()),
            sa.Column("declared_state_of_emergency", sa.Boolean(), default=False),
            sa.Column("declared_at", sa.DateTime(timezone=True)),
            sa.Column("closed_at", sa.DateTime(timezone=True)),
            sa.Column("created_by", sa.String()),
            sa.Column("lab_id", sa.Integer(), nullable=False),
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
        op.create_index("ix_ems_disaster_events_lab_id", "ems_disaster_events", ["lab_id"])
        op.create_index("ix_ems_disaster_events_fhir_id", "ems_disaster_events", ["fhir_id"])

    if not _table_exists("ems_incident_commands"):
        op.create_table(
            "ems_incident_commands",
            sa.Column("disaster_event_id", sa.String(), sa.ForeignKey("ems_disaster_events.id")),
            sa.Column("incident_name", sa.String()),
            sa.Column("incident_number", sa.String()),
            sa.Column("location", sa.Text()),
            sa.Column("command_post_location", sa.Text()),
            sa.Column("operational_period", sa.String()),
            sa.Column("mission_statement", sa.Text()),
            sa.Column("objectives", sa.JSON()),
            sa.Column("command_staff", sa.JSON()),
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
        op.create_index("ix_ems_incident_commands_fhir_id", "ems_incident_commands", ["fhir_id"])
        op.create_index("ix_ems_incident_commands_lab_id", "ems_incident_commands", ["lab_id"])

    if not _table_exists("ems_mass_casualty_incidents"):
        op.create_table(
            "ems_mass_casualty_incidents",
            sa.Column("disaster_event_id", sa.String(), sa.ForeignKey("ems_disaster_events.id")),
            sa.Column("incident_location", sa.Text()),
            sa.Column("incident_type", sa.String()),
            sa.Column("total_patients", sa.Integer(), default=0),
            sa.Column("immediate_count", sa.Integer(), default=0),
            sa.Column("delayed_count", sa.Integer(), default=0),
            sa.Column("minor_count", sa.Integer(), default=0),
            sa.Column("expectant_count", sa.Integer(), default=0),
            sa.Column("deceased_count", sa.Integer(), default=0),
            sa.Column("transported_count", sa.Integer(), default=0),
            sa.Column("hospitals_notified", sa.JSON()),
            sa.Column("resources_deployed", sa.JSON()),
            sa.Column("triage_officer", sa.String()),
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
        op.create_index("ix_ems_mass_casualty_incidents_lab_id", "ems_mass_casualty_incidents", ["lab_id"])
        op.create_index("ix_ems_mass_casualty_incidents_fhir_id", "ems_mass_casualty_incidents", ["fhir_id"])

    if not _table_exists("ems_shelters"):
        op.create_table(
            "ems_shelters",
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("disaster_event_id", sa.String(), sa.ForeignKey("ems_disaster_events.id")),
            sa.Column("location_lat", sa.Float()),
            sa.Column("location_lng", sa.Float()),
            sa.Column("address", sa.Text()),
            sa.Column("capacity", sa.Integer(), default=0),
            sa.Column("current_occupants", sa.Integer(), default=0),
            sa.Column("shelter_type", sa.String()),
            sa.Column("contact_name", sa.String()),
            sa.Column("contact_phone", sa.String()),
            sa.Column("supplies_level", sa.String()),
            sa.Column("status", sa.String(), default="active"),
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
        op.create_index("ix_ems_shelters_fhir_id", "ems_shelters", ["fhir_id"])
        op.create_index("ix_ems_shelters_lab_id", "ems_shelters", ["lab_id"])

    if not _table_exists("ems_hospital_status"):
        op.create_table(
            "ems_hospital_status",
            sa.Column("facility_id", sa.String(), nullable=False),
            sa.Column("facility_name", sa.String()),
            sa.Column("capabilities", sa.JSON()),
            sa.Column("total_beds", sa.Integer(), default=0),
            sa.Column("available_beds", sa.Integer(), default=0),
            sa.Column("icu_beds", sa.Integer(), default=0),
            sa.Column("available_icu_beds", sa.Integer(), default=0),
            sa.Column("ventilators_total", sa.Integer(), default=0),
            sa.Column("ventilators_available", sa.Integer(), default=0),
            sa.Column("emergency_room_status", sa.String(), default="normal"),
            sa.Column("trauma_bays_available", sa.Integer(), default=0),
            sa.Column("operating_rooms_available", sa.Integer(), default=0),
            sa.Column("diversion_status", sa.Boolean(), default=False),
            sa.Column("diversion_reason", sa.Text()),
            sa.Column("last_updated", sa.DateTime(timezone=True)),
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
        op.create_index("ix_ems_hospital_status_fhir_id", "ems_hospital_status", ["fhir_id"])
        op.create_index("ix_ems_hospital_status_facility_id", "ems_hospital_status", ["facility_id"])
        op.create_index("ix_ems_hospital_status_lab_id", "ems_hospital_status", ["lab_id"])



def downgrade() -> None:
    if _table_exists("ems_hospital_status"):
        op.drop_table("ems_hospital_status")
    if _table_exists("ems_shelters"):
        op.drop_table("ems_shelters")
    if _table_exists("ems_mass_casualty_incidents"):
        op.drop_table("ems_mass_casualty_incidents")
    if _table_exists("ems_incident_commands"):
        op.drop_table("ems_incident_commands")
    if _table_exists("ems_disaster_events"):
        op.drop_table("ems_disaster_events")
    if _table_exists("ems_epcr"):
        op.drop_table("ems_epcr")
    if _table_exists("ems_triage_assessments"):
        op.drop_table("ems_triage_assessments")
    if _table_exists("ems_dispatch_assignments"):
        op.drop_table("ems_dispatch_assignments")
    if _table_exists("ems_crew_shifts"):
        op.drop_table("ems_crew_shifts")
    if _table_exists("ems_ambulance_crew"):
        op.drop_table("ems_ambulance_crew")
    if _table_exists("ems_ambulances"):
        op.drop_table("ems_ambulances")
    if _table_exists("ems_incidents"):
        op.drop_table("ems_incidents")
