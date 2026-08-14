"""Live-database schema checks for IAM Phase 6 membership migration."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, inspect

pytestmark = pytest.mark.integration


def _database_url() -> str:
    url = os.getenv("MIGRATION_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not url:
        pytest.skip("MIGRATION_DATABASE_URL or DATABASE_URL is required")
    return url


def test_membership_tables_constraints_and_foreign_keys_exist() -> None:
    engine = create_engine(_database_url())
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        expected_tables = {
            "niam_memberships",
            "niam_membership_invitations",
            "niam_membership_applications",
        }
        assert expected_tables.issubset(tables)

        membership_unique = {
            item["name"]
            for item in inspector.get_unique_constraints("niam_memberships")
        }
        assert {"uq_niam_memberships_uuid", "uq_niam_memberships_key"}.issubset(membership_unique)

        invitation_unique = {
            item["name"]
            for item in inspector.get_unique_constraints("niam_membership_invitations")
        }
        assert {
            "uq_niam_membership_invitations_uuid",
            "uq_niam_membership_invitations_key",
            "uq_niam_membership_invitations_token_hash",
        }.issubset(invitation_unique)

        application_unique = {
            item["name"]
            for item in inspector.get_unique_constraints("niam_membership_applications")
        }
        assert {
            "uq_niam_membership_applications_uuid",
            "uq_niam_membership_applications_key",
        }.issubset(application_unique)

        membership_fks = {
            target["referred_table"]
            for target in inspector.get_foreign_keys("niam_memberships")
        }
        assert {
            "niam_accounts",
            "niam_identities",
            "niam_organizations",
            "niam_admin_facilities",
            "niam_admin_departments",
            "niam_admin_units",
            "niam_workspaces",
        }.issubset(membership_fks)
    finally:
        engine.dispose()
