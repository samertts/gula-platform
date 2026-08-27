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
        }
        assert expected_tables.issubset(tables)

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

        index_names = {index["name"] for index in inspector.get_indexes("core_appointments")}
        assert {"ix_core_appointment_patient_scope", "ix_core_appointment_provider_scope"}.issubset(index_names)

        with engine.connect() as connection:
            permission_count = connection.execute(
                text(
                    "SELECT COUNT(*) FROM niam_permissions "
                    "WHERE permission_key IN ('appointment.request','appointment.confirm','appointment.slot.manage','appointment.read')",
                ),
            ).scalar_one()
        assert permission_count == 4
    finally:
        engine.dispose()
