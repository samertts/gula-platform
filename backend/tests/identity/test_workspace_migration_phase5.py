"""Live-database schema checks for IAM Phase 5 workspace migration."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, inspect

pytestmark = pytest.mark.integration


def _database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL is required for migration integration tests")
    return url


def test_workspace_tables_and_constraints_exist_after_migration() -> None:
    engine = create_engine(_database_url())
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        assert {"niam_workspaces", "niam_workspace_contexts"}.issubset(tables)

        workspace_unique = {
            item["name"]
            for item in inspector.get_unique_constraints("niam_workspaces")
        }
        assert {"uq_niam_workspaces_uuid", "uq_niam_workspaces_key"}.issubset(workspace_unique)

        context_unique = {
            item["name"]
            for item in inspector.get_unique_constraints("niam_workspace_contexts")
        }
        assert "uq_niam_workspace_context_session" in context_unique

        workspace_fks = {
            target["referred_table"]
            for target in inspector.get_foreign_keys("niam_workspaces")
        }
        assert {"niam_accounts", "niam_organizations"}.issubset(workspace_fks)

        context_fks = {
            target["referred_table"]
            for target in inspector.get_foreign_keys("niam_workspace_contexts")
        }
        assert {
            "niam_sessions",
            "niam_accounts",
            "niam_identities",
            "niam_workspaces",
        }.issubset(context_fks)
    finally:
        engine.dispose()
