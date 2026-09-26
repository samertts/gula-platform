"""NR-078 / NR-086 — the one ``MetaData`` the mutually-referencing bases share.

SQLAlchemy resolves a ``ForeignKey`` inside the ``MetaData`` that owns the
**referring** table, and it resolves every one of them while sorting a mapper's
tables during ``flush``. A target that lives in a different ``MetaData`` cannot
be found, so the write raises before a single statement is emitted::

    session.add(NursingTask(...)); session.flush()
    NoReferencedTableError: Foreign key associated with column
    'nursing_tasks.patient_id' could not find table 'patients' with which to
    generate a foreign key to target column 'id'

Reads never sort tables, which is why this stays invisible: the table answers
``SELECT`` perfectly and fails the first time anything tries to persist.

Measured on this branch, 2026-09-26, by walking every loaded base's
``metadata.tables``: **374 unresolvable foreign-key columns across 100 mapped
tables**.

    CareContinuumBase  214 FKs /  45 tables
    EHRBase             70 FKs /  16 tables
    NursingBase         49 FKs /  15 tables
    DataPlatformBase    13 FKs /   9 tables
    PharmacyBase         8 FKs /   4 tables
    TrustBase            8 FKs /   4 tables
    IdentityBase         6 FKs /   2 tables
    InsBase              6 FKs /   5 tables

**Scope, and why it is not every base.** The bases that must share a namespace
are the transitive closure of "declares a cross-base foreign key" and "owns a
table one of those foreign keys names". Measured on this branch that closure is
**eleven**, and it reaches a fixed point immediately because every unresolvable
target is owned by some loaded base (zero targets are undeclared):

    referring:  CareContinuumBase, EHRBase, NursingBase, DataPlatformBase,
                PharmacyBase, TrustBase, IdentityBase, InsBase
    targets:    Base, NationalBase, HospitalBase

The other eight registered bases -- CitizenPlatformBase, ClinicalBase,
DocIntelBase, FinBase, GovernanceBase, HealthDataBase, NHDWBase, RadiologyBase
-- declare nothing across a base boundary and are left exactly as they are.
That is the difference between this and a naive merge of everything that
happens to be imported.

**This closure is eleven, not the seven NR-086 measured.** NR-086 was measured
on a sibling branch before Nursing (BATCH-3) and Pharmacy (M4) were reconciled
against the physical schema; that reconciliation is what introduced
NursingBase's 49 and PharmacyBase's 8, and HospitalBase enters only as the
target of ``nursing_*.department_id``. The number is therefore not stable
across branches and must be re-measured, not assumed --
``tests/verification/test_cross_base_fk_topology.py`` re-measures it on every
run rather than trusting this docstring.

**What this changes, and what it does not.** Nothing about the DDL. No base
carries a ``naming_convention`` and no module constructs a ``MetaData``
explicitly (both verified on this branch), so no constraint or index changes
name; the ``Table`` objects are the same objects, collected in one namespace
instead of eleven. What changes is that ``fk.column`` now resolves, so the ORM
can write.

**The collision it forces, and how NR-006 is resolved here.** Under eleven
namespaces ``national_facilities`` was declared twice -- by
``app.models.clinical_scope.NationalFacility`` on ``Base`` and by
``app.national.domain.facility.Facility`` on ``NationalBase``. Under one
namespace two declarations of one name are illegal, so NR-006's long-open
ownership question has to be answered before the merge can be applied, and the
evidence now answers it:

* The physical table has exactly six columns, and
  ``clinical_scope.NationalFacility`` declares exactly those six.
* ``national.domain.facility.Facility`` declares 28 columns, **24 of which the
  physical table does not have**. It cannot even read: ``SELECT`` through it
  raises ``UndefinedColumn: column national_facilities.facility_type does not
  exist``.
* The only migration on this branch that touches the table is
  ``20260813_0004_clinical_ehr_scope_bridge.py`` -- the clinical_scope lineage
  created it. No migration anywhere on this branch creates the operational
  shape ``Facility`` describes.
* No module imports ``app.national.domain.facility``; it is reachable only
  through the package's own model-loading.

So ``clinical_scope.NationalFacility`` is the owner, on physical evidence, and
``Facility`` is retired as a mapped class. Note that this differs from NR-086's
account on the sibling branch, which recorded the two definitions as
"column-identical" and deleted the *national* one as a redundant anchor: on
this branch they are **not** column-identical, and the one being retired is the
richer of the two. It is retired rather than deleted, and the operational shape
it described is preserved verbatim in
``docs/architecture/NR-006-national-facilities-ownership.md``, because that
shape is a statement of intent about a table the platform does not yet have --
adding those 24 columns is a schema change and a human decision, not something
this module may infer.

**The capability this unblocks, and the one it must not.** Resolving the 374
also lets ``alembic revision --autogenerate`` run, which it previously could
not: one unresolvable foreign key anywhere stops Alembic in ``sorted_tables``.
That block was an accident of topology, and repairing the ORM write path
removes it. What it was accidentally protecting is real -- the platform has
substantial un-reconciled ORM-to-database drift -- so the refusal is made
deliberate instead: ``refuse_unreconciled_destructive_autogenerate`` below is
installed by ``migrations/env.py`` and refuses to write a revision containing
an unreconciled destructive operation, and says which. Converting a loud,
honest failure into a quiet and dangerous capability is the one trade this
change must not make.

**Autogenerate scope is deliberately unchanged.** Sharing a ``MetaData`` would
otherwise sweep five bases into Alembic's comparison that NR-018 recorded a
decision to keep out -- HospitalBase, InsBase, DataPlatformBase, NursingBase
and PharmacyBase. Write correctness and autogenerate scope are independent
concerns and this change holds both: ``AUTOGENERATE_BASE_LABELS`` states the
scope NR-018 authorised, and ``env.py`` filters the shared namespace down to it
rather than passing it whole.
"""

from __future__ import annotations

from sqlalchemy import MetaData, Table

#: The shared namespace. Eleven declarative bases are constructed against it;
#: every other base keeps its own.
SHARED_METADATA = MetaData()

#: The bases that share it. Stated here so a guard can assert the membership
#: rather than infer it, and so the measured closure is reviewable as a list.
SHARED_BASE_LABELS = frozenset({
    # own a table that one of the referring bases names
    "Base",
    "NationalBase",
    "HospitalBase",
    # declare at least one cross-base foreign key
    "CareContinuumBase",
    "EHRBase",
    "NursingBase",
    "DataPlatformBase",
    "PharmacyBase",
    "TrustBase",
    "IdentityBase",
    "InsBase",
})

#: The bases Alembic compares, per NR-018. This is NOT the same set as
#: ``SHARED_BASE_LABELS`` and must not be conflated with it: sharing a
#: ``MetaData`` is about whether the ORM can write, and this is about what
#: autogenerate is allowed to see. ``env.py`` filters on it.
AUTOGENERATE_BASE_LABELS = frozenset({
    "Base",
    "NationalBase",
    "EHRBase",
    "CitizenPlatformBase",
    "ClinicalBase",
    "HealthDataBase",
    "TrustBase",
    "GovernanceBase",
    "CareContinuumBase",
    "IdentityBase",
})


#: Where each autogenerate-authorised base lives, so the scope can be resolved
#: without importing ``migrations/env.py`` -- which is not importable outside an
#: Alembic run, because it reads ``context.config`` at module level. The scope
#: therefore lives here, beside the closure it has to be distinguished from, and
#: a test can assert it.
AUTOGENERATE_BASE_IMPORTS: dict[str, tuple[str, str]] = {
    "Base": ("app.database", "Base"),
    "NationalBase": ("app.national.base", "NationalBase"),
    "EHRBase": ("app.ehr.base", "EHRBase"),
    "CitizenPlatformBase": ("app.citizen_platform.base", "CitizenPlatformBase"),
    "ClinicalBase": ("app.clinical.base", "ClinicalBase"),
    "HealthDataBase": ("app.health_data.base", "HealthDataBase"),
    "TrustBase": ("app.trust.base", "TrustBase"),
    "GovernanceBase": ("app.governance.base", "GovernanceBase"),
    "CareContinuumBase": ("app.care_continuum.base", "CareContinuumBase"),
    "IdentityBase": ("app.identity.base", "IdentityBase"),
}

if set(AUTOGENERATE_BASE_IMPORTS) != set(AUTOGENERATE_BASE_LABELS):
    raise RuntimeError(
        "AUTOGENERATE_BASE_LABELS and AUTOGENERATE_BASE_IMPORTS disagree: "
        f"labels-only={sorted(set(AUTOGENERATE_BASE_LABELS) - set(AUTOGENERATE_BASE_IMPORTS))}, "
        f"imports-only={sorted(set(AUTOGENERATE_BASE_IMPORTS) - set(AUTOGENERATE_BASE_LABELS))}. "
        "NR-018's scope is one decision and must be stated once.",
    )


def autogenerate_bases() -> dict[str, type]:
    """Resolve the authorised bases, importing lazily.

    Lazily because ``app.database`` imports this module to construct ``Base``
    against ``SHARED_METADATA``; importing it back at module scope would be
    circular.
    """
    import importlib

    return {
        label: getattr(importlib.import_module(module), attr)
        for label, (module, attr) in AUTOGENERATE_BASE_IMPORTS.items()
    }


def authorized_table_names() -> set[str]:
    """Table names Alembic's autogenerate may compare, per NR-018.

    Built from mapper ownership rather than ``metadata.tables``, which no longer
    distinguishes the eleven shared bases from one another.
    """
    return {
        table.key
        for base in autogenerate_bases().values()
        for table in own_tables(base)
    }


def autogenerate_target_metadata() -> list[MetaData]:
    """The metadata objects to hand Alembic, de-duplicated by identity.

    Six of the ten authorised bases now share one object, so a naive list would
    pass it six times.
    """
    collected: list[MetaData] = []
    for base in autogenerate_bases().values():
        if not any(md is base.metadata for md in collected):
            collected.append(base.metadata)
    return collected


def make_include_name(authorized: set[str]):
    """Hold NR-018's autogenerate scope over NR-086's shared namespace.

    Only table names are filtered; schemas, columns, indexes and constraints
    pass through, because the scope is a statement about which *tables*
    autogenerate owns. ``name is None`` is Alembic asking about the default
    schema and must be admitted, or nothing is compared at all.

    One deliberate side effect: a table in the database that no authorised base
    maps is now excluded, so autogenerate will not propose dropping it. That is
    strictly safer than the previous behaviour, where such a table was absent
    from every metadata in the list and therefore a drop candidate -- and moot
    in practice, since ``refuse_unreconciled_destructive_autogenerate`` rejects
    any diff carrying a drop regardless.
    """

    def include_name(name, type_, parent_names) -> bool:
        if type_ == "table":
            return name in authorized
        return True

    return include_name


def own_tables(base: type) -> list[Table]:
    """The tables this declarative base's own mappers define.

    ``base.metadata.tables`` no longer answers that question for a shared base
    -- it answers for all eleven at once. A fixture that wants "just this
    base's schema" asks here instead, and keeps the meaning it had before the
    merge.
    """
    tables: dict[str, Table] = {}
    for mapper in base.registry.mappers:
        for table in mapper.tables:
            tables.setdefault(table.key, table)
    return list(tables.values())


def own_metadata(base: type) -> MetaData:
    """A throwaway ``MetaData`` holding only ``base``'s own tables.

    For the handful of call sites that need to hand a ``MetaData`` to something
    (``create_all``, Alembic's ``target_metadata``) and mean one base's schema
    rather than the shared namespace. The ``Table`` objects are shared, not
    copied, so this is a view and not a second definition.
    """
    md = MetaData()
    for table in own_tables(base):
        table.to_metadata(md)
    return md


def _walk_ops(ops):
    for op in getattr(ops, "ops", []):
        yield op
        yield from _walk_ops(op)


def refuse_unreconciled_destructive_autogenerate(context, revision, directives):
    """NR-080 — do not let a resolvable topology become a dangerous one.

    Installed by ``migrations/env.py`` as Alembic's
    ``process_revision_directives``. It lives here, beside the merge, because it
    is the other half of the same decision: the merge is only safe to apply
    while this refusal holds.

    Before the merge, ``alembic revision --autogenerate`` could not run at all
    -- one unresolvable foreign key anywhere stops Alembic in ``sorted_tables``.
    That block was an accident of topology, and repairing the ORM write path
    removed it. What it was accidentally protecting is real: substantial
    pre-existing ORM-to-database drift, including proposed drops of columns
    CLAUDE.md's security invariants require to exist.

    So the refusal stays, and is now deliberate and explains itself. An additive
    diff passes through untouched. A diff containing a destructive operation is
    refused **whole** -- never silently filtered, because a migration that
    quietly drops half of what it was asked to emit is worse than one that does
    not run.

    This lifts on its own as the drift is reconciled: map the unmapped columns,
    and the destructive count falls to zero without this function changing.
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
        "drop is classified -- the set has included patients.national_id, which "
        "Security Invariant #8 requires to hold encrypted national identifiers.\n"
        "See backend/tests/verification/test_cross_base_fk_topology.py for the "
        "measured topology this guard accompanies.\n"
        "To make a schema change now, hand-write the revision: "
        '`alembic revision -m "..."` without --autogenerate.',
    )
