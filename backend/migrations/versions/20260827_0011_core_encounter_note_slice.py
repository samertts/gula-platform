"""Add canonical check-in, encounter, queue and clinical-note slice.

Revision ID: 20260827_0011
Revises: 20260827_0010
"""

from datetime import UTC, datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20260827_0011"
down_revision = "20260827_0010"
branch_labels = None
depends_on = None


def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def _seed_permissions() -> None:
    bind = op.get_bind()
    if not _table_exists("niam_permissions"):
        return
    now = datetime.now(UTC)
    rows = (
        ("P11ENCCHECKIN000000000001", "p11-encounter-checkin-01", "encounter.checkin", "Check in appointment", "تسجيل حضور الموعد", "encounter", "checkin"),
        ("P11ENCMANAGE0000000000001", "p11-encounter-manage-01", "encounter.manage", "Manage encounter", "إدارة الزيارة السريرية", "encounter", "manage"),
        ("P11ENCREAD00000000000001", "p11-encounter-read-01", "encounter.read", "Read encounter", "قراءة الزيارة السريرية", "encounter", "read"),
        ("P11NOTEWRITE0000000000001", "p11-note-write-01", "clinical.note.write", "Write clinical note", "كتابة الملاحظة السريرية", "clinical_note", "write"),
        ("P11NOTESIGN00000000000001", "p11-note-sign-01", "clinical.note.sign", "Sign clinical note", "توقيع الملاحظة السريرية", "clinical_note", "sign"),
        ("P11NOTEAMEND0000000000001", "p11-note-amend-01", "clinical.note.amend", "Amend clinical note", "تعديل الملاحظة السريرية", "clinical_note", "amend"),
    )
    for row in rows:
        exists = bind.execute(sa.text("SELECT 1 FROM niam_permissions WHERE permission_key = :permission_key"), {"permission_key": row[2]}).scalar()
        if not exists:
            bind.execute(
                sa.text(
                    "INSERT INTO niam_permissions "
                    "(id, uuid, permission_key, name, name_ar, description, resource, action, sensitivity, status, version, created_at, updated_at) "
                    "VALUES (:id, :uuid, :permission_key, :name, :name_ar, :description, :resource, :action, 'high', 'active', 1, :created_at, :updated_at)"
                ),
                {"id": row[0], "uuid": row[1], "permission_key": row[2], "name": row[3], "name_ar": row[4], "description": row[3], "resource": row[5], "action": row[6], "created_at": now, "updated_at": now},
            )


def upgrade() -> None:
    if not _table_exists("core_encounters"):
        op.create_table(
            "core_encounters",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("appointment_id", sa.String(26), sa.ForeignKey("core_appointments.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("patient_person_id", sa.String(26), sa.ForeignKey("niam_persons.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("provider_account_id", sa.String(26), sa.ForeignKey("niam_accounts.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("organization_id", sa.String(26), sa.ForeignKey("niam_organizations.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("facility_id", sa.String(26), sa.ForeignKey("niam_admin_facilities.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("workspace_id", sa.String(26), sa.ForeignKey("niam_workspaces.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("status", sa.String(24), nullable=False, server_default="PLANNED"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("checked_in_at", sa.DateTime(timezone=True)),
            sa.Column("started_at", sa.DateTime(timezone=True)),
            sa.Column("completed_at", sa.DateTime(timezone=True)),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("appointment_id", name="uq_core_encounter_appointment"),
            sa.CheckConstraint("status IN ('PLANNED','CHECKED_IN','IN_PROGRESS','COMPLETED','CANCELLED')", name="ck_core_encounter_status"),
            sa.CheckConstraint("version > 0", name="ck_core_encounter_version_positive"),
        )
        for column in ("appointment_id", "patient_person_id", "provider_account_id", "organization_id", "facility_id", "workspace_id", "status"):
            op.create_index(f"ix_core_encounters_{column}", "core_encounters", [column])
        op.create_index("ix_core_encounter_patient_scope", "core_encounters", ["patient_person_id", "organization_id", "workspace_id", "created_at"])
        op.create_index("ix_core_encounter_provider_scope", "core_encounters", ["provider_account_id", "organization_id", "workspace_id", "created_at"])

    if not _table_exists("core_encounter_queue"):
        op.create_table(
            "core_encounter_queue",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("encounter_id", sa.String(26), sa.ForeignKey("core_encounters.id", ondelete="CASCADE"), nullable=False),
            sa.Column("organization_id", sa.String(26), sa.ForeignKey("niam_organizations.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("facility_id", sa.String(26), sa.ForeignKey("niam_admin_facilities.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("workspace_id", sa.String(26), sa.ForeignKey("niam_workspaces.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("status", sa.String(24), nullable=False, server_default="WAITING"),
            sa.Column("position", sa.Integer()),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("encounter_id", name="uq_core_encounter_queue_encounter"),
            sa.CheckConstraint("status IN ('WAITING','CALLED','IN_SERVICE','COMPLETED','NO_SHOW','CANCELLED')", name="ck_core_encounter_queue_status"),
            sa.CheckConstraint("version > 0", name="ck_core_encounter_queue_version_positive"),
        )
        for column in ("encounter_id", "organization_id", "facility_id", "workspace_id", "status"):
            op.create_index(f"ix_core_encounter_queue_{column}", "core_encounter_queue", [column])
        op.create_index("ix_core_encounter_queue_scope_status", "core_encounter_queue", ["organization_id", "facility_id", "workspace_id", "status"])

    if not _table_exists("core_clinical_notes"):
        op.create_table(
            "core_clinical_notes",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column("note_id", sa.String(26), nullable=False),
            sa.Column("encounter_id", sa.String(26), sa.ForeignKey("core_encounters.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("patient_person_id", sa.String(26), sa.ForeignKey("niam_persons.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("author_account_id", sa.String(26), sa.ForeignKey("niam_accounts.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("organization_id", sa.String(26), sa.ForeignKey("niam_organizations.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("facility_id", sa.String(26), sa.ForeignKey("niam_admin_facilities.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("workspace_id", sa.String(26), sa.ForeignKey("niam_workspaces.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("status", sa.String(24), nullable=False, server_default="DRAFT"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("chief_complaint", sa.Text()),
            sa.Column("history", sa.Text()),
            sa.Column("examination", sa.Text()),
            sa.Column("assessment", sa.Text()),
            sa.Column("plan", sa.Text()),
            sa.Column("amendment_reason", sa.String(500)),
            sa.Column("supersedes_id", sa.String(26), sa.ForeignKey("core_clinical_notes.id", ondelete="RESTRICT")),
            sa.Column("signed_by_account_id", sa.String(26), sa.ForeignKey("niam_accounts.id", ondelete="RESTRICT")),
            sa.Column("signed_at", sa.DateTime(timezone=True)),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("note_id", "version", name="uq_core_clinical_note_version"),
            sa.CheckConstraint("status IN ('DRAFT','COMPLETED','SIGNED','AMENDED')", name="ck_core_clinical_note_status"),
            sa.CheckConstraint("version > 0", name="ck_core_clinical_note_version_positive"),
        )
        for column in ("note_id", "encounter_id", "patient_person_id", "author_account_id", "organization_id", "facility_id", "workspace_id", "status", "supersedes_id"):
            op.create_index(f"ix_core_clinical_notes_{column}", "core_clinical_notes", [column])
        op.create_index("ix_core_note_encounter_scope", "core_clinical_notes", ["encounter_id", "organization_id", "workspace_id", "created_at"])

    _seed_permissions()


def downgrade() -> None:
    if _table_exists("core_clinical_notes"):
        op.drop_table("core_clinical_notes")
    if _table_exists("core_encounter_queue"):
        op.drop_table("core_encounter_queue")
    if _table_exists("core_encounters"):
        op.drop_table("core_encounters")
    # Shared permission catalog rows are intentionally retained.
