"""Unify professional identity: civil professional registry, identity providers,
and separable professional authorizations.

Revision ID: 20261114_0004
Revises: 20261114_0003
Create Date: 2026-11-14

Carried forward from local revision 20260805_0002_stable_identity_platform
(professional registry + identity providers) and
20260810_0001_professional_authorizations.

The local workspace platform in 20260805_0002 is intentionally NOT replayed:
origin/main supersedes it with `niam_workspace_contexts`, `niam_memberships`,
`niam_roles`/`niam_permissions` (revisions 20260814_0003..0005) and
`verification_records` (20260814_0001). See GOVERNANCE/MIGRATION_RECONCILIATION_MATRIX.md.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "20261114_0004"
down_revision = "20261114_0003"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    return name in inspect(op.get_bind()).get_table_names()


def upgrade() -> None:
    if not _has_table("niam_professional_registry"):
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
            sa.ForeignKeyConstraint(
                ["issuing_authority_id"],
                ["niam_identity_authorities.id"],
                ondelete="SET NULL",
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_niam_professional_registry_uuid", "niam_professional_registry", ["uuid"], unique=True)
        op.create_index(
            "ix_niam_professional_registry_registry_id",
            "niam_professional_registry",
            ["registry_id"],
            unique=True,
        )
        op.create_index(
            "ix_niam_professional_registry_registration_number",
            "niam_professional_registry",
            ["registration_number"],
            unique=True,
        )
        op.create_index("ix_niam_professional_registry_person_id", "niam_professional_registry", ["person_id"])
        op.create_index("ix_niam_professional_registry_identity_id", "niam_professional_registry", ["identity_id"])
        op.create_index("ix_niam_professional_registry_profession", "niam_professional_registry", ["profession"])
        op.create_index(
            "ix_niam_professional_registry_issuing_country",
            "niam_professional_registry",
            ["issuing_country"],
        )
        op.create_index("ix_niam_professional_registry_status", "niam_professional_registry", ["status"])

    if not _has_table("niam_identity_providers"):
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
            "ix_niam_identity_providers_provider_id",
            "niam_identity_providers",
            ["provider_id"],
            unique=True,
        )
        op.create_index("ix_niam_identity_providers_provider_type", "niam_identity_providers", ["provider_type"])
        op.create_index("ix_niam_identity_providers_country", "niam_identity_providers", ["country"])
        op.create_index("ix_niam_identity_providers_status", "niam_identity_providers", ["status"])

    if not _has_table("niam_professional_authorizations"):
        op.create_table(
            "niam_professional_authorizations",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("uuid", sa.String(length=36), nullable=False),
            sa.Column("authorization_id", sa.String(length=100), nullable=False),
            sa.Column("registry_id", sa.String(length=26), nullable=False),
            sa.Column("person_id", sa.String(length=26), nullable=False),
            sa.Column("profession", sa.String(length=50), nullable=False),
            sa.Column("scope_type", sa.String(length=30), nullable=False),
            sa.Column("scope_id", sa.String(length=26), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("status_reason", sa.Text(), nullable=True),
            sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("granted_by", sa.String(length=100), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.ForeignKeyConstraint(["person_id"], ["niam_persons.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(
                ["registry_id"], ["niam_professional_registry.id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_niam_professional_authorizations_uuid",
            "niam_professional_authorizations",
            ["uuid"],
            unique=True,
        )
        op.create_index(
            "ix_niam_professional_authorizations_authorization_id",
            "niam_professional_authorizations",
            ["authorization_id"],
            unique=True,
        )
        op.create_index(
            "ix_niam_professional_authorizations_registry_id",
            "niam_professional_authorizations",
            ["registry_id"],
        )
        op.create_index(
            "ix_niam_professional_authorizations_person_id",
            "niam_professional_authorizations",
            ["person_id"],
        )
        op.create_index(
            "ix_niam_professional_authorizations_profession",
            "niam_professional_authorizations",
            ["profession"],
        )
        op.create_index(
            "ix_niam_professional_authorizations_scope_type",
            "niam_professional_authorizations",
            ["scope_type"],
        )
        op.create_index(
            "ix_niam_professional_authorizations_scope_id",
            "niam_professional_authorizations",
            ["scope_id"],
        )
        op.create_index(
            "ix_niam_professional_authorizations_status",
            "niam_professional_authorizations",
            ["status"],
        )


def downgrade() -> None:
    for table in (
        "niam_professional_authorizations",
        "niam_identity_providers",
        "niam_professional_registry",
    ):
        if _has_table(table):
            op.drop_table(table)
