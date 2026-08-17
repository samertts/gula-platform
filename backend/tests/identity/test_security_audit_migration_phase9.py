from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, inspect, text

pytestmark = pytest.mark.integration


def _database_url() -> str:
    url = os.getenv("MIGRATION_DATABASE_URL")
    if not url:
        pytest.skip("MIGRATION_DATABASE_URL is required for the live migration schema check")
    return url


def test_phase9_security_audit_schema_and_catalog_exist() -> None:
    engine = create_engine(_database_url())
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        assert {
            "niam_consents",
            "niam_security_incidents",
            "niam_audit_entries",
        }.issubset(tables)

        audit_columns = {column["name"] for column in inspector.get_columns("niam_audit_entries")}
        assert {
            "event_type",
            "event_version",
            "category",
            "decision",
            "reason_code",
            "request_id",
            "correlation_id",
            "source",
            "data_classification",
            "previous_hash",
            "entry_hash",
        }.issubset(audit_columns)

        consent_columns = {column["name"] for column in inspector.get_columns("niam_consents")}
        assert {"subject_account_id", "grantee_account_id", "purpose", "scope", "version", "supersedes_id"}.issubset(consent_columns)
        consent_constraints = {constraint["name"] for constraint in inspector.get_unique_constraints("niam_consents")}
        assert "uq_niam_consent_version" in consent_constraints

        incident_columns = {column["name"] for column in inspector.get_columns("niam_security_incidents")}
        assert {"incident_key", "severity", "category", "organization_id", "status", "version"}.issubset(incident_columns)

        check_columns = {column["name"] for column in inspector.get_columns("niam_comp_checks")}
        assert "organization_id" in check_columns

        with engine.connect() as connection:
            role_count = connection.execute(
                text("SELECT COUNT(*) FROM niam_roles WHERE role_key IN ('audit_reviewer', 'security_administrator', 'ministry_auditor', 'organization_administrator', 'compliance_officer')"),
            ).scalar_one()
            permission_count = connection.execute(
                text("SELECT COUNT(*) FROM niam_permissions WHERE permission_key IN ('audit.export', 'audit.verify_integrity', 'security.incident.read', 'security.incident.manage', 'compliance.read', 'compliance.manage', 'compliance.report')"),
            ).scalar_one()
            manager_audit_grant = connection.execute(
                text("""SELECT COUNT(*) FROM niam_role_permissions rp
                JOIN niam_roles r ON r.id = rp.role_id
                JOIN niam_permissions p ON p.id = rp.permission_id
                WHERE r.role_key = 'organization_manager' AND p.permission_key = 'audit.read'"""),
            ).scalar_one()
        assert role_count == 5
        assert permission_count == 7
        assert manager_audit_grant == 0
    finally:
        engine.dispose()
