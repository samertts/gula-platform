"""Extend account-request lifecycle metadata and governance permissions.

Revision ID: 20260815_0023
Revises: 20260815_0022
"""
from __future__ import annotations

from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import context, op

revision = "20260815_0023"
down_revision = "20260815_0022"
branch_labels = None
depends_on = None

_REQUEST_COLUMNS = (
    ("reviewed_reason_encrypted", sa.String(length=1024)),
    ("verification_method", sa.String(length=50)),
    ("verification_provider", sa.String(length=100)),
    ("verification_reference", sa.String(length=255)),
    ("verified_at", sa.DateTime(timezone=True)),
    ("expires_at", sa.DateTime(timezone=True)),
    ("activation_token_hash", sa.String(length=64)),
    ("activation_token_expires_at", sa.DateTime(timezone=True)),
)

_ACCOUNT_COLUMNS = (
    ("suspended_until", sa.DateTime(timezone=True)),
)

_PERMISSION_ROWS = (
    {
        "id": "ACCTREQ_PERM_0000000000000",
        "uuid": "2a0e4bf2-9e9e-45b4-ae00-000000000001",
        "permission_key": "identity.account_request.manage",
        "name": "Manage account requests",
        "name_ar": "إدارة طلبات الحسابات",
        "description": "Review, approve, reject and expire governed account requests.",
        "resource": "account_request",
        "action": "manage",
        "sensitivity": "critical",
    },
    {
        "id": "ACCTMGMT_PERM_000000000000",
        "uuid": "2a0e4bf2-9e9e-45b4-ae00-000000000002",
        "permission_key": "identity.account.manage",
        "name": "Manage account lifecycle",
        "name_ar": "إدارة دورة حياة الحساب",
        "description": "Suspend, lock, reactivate and deactivate governed accounts.",
        "resource": "account",
        "action": "manage",
        "sensitivity": "critical",
    },
)


def _has_table(table: str) -> bool:
    if context.is_offline_mode():
        return False
    return bool(sa.inspect(op.get_bind()).has_table(table))


def _columns(table: str) -> set[str]:
    if context.is_offline_mode():
        return set()
    return {item["name"] for item in sa.inspect(op.get_bind()).get_columns(table)} if _has_table(table) else set()


def _indexes(table: str) -> set[str]:
    if context.is_offline_mode():
        return set()
    return {item["name"] for item in sa.inspect(op.get_bind()).get_indexes(table)} if _has_table(table) else set()


def upgrade() -> None:
    bind = op.get_bind()
    if _has_table("niam_account_creation_requests"):
        existing_columns = _columns("niam_account_creation_requests")
        for column_name, column_type in _REQUEST_COLUMNS:
            if column_name not in existing_columns:
                op.add_column(
                    "niam_account_creation_requests",
                    sa.Column(column_name, column_type, nullable=True),
                )
        existing_indexes = _indexes("niam_account_creation_requests")
        if "expires_at" in _columns("niam_account_creation_requests") and "ix_niam_account_creation_requests_expires_at" not in existing_indexes:
            op.create_index(
                "ix_niam_account_creation_requests_expires_at",
                "niam_account_creation_requests",
                ["expires_at"],
            )
        if "activation_token_hash" in _columns("niam_account_creation_requests") and "ix_niam_account_creation_requests_activation_token_hash" not in existing_indexes:
            op.create_index(
                "ix_niam_account_creation_requests_activation_token_hash",
                "niam_account_creation_requests",
                ["activation_token_hash"],
            )

    if _has_table("niam_accounts"):
        existing_account_columns = _columns("niam_accounts")
        for column_name, column_type in _ACCOUNT_COLUMNS:
            if column_name not in existing_account_columns:
                op.add_column("niam_accounts", sa.Column(column_name, column_type, nullable=True))

    if _has_table("niam_permissions"):

        now = datetime.now(UTC)
        for row in _PERMISSION_ROWS:
            existing = bind.execute(
                sa.text("SELECT id FROM niam_permissions WHERE permission_key = :permission_key"),
                {"permission_key": row["permission_key"]},
            ).scalar_one_or_none()
            if existing is None:
                bind.execute(
                    sa.text(
                        """INSERT INTO niam_permissions
                        (id, uuid, permission_key, name, name_ar, description, resource, action, sensitivity, status, version, created_at, updated_at)
                        VALUES (:id, :uuid, :permission_key, :name, :name_ar, :description, :resource, :action, :sensitivity, 'active', 1, :created_at, :updated_at)""",
                    ),
                    {
                        **row,
                        "created_at": now,
                        "updated_at": now,
                    },
                )


def downgrade() -> None:
    bind = op.get_bind()
    if _has_table("niam_permissions"):
        for row in _PERMISSION_ROWS:
            permission_id = bind.execute(
                sa.text("SELECT id FROM niam_permissions WHERE permission_key = :permission_key"),
                {"permission_key": row["permission_key"]},
            ).scalar_one_or_none()
            if permission_id is not None:
                if _has_table("niam_role_permissions"):
                    bind.execute(
                        sa.text("DELETE FROM niam_role_permissions WHERE permission_id = :permission_id"),
                        {"permission_id": permission_id},
                    )
                bind.execute(
                    sa.text("DELETE FROM niam_permissions WHERE id = :permission_id"),
                    {"permission_id": permission_id},
                )

    if _has_table("niam_account_creation_requests"):
        existing_indexes = _indexes("niam_account_creation_requests")
        for index_name in (
            "ix_niam_account_creation_requests_activation_token_hash",
            "ix_niam_account_creation_requests_expires_at",
        ):
            if index_name in existing_indexes:
                op.drop_index(index_name, table_name="niam_account_creation_requests")
        existing_columns = _columns("niam_account_creation_requests")
        for column_name, _ in reversed(_REQUEST_COLUMNS):
            if column_name in existing_columns:
                op.drop_column("niam_account_creation_requests", column_name)

    if _has_table("niam_accounts"):
        existing_account_columns = _columns("niam_accounts")
        for column_name, _ in reversed(_ACCOUNT_COLUMNS):
            if column_name in existing_account_columns:
                op.drop_column("niam_accounts", column_name)
