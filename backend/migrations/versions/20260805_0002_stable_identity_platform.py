"""PROGRAM-STABLE-003: workspace platform, professional registry,
citizen registry providers, session workspace binding.

Revision ID: 20260805_0001
Revises: 20260723_0002
Create Date: 2026-08-05
"""

import sqlalchemy as sa
from alembic import op

revision = "20260805_0002"
down_revision = "20260805_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Workspaces ──────────────────────────────────────────────────────────
    op.create_table(
        "niam_workspaces",
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=100), nullable=False),
        sa.Column("owner_identity_id", sa.String(length=26), nullable=False),
        sa.Column("owner_person_id", sa.String(length=26), nullable=False),
        sa.Column("organization_id", sa.String(length=26), nullable=True),
        sa.Column("name_en", sa.String(length=300), nullable=False),
        sa.Column("name_ar", sa.String(length=300), nullable=False),
        sa.Column("workspace_type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("settings", sa.JSON(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["owner_identity_id"], ["niam_identities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_person_id"], ["niam_persons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["niam_organizations.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_niam_workspaces_uuid", "niam_workspaces", ["uuid"], unique=True)
    op.create_index("ix_niam_workspaces_workspace_id", "niam_workspaces", ["workspace_id"], unique=True)
    op.create_index("ix_niam_workspaces_owner_identity_id", "niam_workspaces", ["owner_identity_id"])
    op.create_index("ix_niam_workspaces_owner_person_id", "niam_workspaces", ["owner_person_id"])
    op.create_index("ix_niam_workspaces_organization_id", "niam_workspaces", ["organization_id"])
    op.create_index("ix_niam_workspaces_workspace_type", "niam_workspaces", ["workspace_type"])
    op.create_index("ix_niam_workspaces_status", "niam_workspaces", ["status"])

    op.create_table(
        "niam_workspace_roles",
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("role_id", sa.String(length=100), nullable=False),
        sa.Column("workspace_id", sa.String(length=26), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("permissions", sa.JSON(), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["niam_workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_niam_workspace_roles_uuid", "niam_workspace_roles", ["uuid"], unique=True)
    op.create_index("ix_niam_workspace_roles_role_id", "niam_workspace_roles", ["role_id"], unique=True)
    op.create_index("ix_niam_workspace_roles_workspace_id", "niam_workspace_roles", ["workspace_id"])

    op.create_table(
        "niam_workspace_members",
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("membership_id", sa.String(length=100), nullable=False),
        sa.Column("workspace_id", sa.String(length=26), nullable=False),
        sa.Column("identity_id", sa.String(length=26), nullable=False),
        sa.Column("person_id", sa.String(length=26), nullable=False),
        sa.Column("role_id", sa.String(length=26), nullable=True),
        sa.Column("role_name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("invited_by", sa.String(length=26), nullable=True),
        sa.Column("invited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("active_workspace", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["niam_workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["identity_id"], ["niam_identities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["person_id"], ["niam_persons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["niam_workspace_roles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["invited_by"], ["niam_persons.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_niam_workspace_members_uuid", "niam_workspace_members", ["uuid"], unique=True)
    op.create_index(
        "ix_niam_workspace_members_membership_id", "niam_workspace_members", ["membership_id"], unique=True
    )
    op.create_index("ix_niam_workspace_members_workspace_id", "niam_workspace_members", ["workspace_id"])
    op.create_index("ix_niam_workspace_members_identity_id", "niam_workspace_members", ["identity_id"])
    op.create_index("ix_niam_workspace_members_person_id", "niam_workspace_members", ["person_id"])
    op.create_index("ix_niam_workspace_members_status", "niam_workspace_members", ["status"])

    op.create_table(
        "niam_workspace_permission_templates",
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("template_id", sa.String(length=100), nullable=False),
        sa.Column("workspace_id", sa.String(length=26), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("permissions", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["niam_workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_niam_workspace_permission_templates_uuid",
        "niam_workspace_permission_templates",
        ["uuid"],
        unique=True,
    )
    op.create_index(
        "ix_niam_workspace_permission_templates_template_id",
        "niam_workspace_permission_templates",
        ["template_id"],
        unique=True,
    )
    op.create_index(
        "ix_niam_workspace_permission_templates_workspace_id",
        "niam_workspace_permission_templates",
        ["workspace_id"],
    )

    op.create_table(
        "niam_workspace_departments",
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("dept_id", sa.String(length=100), nullable=False),
        sa.Column("workspace_id", sa.String(length=26), nullable=False),
        sa.Column("name_en", sa.String(length=300), nullable=False),
        sa.Column("name_ar", sa.String(length=300), nullable=False),
        sa.Column("dept_type", sa.String(length=50), nullable=True),
        sa.Column("head_person_id", sa.String(length=26), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["niam_workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["head_person_id"], ["niam_persons.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_niam_workspace_departments_uuid", "niam_workspace_departments", ["uuid"], unique=True)
    op.create_index("ix_niam_workspace_departments_dept_id", "niam_workspace_departments", ["dept_id"], unique=True)
    op.create_index(
        "ix_niam_workspace_departments_workspace_id", "niam_workspace_departments", ["workspace_id"]
    )

    op.create_table(
        "niam_workspace_teams",
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("team_id", sa.String(length=100), nullable=False),
        sa.Column("workspace_id", sa.String(length=26), nullable=False),
        sa.Column("department_id", sa.String(length=26), nullable=True),
        sa.Column("name_en", sa.String(length=300), nullable=False),
        sa.Column("name_ar", sa.String(length=300), nullable=False),
        sa.Column("leader_person_id", sa.String(length=26), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["niam_workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["department_id"], ["niam_workspace_departments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["leader_person_id"], ["niam_persons.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_niam_workspace_teams_uuid", "niam_workspace_teams", ["uuid"], unique=True)
    op.create_index("ix_niam_workspace_teams_team_id", "niam_workspace_teams", ["team_id"], unique=True)
    op.create_index("ix_niam_workspace_teams_workspace_id", "niam_workspace_teams", ["workspace_id"])
    op.create_index("ix_niam_workspace_teams_department_id", "niam_workspace_teams", ["department_id"])

    op.create_table(
        "niam_workspace_invitations",
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("invitation_id", sa.String(length=100), nullable=False),
        sa.Column("workspace_id", sa.String(length=26), nullable=False),
        sa.Column("invited_by", sa.String(length=26), nullable=True),
        sa.Column("invitee_email", sa.String(length=200), nullable=False),
        sa.Column("invitee_person_id", sa.String(length=26), nullable=True),
        sa.Column("role_id", sa.String(length=26), nullable=True),
        sa.Column("role_name", sa.String(length=100), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["niam_workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["invited_by"], ["niam_persons.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["invitee_person_id"], ["niam_persons.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["role_id"], ["niam_workspace_roles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_niam_workspace_invitations_uuid", "niam_workspace_invitations", ["uuid"], unique=True)
    op.create_index(
        "ix_niam_workspace_invitations_invitation_id", "niam_workspace_invitations", ["invitation_id"], unique=True
    )
    op.create_index("ix_niam_workspace_invitations_workspace_id", "niam_workspace_invitations", ["workspace_id"])
    op.create_index("ix_niam_workspace_invitations_invitee_email", "niam_workspace_invitations", ["invitee_email"])
    op.create_index(
        "ix_niam_workspace_invitations_invitee_person_id", "niam_workspace_invitations", ["invitee_person_id"]
    )
    op.create_index("ix_niam_workspace_invitations_token", "niam_workspace_invitations", ["token"], unique=True)

    op.create_table(
        "niam_workspace_delegations",
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("delegation_id", sa.String(length=100), nullable=False),
        sa.Column("workspace_id", sa.String(length=26), nullable=False),
        sa.Column("delegated_from_person_id", sa.String(length=26), nullable=False),
        sa.Column("delegated_to_person_id", sa.String(length=26), nullable=False),
        sa.Column("permissions", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by", sa.String(length=26), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["niam_workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["delegated_from_person_id"], ["niam_persons.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["delegated_to_person_id"], ["niam_persons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["revoked_by"], ["niam_persons.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_niam_workspace_delegations_uuid", "niam_workspace_delegations", ["uuid"], unique=True)
    op.create_index(
        "ix_niam_workspace_delegations_delegation_id", "niam_workspace_delegations", ["delegation_id"], unique=True
    )
    op.create_index(
        "ix_niam_workspace_delegations_workspace_id", "niam_workspace_delegations", ["workspace_id"]
    )

    # ── Professional Registry (Phase 4) ─────────────────────────────────────
    op.create_table(
        "niam_professional_registry",
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("registry_id", sa.String(length=100), nullable=False),
        sa.Column("person_id", sa.String(length=26), nullable=False),
        sa.Column("identity_id", sa.String(length=26), nullable=False),
        sa.Column("profession", sa.String(length=50), nullable=False),
        sa.Column("specialty", sa.String(length=200), nullable=True),
        sa.Column("registration_number", sa.String(length=100), nullable=False),
        sa.Column("issuing_authority", sa.String(length=200), nullable=False),
        sa.Column("issuing_authority_id", sa.String(length=26), nullable=True),
        sa.Column("issuing_country", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("status_reason", sa.Text(), nullable=True),
        sa.Column("verified", sa.Boolean(), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_by", sa.String(length=100), nullable=True),
        sa.Column("verification_method", sa.String(length=100), nullable=True),
        sa.Column("license_number", sa.String(length=100), nullable=True),
        sa.Column("license_verified", sa.Boolean(), nullable=False),
        sa.Column("issued_at", sa.Date(), nullable=False),
        sa.Column("expires_at", sa.Date(), nullable=True),
        sa.Column("privileges_activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("privileges_activated_by", sa.String(length=100), nullable=True),
        sa.Column("attachments", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["person_id"], ["niam_persons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["identity_id"], ["niam_identities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["issuing_authority_id"], ["niam_identity_authorities.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_niam_professional_registry_uuid", "niam_professional_registry", ["uuid"], unique=True)
    op.create_index(
        "ix_niam_professional_registry_registry_id", "niam_professional_registry", ["registry_id"], unique=True
    )
    op.create_index(
        "ix_niam_professional_registry_registration_number",
        "niam_professional_registry",
        ["registration_number"],
        unique=True,
    )
    op.create_index("ix_niam_professional_registry_person_id", "niam_professional_registry", ["person_id"])
    op.create_index(
        "ix_niam_professional_registry_identity_id", "niam_professional_registry", ["identity_id"]
    )
    op.create_index("ix_niam_professional_registry_profession", "niam_professional_registry", ["profession"])
    op.create_index(
        "ix_niam_professional_registry_issuing_country", "niam_professional_registry", ["issuing_country"]
    )
    op.create_index("ix_niam_professional_registry_status", "niam_professional_registry", ["status"])

    # ── Citizen Registry Providers (Phase 5) ────────────────────────────────
    op.create_table(
        "niam_identity_providers",
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("provider_id", sa.String(length=100), nullable=False),
        sa.Column("name_en", sa.String(length=300), nullable=False),
        sa.Column("name_ar", sa.String(length=300), nullable=True),
        sa.Column("provider_type", sa.String(length=50), nullable=False),
        sa.Column("country", sa.String(length=3), nullable=False),
        sa.Column("identifier_types", sa.JSON(), nullable=False),
        sa.Column("verification_methods", sa.JSON(), nullable=True),
        sa.Column("configuration", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_niam_identity_providers_uuid", "niam_identity_providers", ["uuid"], unique=True)
    op.create_index(
        "ix_niam_identity_providers_provider_id", "niam_identity_providers", ["provider_id"], unique=True
    )
    op.create_index("ix_niam_identity_providers_provider_type", "niam_identity_providers", ["provider_type"])
    op.create_index("ix_niam_identity_providers_country", "niam_identity_providers", ["country"])
    op.create_index("ix_niam_identity_providers_status", "niam_identity_providers", ["status"])

    op.create_table(
        "niam_citizen_identity_verifications",
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("verification_id", sa.String(length=100), nullable=False),
        sa.Column("person_id", sa.String(length=26), nullable=False),
        sa.Column("provider_id", sa.String(length=26), nullable=False),
        sa.Column("identifier_type", sa.String(length=50), nullable=False),
        sa.Column("identifier_hash", sa.String(length=255), nullable=False),
        sa.Column("identifier_display", sa.String(length=100), nullable=True),
        sa.Column("verification_status", sa.String(length=20), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_by", sa.String(length=100), nullable=True),
        sa.Column("raw_response", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["person_id"], ["niam_persons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["provider_id"], ["niam_identity_providers.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_niam_citizen_identity_verifications_uuid",
        "niam_citizen_identity_verifications",
        ["uuid"],
        unique=True,
    )
    op.create_index(
        "ix_niam_citizen_identity_verifications_verification_id",
        "niam_citizen_identity_verifications",
        ["verification_id"],
        unique=True,
    )
    op.create_index(
        "ix_niam_citizen_identity_verifications_person_id",
        "niam_citizen_identity_verifications",
        ["person_id"],
    )
    op.create_index(
        "ix_niam_citizen_identity_verifications_provider_id",
        "niam_citizen_identity_verifications",
        ["provider_id"],
    )
    op.create_index(
        "ix_niam_citizen_identity_verifications_identifier_type",
        "niam_citizen_identity_verifications",
        ["identifier_type"],
    )
    op.create_index(
        "ix_niam_citizen_identity_verifications_identifier_hash",
        "niam_citizen_identity_verifications",
        ["identifier_hash"],
    )

    # ── Session workspace binding (Phase 7) ─────────────────────────────────
    op.add_column(
        "niam_sessions",
        sa.Column("workspace_id", sa.String(length=26), nullable=True),
    )
    op.add_column(
        "niam_sessions",
        sa.Column("workspace_bound_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_niam_sessions_workspace_id",
        "niam_sessions",
        "niam_workspaces",
        ["workspace_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_niam_sessions_workspace_id", "niam_sessions", ["workspace_id"])


def downgrade() -> None:
    op.drop_index("ix_niam_sessions_workspace_id", table_name="niam_sessions")
    op.drop_constraint("fk_niam_sessions_workspace_id", "niam_sessions", type_="foreignkey")
    op.drop_column("niam_sessions", "workspace_bound_at")
    op.drop_column("niam_sessions", "workspace_id")

    op.drop_table("niam_citizen_identity_verifications")
    op.drop_table("niam_identity_providers")
    op.drop_table("niam_professional_registry")

    op.drop_table("niam_workspace_delegations")
    op.drop_table("niam_workspace_invitations")
    op.drop_table("niam_workspace_teams")
    op.drop_table("niam_workspace_departments")
    op.drop_table("niam_workspace_permission_templates")
    op.drop_table("niam_workspace_members")
    op.drop_table("niam_workspace_roles")
    op.drop_table("niam_workspaces")
