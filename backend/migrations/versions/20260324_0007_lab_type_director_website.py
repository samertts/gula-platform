"""Add lab_type, director_name, website to labs; doctors handled via users table.

labs:
  + lab_type      VARCHAR(50)  NULL  (private / government / hospital / clinic)
  + director_name VARCHAR(200) NULL  (مدير المختبر)
  + website       VARCHAR(300) NULL

Note: doctor-specific fields (license_number, specialty) are already on the
users table from a previous migration. No changes to users needed here.

Revision ID : 20260324_0007
Revises     : 20260324_0006
Create Date : 2026-03-24
"""

from alembic import context, op
import sqlalchemy as sa
from sqlalchemy import inspect

revision      = "20260324_0007"
down_revision = "20260324_0006"
branch_labels = None
depends_on    = None


def _col_exists(table: str, col: str) -> bool:
    if context.is_offline_mode():
        return False
    return col in [c["name"] for c in inspect(op.get_bind()).get_columns(table)]


def _table_exists(table: str) -> bool:
    if context.is_offline_mode():
        return True
    return inspect(op.get_bind()).has_table(table)


def upgrade() -> None:
    if not _table_exists("labs"):
        return

    if not _col_exists("labs", "lab_type"):
        op.add_column("labs", sa.Column("lab_type", sa.String(50), nullable=True))
        op.create_index("ix_labs_lab_type", "labs", ["lab_type"])

    if not _col_exists("labs", "director_name"):
        op.add_column("labs", sa.Column("director_name", sa.String(200), nullable=True))

    if not _col_exists("labs", "website"):
        op.add_column("labs", sa.Column("website", sa.String(300), nullable=True))


def downgrade() -> None:
    if not _table_exists("labs"):
        return
    for col in ("website", "director_name"):
        if _col_exists("labs", col):
            op.drop_column("labs", col)
    if _col_exists("labs", "lab_type"):
        op.drop_index("ix_labs_lab_type", table_name="labs")
        op.drop_column("labs", "lab_type")
