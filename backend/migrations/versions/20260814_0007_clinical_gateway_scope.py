"""Phase 10-B reviewed NIAM scope mapping and clinical read permissions.

Revision ID: 20260814_0007
Revises: 20260814_0006
"""

from __future__ import annotations

from datetime import UTC, datetime
from alembic import op
import sqlalchemy as sa

revision = "20260814_0007"
down_revision = "20260814_0006"
branch_labels = None
depends_on = None

_TABLE = "clinical_lab_facility_bindings"


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(name: str) -> bool:
    return name in _inspector().get_table_names()


def _has_column(table: str, name: str) -> bool:
    return any(item["name"] == name for item in _inspector().get_columns(table))


def upgrade() -> None:
    bind = op.get_bind()
    now = datetime.now(UTC)

    if _has_table(_TABLE):
        additions = [
            (
                "niam_organization_id",
                sa.String(length=26),
                sa.ForeignKey("niam_organizations.id", ondelete="RESTRICT"),
            ),
            (
                "niam_facility_id",
                sa.String(length=26),
                sa.ForeignKey("niam_admin_facilities.id", ondelete="RESTRICT"),
            ),
        ]
        for name, column_type, foreign_key in additions:
            if not _has_column(_TABLE, name):
                op.add_column(_TABLE, sa.Column(name, column_type, foreign_key, nullable=True))
                op.create_index(f"ix_{_TABLE}_{name}", _TABLE, [name])

    if _has_table("niam_permissions"):
        permissions = [
            ("P10PATIENTSREAD0000001", "patients.read", "Read Clinical Patients", "قراءة المرضى السريرية", "high"),
            ("P10ORDERSREAD00000001", "orders.read", "Read Clinical Orders", "قراءة الطلبات السريرية", "high"),
        ]
        for permission_id, permission_key, name, name_ar, sensitivity in permissions:
            existing = bind.execute(
                sa.text("SELECT id FROM niam_permissions WHERE permission_key = :permission_key"),
                {"permission_key": permission_key},
            ).scalar_one_or_none()
            if existing is None:
                bind.execute(
                    sa.text("""INSERT INTO niam_permissions
                    (id, uuid, permission_key, name, name_ar, description, resource, action, sensitivity, status, version, created_at, updated_at)
                    VALUES (:id, :uuid, :permission_key, :name, :name_ar, :description, :resource, :action, :sensitivity, 'active', 1, :created_at, :updated_at)"""),
                    {
                        "id": permission_id,
                        "uuid": f"{permission_key}-phase10b",
                        "permission_key": permission_key,
                        "name": name,
                        "name_ar": name_ar,
                        "description": "Explicit P0 canonical clinical read capability; no role assignment is created automatically.",
                        "resource": permission_key.split(".", 1)[0],
                        "action": permission_key.split(".", 1)[1],
                        "sensitivity": sensitivity,
                        "created_at": now,
                        "updated_at": now,
                    },
                )


def downgrade() -> None:
    bind = op.get_bind()
    if _has_table("niam_permissions"):
        for permission_key in ("patients.read", "orders.read"):
            permission_id = bind.execute(
                sa.text("SELECT id FROM niam_permissions WHERE permission_key = :permission_key"),
                {"permission_key": permission_key},
            ).scalar_one_or_none()
            if permission_id is not None:
                bind.execute(
                    sa.text("DELETE FROM niam_role_permissions WHERE permission_id = :permission_id"),
                    {"permission_id": permission_id},
                )
                bind.execute(
                    sa.text("DELETE FROM niam_permissions WHERE id = :permission_id"),
                    {"permission_id": permission_id},
                )
    if _has_table(_TABLE):
        inspector = _inspector()
        bind_name = bind.dialect.name
        columns = ["niam_facility_id", "niam_organization_id"]
        if bind_name == "sqlite":
            with op.batch_alter_table(_TABLE) as batch_op:
                for name in columns:
                    if _has_column(_TABLE, name):
                        batch_op.drop_column(name)
        else:
            for name in columns:
                if _has_column(_TABLE, name):
                    index_name = f"ix_{_TABLE}_{name}"
                    if index_name in {index["name"] for index in inspector.get_indexes(_TABLE)}:
                        op.drop_index(index_name, table_name=_TABLE)
                    op.drop_column(_TABLE, name)
