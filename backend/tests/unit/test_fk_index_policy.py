"""PROGRAM-STABLE-001: foreign-key index policy regression tests.

PostgreSQL does not auto-index FK columns. The 20260802_0002 migration adds
a leading-column index for every FK column that lacked one (200 detected by
the information_schema + pg_index scan). These tests guard that:

  1. The migration exists, has correct revision metadata, compiles, and
     defines upgrade() + downgrade().
  2. Every CREATE INDEX statement in the migration targets a (table, column)
     pair that is a foreign key per the SQLAlchemy metadata — i.e. the
     migration never invents indexes on non-FK columns.
  3. Index names are deterministic (ix_<table>_<column>) and length-safe.
"""

from __future__ import annotations

import re
from pathlib import Path

import sqlalchemy
from app.database import Base

BACKEND = Path(__file__).resolve().parent.parent.parent
MIGRATION = BACKEND / "migrations" / "versions" / "20260802_0002_stable_fk_indexes.py"


def _fk_columns_from_metadata() -> set[tuple[str, str]]:
    """(table, column) pairs for every ForeignKey column in the metadata."""
    pairs: set[tuple[str, str]] = set()
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if column.foreign_keys:
                pairs.add((table.name, column.name))
    return pairs


class TestFkIndexMigration:
    def test_migration_file_exists(self):
        assert MIGRATION.exists(), "20260802_0002 migration file not found"

    def test_migration_metadata(self):
        src = MIGRATION.read_text()
        rev = re.search(r'^revision\s*=\s*["\']([^"\']+)["\']', src, re.MULTILINE)
        down = re.search(r'^down_revision\s*=\s*["\']([^"\']+)["\']', src, re.MULTILINE)
        assert rev and rev.group(1) == "20260802_0002"
        assert down and down.group(1) == "20260802_0001"

    def test_migration_has_upgrade_and_downgrade(self):
        src = MIGRATION.read_text()
        assert "def upgrade() -> None:" in src
        assert "def downgrade():" in src

    def test_migration_syntax(self):
        import py_compile

        py_compile.compile(str(MIGRATION), doraise=True)

    def test_all_indexes_are_fk_columns(self):
        """Indexes on metadata-known tables must target real FK columns.

        Dormant bounded contexts are not registered on Base.metadata, so the
        migration legitimately contains indexes on their tables; the guard is
        that no index claims a non-FK column on a metadata-known table.
        """
        src = MIGRATION.read_text()
        known = {table.name: {c.name for c in table.columns} for table in Base.metadata.tables.values()}
        fk_columns = _fk_columns_from_metadata()
        stmts = re.findall(r"CREATE INDEX IF NOT EXISTS (\w+) ON (\w+) \((\w+)\)", src)
        assert stmts, "no CREATE INDEX statements found"
        unknown = [
            f"{table}({col})" for idx, table, col in stmts
            if table in known and (table, col) not in fk_columns
        ]
        assert not unknown, f"indexes on non-FK columns: {unknown[:10]}"
        not_in_metadata = [f"{t}({c})" for _, t, c in stmts if t not in known]
        assert not_in_metadata, "expected indexes on dormant-context tables too"
        assert len(stmts) >= 190, f"expected ~200 indexes, found {len(stmts)}"

    def test_index_names_deterministic_and_length_safe(self):
        src = MIGRATION.read_text()
        stmts = re.findall(r"CREATE INDEX IF NOT EXISTS (\w+) ON (\w+) \((\w+)\)", src)
        for idx, table, col in stmts:
            assert idx == f"ix_{table}_{col}", f"non-deterministic index name {idx}"
            assert len(idx) <= 63, f"index name too long: {idx} ({len(idx)})"
        assert len(stmts) >= 190, f"expected ~200 indexes, found {len(stmts)}"

    def test_downgrade_drops_every_index(self):
        src = MIGRATION.read_text()
        created = set(re.findall(r"CREATE INDEX IF NOT EXISTS (\w+) ON", src))
        dropped = set(re.findall(r"DROP INDEX IF EXISTS (\w+)", src))
        assert created == dropped, "downgrade must drop exactly the indexes created"

    def test_migration_covers_every_detected_gap(self):
        """The migration must index EXACTLY the 200 FK columns that the live
        information_schema + pg_index scan flagged (snapshot of 2026-08-02).

        This guards the completeness contract: any FK column detected as
        unindexed at scan time must appear in the migration.
        """
        detected = {
            ("abac_policies", "approved_by"), ("abac_policies", "created_by"), ("ai_agent_executions", "user_id"), ("ai_evaluations", "lab_id"), ("ai_unresolved_questions", "interaction_id"), ("authorization_audit", "delegation_id"),
            ("biomed_maintenance_schedules", "device_id"), ("biomed_service_contracts", "device_id"), ("break_glass_sessions", "patient_id"), ("break_glass_sessions", "reviewed_by"), ("cc_after_action_reports", "emergency_id"), ("consents", "created_by_user_id"),
            ("critical_care_alerts", "admission_id"), ("critical_care_daily_checklists", "admission_id"), ("critical_care_early_warning_scores", "admission_id"), ("critical_care_fluid_balance", "admission_id"), ("critical_care_infusions", "admission_id"), ("critical_care_rounds", "admission_id"),
            ("critical_care_scores", "admission_id"), ("critical_care_ventilator_settings", "admission_id"), ("critical_care_vital_signs", "admission_id"), ("delegations", "revoked_by"), ("delegations", "role_id"), ("edge_devices", "owner_user_id"),
            ("edge_policies", "updated_by_user_id"), ("edge_tasks", "submitted_by_user_id"), ("edge_telemetry", "lab_id"), ("ems_dispatch_assignments", "ambulance_id"), ("ems_incident_commands", "disaster_event_id"), ("ems_mass_casualty_incidents", "disaster_event_id"),
            ("ems_shelters", "disaster_event_id"), ("feature_flags", "set_by"), ("identity_claims", "claimed_by_user_id"), ("identity_claims", "local_patient_id"), ("lab_results", "test_type_id"), ("lab_users", "created_by"),
            ("lims_calibrations", "performed_by"), ("lims_consumables", "lot_id"), ("lims_consumables", "supplier_id"), ("lims_electronic_signatures", "lab_id"), ("lims_eqa", "program_id"), ("lims_eqa", "reviewed_by"),
            ("lims_eqa", "submitted_by"), ("lims_equipment_logs", "logged_by"), ("lims_instruments", "workstation_id"), ("lims_iqc", "instrument_id"), ("lims_iqc", "performed_by"), ("lims_lots", "manufacturer_id"),
            ("lims_lots", "opened_by"), ("lims_maintenance", "performed_by"), ("lims_orders", "ordered_by"), ("lims_orders", "original_order_id"), ("lims_orders", "referring_lab_id"), ("lims_panels", "department_id"),
            ("lims_qc_programs", "instrument_id"), ("lims_reagents", "lot_id"), ("lims_reagents", "manufacturer_id"), ("lims_reagents", "supplier_id"), ("lims_reference_ranges", "instrument_id"), ("lims_reference_ranges", "lab_id"),
            ("lims_report_attachments", "uploaded_by"), ("lims_reports", "corrected_by"), ("lims_reports", "finalized_by"), ("lims_reports", "generated_by"), ("lims_reports", "printed_by"), ("lims_result_releases", "lab_id"),
            ("lims_result_releases", "released_by"), ("lims_result_validations", "validated_by"), ("lims_results", "instrument_id"), ("lims_results", "order_id"), ("lims_results", "performed_by"), ("lims_results", "validated_by"),
            ("lims_specimens", "accepted_by"), ("lims_specimens", "collected_by"), ("lims_specimens", "control_specimen_id"), ("lims_specimens", "parent_specimen_id"), ("lims_specimens", "received_by"), ("lims_specimens", "rejected_by"),
            ("lims_specimens", "released_by"), ("lims_specimens", "storage_id"), ("lims_specimens", "validated_by"), ("lims_specimens", "verified_by"), ("lims_storage", "parent_id"), ("lims_temperature_logs", "lab_id"),
            ("lims_temperature_logs", "recorded_by"), ("lims_transportation", "lab_id"), ("mpi_merge_audit", "decided_by_user_id"), ("nhdw_care_plans", "reviewed_by"), ("nhdw_clinical_tasks", "completed_by"), ("nhdw_hospital_alerts", "read_by"),
            ("nhdw_hospital_messages", "acknowledged_by"), ("nhdw_hospital_messages", "parent_message_id"), ("nhdw_resource_schedules", "booked_by"), ("nhdw_resource_schedules", "booked_for_patient_id"), ("niam_machine_identities", "assigned_to_person"), ("nursing_care_plans", "reviewed_by"),
            ("nursing_clinical_checklists", "assigned_to"), ("nursing_clinical_checklists", "completed_by"), ("nursing_clinical_checklists", "verified_by"), ("nursing_delegations", "patient_id"), ("nursing_delegations", "supervised_by"), ("nursing_escalation_records", "admission_id"),
            ("nursing_fall_risk_assessments", "admission_id"), ("nursing_fall_risk_assessments", "assessed_by"), ("nursing_fluid_balance", "admission_id"), ("nursing_fluid_balance", "recorded_by"), ("nursing_fluid_balance", "witnessed_by"), ("nursing_notes", "signed_by"),
            ("nursing_nutrition_assessments", "admission_id"), ("nursing_nutrition_assessments", "assessed_by"), ("nursing_pain_assessments", "admission_id"), ("nursing_pain_assessments", "assessed_by"), ("nursing_pressure_injury_assessments", "admission_id"), ("nursing_pressure_injury_assessments", "assessed_by"),
            ("nursing_shift_handovers", "from_nurse_id"), ("nursing_shift_handovers", "to_nurse_id"), ("nursing_tasks", "assigned_by"), ("nursing_tasks", "completed_by"), ("nursing_tasks", "witnessed_by"), ("nursing_vital_signs", "recorded_by"),
            ("pharmacy_dispense_queue", "patient_id"), ("pharmacy_dispense_queue", "prescription_id"), ("pharmacy_dispense_queue", "prescription_item_id"), ("pharmacy_dispense_records", "batch_id"), ("pharmacy_dispense_records", "counselled_by"), ("pharmacy_dispense_records", "dispensed_by"),
            ("pharmacy_dispense_records", "prescription_item_id"), ("pharmacy_dispense_records", "verified_by"), ("pharmacy_drug_batches", "received_by"), ("pharmacy_drug_batches", "supplier_id"), ("pharmacy_drug_monitoring", "performed_by"), ("pharmacy_drug_monitoring", "prescription_id"),
            ("pharmacy_drug_returns", "approved_by"), ("pharmacy_drug_returns", "batch_id"), ("pharmacy_drug_returns", "patient_id"), ("pharmacy_drug_returns", "returned_by"), ("pharmacy_inventory_transfer_items", "batch_id"), ("pharmacy_inventory_transfers", "approved_by"),
            ("pharmacy_inventory_transfers", "dispatched_by"), ("pharmacy_inventory_transfers", "from_warehouse_id"), ("pharmacy_inventory_transfers", "received_by"), ("pharmacy_inventory_transfers", "requested_by"), ("pharmacy_inventory_transfers", "to_warehouse_id"), ("pharmacy_prescription_items", "batch_id"),
            ("pharmacy_recalls", "initiated_by"), ("pharmacy_stock_levels", "last_counted_by"), ("pharmacy_stock_levels", "warehouse_id"), ("pharmacy_stock_movements", "performed_by"), ("pharmacy_waste_records", "wasted_by"), ("pharmacy_waste_records", "witnessed_by"),
            ("pilot_readiness_checklists", "pilot_id"), ("radiology_ai_analysis_jobs", "image_id"), ("radiology_ai_analysis_jobs", "patient_id"), ("radiology_ai_analysis_jobs", "reviewed_by"), ("radiology_appointments", "device_id"), ("radiology_appointments", "radiologist_id"),
            ("radiology_appointments", "technician_id"), ("radiology_critical_findings", "acknowledged_by"), ("radiology_critical_findings", "exam_id"), ("radiology_critical_findings", "identified_by"), ("radiology_critical_findings", "order_id"), ("radiology_critical_findings", "report_id"),
            ("radiology_dicom_storage", "patient_id"), ("radiology_dicom_studies", "exam_id"), ("radiology_dicom_studies", "patient_id"), ("radiology_exams", "appointment_id"), ("radiology_exams", "device_id"), ("radiology_exams", "performed_by"),
            ("radiology_exams", "protocol_id"), ("radiology_exams", "technician_id"), ("radiology_image_annotations", "verified_by"), ("radiology_image_measurements", "annotation_id"), ("radiology_image_measurements", "created_by"), ("radiology_image_shares", "exam_id"),
            ("radiology_mpps", "exam_id"), ("radiology_orders", "cancelled_by"), ("radiology_orders", "ordered_by"), ("radiology_reports", "approved_by"), ("radiology_reports", "critical_finding_id"), ("radiology_reports", "drafted_by"),
            ("radiology_reports", "exam_id"), ("radiology_reports", "original_report_id"), ("radiology_reports", "reviewed_by"), ("radiology_reports", "template_id"), ("radiology_worklist_entries", "appointment_id"), ("radiology_worklist_entries", "patient_id"),
            ("radiology_worklist_entries", "performed_by"), ("role_assignments", "assigned_by"), ("role_assignments", "facility_id"), ("role_assignments", "organization_id"), ("trust_compliance_checks", "checked_by"), ("trust_compliance_evidence", "collected_by"),
            ("trust_consent_records", "guardian_id"), ("trust_service_logs", "lab_id"), ("trust_service_logs", "patient_id"), ("trust_service_logs", "user_id"), ("upgrade_requests", "requester_id"), ("upgrade_requests", "reviewed_by"),
            ("users", "facility_id"), ("users", "lab_id"),
        }
        src = MIGRATION.read_text()
        stmts = set(re.findall(r"CREATE INDEX IF NOT EXISTS \w+ ON (\w+) \((\w+)\)", src))
        assert detected.issubset(stmts), (
            f"migration missing detected gaps: {sorted(detected - stmts)[:8]}"
        )
        assert len(stmts) == len(detected), (
            f"migration has {len(stmts)} indexes, snapshot has {len(detected)}"
        )
