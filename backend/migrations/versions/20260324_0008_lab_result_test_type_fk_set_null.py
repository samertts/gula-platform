"""Fix lab_results.test_type_id FK to use ON DELETE SET NULL.

Previously the foreign key had no ON DELETE action, meaning that deleting a
TestType would leave orphaned rows with a dangling reference (or raise a FK
violation depending on the DB driver).  Correct behaviour is to NULL the
field so the result is preserved but no longer linked to a deleted test type.

lab_results:
  ~ test_type_id  FK → test_types.id  (no action → SET NULL)

Revision ID : 20260324_0008
Revises     : 20260324_0007
Create Date : 2026-03-24
"""

from alembic import op
from sqlalchemy import inspect

revision      = "20260324_0008"
down_revision = "20260324_0007"
branch_labels = None
depends_on    = None


def _fk_exists(table: str, name: str) -> bool:
    return any(
        fk["name"] == name
        for fk in inspect(op.get_bind()).get_foreign_keys(table)
    )


def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def upgrade() -> None:
    if not _table_exists("lab_results"):
        return

    # Drop the old FK (no ON DELETE rule) and recreate with SET NULL.
    # The constraint name follows SQLAlchemy's auto-naming convention; adjust
    # if your DB used a different name.
    old_fk = "lab_results_test_type_id_fkey"
    if _fk_exists("lab_results", old_fk):
        op.drop_constraint(old_fk, "lab_results", type_="foreignkey")

    op.create_foreign_key(
        "lab_results_test_type_id_fkey",
        "lab_results",
        "test_types",
        ["test_type_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    if not _table_exists("lab_results"):
        return

    new_fk = "lab_results_test_type_id_fkey"
    if _fk_exists("lab_results", new_fk):
        op.drop_constraint(new_fk, "lab_results", type_="foreignkey")

    op.create_foreign_key(
        "lab_results_test_type_id_fkey",
        "lab_results",
        "test_types",
        ["test_type_id"],
        ["id"],
    )
