"""Point `niam_citizen_relationships.citizen_id` at the canonical person.

NR-064.

`POST /admin/citizen-relationships` is registered at ``factory.py:599`` and
reachable by a ministry actor holding ``platform:manage_users``. Its workflow
validated the subject with ``db.query(Citizen)`` over ``national_citizens`` --
a table no migration creates -- so every create raised ``UndefinedTable`` before
a row existed, and the route's ``except Exception`` reported it as a generic
500. The workflow is otherwise careful: explicit keywords, an idempotency key,
an optimistic version and a hash-chained audit write. Only its subject lookup
was pointed at nothing.

The subject of a citizen relationship is a natural person, and NR-022 settles
which table that is: ``niam_persons``. Both are ``VARCHAR(26)``, so this is a
constraint the database can actually enforce -- unlike the declared foreign key
it replaces, which the foundation migration (``20260811_0002``) had to guard on
``_has_table`` and therefore never created.

**Fail-closed.** No value is cast, defaulted or deleted. If any existing row
carries a ``citizen_id`` with no matching person, this migration refuses and
reports the count rather than creating a constraint that would silently reject
those rows later. In a deployment that has only ever run this codebase the table
is necessarily empty of workflow-created rows -- the create path has never
succeeded -- but "necessarily" is an argument, and a count is evidence.

``patient_id`` is deliberately untouched. It names ``national_patients``, also
unbuilt, and the built clinical patient table keys on ``INTEGER`` against this
``VARCHAR(26)`` column -- so there is no target to point it at until NR-022
decides the clinical subject. The API now refuses the input instead of querying
an absent table, and the column stays so that decision stays open.

Additive and reversible: the downgrade drops the foreign key and leaves the
column, its index and every row exactly as it found them.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
from sqlalchemy import inspect, text

revision: str = "20260914_0001"
down_revision: str | None = "20260913_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "niam_citizen_relationships"
_COLUMN = "citizen_id"
_TARGET = "niam_persons"
_FK = "fk_citizen_relationship_person"
_STALE_FK = "fk_citizen_relationship_citizen"


def _has_table(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def _foreign_keys(table: str) -> set[str]:
    return {
        fk["name"]
        for fk in inspect(op.get_bind()).get_foreign_keys(table)
        if fk.get("name")
    }


def upgrade() -> None:
    if not _has_table(_TABLE) or not _has_table(_TARGET):
        return

    bind = op.get_bind()

    # Fail closed. A row whose citizen_id resolves to no person would be
    # rejected by the constraint below; refuse and report rather than discover
    # that during the ALTER.
    unresolved = bind.execute(
        text(
            f"SELECT COUNT(*) FROM {_TABLE} r "
            f"WHERE r.{_COLUMN} IS NOT NULL "
            f"  AND NOT EXISTS (SELECT 1 FROM {_TARGET} p WHERE p.id = r.{_COLUMN})"
        )
    ).scalar_one()
    if unresolved:
        raise RuntimeError(
            f"{_TABLE}.{_COLUMN} has {unresolved} value(s) that do not resolve to "
            f"{_TARGET}.id. NR-064 re-points this column at the canonical person; "
            "reconcile or remove those rows before upgrading. No data was changed."
        )

    existing = _foreign_keys(_TABLE)

    # Only reachable in a deployment that somehow built national_citizens; the
    # guarded foundation migration would have created this constraint there.
    if _STALE_FK in existing:
        op.drop_constraint(_STALE_FK, _TABLE, type_="foreignkey")

    if _FK not in existing:
        op.create_foreign_key(
            _FK, _TABLE, _TARGET, [_COLUMN], ["id"], ondelete="RESTRICT",
        )


def downgrade() -> None:
    if not _has_table(_TABLE):
        return
    if _FK in _foreign_keys(_TABLE):
        op.drop_constraint(_FK, _TABLE, type_="foreignkey")
