"""Give `organizations` the parent reference its own bootstrap already writes.

NR-047.

The Organization ORM was written in NIAMOrganization's vocabulary. Three of the
four columns it declared and the table lacked were pure naming — `org_id` and
`org_type` are physically `organization_id` and `organization_type`, and
`updated_at` is read, written and serialised by nothing, so it was removed from
the model rather than added here. Adding a column only to make a model and a
table look alike is drift in the other direction.

`parent_org_id` is the one that is real. `build_directorate_defs` seeds the
eighteen Iraqi governorate health directorates with
``parent_org_id=MINISTRY_ORG_ID``, and ``validation.py`` asserts the resulting
hierarchy. The concept is used; only the column was missing.

Its type comes from that contract, not from the matching name in NIAM.
``OrganizationDef.parent_org_id`` is ``str | None`` and carries a *public*
identifier ("org-iraq-moh"), so this is ``VARCHAR(100)`` against
``organizations.organization_id`` — deliberately **not** the integer self-FK
``niam_organizations.parent_org_id`` uses. The names coincide because of the
same drift that caused NR-047; the semantics never did.

No foreign key is declared. ``organization_id`` is UNIQUE so one would be
well-formed, but it would impose a seed ordering constraint on a bootstrap that
does not need it today, and NR-047's remit is to make the ORM and the schema
agree — not to add referential rules nobody asked for. Recorded as a deliberate
omission rather than an oversight.

Additive, nullable, idempotent and reversible. The ministry row itself has no
parent, so nullable is the correct and permanent state, not a staging step.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260913_0001"
down_revision: str | None = "20260912_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "organizations"
_COLUMN = "parent_org_id"
_INDEX = "ix_organizations_parent_org_id"


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    return column in {col["name"] for col in inspect(bind).get_columns(table)}


def _has_index(table: str, index: str) -> bool:
    bind = op.get_bind()
    return index in {ix["name"] for ix in inspect(bind).get_indexes(table)}


def _has_table(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def upgrade() -> None:
    if not _has_table(_TABLE):
        return
    if not _has_column(_TABLE, _COLUMN):
        op.add_column(_TABLE, sa.Column(_COLUMN, sa.String(length=100), nullable=True))
    if not _has_index(_TABLE, _INDEX):
        op.create_index(_INDEX, _TABLE, [_COLUMN])


def downgrade() -> None:
    if not _has_table(_TABLE):
        return
    if _has_index(_TABLE, _INDEX):
        op.drop_index(_INDEX, table_name=_TABLE)
    if _has_column(_TABLE, _COLUMN):
        op.drop_column(_TABLE, _COLUMN)
