"""NIAM Identity & Access Management platform tables

Revision ID: 20260723_0001
Revises: 20260722_0001
Create Date: 2026-07-23

Tables:
  - niam_persons                 — Person registry (citizens, healthcare workers, etc.)
  - niam_organizations           — Healthcare organization hierarchy (ministry → facility)
  - niam_identities             — Identity records linked to persons
  - niam_accounts               — User/machine/service accounts
  - niam_devices                — Registered devices for persons/accounts
  - niam_sessions               — Authentication sessions
  - niam_employments            — Employment records linking persons to organizations
  - niam_assignments            — Role/task assignments within employments
  - niam_licenses               — Professional licenses and certifications
  - niam_credentials            — Credential store (passwords, passkeys, certs, etc.)
  - niam_enterprise_accounts    — Enterprise/organization-level API accounts
  - niam_machine_identities     — Machine/device identities (IoT, workstations, etc.)
  - niam_policies               — Identity governance policies
  - niam_audit_entries          — Immutable audit trail for identity operations
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import context, op

revision: str = "20260723_0001"
down_revision: Union[str, None] = "20260722_0001"


def _has_table(name: str) -> bool:
    if context.is_offline_mode():
        return False
    conn = op.get_bind()
    return conn.dialect.has_table(conn, name)


def _has_column(table: str, column: str) -> bool:
    if context.is_offline_mode():
        return False
    conn = op.get_bind()
    if not conn.dialect.has_table(conn, table):
        return False
    insp = sa.inspect(conn)
    cols = [c["name"] for c in insp.get_columns(table)]
    return column in cols


def upgrade() -> None:
    # ── 1. niam_persons ───────────────────────────────────────────────────────
    if not _has_table("niam_persons"):
        op.create_table(
            "niam_persons",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("national_id_hash", sa.String(length=255), nullable=True, index=True),
            sa.Column("health_id", sa.String(length=100), nullable=True, index=True),
            sa.Column("passport_number", sa.String(length=50), nullable=True, index=True),
            sa.Column("given_name", sa.String(length=100), nullable=False),
            sa.Column("middle_name", sa.String(length=100), nullable=True),
            sa.Column("family_name", sa.String(length=100), nullable=False),
            sa.Column("full_name_ar", sa.String(length=300), nullable=True),
            sa.Column("gender", sa.String(length=20), nullable=True),
            sa.Column("birth_date", sa.Date(), nullable=True),
            sa.Column("nationality", sa.String(length=3), nullable=True, server_default=sa.text("'IRQ'")),
            sa.Column("email", sa.String(length=200), nullable=True, index=True),
            sa.Column("phone", sa.String(length=30), nullable=True, index=True),
            sa.Column("address", sa.Text(), nullable=True),
            sa.Column("emergency_contact_name", sa.String(length=200), nullable=True),
            sa.Column("emergency_contact_phone", sa.String(length=30), nullable=True),
            sa.Column("emergency_contact_relation", sa.String(length=50), nullable=True),
            sa.Column("is_deceased", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("deceased_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("tags", sa.JSON(), nullable=True),
            sa.Column("extra_metadata", sa.JSON(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("national_id_hash"),
            sa.UniqueConstraint("health_id"),
            sa.UniqueConstraint("passport_number"),
        )

    # ── 2. niam_organizations ─────────────────────────────────────────────────
    if not _has_table("niam_organizations"):
        op.create_table(
            "niam_organizations",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("org_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("name_en", sa.String(length=300), nullable=False),
            sa.Column("name_ar", sa.String(length=300), nullable=False),
            sa.Column("org_type", sa.String(length=50), nullable=False, index=True),
            sa.Column("parent_org_id", sa.String(length=26), sa.ForeignKey("niam_organizations.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("license_number", sa.String(length=100), nullable=True),
            sa.Column("accreditation", sa.String(length=200), nullable=True),
            sa.Column("accreditation_expires", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'active'"), index=True),
            sa.Column("fhir_endpoint", sa.String(length=500), nullable=True),
            sa.Column("digital_certificate", sa.Text(), nullable=True),
            sa.Column("certificate_expires", sa.DateTime(timezone=True), nullable=True),
            sa.Column("contact_email", sa.String(length=200), nullable=True),
            sa.Column("contact_phone", sa.String(length=30), nullable=True),
            sa.Column("address", sa.Text(), nullable=True),
            sa.Column("website", sa.String(length=300), nullable=True),
            sa.Column("governorate", sa.String(length=50), nullable=True),
            sa.Column("district", sa.String(length=50), nullable=True),
            sa.Column("subscriptions", sa.JSON(), nullable=True),
            sa.Column("settings", sa.JSON(), nullable=True),
            sa.Column("tags", sa.JSON(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("org_id"),
            sa.UniqueConstraint("license_number"),
        )

    # ── 3. niam_identities ────────────────────────────────────────────────────
    if not _has_table("niam_identities"):
        op.create_table(
            "niam_identities",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("person_id", sa.String(length=26), sa.ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("identity_type", sa.String(length=30), nullable=False, index=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'active'"), index=True),
            sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("verified_by", sa.String(length=100), nullable=True),
            sa.Column("verification_method", sa.String(length=50), nullable=True),
            sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("issued_by_organization", sa.String(length=26), sa.ForeignKey("niam_organizations.id", ondelete="SET NULL"), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
        )
        op.create_index("ix_niam_identities_issued_by_org", "niam_identities", ["issued_by_organization"])

    # ── 4. niam_accounts ──────────────────────────────────────────────────────
    if not _has_table("niam_accounts"):
        op.create_table(
            "niam_accounts",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("identity_id", sa.String(length=26), sa.ForeignKey("niam_identities.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("account_type", sa.String(length=20), nullable=False, server_default=sa.text("'human'")),
            sa.Column("status", sa.String(length=30), nullable=False, server_default=sa.text("'pending_verification'"), index=True),
            sa.Column("email", sa.String(length=200), nullable=True, index=True),
            sa.Column("phone", sa.String(length=30), nullable=True, index=True),
            sa.Column("username", sa.String(length=100), nullable=True, index=True),
            sa.Column("password_hash", sa.String(length=255), nullable=True),
            sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("password_expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("mfa_methods", sa.String(length=200), nullable=True),
            sa.Column("mfa_secret", sa.String(length=255), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
            sa.Column("lock_reason", sa.String(length=200), nullable=True),
            sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
            sa.Column("last_failed_login", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_login_ip", sa.String(length=45), nullable=True),
            sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("phone_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("identity_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deactivation_reason", sa.String(length=200), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("email"),
            sa.UniqueConstraint("phone"),
            sa.UniqueConstraint("username"),
        )

    # ── 5. niam_devices ───────────────────────────────────────────────────────
    if not _has_table("niam_devices"):
        op.create_table(
            "niam_devices",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("person_id", sa.String(length=26), sa.ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("account_id", sa.String(length=26), sa.ForeignKey("niam_accounts.id", ondelete="CASCADE"), nullable=True, index=True),
            sa.Column("device_name", sa.String(length=200), nullable=True),
            sa.Column("device_type", sa.String(length=50), nullable=True),
            sa.Column("manufacturer", sa.String(length=100), nullable=True),
            sa.Column("model", sa.String(length=100), nullable=True),
            sa.Column("os", sa.String(length=100), nullable=True),
            sa.Column("os_version", sa.String(length=50), nullable=True),
            sa.Column("browser", sa.String(length=100), nullable=True),
            sa.Column("browser_version", sa.String(length=50), nullable=True),
            sa.Column("device_fingerprint", sa.String(length=255), nullable=False, index=True),
            sa.Column("device_id", sa.String(length=255), nullable=True),
            sa.Column("public_key", sa.Text(), nullable=True),
            sa.Column("trusted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("trusted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_ip", sa.String(length=45), nullable=True),
            sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("device_fingerprint"),
            sa.UniqueConstraint("device_id"),
        )

    # ── 6. niam_sessions ──────────────────────────────────────────────────────
    if not _has_table("niam_sessions"):
        op.create_table(
            "niam_sessions",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("account_id", sa.String(length=26), sa.ForeignKey("niam_accounts.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("token_jti", sa.String(length=128), nullable=False, index=True),
            sa.Column("refresh_token_jti", sa.String(length=128), nullable=True, index=True),
            sa.Column("session_type", sa.String(length=20), nullable=False, server_default=sa.text("'web'")),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("ip_address", sa.String(length=45), nullable=True),
            sa.Column("user_agent", sa.Text(), nullable=True),
            sa.Column("device_id", sa.String(length=26), sa.ForeignKey("niam_devices.id", ondelete="SET NULL"), nullable=True),
            sa.Column("location_city", sa.String(length=100), nullable=True),
            sa.Column("location_country", sa.String(length=3), nullable=True),
            sa.Column("location_lat", sa.String(length=20), nullable=True),
            sa.Column("location_lng", sa.String(length=20), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("terminated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("termination_reason", sa.String(length=100), nullable=True),
            sa.Column("terminated_by", sa.String(length=100), nullable=True),
            sa.Column("auth_method", sa.String(length=50), nullable=True),
            sa.Column("mfa_used", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("risk_score", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("token_jti"),
            sa.UniqueConstraint("refresh_token_jti"),
        )
        op.create_index("ix_niam_sessions_device", "niam_sessions", ["device_id"])

    # ── 7. niam_employments ───────────────────────────────────────────────────
    if not _has_table("niam_employments"):
        op.create_table(
            "niam_employments",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("person_id", sa.String(length=26), sa.ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("organization_id", sa.String(length=26), sa.ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("employee_id", sa.String(length=50), nullable=True, index=True),
            sa.Column("employment_type", sa.String(length=50), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'active'"), index=True),
            sa.Column("position", sa.String(length=200), nullable=False),
            sa.Column("department", sa.String(length=200), nullable=True),
            sa.Column("title", sa.String(length=200), nullable=True),
            sa.Column("start_date", sa.Date(), nullable=False),
            sa.Column("end_date", sa.Date(), nullable=True),
            sa.Column("contract_type", sa.String(length=50), nullable=True),
            sa.Column("contract_end_date", sa.Date(), nullable=True),
            sa.Column("supervisor_person_id", sa.String(length=26), sa.ForeignKey("niam_persons.id", ondelete="SET NULL"), nullable=True),
            sa.Column("is_primary_employment", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("termination_reason", sa.Text(), nullable=True),
            sa.Column("termination_date", sa.Date(), nullable=True),
            sa.Column("transfer_from_employment", sa.String(length=26), sa.ForeignKey("niam_employments.id", ondelete="SET NULL"), nullable=True),
            sa.Column("transfer_to_organization", sa.String(length=26), sa.ForeignKey("niam_organizations.id", ondelete="SET NULL"), nullable=True),
            sa.Column("transfer_date", sa.Date(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
        )
        op.create_index("ix_niam_employments_supervisor", "niam_employments", ["supervisor_person_id"])
        op.create_index("ix_niam_employments_transfer_from", "niam_employments", ["transfer_from_employment"])
        op.create_index("ix_niam_employments_transfer_to", "niam_employments", ["transfer_to_organization"])

    # ── 8. niam_assignments ───────────────────────────────────────────────────
    if not _has_table("niam_assignments"):
        op.create_table(
            "niam_assignments",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("employment_id", sa.String(length=26), sa.ForeignKey("niam_employments.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("person_id", sa.String(length=26), sa.ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("organization_id", sa.String(length=26), sa.ForeignKey("niam_organizations.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("facility_id", sa.String(length=26), nullable=True, index=True),
            sa.Column("department_id", sa.String(length=26), nullable=True, index=True),
            sa.Column("unit", sa.String(length=200), nullable=True),
            sa.Column("committee", sa.String(length=200), nullable=True),
            sa.Column("task_force", sa.String(length=200), nullable=True),
            sa.Column("role_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("assignment_type", sa.String(length=50), nullable=False),
            sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'active'"), index=True),
            sa.Column("start_date", sa.Date(), nullable=False),
            sa.Column("end_date", sa.Date(), nullable=True),
            sa.Column("expected_end_date", sa.Date(), nullable=True),
            sa.Column("is_temporary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("is_emergency", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("is_delegated", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("delegated_from", sa.String(length=26), sa.ForeignKey("niam_assignments.id", ondelete="SET NULL"), nullable=True),
            sa.Column("delegated_by", sa.String(length=26), sa.ForeignKey("niam_persons.id", ondelete="SET NULL"), nullable=True),
            sa.Column("max_duration_hours", sa.Integer(), nullable=True),
            sa.Column("requires_mfa", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("assigned_by", sa.String(length=26), sa.ForeignKey("niam_persons.id", ondelete="SET NULL"), nullable=True),
            sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
        )
        op.create_index("ix_niam_assignments_delegated_from", "niam_assignments", ["delegated_from"])
        op.create_index("ix_niam_assignments_delegated_by", "niam_assignments", ["delegated_by"])
        op.create_index("ix_niam_assignments_assigned_by", "niam_assignments", ["assigned_by"])

    # ── 9. niam_licenses ──────────────────────────────────────────────────────
    if not _has_table("niam_licenses"):
        op.create_table(
            "niam_licenses",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("person_id", sa.String(length=26), sa.ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("license_type", sa.String(length=50), nullable=False, index=True),
            sa.Column("license_number", sa.String(length=100), nullable=False, index=True),
            sa.Column("license_name", sa.String(length=200), nullable=False),
            sa.Column("issuing_authority", sa.String(length=200), nullable=False),
            sa.Column("issuing_country", sa.String(length=3), nullable=False, server_default=sa.text("'IRQ'")),
            sa.Column("issue_date", sa.Date(), nullable=False),
            sa.Column("expiry_date", sa.Date(), nullable=True),
            sa.Column("verification_date", sa.Date(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'active'"), index=True),
            sa.Column("status_reason", sa.Text(), nullable=True),
            sa.Column("board_certification", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("board_name", sa.String(length=200), nullable=True),
            sa.Column("board_certified_at", sa.Date(), nullable=True),
            sa.Column("degree_type", sa.String(length=50), nullable=True),
            sa.Column("degree_name", sa.String(length=200), nullable=True),
            sa.Column("degree_institution", sa.String(length=200), nullable=True),
            sa.Column("degree_year", sa.Integer(), nullable=True),
            sa.Column("degree_country", sa.String(length=3), nullable=True),
            sa.Column("continuing_education_hours", sa.Integer(), nullable=True),
            sa.Column("continuing_education_expires", sa.Date(), nullable=True),
            sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("verified_by", sa.String(length=100), nullable=True),
            sa.Column("attachments", sa.Text(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
        )

    # ── 10. niam_credentials ──────────────────────────────────────────────────
    if not _has_table("niam_credentials"):
        op.create_table(
            "niam_credentials",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("account_id", sa.String(length=26), sa.ForeignKey("niam_accounts.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("credential_type", sa.String(length=30), nullable=False, index=True),
            sa.Column("credential_value", sa.Text(), nullable=False),
            sa.Column("credential_identifier", sa.String(length=255), nullable=True, index=True),
            sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revocation_reason", sa.String(length=200), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("device_info", sa.String(length=500), nullable=True),
            sa.Column("ip_address", sa.String(length=45), nullable=True),
            sa.Column("user_agent", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
        )

    # ── 11. niam_enterprise_accounts ──────────────────────────────────────────
    if not _has_table("niam_enterprise_accounts"):
        op.create_table(
            "niam_enterprise_accounts",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("organization_id", sa.String(length=26), sa.ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("display_name", sa.String(length=200), nullable=False),
            sa.Column("api_key_prefix", sa.String(length=10), nullable=True, index=True),
            sa.Column("api_key_hash", sa.String(length=255), nullable=True),
            sa.Column("api_key_rotated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("oauth2_client_id", sa.String(length=100), nullable=True, index=True),
            sa.Column("oauth2_client_secret_hash", sa.String(length=255), nullable=True),
            sa.Column("certificate", sa.Text(), nullable=True),
            sa.Column("certificate_thumbprint", sa.String(length=100), nullable=True),
            sa.Column("certificate_expires", sa.DateTime(timezone=True), nullable=True),
            sa.Column("digital_signature_key", sa.Text(), nullable=True),
            sa.Column("fhir_endpoint", sa.String(length=500), nullable=True),
            sa.Column("scopes", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("oauth2_client_id"),
        )

    # ── 12. niam_machine_identities ───────────────────────────────────────────
    if not _has_table("niam_machine_identities"):
        op.create_table(
            "niam_machine_identities",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("organization_id", sa.String(length=26), sa.ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("machine_name", sa.String(length=200), nullable=False),
            sa.Column("machine_type", sa.String(length=50), nullable=False),
            sa.Column("serial_number", sa.String(length=100), nullable=True),
            sa.Column("ip_address", sa.String(length=45), nullable=True),
            sa.Column("mac_address", sa.String(length=17), nullable=True),
            sa.Column("hostname", sa.String(length=255), nullable=True),
            sa.Column("os", sa.String(length=100), nullable=True),
            sa.Column("os_version", sa.String(length=50), nullable=True),
            sa.Column("agent_version", sa.String(length=30), nullable=True),
            sa.Column("public_key", sa.Text(), nullable=True),
            sa.Column("certificate_sn", sa.String(length=100), nullable=True),
            sa.Column("certificate", sa.Text(), nullable=True),
            sa.Column("certificate_expires", sa.DateTime(timezone=True), nullable=True),
            sa.Column("assigned_to_person", sa.String(length=26), sa.ForeignKey("niam_persons.id", ondelete="SET NULL"), nullable=True),
            sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("location", sa.String(length=200), nullable=True),
            sa.Column("last_heartbeat", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("is_compromised", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("compromised_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("serial_number"),
            sa.UniqueConstraint("mac_address"),
            sa.UniqueConstraint("certificate_sn"),
        )

    # ── 13. niam_policies ─────────────────────────────────────────────────────
    if not _has_table("niam_policies"):
        op.create_table(
            "niam_policies",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("policy_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("policy_type", sa.String(length=50), nullable=False, index=True),
            sa.Column("category", sa.String(length=50), nullable=True, index=True),
            sa.Column("effect", sa.String(length=10), nullable=False),
            sa.Column("actions", sa.JSON(), nullable=False),
            sa.Column("resources", sa.JSON(), nullable=False),
            sa.Column("subjects", sa.JSON(), nullable=True),
            sa.Column("conditions", sa.JSON(), nullable=True),
            sa.Column("priority", sa.Integer(), nullable=False, server_default=sa.text("0")),
            sa.Column("version", sa.String(length=20), nullable=False, server_default=sa.text("'1.0'")),
            sa.Column("applies_to_org_types", sa.JSON(), nullable=True),
            sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_by", sa.String(length=100), nullable=False),
            sa.Column("approved_by", sa.String(length=100), nullable=True),
            sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("tags", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("policy_id"),
        )

    # ── 14. niam_audit_entries ────────────────────────────────────────────────
    if not _has_table("niam_audit_entries"):
        op.create_table(
            "niam_audit_entries",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("action", sa.String(length=50), nullable=False, index=True),
            sa.Column("actor_id", sa.String(length=36), nullable=True, index=True),
            sa.Column("actor_type", sa.String(length=30), nullable=True),
            sa.Column("target_type", sa.String(length=50), nullable=True, index=True),
            sa.Column("target_id", sa.String(length=36), nullable=True, index=True),
            sa.Column("changes", sa.JSON(), nullable=True),
            sa.Column("extra_data", sa.JSON(), nullable=True),
            sa.Column("context", sa.JSON(), nullable=True),
            sa.Column("ip_address", sa.String(length=45), nullable=True),
            sa.Column("user_agent", sa.Text(), nullable=True),
            sa.Column("session_id", sa.String(length=36), nullable=True),
            sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, index=True),
            sa.Column("organization_id", sa.String(length=36), nullable=True, index=True),
            sa.Column("outcome", sa.String(length=20), nullable=False, server_default=sa.text("'success'")),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
        )


def downgrade() -> None:
    tables = [
        "niam_audit_entries",
        "niam_policies",
        "niam_machine_identities",
        "niam_enterprise_accounts",
        "niam_credentials",
        "niam_licenses",
        "niam_assignments",
        "niam_employments",
        "niam_sessions",
        "niam_devices",
        "niam_accounts",
        "niam_identities",
        "niam_organizations",
        "niam_persons",
    ]
    for table in tables:
        if _has_table(table):
            op.drop_table(table)
