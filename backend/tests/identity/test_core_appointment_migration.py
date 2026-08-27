import os

import pytest
from sqlalchemy import create_engine, inspect, text

pytestmark = pytest.mark.integration


def _database_url() -> str:
    url = os.getenv("MIGRATION_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not url or url.startswith("sqlite"):
        pytest.skip("A PostgreSQL migration database is required for this integration test")
    return url


def test_core_appointment_schema_has_integrity_guards() -> None:
    engine = create_engine(_database_url())
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        expected_tables = {
            "core_appointment_slots",
            "core_appointments",
            "core_appointment_idempotency",
            "core_encounters",
            "core_encounter_queue",
            "core_clinical_notes",
            "core_clinical_command_receipts",
            "core_lab_orders",
            "core_lab_order_items",
            "core_specimens",
            "core_specimen_events",
            "core_lab_results",
            "core_critical_result_events",
            "core_clinical_notifications",
            "core_access_grants",
            "core_access_history",
            "core_medication_catalog",
            "core_prescriptions",
            "core_prescription_items",
            "core_medication_batches",
            "core_medication_stock_ledger",
            "core_medication_dispenses",
            "core_imaging_orders",
            "core_imaging_studies",
            "core_imaging_reports",
            "core_imaging_instances",
            "core_imaging_critical_events",
        }
        assert expected_tables.issubset(tables)

        encounter_columns = {column["name"] for column in inspector.get_columns("core_encounters")}
        assert {"appointment_id", "patient_person_id", "provider_account_id", "organization_id", "facility_id", "workspace_id", "status", "version"}.issubset(encounter_columns)
        queue_columns = {column["name"] for column in inspector.get_columns("core_encounter_queue")}
        assert {"encounter_id", "organization_id", "facility_id", "workspace_id", "status", "position", "version"}.issubset(queue_columns)
        note_columns = {column["name"] for column in inspector.get_columns("core_clinical_notes")}
        assert {"note_id", "encounter_id", "patient_person_id", "author_account_id", "status", "version", "amendment_reason", "supersedes_id"}.issubset(note_columns)

        slot_columns = {column["name"] for column in inspector.get_columns("core_appointment_slots")}
        assert {
            "organization_id", "facility_id", "workspace_id", "provider_account_id",
            "service_code", "starts_at", "ends_at", "status", "version", "is_active",
        }.issubset(slot_columns)
        idempotency_columns = {column["name"] for column in inspector.get_columns("core_appointment_idempotency")}
        assert {
            "actor_account_id", "operation", "idempotency_key", "request_fingerprint",
            "resource_id", "status", "response_body",
        }.issubset(idempotency_columns)
        appointment_columns = {column["name"] for column in inspector.get_columns("core_appointments")}
        assert {
            "patient_person_id", "requester_account_id", "provider_account_id",
            "organization_id", "facility_id", "workspace_id", "slot_id",
            "state", "version", "purpose",
        }.issubset(appointment_columns)

        encounter_unique = {constraint["name"] for constraint in inspector.get_unique_constraints("core_encounters")}
        queue_unique = {constraint["name"] for constraint in inspector.get_unique_constraints("core_encounter_queue")}
        note_unique = {constraint["name"] for constraint in inspector.get_unique_constraints("core_clinical_notes")}
        assert "uq_core_encounter_appointment" in encounter_unique
        assert "uq_core_encounter_queue_encounter" in queue_unique
        assert "uq_core_clinical_note_version" in note_unique

        slot_unique = {constraint["name"] for constraint in inspector.get_unique_constraints("core_appointment_slots")}
        appointment_unique = {constraint["name"] for constraint in inspector.get_unique_constraints("core_appointments")}
        idempotency_unique = {constraint["name"] for constraint in inspector.get_unique_constraints("core_appointment_idempotency")}
        assert "uq_core_appointment_slot_provider_window" in slot_unique
        assert "uq_core_appointment_slot_id" in appointment_unique
        assert "uq_core_appointment_idem_actor_op_key" in idempotency_unique

        idempotency_fks = {
            (fk["referred_table"], fk["referred_columns"][0])
            for fk in inspector.get_foreign_keys("core_appointment_idempotency")
        }
        assert ("niam_accounts", "id") in idempotency_fks
        idempotency_indexes = {index["name"] for index in inspector.get_indexes("core_appointment_idempotency")}
        assert "ix_core_appointment_idempotency_resource_id" in idempotency_indexes

        slot_checks = {constraint["name"] for constraint in inspector.get_check_constraints("core_appointment_slots")}
        appointment_checks = {constraint["name"] for constraint in inspector.get_check_constraints("core_appointments")}
        assert {"ck_core_appointment_slot_positive_window", "ck_core_appointment_slot_status"}.issubset(slot_checks)
        assert {"ck_core_appointment_positive_window", "ck_core_appointment_state"}.issubset(appointment_checks)

        slot_fks = {(fk["referred_table"], fk["referred_columns"][0]) for fk in inspector.get_foreign_keys("core_appointment_slots")}
        appointment_fks = {(fk["referred_table"], fk["referred_columns"][0]) for fk in inspector.get_foreign_keys("core_appointments")}
        assert {
            ("niam_organizations", "id"), ("niam_admin_facilities", "id"),
            ("niam_workspaces", "id"), ("niam_accounts", "id"),
        }.issubset(slot_fks)
        assert {
            ("niam_persons", "id"), ("niam_accounts", "id"), ("niam_organizations", "id"),
            ("niam_admin_facilities", "id"), ("niam_workspaces", "id"),
            ("core_appointment_slots", "id"),
        }.issubset(appointment_fks)

        encounter_checks = {constraint["name"] for constraint in inspector.get_check_constraints("core_encounters")}
        queue_checks = {constraint["name"] for constraint in inspector.get_check_constraints("core_encounter_queue")}
        note_checks = {constraint["name"] for constraint in inspector.get_check_constraints("core_clinical_notes")}
        assert {"ck_core_encounter_status", "ck_core_encounter_version_positive"}.issubset(encounter_checks)
        assert {"ck_core_encounter_queue_status", "ck_core_encounter_queue_version_positive"}.issubset(queue_checks)
        assert {"ck_core_clinical_note_status", "ck_core_clinical_note_version_positive"}.issubset(note_checks)

        lab_order_checks = {constraint["name"] for constraint in inspector.get_check_constraints("core_lab_orders")}
        specimen_checks = {constraint["name"] for constraint in inspector.get_check_constraints("core_specimens")}
        result_checks = {constraint["name"] for constraint in inspector.get_check_constraints("core_lab_results")}
        grant_checks = {constraint["name"] for constraint in inspector.get_check_constraints("core_access_grants")}
        assert {"ck_core_lab_order_status", "ck_core_lab_order_priority", "ck_core_lab_order_version_positive"}.issubset(lab_order_checks)
        assert {"ck_core_specimen_status", "ck_core_specimen_version_positive"}.issubset(specimen_checks)
        assert {"ck_core_lab_result_status", "ck_core_lab_result_provenance", "ck_core_lab_result_version_positive"}.issubset(result_checks)
        assert {"ck_core_access_grant_status", "ck_core_access_grant_purpose", "ck_core_access_grant_version_positive"}.issubset(grant_checks)

        medication_checks = {constraint["name"] for constraint in inspector.get_check_constraints("core_medication_catalog")}
        prescription_checks = {constraint["name"] for constraint in inspector.get_check_constraints("core_prescriptions")}
        dispense_checks = {constraint["name"] for constraint in inspector.get_check_constraints("core_medication_dispenses")}
        imaging_study_checks = {constraint["name"] for constraint in inspector.get_check_constraints("core_imaging_studies")}
        imaging_report_checks = {constraint["name"] for constraint in inspector.get_check_constraints("core_imaging_reports")}
        imaging_instance_checks = {constraint["name"] for constraint in inspector.get_check_constraints("core_imaging_instances")}
        assert {"ck_core_medication_controlled_bool", "ck_core_medication_active_bool"}.issubset(medication_checks)
        assert {"ck_core_prescription_status", "ck_core_prescription_version_positive", "ck_core_prescription_controlled_policy"}.issubset(prescription_checks)
        assert {"ck_core_dispense_quantity_positive", "ck_core_dispense_status", "ck_core_dispense_version_positive"}.issubset(dispense_checks)
        assert {"ck_core_imaging_study_status", "ck_core_imaging_study_provenance", "ck_core_imaging_study_version_positive"}.issubset(imaging_study_checks)
        assert {"ck_core_imaging_report_status", "ck_core_imaging_report_version_positive"}.issubset(imaging_report_checks)
        assert {"ck_core_imaging_instance_size_positive", "ck_core_imaging_instance_no_public_url"}.issubset(imaging_instance_checks)

        medication_fks = {(fk["referred_table"], fk["referred_columns"][0]) for fk in inspector.get_foreign_keys("core_prescription_items")}
        dispense_fks = {(fk["referred_table"], fk["referred_columns"][0]) for fk in inspector.get_foreign_keys("core_medication_dispenses")}
        imaging_fks = {(fk["referred_table"], fk["referred_columns"][0]) for fk in inspector.get_foreign_keys("core_imaging_studies")}
        assert {("core_prescriptions", "id"), ("core_medication_catalog", "id")}.issubset(medication_fks)
        assert {("core_prescriptions", "id"), ("core_prescription_items", "id"), ("core_medication_batches", "id")}.issubset(dispense_fks)
        assert {("core_imaging_orders", "id")}.issubset(imaging_fks)

        index_names = {index["name"] for index in inspector.get_indexes("core_appointments")}
        assert {"ix_core_appointment_patient_scope", "ix_core_appointment_provider_scope"}.issubset(index_names)

        with engine.connect() as connection:
            revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            assert revision == "20260828_0014"
            permission_count = connection.execute(
                text(
                    "SELECT COUNT(*) FROM niam_permissions "
                    "WHERE permission_key IN ('appointment.request','appointment.confirm','appointment.slot.manage','appointment.read','encounter.checkin','encounter.manage','encounter.read','clinical.note.write','clinical.note.sign','clinical.note.amend','clinical.lab_order.create','clinical.lab_order.read','clinical.lab_order.verify','clinical.specimen.manage','clinical.result.write','clinical.result.read','clinical.result.validate_technical','clinical.result.validate_clinical','clinical.result.release','clinical.result.amend','clinical.critical.acknowledge','clinical.medication.catalog_manage','clinical.medication.prescribe','clinical.medication.sign','clinical.medication.amend','clinical.medication.inventory','clinical.medication.dispense','clinical.medication.read','clinical.imaging.order','clinical.imaging.ingest','clinical.imaging.report.write','clinical.imaging.report.sign','clinical.imaging.report.release','clinical.imaging.report.amend','clinical.imaging.critical_ack','clinical.imaging.report.read','clinical.record.read')",
                ),
            ).scalar_one()
        assert permission_count == 37
    finally:
        engine.dispose()
