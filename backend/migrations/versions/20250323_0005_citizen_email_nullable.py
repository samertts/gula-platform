"""Make users.email nullable for citizens who register without email.

Citizens may not have an email address. The unique constraint is kept
so no two accounts can share the same email when provided.

Changes:
  users:
    - ALTER COLUMN email DROP NOT NULL  (email remains UNIQUE when set)

Revision ID : 20250323_0005
Revises     : 20250323_0004
Create Date : 2025-03-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision = "20250323_0005"
down_revision = "20250323_0004"
branch_labels = None
depends_on = None


def _pg() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def upgrade() -> None:
    # Make users.email nullable so citizens without email can register
    if _table_exists("users") and _pg():
        op.execute(text("ALTER TABLE users ALTER COLUMN email DROP NOT NULL"))


def downgrade() -> None:
    # Restore NOT NULL only if all rows already have a non-null email
    if _table_exists("users") and _pg():
        op.execute(
            text(
                "UPDATE users SET email = 'unknown_' || id || '@placeholder.local' "
                "WHERE email IS NULL"
            )
        )
        op.execute(text("ALTER TABLE users ALTER COLUMN email SET NOT NULL"))
