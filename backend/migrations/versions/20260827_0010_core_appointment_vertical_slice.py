"""Core appointment vertical slice: additive canonical scheduling tables.

This migration is deliberately non-destructive. Legacy National Scheduling tables
remain untouched and are reconciled through a later shadow-read/switch plan.
"""

from __future__ import annotations

from datetime import UTC, datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20260827_0010"
down_revision = "20260825_0009"
branch_labels = None
depends_on = None


def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def _seed_appointment_permissions() -> None:
    bind = op.get_bind()
    now = datetime.now(UTC)
    permission_rows = (
        {
            "id": "P10APPTREQUEST00000000001",
            "uuid": "p10-appointment-request-0001",
            "permission_key": "appointment.request",
            "name": "Request Appointment",
            "name_ar": "طلب موعد",
            "description": "Request an appointment for the authenticated person's active scope.",
            "resource": "appointment",
            "action": "request",
            "sensitivity": "high",
            "status": "active",
            "version": 1,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": "P10APPTCONFIRM00000000001",
            "uuid": "p10-appointment-confirm-0001",
            "permission_key": "appointment.confirm",
            "name": "Confirm Appointment",
            "name_ar": "تأكيد موعد",
            "description": "Confirm an appointment inside an authorized workspace scope.",
            "resource": "appointment",
            "action": "confirm",
            "sensitivity": "high",
            "status": "active",
            "version": 1,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": "P10APPTSLOTMANAGE00000001",
            "uuid": "p10-appointment-slot-manage-01",
            "permission_key": "appointment.slot.manage",
            "name": "Manage Appointment Slots",
            "name_ar": "إدارة فترات المواعيد",
            "description": "Create appointment slots inside an authorized workspace scope.",
            "resource": "appointment_slot",
            "action": "manage",
            "sensitivity": "high",
            "status": "active",
            "version": 1,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": "P10APPTREAD000000000001",
            "uuid": "p10-appointment-read-00001",
            "permission_key": "appointment.read",
            "name": "Read Appointments",
            "name_ar": "قراءة المواعيد",
            "description": "Read appointments inside an authorized workspace scope.",
            "resource": "appointment",
            "action": "read",
            "sensitivity": "high",
            "status": "active",
            "version": 1,
            "created_at": now,
            "updated_at": now,
        },
    )
    for row in permission_rows:
        exists = bind.execute(
            sa.text("SELECT 1 FROM niam_permissions WHERE permission_key = :permission_key"),
            {"permission_key": row["permission_key"]},
        ).scalar()
        if not exists:
            bind.execute(
                sa.text(
                    "INSERT INTO niam_permissions "
                    "(id, uuid, permission_key, name, name_ar, description, resource, action, sensitivity, status, version, created_at, updated_at) "
                    "VALUES (:id, :uuid, :permission_key, :name, :name_ar, :description, :resource, :action, :sensitivity, :status, :version, :created_at, :updated_at)",
                ),
                row,
            )


def upgrade() -> None:
    if not _table_exists("core_appointment_slots"):
        op.create_table(
            "core_appointment_slots",
            sa.Column("id", sa.String(length=26), primary_key=True),
            sa.Column("organization_id", sa.String(length=26), sa.ForeignKey("niam_organizations.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("facility_id", sa.String(length=26), sa.ForeignKey("niam_admin_facilities.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("workspace_id", sa.String(length=26), sa.ForeignKey("niam_workspaces.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("provider_account_id", sa.String(length=26), sa.ForeignKey("niam_accounts.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("service_code", sa.String(length=120), nullable=False),
            sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("status", sa.String(length=24), nullable=False, server_default="AVAILABLE"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("workspace_id", "provider_account_id", "starts_at", "ends_at", name="uq_core_appointment_slot_provider_window"),
            sa.CheckConstraint("ends_at > starts_at", name="ck_core_appointment_slot_positive_window"),
            sa.CheckConstraint("status IN ('AVAILABLE','BOOKED','BLOCKED')", name="ck_core_appointment_slot_status"),
        )
        op.create_index("ix_core_appointment_slots_organization_id", "core_appointment_slots", ["organization_id"])
        op.create_index("ix_core_appointment_slots_facility_id", "core_appointment_slots", ["facility_id"])
        op.create_index("ix_core_appointment_slots_workspace_id", "core_appointment_slots", ["workspace_id"])
        op.create_index("ix_core_appointment_slots_provider_account_id", "core_appointment_slots", ["provider_account_id"])
        op.create_index("ix_core_appointment_slots_starts_at", "core_appointment_slots", ["starts_at"])
        op.create_index("ix_core_appointment_slots_status", "core_appointment_slots", ["status"])
        op.create_index("ix_core_appointment_slot_scope_time", "core_appointment_slots", ["organization_id", "facility_id", "workspace_id", "starts_at"])

    if not _table_exists("core_appointments"):
        op.create_table(
            "core_appointments",
            sa.Column("id", sa.String(length=26), primary_key=True),
            sa.Column("patient_person_id", sa.String(length=26), sa.ForeignKey("niam_persons.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("requester_account_id", sa.String(length=26), sa.ForeignKey("niam_accounts.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("provider_account_id", sa.String(length=26), sa.ForeignKey("niam_accounts.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("organization_id", sa.String(length=26), sa.ForeignKey("niam_organizations.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("facility_id", sa.String(length=26), sa.ForeignKey("niam_admin_facilities.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("workspace_id", sa.String(length=26), sa.ForeignKey("niam_workspaces.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("slot_id", sa.String(length=26), sa.ForeignKey("core_appointment_slots.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("service_code", sa.String(length=120), nullable=False),
            sa.Column("purpose", sa.String(length=40), nullable=False, server_default="TREATMENT"),
            sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("state", sa.String(length=24), nullable=False, server_default="REQUESTED"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("slot_id", name="uq_core_appointment_slot_id"),
            sa.CheckConstraint("ends_at > starts_at", name="ck_core_appointment_positive_window"),
            sa.CheckConstraint(
                "state IN ('REQUESTED','CONFIRMED','CHECKED_IN','IN_PROGRESS','COMPLETED','CANCELLED','NO_SHOW','RESCHEDULED','EXPIRED')",
                name="ck_core_appointment_state",
            ),
        )
        for column in (
            "patient_person_id",
            "requester_account_id",
            "provider_account_id",
            "organization_id",
            "facility_id",
            "workspace_id",
            "slot_id",
            "state",
        ):
            op.create_index(f"ix_core_appointments_{column}", "core_appointments", [column])
        op.create_index("ix_core_appointment_patient_scope", "core_appointments", ["patient_person_id", "organization_id", "workspace_id", "created_at"])
        op.create_index("ix_core_appointment_provider_scope", "core_appointments", ["provider_account_id", "organization_id", "workspace_id", "created_at"])

    if not _table_exists("core_appointment_idempotency"):
        op.create_table(
            "core_appointment_idempotency",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("actor_account_id", sa.String(length=26), sa.ForeignKey("niam_accounts.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("operation", sa.String(length=80), nullable=False),
            sa.Column("idempotency_key", sa.String(length=128), nullable=False),
            sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
            # The operation identifies whether resource_id is a slot or appointment.
            sa.Column("resource_id", sa.String(length=26), nullable=True),
            sa.Column("status", sa.String(length=24), nullable=False, server_default="CLAIMED"),
            sa.Column("response_body", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("actor_account_id", "operation", "idempotency_key", name="uq_core_appointment_idem_actor_op_key"),
            sa.CheckConstraint("status IN ('CLAIMED','COMPLETED','REJECTED')", name="ck_core_appointment_idem_status"),
        )
        op.create_index("ix_core_appointment_idempotency_actor_account_id", "core_appointment_idempotency", ["actor_account_id"])
        op.create_index("ix_core_appointment_idempotency_operation", "core_appointment_idempotency", ["operation"])
        op.create_index("ix_core_appointment_idempotency_resource_id", "core_appointment_idempotency", ["resource_id"])
        op.create_index("ix_core_appointment_idem_lookup", "core_appointment_idempotency", ["actor_account_id", "operation", "created_at"])

    _seed_appointment_permissions()


def downgrade() -> None:
    if _table_exists("core_appointment_idempotency"):
        op.drop_table("core_appointment_idempotency")
    if _table_exists("core_appointments"):
        op.drop_table("core_appointments")
    if _table_exists("core_appointment_slots"):
        op.drop_table("core_appointment_slots")

    # Permission catalog rows are shared and may predate this revision. Leave
    # them intact on downgrade; removing them would be destructive when the
    # same keys are referenced by another deployment or seed source.
