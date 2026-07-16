"""Add MFA, OAuth2, SAML, Service Account, Password Reset tables

Revision ID: 20260716_0015
Revises: 20260716_0014
Create Date: 2026-07-16

Tables:
  - mfa_devices         — TOTP / WebAuthn / FIDO2 authenticator devices
  - mfa_sessions        — MFA step-up session tokens
  - oauth2_clients      — OAuth2 / OIDC client registrations
  - oauth2_tokens       — OAuth2 access, refresh, ID tokens
  - service_accounts    — Machine-to-machine API keys
  - lab_users           — ADD reset_token, reset_token_expires columns
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260716_0015"
down_revision: Union[str, None] = "20260716_0014"


def _has_table(name: str) -> bool:
    conn = op.get_bind()
    return conn.dialect.has_table(conn, name)


def _has_column(table: str, column: str) -> bool:
    conn = op.get_bind()
    if not conn.dialect.has_table(conn, table):
        return False
    insp = sa.inspect(conn)
    cols = [c["name"] for c in insp.get_columns(table)]
    return column in cols


def upgrade() -> None:
    if not _has_table("mfa_devices"):
        op.create_table(
            "mfa_devices",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False, index=True),
            sa.Column("device_type", sa.String(length=30), nullable=False),
            sa.Column("device_name", sa.String(length=100), nullable=True),
            sa.Column("secret", sa.String(length=500), nullable=True),
            sa.Column("credential_id", sa.String(length=500), nullable=True, index=True),
            sa.Column("public_key", sa.Text(), nullable=True),
            sa.Column("sign_count", sa.Integer(), nullable=True, server_default=sa.text("0")),
            sa.Column("transports", sa.String(length=500), nullable=True),
            sa.Column("backup_codes", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.text("true")),
            sa.Column("is_primary", sa.Boolean(), nullable=True, server_default=sa.text("false")),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["lab_users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_table("mfa_sessions"):
        op.create_table(
            "mfa_sessions",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False, index=True),
            sa.Column("session_token", sa.String(length=255), nullable=False, index=True),
            sa.Column("mfa_method", sa.String(length=30), nullable=False),
            sa.Column("is_verified", sa.Boolean(), nullable=True, server_default=sa.text("false")),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["lab_users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("session_token"),
        )

    if not _has_table("oauth2_clients"):
        op.create_table(
            "oauth2_clients",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("client_id", sa.String(length=100), nullable=False, unique=True, index=True),
            sa.Column("client_secret_hash", sa.String(length=255), nullable=True),
            sa.Column("redirect_uris", sa.Text(), nullable=True),
            sa.Column("allowed_scopes", sa.Text(), nullable=True),
            sa.Column("grant_types", sa.Text(), nullable=True),
            sa.Column("response_types", sa.Text(), nullable=True),
            sa.Column("is_confidential", sa.Boolean(), nullable=True, server_default=sa.text("false")),
            sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.text("true")),
            sa.Column("token_endpoint_auth_method", sa.String(length=50), nullable=True, server_default=sa.text("'client_secret_basic'")),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_table("oauth2_tokens"):
        op.create_table(
            "oauth2_tokens",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("client_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("user_id", sa.Integer(), nullable=True, index=True),
            sa.Column("token_type", sa.String(length=20), nullable=False),
            sa.Column("token_hash", sa.String(length=255), nullable=False, unique=True, index=True),
            sa.Column("scope", sa.String(length=500), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("code_challenge", sa.String(length=255), nullable=True),
            sa.Column("code_challenge_method", sa.String(length=10), nullable=True),
            sa.Column("is_revoked", sa.Boolean(), nullable=True, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_table("service_accounts"):
        op.create_table(
            "service_accounts",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("api_key_hash", sa.String(length=255), nullable=False),
            sa.Column("api_key_prefix", sa.String(length=20), nullable=True, index=True),
            sa.Column("roles", sa.Text(), nullable=True),
            sa.Column("scopes", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.text("true")),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    # ── lab_users: password reset columns ──
    if not _has_column("lab_users", "reset_token"):
        op.add_column("lab_users", sa.Column("reset_token", sa.String(length=255), nullable=True, index=True))
    if not _has_column("lab_users", "reset_token_expires"):
        op.add_column("lab_users", sa.Column("reset_token_expires", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_table("service_accounts")
    op.drop_table("oauth2_tokens")
    op.drop_table("oauth2_clients")
    op.drop_table("mfa_sessions")
    op.drop_table("mfa_devices")
    if _has_column("lab_users", "reset_token_expires"):
        op.drop_column("lab_users", "reset_token_expires")
    if _has_column("lab_users", "reset_token"):
        op.drop_column("lab_users", "reset_token")
