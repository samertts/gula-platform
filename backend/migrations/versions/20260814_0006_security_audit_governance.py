"""IAM Phase 9 security, canonical audit, consent and incidents.

Revision ID: 20260814_0006
Revises: 20260814_0005
"""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256

from alembic import op
import sqlalchemy as sa

revision = "20260814_0006"
down_revision = "20260814_0005"
branch_labels = None
depends_on = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(name: str) -> bool:
    return name in _inspector().get_table_names()


def _has_column(table: str, column: str) -> bool:
    return any(item["name"] == column for item in _inspector().get_columns(table))


def upgrade() -> None:
    bind = op.get_bind()
    now = datetime.now(UTC)

    if _has_table("niam_comp_checks") and not _has_column("niam_comp_checks", "organization_id"):
        op.add_column("niam_comp_checks", sa.Column("organization_id", sa.String(length=26), nullable=True))
        op.create_index("ix_niam_comp_checks_organization_id", "niam_comp_checks", ["organization_id"])

    if _has_table("niam_audit_entries"):
        additions = [
            ("event_type", sa.String(length=120), "'LEGACY'"),
            ("event_version", sa.String(length=20), "'1'"),
            ("category", sa.String(length=40), None),
            ("actor_identity_id", sa.String(length=26), None),
            ("facility_id", sa.String(length=26), None),
            ("department_id", sa.String(length=26), None),
            ("workspace_id", sa.String(length=26), None),
            ("decision", sa.String(length=20), None),
            ("reason_code", sa.String(length=120), None),
            ("request_id", sa.String(length=120), None),
            ("correlation_id", sa.String(length=120), None),
            ("source", sa.String(length=40), None),
            ("data_classification", sa.String(length=30), None),
        ]
        for name, column_type, default in additions:
            if not _has_column("niam_audit_entries", name):
                kwargs = {"nullable": True}
                if default is not None:
                    kwargs["server_default"] = sa.text(default)
                op.add_column("niam_audit_entries", sa.Column(name, column_type, **kwargs))
                op.create_index(f"ix_niam_audit_entries_{name}", "niam_audit_entries", [name])

    if not _has_table("niam_consents"):
        op.create_table(
            "niam_consents",
            sa.Column("id", sa.String(length=26), primary_key=True, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False),
            sa.Column("subject_account_id", sa.String(length=26), nullable=False),
            sa.Column("grantee_account_id", sa.String(length=26), nullable=False),
            sa.Column("purpose", sa.String(length=80), nullable=False),
            sa.Column("scope", sa.JSON(), nullable=False),
            sa.Column("resource_domain", sa.String(length=120), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="ACTIVE"),
            sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("source", sa.String(length=40), nullable=False, server_default="USER_PORTAL"),
            sa.Column("legal_basis", sa.String(length=120), nullable=True),
            sa.Column("created_by", sa.String(length=26), nullable=True),
            sa.Column("supersedes_id", sa.String(length=26), nullable=True),
            sa.Column("reason", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.ForeignKeyConstraint(["subject_account_id"], ["niam_accounts.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["grantee_account_id"], ["niam_accounts.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["created_by"], ["niam_accounts.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["supersedes_id"], ["niam_consents.id"], ondelete="SET NULL"),
            sa.UniqueConstraint(
                "subject_account_id",
                "grantee_account_id",
                "purpose",
                "resource_domain",
                "version",
                name="uq_niam_consent_version",
            ),
        )
        for column in ("subject_account_id", "grantee_account_id", "purpose", "resource_domain", "status", "expires_at", "supersedes_id"):
            op.create_index(f"ix_niam_consents_{column}", "niam_consents", [column])

    if not _has_table("niam_security_incidents"):
        op.create_table(
            "niam_security_incidents",
            sa.Column("id", sa.String(length=26), primary_key=True, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False),
            sa.Column("incident_key", sa.String(length=80), nullable=False),
            sa.Column("severity", sa.String(length=4), nullable=False),
            sa.Column("category", sa.String(length=80), nullable=False),
            sa.Column("organization_id", sa.String(length=26), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="OPEN"),
            sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("reported_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("assigned_to", sa.String(length=26), nullable=True),
            sa.Column("affected_scope", sa.JSON(), nullable=True),
            sa.Column("containment_status", sa.String(length=30), nullable=True),
            sa.Column("resolution", sa.Text(), nullable=True),
            sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_by", sa.String(length=26), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.ForeignKeyConstraint(["organization_id"], ["niam_organizations.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["created_by"], ["niam_accounts.id"], ondelete="RESTRICT"),
            sa.UniqueConstraint("uuid", name="uq_niam_security_incidents_uuid"),
            sa.UniqueConstraint("incident_key", name="uq_niam_security_incidents_key"),
        )
        for column in ("incident_key", "severity", "category", "organization_id", "status", "detected_at", "created_by"):
            op.create_index(f"ix_niam_security_incidents_{column}", "niam_security_incidents", [column])

    # Seed catalog only. No role assignments are created automatically.
    if _has_table("niam_roles") and _has_table("niam_permissions") and _has_table("niam_role_permissions"):
        roles = [
            ("R9AUDITREVIEWER00000001", "audit_reviewer", "Audit Reviewer", "مراجع تدقيق"),
            ("R9SECURITYADMIN00000001", "security_administrator", "Security Administrator", "مسؤول أمن"),
            ("R9MINISTRYAUDITOR000001", "ministry_auditor", "Ministry Auditor", "مدقق وزارة"),
            ("R9ORGADMIN000000000001", "organization_administrator", "Organization Administrator", "مسؤول المنظمة"),
            ("R9COMPLIANCEOFFICER0001", "compliance_officer", "Compliance Officer", "مسؤول الامتثال"),
        ]
        permissions = [
            ("P9AUDITREADSENSITIVE01", "audit.read_sensitive", "Read Sensitive Audit", "قراءة التدقيق الحساس", "critical"),
            ("P9AUDITEXPORT000000001", "audit.export", "Export Audit", "تصدير التدقيق", "critical"),
            ("P9AUDITVERIFY000000001", "audit.verify_integrity", "Verify Audit Integrity", "التحقق من سلامة التدقيق", "critical"),
            ("P9SECINCIDENTREAD00001", "security.incident.read", "Read Security Incidents", "قراءة حوادث الأمن", "high"),
            ("P9SECINCIDENTMANAGE001", "security.incident.manage", "Manage Security Incidents", "إدارة حوادث الأمن", "critical"),
            ("P9ORGREAD000000000001", "organization.read", "Read Organization Administration", "قراءة إدارة المنظمة", "high"),
            ("P9ORGMANAGE00000000001", "organization.manage", "Manage Organization Administration", "إدارة المنظمة", "critical"),
            ("P9SUBMANAGE000000000001", "subscription.manage", "Manage Subscription", "إدارة الاشتراك", "critical"),
            ("P9INTMANAGE000000000001", "integration.manage", "Manage Integrations", "إدارة التكاملات", "critical"),
            ("P9COMPLIANCEREAD00001", "compliance.read", "Read Compliance", "قراءة الامتثال", "high"),
            ("P9COMPLIANCEMANAGE0001", "compliance.manage", "Manage Compliance", "إدارة الامتثال", "critical"),
            ("P9COMPLIANCEREPORT001", "compliance.report", "Generate Compliance Report", "إنشاء تقرير امتثال", "critical"),
        ]
        role_ids: dict[str, str] = {}
        permission_ids: dict[str, str] = {}
        for role_id, role_key, name, name_ar in roles:
            existing = bind.execute(sa.text("SELECT id FROM niam_roles WHERE role_key = :role_key"), {"role_key": role_key}).scalar_one_or_none()
            if existing is None:
                bind.execute(
                    sa.text("""INSERT INTO niam_roles (id, uuid, role_key, name, name_ar, description, scope_type, status, is_system, version, created_at, updated_at)
                    VALUES (:id, :uuid, :role_key, :name, :name_ar, :description, 'organization', 'active', true, 1, :created_at, :updated_at)"""),
                    {"id": role_id, "uuid": f"{role_key}-phase9", "role_key": role_key, "name": name, "name_ar": name_ar, "description": "Explicitly provisioned Phase 9 security role.", "created_at": now, "updated_at": now},
                )
                existing = role_id
            role_ids[role_key] = existing
        for permission_id, permission_key, name, name_ar, sensitivity in permissions:
            existing = bind.execute(sa.text("SELECT id FROM niam_permissions WHERE permission_key = :permission_key"), {"permission_key": permission_key}).scalar_one_or_none()
            if existing is None:
                bind.execute(
                    sa.text("""INSERT INTO niam_permissions (id, uuid, permission_key, name, name_ar, description, resource, action, sensitivity, status, version, created_at, updated_at)
                    VALUES (:id, :uuid, :permission_key, :name, :name_ar, :description, :resource, :action, :sensitivity, 'active', 1, :created_at, :updated_at)"""),
                    {"id": permission_id, "uuid": f"{permission_key}-phase9", "permission_key": permission_key, "name": name, "name_ar": name_ar, "description": "Phase 9 security capability; explicit assignment required.", "resource": permission_key.split(".")[0], "action": permission_key.split(".", 1)[1], "sensitivity": sensitivity, "created_at": now, "updated_at": now},
                )
                existing = permission_id
            permission_ids[permission_key] = existing
        # Repair Phase 7 over-grant: organization_manager must not automatically read audit data.
        bind.execute(
            sa.text("""DELETE FROM niam_role_permissions
            WHERE role_id = (SELECT id FROM niam_roles WHERE role_key = 'organization_manager')
              AND permission_id = (SELECT id FROM niam_permissions WHERE permission_key = 'audit.read')"""),
        )
        relations = {
            "audit_reviewer": ["audit.read"],
            "security_administrator": ["audit.read", "audit.read_sensitive", "audit.verify_integrity", "security.incident.read", "security.incident.manage"],
            "ministry_auditor": ["audit.read", "audit.read_sensitive", "audit.export", "audit.verify_integrity"],
            "organization_administrator": ["organization.read", "organization.manage", "subscription.manage", "integration.manage"],
            "compliance_officer": ["compliance.read", "compliance.manage", "compliance.report"],
        }
        for role_key, permission_keys in relations.items():
            role_id = role_ids[role_key]
            for permission_key in permission_keys:
                permission_id = permission_ids.get(permission_key) or bind.execute(sa.text("SELECT id FROM niam_permissions WHERE permission_key = :permission_key"), {"permission_key": permission_key}).scalar_one()
                relation_exists = bind.execute(sa.text("SELECT id FROM niam_role_permissions WHERE role_id = :role_id AND permission_id = :permission_id"), {"role_id": role_id, "permission_id": permission_id}).scalar_one_or_none()
                if relation_exists is None:
                    bind.execute(
                        sa.text("""INSERT INTO niam_role_permissions (id, role_id, permission_id, status, created_at, updated_at)
                        VALUES (:id, :role_id, :permission_id, 'active', :created_at, :updated_at)"""),
                        {
                            "id": f"RP9{sha256(f'{role_key}:{permission_key}'.encode()).hexdigest().upper()[:20]}",
                            "role_id": role_id,
                            "permission_id": permission_id,
                            "created_at": now,
                            "updated_at": now,
                        },
                    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "niam_security_incidents" in inspector.get_table_names():
        # DROP TABLE removes its owned indexes and UNIQUE constraints together.
        op.drop_table("niam_security_incidents")
    if "niam_consents" in inspector.get_table_names():
        # DROP TABLE removes its owned indexes and UNIQUE constraints together.
        op.drop_table("niam_consents")
    if "niam_comp_checks" in inspector.get_table_names() and _has_column("niam_comp_checks", "organization_id"):
        if bind.dialect.name == "sqlite":
            op.drop_index("ix_niam_comp_checks_organization_id", table_name="niam_comp_checks")
            with op.batch_alter_table("niam_comp_checks", recreate="always") as batch_op:
                batch_op.drop_column("organization_id")
        else:
            op.drop_index("ix_niam_comp_checks_organization_id", table_name="niam_comp_checks")
            op.drop_column("niam_comp_checks", "organization_id")
    if "niam_audit_entries" in inspector.get_table_names():
        bind_name = bind.dialect.name
        columns = [
            "data_classification", "source", "correlation_id", "request_id", "reason_code", "decision",
            "workspace_id", "department_id", "facility_id", "actor_identity_id", "category", "event_version", "event_type",
        ]
        index_names = {index["name"] for index in inspector.get_indexes("niam_audit_entries")}
        # Drop indexes before a SQLite batch rebuild so they are not reflected
        # and recreated with references to columns being removed.
        for column in columns:
            index_name = f"ix_niam_audit_entries_{column}"
            if index_name in index_names:
                op.drop_index(index_name, table_name="niam_audit_entries")
        if bind_name == "sqlite":
            with op.batch_alter_table("niam_audit_entries", recreate="always") as batch_op:
                for column in columns:
                    if _has_column("niam_audit_entries", column):
                        batch_op.drop_column(column)
        else:
            for column in columns:
                if _has_column("niam_audit_entries", column):
                    op.drop_column("niam_audit_entries", column)
