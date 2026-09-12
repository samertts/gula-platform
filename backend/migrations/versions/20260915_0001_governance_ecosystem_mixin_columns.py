"""Build the timestamp and optimistic-lock columns eight mappers already declare.

NR-083.

Eight tables are mapped by an ORM class that inherits a timestamp mixin, an
optimistic-lock mixin, or both -- and the migration that created the table never
built those columns. The mapper therefore names a column the table does not
have, so **every** statement SQLAlchemy emits for it, including a plain
``SELECT``, fails with ``UndefinedColumn`` before touching a row. Not a
degraded path: no query against these eight tables has ever worked against a
migrated database.

Two of the eight decide whether a concurrent write can be lost:

* ``gov_break_glass_accesses`` records emergency override of normal access
  control;
* ``gov_merge_proposals`` records proposals to merge two patient identities.

CLAUDE.md Security Invariant #6 requires the ``version`` column to be checked on
mutation. On these tables it could not be checked, because it did not exist.

**Additive only.** Every column added here is new, nullable or
``server_default``-backed, and absent from the table today; nothing is dropped,
renamed, retyped or backfilled from another column. ``server_default`` exists so
rows written by a path that does not set the value still satisfy the mapper --
it is not a substitute for the application default, which stays authoritative.

Guarded on ``_has_table``/``_has_column`` so it is idempotent and so a database
that already carries a column is left alone.

**A ninth table is deliberately not repaired here.**
``ecosystem_partner_agreements`` also fails to read, on ``version`` -- but there
the mapper declares ``version = Column(String(20), nullable=False)``, a document
version that *shadows* the inherited integer lock, while the table carries
``agreement_version``. Adding an integer ``version`` would contradict the
mapper; mapping ``version`` onto ``agreement_version`` would silently confirm
that this entity has no optimistic lock. Which of the two is intended is a
question about the entity, not about the schema, so it is left failing and
recorded in ``test_mapped_tables_are_readable.py`` rather than guessed at.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260915_0001"
down_revision: str | None = "20260914_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NOW = sa.text("CURRENT_TIMESTAMP")

#: table -> ((column, type, server_default), ...). Exactly the columns each
#: mapper declares and the table lacks, measured against a database at head --
#: not every column the mixin could contribute.
_ADDITIONS: dict[str, tuple[tuple[str, object, object], ...]] = {
    "gov_break_glass_accesses": (
        ("updated_at", sa.DateTime(timezone=True), _NOW),
        ("version", sa.Integer(), sa.text("1")),
    ),
    "gov_guardians": (
        ("created_at", sa.DateTime(timezone=True), _NOW),
        ("updated_at", sa.DateTime(timezone=True), _NOW),
    ),
    "gov_identity_records": (
        ("version", sa.Integer(), sa.text("1")),
    ),
    "gov_merge_proposals": (
        ("updated_at", sa.DateTime(timezone=True), _NOW),
        ("version", sa.Integer(), sa.text("1")),
    ),
    "gov_qr_codes": (
        ("updated_at", sa.DateTime(timezone=True), _NOW),
    ),
    "gov_recovery_requests": (
        ("updated_at", sa.DateTime(timezone=True), _NOW),
    ),
    "ecosystem_partners": (
        ("version", sa.Integer(), sa.text("1")),
    ),
    "ecosystem_partner_certificates": (
        ("version", sa.Integer(), sa.text("1")),
    ),
}


def _has_table(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def _has_column(table: str, column: str) -> bool:
    return column in {col["name"] for col in inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    for table, columns in _ADDITIONS.items():
        if not _has_table(table):
            continue
        for name, type_, server_default in columns:
            if _has_column(table, name):
                continue
            op.add_column(
                table,
                sa.Column(name, type_, nullable=True, server_default=server_default),
            )


def downgrade() -> None:
    for table, columns in _ADDITIONS.items():
        if not _has_table(table):
            continue
        for name, _type, _default in columns:
            if _has_column(table, name):
                op.drop_column(table, name)
