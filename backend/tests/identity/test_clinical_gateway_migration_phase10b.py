from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, inspect, text

pytestmark = pytest.mark.integration


def _database_url() -> str:
    url = os.getenv("MIGRATION_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not url:
        pytest.skip("MIGRATION_DATABASE_URL or DATABASE_URL is required")
    if url.startswith("sqlite"):
        pytest.skip("Phase 10-B migration gate requires PostgreSQL fixtures")
    return url


def test_phase10b_clinical_scope_mapping_and_read_permissions_exist() -> None:
    engine = create_engine(_database_url())
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        assert "clinical_lab_facility_bindings" in tables

        columns = {column["name"] for column in inspector.get_columns("clinical_lab_facility_bindings")}
        assert {"niam_organization_id", "niam_facility_id", "mapping_version"}.issubset(columns)

        with engine.connect() as connection:
            permissions = connection.execute(
                text("""SELECT permission_key FROM niam_permissions
                WHERE permission_key IN ('patients.read', 'orders.read')"""),
            ).scalars().all()
            assignments = connection.execute(
                text("""SELECT COUNT(*) FROM niam_role_permissions rp
                JOIN niam_permissions p ON p.id = rp.permission_id
                WHERE p.permission_key IN ('patients.read', 'orders.read')"""),
            ).scalar_one()
        assert set(permissions) == {"patients.read", "orders.read"}
        assert assignments == 0
    finally:
        engine.dispose()
