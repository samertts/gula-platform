"""Create National Ecosystem partner tables.

Creates ecosystem partner tables for the National Digital Health Ecosystem:
  - ecosystem_partners: Partner registry
  - ecosystem_partner_credentials: API keys and credentials
  - ecosystem_partner_certificates: mTLS certificates
  - ecosystem_partner_rate_limits: Per-endpoint rate limiting
  - ecosystem_partner_audit_logs: Partner activity audit trail
  - ecosystem_partner_agreements: Partner legal agreements

Revision ID: 20260715_0001
Revises: 20260714_0001
Create Date: 2026-07-15
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import inspect

revision: str = "20260715_0001"
down_revision: Union[str, None] = "20260714_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def _index_exists(idx_name: str) -> bool:
    insp = inspect(op.get_bind())
    for table in insp.get_table_names():
        for idx in insp.get_indexes(table):
            if idx["name"] == idx_name:
                return True
    return False


def upgrade() -> None:
    if not _table_exists("ecosystem_partners"):
        op.create_table(
            "ecosystem_partners",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("name", sa.String(255), nullable=False, index=True),
            sa.Column("org_type", sa.String(100), nullable=False),
            sa.Column("contact_name", sa.String(255), nullable=True),
            sa.Column("contact_email", sa.String(255), nullable=True, index=True),
            sa.Column("contact_phone", sa.String(50), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="active"),
            sa.Column("tier", sa.String(20), nullable=False, server_default="bronze"),
            sa.Column("agreement_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("agreement_version", sa.String(20), nullable=True),
            sa.Column("api_quota", sa.Integer, nullable=False, server_default="1000"),
            sa.Column("rate_limit", sa.Integer, nullable=False, server_default="60"),
            sa.Column("created_by", sa.Integer, nullable=True),
            sa.Column("metadata", JSONB, nullable=True, server_default=sa.text("'{}'::jsonb")),
            sa.Column("fhir_id", sa.String(64), nullable=True, index=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("version", sa.Integer, nullable=False, server_default="1"),
            sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="false"),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.func.now()),
        )

    if not _table_exists("ecosystem_partner_credentials"):
        op.create_table(
            "ecosystem_partner_credentials",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("partner_id", sa.String(26),
                      sa.ForeignKey("ecosystem_partners.id"), nullable=False, index=True),
            sa.Column("credential_type", sa.String(50), nullable=False),
            sa.Column("credential_name", sa.String(255), nullable=False),
            sa.Column("credential_value", sa.Text, nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="active"),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.func.now()),
        )

    if not _table_exists("ecosystem_partner_certificates"):
        op.create_table(
            "ecosystem_partner_certificates",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("partner_id", sa.String(26),
                      sa.ForeignKey("ecosystem_partners.id"), nullable=False, index=True),
            sa.Column("certificate_pem", sa.Text, nullable=False),
            sa.Column("certificate_serial", sa.String(255), nullable=True, index=True),
            sa.Column("issuer", sa.String(255), nullable=True),
            sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
            sa.Column("valid_to", sa.DateTime(timezone=True), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="active"),
            sa.Column("fingerprint", sa.String(255), nullable=True, index=True),
            sa.Column("fhir_id", sa.String(64), nullable=True, index=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("version", sa.Integer, nullable=False, server_default="1"),
            sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="false"),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.func.now()),
        )

    if not _table_exists("ecosystem_partner_rate_limits"):
        op.create_table(
            "ecosystem_partner_rate_limits",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("partner_id", sa.String(26),
                      sa.ForeignKey("ecosystem_partners.id"), nullable=False, index=True),
            sa.Column("endpoint_pattern", sa.String(500), nullable=False),
            sa.Column("requests_per_minute", sa.Integer, nullable=False, server_default="60"),
            sa.Column("requests_per_hour", sa.Integer, nullable=False, server_default="1000"),
            sa.Column("requests_per_day", sa.Integer, nullable=False, server_default="10000"),
            sa.Column("concurrent_limit", sa.Integer, nullable=False, server_default="10"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.func.now()),
        )

    if not _table_exists("ecosystem_partner_audit_logs"):
        op.create_table(
            "ecosystem_partner_audit_logs",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("partner_id", sa.String(26),
                      sa.ForeignKey("ecosystem_partners.id"), nullable=False, index=True),
            sa.Column("action", sa.String(100), nullable=False),
            sa.Column("resource", sa.String(255), nullable=True),
            sa.Column("details", JSONB, nullable=True),
            sa.Column("ip_address", sa.String(45), nullable=True),
            sa.Column("user_agent", sa.String(500), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="success"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.func.now(), index=True),
        )

    if not _table_exists("ecosystem_partner_agreements"):
        op.create_table(
            "ecosystem_partner_agreements",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("partner_id", sa.String(26),
                      sa.ForeignKey("ecosystem_partners.id"), nullable=False, index=True),
            sa.Column("agreement_type", sa.String(50), nullable=False),
            sa.Column("version", sa.String(20), nullable=False),
            sa.Column("content", sa.Text, nullable=False),
            sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("accepted_by", sa.String(255), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("fhir_id", sa.String(64), nullable=True, index=True),
            sa.Column("fhir_resource_type", sa.String(32), nullable=True),
            sa.Column("version", sa.Integer, nullable=False, server_default="1"),
            sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="false"),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.func.now()),
        )


def downgrade() -> None:
    op.drop_table("ecosystem_partner_agreements")
    op.drop_table("ecosystem_partner_audit_logs")
    op.drop_table("ecosystem_partner_rate_limits")
    op.drop_table("ecosystem_partner_certificates")
    op.drop_table("ecosystem_partner_credentials")
    op.drop_table("ecosystem_partners")
