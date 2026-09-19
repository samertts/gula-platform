"""NR-086 / NR-078 — the one `MetaData` the mutually-referencing bases share.

SQLAlchemy resolves a `ForeignKey` inside the `MetaData` that owns the
**referring** table, and it resolves every one of them while sorting a mapper's
tables during `flush`. A target that lives in a different `MetaData` cannot be
found, so the write raises before a single statement is emitted::

    session.add(ConsentRecord(...)); session.flush()
    NoReferencedTableError: Foreign key associated with column
    'trust_consent_records.guardian_id' could not find table 'lab_users'

Reads never sort tables, which is why this stayed invisible for so long: the
table answers `SELECT` perfectly and fails the first time anything tries to
persist. NR-086 measured the population at **76 mapped tables carrying 310
unresolvable foreign keys**, six of them behind live write endpoints —
`POST /api/v1/trust/consent` and `/consent/{id}/withdraw` among them.

**Scope, and why it is not every base.** The bases that must share a namespace
are the transitive closure of "declares a cross-base foreign key" and "owns a
table one of those foreign keys names". Measured, that closure is seven and
reaches a fixed point immediately:

    referring:  CareContinuumBase (214), EHRBase (70), DataPlatformBase (13),
                TrustBase (8), IdentityBase (5)
    targets:    Base, NationalBase

The other eleven registered bases declare nothing across a base boundary and
are left exactly as they are. That is the difference between this and a naive
merge of everything that happens to be imported: `InsBase` and
`app.national.task_engine` are deliberately unregistered (NR-018), and a merge
that swept them in would put 28 tables in front of autogenerate that a recorded
decision keeps out of it.

**What this changes, and what it does not.** Nothing about the DDL. No base
carried a `naming_convention`, so no constraint or index changes name; the
`Table` objects are the same objects, collected in one namespace instead of
seven. What changes is that `fk.column` now resolves, so the ORM can write.

**The one collision it forces.** `national_facilities` was declared twice —
once by `models.clinical_scope.NationalFacility` and once as a bare foreign-key
anchor in `app.national.domain.facility`, added by NR-006 precisely so that
seventeen `app/national` models could resolve it inside `NationalBase`. Under
one namespace the anchor is both redundant and illegal, and it is deleted: the
canonical model now serves every one of those references directly. The two
definitions were column-identical, which is why this is a deletion and not a
choice of owner.

**The capability this unblocks, and the one it must not.** Resolving all 310
also lets `alembic revision --autogenerate` run, and NR-080 measured what its
first complete run proposes: 5039 operations, 1367 destructive, including
``DROP COLUMN patients.national_id`` — the column CLAUDE.md Security Invariant
#8 requires to hold encrypted national identifiers. Converting a loud, honest
failure into a quiet and dangerous capability is the trade NR-078 refused, and
it is still refused: `backend/migrations/env.py` installs an explicit
`process_revision_directives` guard that refuses to write a revision containing
an unreconciled destructive operation, and says which. The block on
autogenerate is now deliberate and explains itself, where before it was an
accident of topology that reported `ehr_allergies.citizen_id`.
"""

from __future__ import annotations

from sqlalchemy import MetaData, Table

#: The shared namespace. Seven declarative bases are constructed against it;
#: every other base keeps its own.
SHARED_METADATA = MetaData()

#: The bases that share it, by the attribute path `migrations/env.py` uses.
#: Stated here so a guard can assert the membership rather than infer it.
SHARED_BASE_LABELS = frozenset({
    "Base",
    "NationalBase",
    "EHRBase",
    "CareContinuumBase",
    "DataPlatformBase",
    "IdentityBase",
    "TrustBase",
})


def own_tables(base: type) -> list[Table]:
    """The tables this declarative base's own mappers define.

    `base.metadata.tables` no longer answers that question for a shared base —
    it answers for all seven at once. A fixture that wants "just this base's
    schema" asks here instead, and keeps the meaning it had before the merge.
    """
    tables: dict[str, Table] = {}
    for mapper in base.registry.mappers:
        for table in mapper.tables:
            tables.setdefault(table.key, table)
    return list(tables.values())


def _walk_ops(ops):
    for op in getattr(ops, "ops", []):
        yield op
        yield from _walk_ops(op)


def refuse_unreconciled_destructive_autogenerate(context, revision, directives):
    """NR-080 — do not let a resolvable topology become a dangerous one.

    Installed by `migrations/env.py` as Alembic's `process_revision_directives`.
    It lives here, beside the merge, because it is the other half of the same
    decision: the merge is only safe to apply while this refusal holds.

    Before the merge, `alembic revision --autogenerate` could not run at all —
    one unresolvable foreign key anywhere stops Alembic in `sorted_tables`, and
    it reported `ehr_allergies.citizen_id`, a message that says nothing about
    what the run would have proposed. That block was an accident of topology,
    and repairing the ORM write path removed it.

    What it was accidentally protecting is real. The first complete ORM-to-
    database comparison this platform produced is 5039 operations, 1367 of them
    destructive, including ``DROP COLUMN patients.national_id`` — the column
    CLAUDE.md Security Invariant #8 requires to hold encrypted national
    identifiers. None of that is caused by the merge; it is pre-existing drift
    the merge made visible, and it is recorded as NR-080.

    So the refusal stays, and is now deliberate and explains itself. An additive
    diff passes through untouched. A diff containing a destructive operation is
    refused **whole** — never silently filtered, because a migration that quietly
    drops half of what it was asked to emit is worse than one that does not run.

    This lifts on its own as NR-080 is reconciled: map the unmapped columns, and
    the destructive count falls to zero without this function changing.
    """
    if not directives:
        return
    upgrade_ops = getattr(directives[0], "upgrade_ops", None)
    if upgrade_ops is None:
        return

    destructive = [op for op in _walk_ops(upgrade_ops) if type(op).__name__.startswith("Drop")]
    if not destructive:
        return

    counts: dict[str, int] = {}
    for op in destructive:
        counts[type(op).__name__] = counts.get(type(op).__name__, 0) + 1
    sample = sorted({
        f"{getattr(op, 'table_name', '?')}."
        f"{getattr(op, 'column_name', None) or getattr(op, 'constraint_name', None) or getattr(op, 'index_name', None) or '*'}"
        for op in destructive
    })[:10]

    raise RuntimeError(
        "REFUSED: autogenerate proposed "
        f"{len(destructive)} destructive operations "
        f"({', '.join(f'{k}={v}' for k, v in sorted(counts.items()))}).\n"
        f"First ten, sorted: {sample}\n\n"
        "This is NR-080: pre-existing ORM-to-database drift, not a consequence "
        "of your change. Autogenerate can run (NR-086 made the metadata "
        "resolvable) but its output may not be committed until every proposed "
        "drop is classified -- the set includes patients.national_id, which "
        "Security Invariant #8 requires to hold encrypted national identifiers.\n"
        "Read docs/architecture/NR-078-autogenerate-cannot-run.md, and see "
        "backend/tests/test_autogenerate_is_safe.py for the measured ledger.\n"
        "To make a schema change now, hand-write the revision: "
        '`alembic revision -m "..."` without --autogenerate.',
    )
