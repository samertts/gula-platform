"""PROGRAM-STABLE-004: Domain Platform Framework — domain registrations,
instances, versions, contracts, lifecycle events, workspace bindings.

Revision ID: 20260806_0001
Revises: 20260805_0002
Create Date: 2026-08-06
"""

import sqlalchemy as sa
from alembic import op

revision = "20260806_0001"
down_revision = "20260805_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Domain registrations (Phase 1/5) ────────────────────────────────────
    op.create_table(
        "niam_domain_registrations",
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
        sa.Column("domain_code", sa.String(length=50), nullable=False),
        sa.Column("name_en", sa.String(length=300), nullable=False),
        sa.Column("name_ar", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.String(length=30), nullable=False),
        sa.Column("workspace_type", sa.String(length=50), nullable=False),
        sa.Column("lifecycle_state", sa.String(length=20), nullable=False),
        sa.Column("blueprint", sa.JSON(), nullable=False),
        sa.Column("contracts", sa.JSON(), nullable=True),
        sa.Column("shared_core_usage", sa.JSON(), nullable=True),
        sa.Column("certification", sa.JSON(), nullable=True),
        sa.Column("settings", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_niam_domain_registrations_uuid", "niam_domain_registrations", ["uuid"], unique=True)
    op.create_index(
        "ix_niam_domain_registrations_domain_code",
        "niam_domain_registrations",
        ["domain_code"],
        unique=True,
    )
    op.create_index(
        "ix_niam_domain_registrations_workspace_type",
        "niam_domain_registrations",
        ["workspace_type"],
    )
    op.create_index(
        "ix_niam_domain_registrations_lifecycle_state",
        "niam_domain_registrations",
        ["lifecycle_state"],
    )

    # ── Domain instances (Phase 5: independent deployability) ──────────────
    op.create_table(
        "niam_domain_instances",
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
        sa.Column("instance_id", sa.String(length=100), nullable=False),
        sa.Column("domain_id", sa.String(length=26), nullable=False),
        sa.Column("environment", sa.String(length=50), nullable=False),
        sa.Column("version", sa.String(length=30), nullable=False),
        sa.Column("state", sa.String(length=20), nullable=False),
        sa.Column("deployed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("health", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["domain_id"], ["niam_domain_registrations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_niam_domain_instances_uuid", "niam_domain_instances", ["uuid"], unique=True)
    op.create_index("ix_niam_domain_instances_instance_id", "niam_domain_instances", ["instance_id"], unique=True)
    op.create_index("ix_niam_domain_instances_domain_id", "niam_domain_instances", ["domain_id"])

    # ── Domain versions (Phase 5: independent versioning) ───────────────────
    op.create_table(
        "niam_domain_versions",
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
        sa.Column("domain_id", sa.String(length=26), nullable=False),
        sa.Column("version", sa.String(length=30), nullable=False),
        sa.Column("semver", sa.String(length=30), nullable=False),
        sa.Column("certified", sa.Boolean(), nullable=False),
        sa.Column("compatibility", sa.JSON(), nullable=True),
        sa.Column("changelog", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["domain_id"], ["niam_domain_registrations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_niam_domain_versions_uuid", "niam_domain_versions", ["uuid"], unique=True)
    op.create_index("ix_niam_domain_versions_domain_id", "niam_domain_versions", ["domain_id"])

    # ── Cross-domain contracts (Phase 4) ────────────────────────────────────
    op.create_table(
        "niam_domain_contracts",
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
        sa.Column("contract_id", sa.String(length=100), nullable=False),
        sa.Column("provider_domain_id", sa.String(length=26), nullable=False),
        sa.Column("consumer_domain_id", sa.String(length=26), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("version", sa.String(length=30), nullable=False),
        sa.Column("endpoint", sa.String(length=300), nullable=False),
        sa.Column("documentation_url", sa.String(length=300), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["consumer_domain_id"], ["niam_domain_registrations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["provider_domain_id"], ["niam_domain_registrations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_niam_domain_contracts_uuid", "niam_domain_contracts", ["uuid"], unique=True)
    op.create_index("ix_niam_domain_contracts_contract_id", "niam_domain_contracts", ["contract_id"], unique=True)
    op.create_index("ix_niam_domain_contracts_provider_domain_id", "niam_domain_contracts", ["provider_domain_id"])
    op.create_index("ix_niam_domain_contracts_consumer_domain_id", "niam_domain_contracts", ["consumer_domain_id"])

    # ── Lifecycle events (Phase 5 audit trail) ──────────────────────────────
    op.create_table(
        "niam_domain_lifecycle_events",
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
        sa.Column("domain_id", sa.String(length=26), nullable=False),
        sa.Column("action", sa.String(length=30), nullable=False),
        sa.Column("from_state", sa.String(length=20), nullable=False),
        sa.Column("to_state", sa.String(length=20), nullable=False),
        sa.Column("version", sa.String(length=30), nullable=True),
        sa.ForeignKeyConstraint(["domain_id"], ["niam_domain_registrations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_niam_domain_lifecycle_events_uuid", "niam_domain_lifecycle_events", ["uuid"], unique=True)
    op.create_index("ix_niam_domain_lifecycle_events_domain_id", "niam_domain_lifecycle_events", ["domain_id"])

    # ── Workspace bindings (Phase 6) ────────────────────────────────────────
    op.create_table(
        "niam_domain_workspace_bindings",
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
        sa.Column("domain_id", sa.String(length=26), nullable=False),
        sa.Column("workspace_type", sa.String(length=50), nullable=False),
        sa.Column("ui", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["domain_id"], ["niam_domain_registrations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_niam_domain_workspace_bindings_uuid", "niam_domain_workspace_bindings", ["uuid"], unique=True)
    op.create_index(
        "ix_niam_domain_workspace_bindings_workspace_type",
        "niam_domain_workspace_bindings",
        ["workspace_type"],
    )


def downgrade() -> None:
    op.drop_table("niam_domain_workspace_bindings")
    op.drop_table("niam_domain_lifecycle_events")
    op.drop_table("niam_domain_contracts")
    op.drop_table("niam_domain_versions")
    op.drop_table("niam_domain_instances")
    op.drop_table("niam_domain_registrations")
