"""NR-078 / NR-080 — run Alembic autogenerate for real, and refuse to act on it blindly.

Every other guard in this suite reasons about what autogenerate *would* propose.
None had ever asked it to propose anything, and that is how NR-078 stayed
invisible: `alembic revision --autogenerate` terminates with
`NoReferencedTableError` before emitting a single operation, and the command
CLAUDE.md names as mandatory for any schema change has no working path.

This file executes it, against a disposable PostgreSQL database migrated to
head, and asserts on the result.

**What the experiment found, and why the topology change is deliberately NOT
applied here.**

Two options were measured rather than argued:

* **Option B** -- keep the separate metadata and drop the ORM-level
  `ForeignKey` on the 310 cross-base declarations, keeping the columns and the
  physical constraints. It removes nothing the ORM uses: **not one** of the 76
  tables holding a cross-base FK carries a single `relationship()`, so there is
  no navigation to lose. It clears all 310. It then fails anyway, on a second
  and independent blocker: `ValueError: Duplicate table keys across multiple
  MetaData objects: "national_facilities"`. Alembic refuses a multi-metadata
  target that claims one table twice, and NR-006's repair deliberately declares
  `national_facilities` a second time as a **foreign-key anchor** so that
  seventeen `app/national` models can resolve it. The anchor is what makes the
  FKs work and what makes autogenerate refuse; the two goals are in direct
  tension and Option B cannot hold both.
* **Option A** -- one shared MetaData. Measured: **one** duplicate table key
  (that same anchor), and the two definitions are **column-identical**, so the
  collision is resolved by deleting one declaration rather than by choosing an
  owner. **Zero** unresolved foreign keys. `sorted_tables` succeeds.
  Autogenerate runs.

So Option A is the mechanically correct topology, and the repository is one
deleted `Table` away from it.

It is still not applied, because making autogenerate *run* is not the same as
making it *usable*, and the first complete ORM-to-database comparison this
platform has ever produced says so:

    5039 operations, of which 1367 are destructive

      2372  CreateIndexOp             293  AddColumnOp
       585  ModifyTableOps             85  AlterColumnOp
       538  DropConstraintOp *         27  CreateForeignKeyOp
       454  DropIndexOp      *         10  DropTableOp        *
       365  DropColumnOp     *          7  CreateUniqueConstraintOp
       303  CreateTableOp

    (`*` marks the four destructive kinds; every kind autogenerate proposes is
    listed, and the eleven counts sum to 5039.)

    This block previously read "5060 operations, of which 1379 are destructive".
    Both figures were correct when written, and every one of the 21 operations
    separating them from today's has a named cause:

        DropColumnOp     377 -> 365   (-12)  NR-089
        AlterColumnOp     73 ->  85   (+12)  NR-089
        AddColumnOp      314 -> 293   (-21)  20260915_0001 (11), _0002 (10)
                                      -----
                                       -21   5060 -> 5039

    The first two are one change seen twice. NR-089 mixed in the
    `TrustSoftDeleteMixin` that had been declared and never used, so twelve
    physical trust columns stopped being unmapped -- they left `DropColumnOp`
    and arrived in `AlterColumnOp`, because the ORM now maps them with a type
    the database does not share. A reconciliation that moves a column from
    "invisible" to "wrong type" is progress, and the budget above records only
    the half of it that fell. The third is two migrations building columns the
    ORM already declared: eleven `created_at`/`updated_at`/`version` columns
    across six `gov_*` and two `ecosystem_*` tables, and the ten attestation
    columns on `niam_machine_identities`.

    That the three causes sum to the observed delta exactly, with no remainder,
    is the useful part. A drift figure that only ever gets re-measured cannot
    distinguish reconciliation from churn; one that reconciles operation by
    operation to named commits can.

    The defect this docstring carried was the itemisation, not the arithmetic:
    four of eleven kinds listed under a total covering all eleven. Nothing in
    those four lines had to change for the headline above them to stop being
    true. All eleven are listed now, and
    `test_the_itemised_destructive_kinds_are_the_only_destructive_kinds` fails
    if a kind appears that this list does not name.

Every one of those is pre-existing drift that Option A merely made visible --
none of it is caused by the topology. Two samples decide the matter:

* the 10 proposed `DROP TABLE` are **exactly** the ten physical tables no ORM
  maps, independently pinned in `test_alembic_metadata_registry.py` as
  `UNMAPPED_PHYSICAL_TABLES` -- Financial Engine Phase A (schema-only by
  design), `visits`, `sndhs_audit_logs`, `idempotency_keys` and
  `radiology_ai_analysis_jobs`. Two instruments, derived independently, produce
  the same list;
* the proposed `DROP COLUMN` set includes **`patients.national_id`**,
  `patients.sndhs_health_id`, `patients.identity_level`,
  `patients.consent_flags` and `lab_orders.visit_id` -- the SNDHS Phase 1
  columns. `patients.national_id` is the column CLAUDE.md Security Invariant #8
  requires to hold encrypted national identifiers. The ORM maps
  `national_id_hash` and none of the others.

Applying Option A would therefore replace a loud, honest failure ("autogenerate
cannot run") with a quiet and dangerous capability ("autogenerate runs, and
proposes dropping your encrypted national IDs"). That is the same trade NR-076
refuses, in the same direction, and it was refused here for the same reason.

── UPDATE: Option A is applied, and the refusal is now explicit (NR-086) ────

The reasoning above weighed a tooling risk against a tooling inconvenience and
got the answer right for that pair. It was the wrong pair. NR-086 measured the
other cost of leaving the topology unresolved: the same 310 declarations mean
**76 mapped tables cannot be written through the ORM at all**, because a flush
sorts the mapper's tables and sorting resolves every foreign key. Six live write
endpoints were failing on it, consent capture and consent withdrawal included.

The two halves were never actually coupled. Option A is applied in
`app/orm_topology.py` -- seven bases, the measured closure, one shared MetaData
-- so the ORM writes. What Option A *also* did, accidentally, was remove the
block on autogenerate, and that block is now deliberate:
`migrations/env.py` installs a `process_revision_directives` hook that refuses to
write a revision containing an unreconciled destructive operation and names the
first ten. An additive diff passes through. Nothing is ever silently filtered.

So the drift below is unchanged and still governs. What changed is that the
thing protecting you from it is a guard that explains itself, rather than a
`NoReferencedTableError` on `ehr_allergies.citizen_id` that mentions none of it
-- and 76 tables became writable on the way.

**What this file does.** It merges the remaining eleven bases onto the shared
one, in the gate, and runs autogenerate against a disposable PostgreSQL migrated
to head. The destructive proposals are pinned with their explanations and
ratcheted, so the drift is visible, bounded, and cannot grow unnoticed.

The ledgers may shrink. They may never grow.
"""

from __future__ import annotations

import collections
import os

import pytest
from sqlalchemy import MetaData, create_engine

pytestmark = pytest.mark.integration

#: Owned by this guard, like the other PostgreSQL guards: `conftest.py` pins
#: DATABASE_URL to in-memory SQLite for the whole suite before anything here
#: runs, so a value read from it would describe a different database.
DATABASE_URL = os.environ.get("GULA_SCHEMA_DATABASE_URL") or os.environ.get(
    "MIGRATION_DATABASE_URL",
)

#: Duplicate table keys across all registered metadata. This held
#: `national_facilities` -- NR-006 declared it a second time, as a bare `Table`,
#: so that seventeen `app/national` models could resolve
#: `ForeignKey("national_facilities.id")` inside their own MetaData. NR-086 gave
#: those bases one MetaData, the anchor became illegal as well as redundant, and
#: it is gone. Empty, and it may not grow.
DECLARED_DUPLICATE_TABLE_KEYS: frozenset[str] = frozenset()

#: Physical tables no ORM maps, which autogenerate therefore proposes to DROP.
#: Identical to `UNMAPPED_PHYSICAL_TABLES` in
#: `test_alembic_metadata_registry.py`, derived by a completely different route:
#: that guard subtracts mapped from physical, this one reads what Alembic emits.
#: Two instruments agreeing is worth more than either alone.
DECLARED_DROP_TABLE_PROPOSALS = {
    # Financial Engine Phase A is schema-only by design (CLAUDE.md): the tables
    # are bootstrapped, the routes and services are deferred to Phase B+.
    "fin_ads_campaigns", "fin_ads_clicks", "fin_ads_conversions",
    "fin_clinical_behavior", "fin_fraud_logs", "fin_market_benchmarks",
    # Infrastructure, written by middleware rather than by a model.
    "idempotency_keys",
    # The only radiology table of eighteen with no model (CREATE_ORM).
    "radiology_ai_analysis_jobs",
    # A parallel UUID-keyed audit surface from SNDHS Phase 1 whose promised
    # service was never written.
    "sndhs_audit_logs",
    # The clinical episode anchor; adopting Visit as canonical waits on the
    # clinical owner.
    "visits",
}

#: Columns that are physical, carry protected or flag-gated data, and are not
#: mapped -- so autogenerate proposes dropping them. Named individually because
#: `patients.national_id` is the column Security Invariant #8 governs, and a
#: count would not say that. Mapping one of these is the fix; the guard then
#: fails and the entry is removed.
DECLARED_PROTECTED_DROP_COLUMNS = {
    ("patients", "national_id"),
    ("patients", "sndhs_health_id"),
    ("patients", "identity_level"),
    ("patients", "consent_flags"),
    ("lab_orders", "visit_id"),
}

#: The destructive budget, per operation type. This is drift that predates the
#: measurement, not a regression -- and it is the reason autogenerate output may
#: not be committed as a migration without a per-operation review.
DECLARED_DESTRUCTIVE_BUDGET = {
    "DropConstraintOp": 538,
    "DropIndexOp": 454,
    "DropColumnOp": 365,
    "DropTableOp": 10,
}


#: Every operation kind autogenerate currently proposes, and whether it destroys
#: something. `DECLARED_DESTRUCTIVE_BUDGET` above counts four kinds; this says
#: those four are *all* of them.
#:
#: The budget's own novelty check reads `if "Drop" in name`, so it can only
#: notice a new destructive kind whose class name happens to contain "Drop".
#: `ExecuteSQLOp` does not, and a custom comparator emitting one would raise the
#: true destructive total while every assertion above stayed green. This map is
#: the closure: a kind that is not named here fails the gate and has to be
#: classified before anything else can proceed.
DECLARED_OPERATION_KINDS = {
    "CreateIndexOp": False,
    "ModifyTableOps": False,
    "DropConstraintOp": True,
    "DropIndexOp": True,
    "DropColumnOp": True,
    "CreateTableOp": False,
    "AddColumnOp": False,
    "AlterColumnOp": False,
    "CreateForeignKeyOp": False,
    "DropTableOp": True,
    "CreateUniqueConstraintOp": False,
}


#: Where the 365 proposed column drops actually live. The aggregate budget above
#: cannot see redistribution: radiology shrinking by ten while trust grows by ten
#: leaves 365 unchanged and hides a new defect behind a reconciliation. Measured
#: per domain so that cannot happen.
#:
#: **342 of the 365 are radiology and NHDW**, both blocked on a domain owner
#: (NR-082, NR-074). What is left is small: ten `fin_*` columns that are
#: Financial Engine Phase A behaving exactly as CLAUDE.md says it should
#: (schema-only, routes deferred), the five SNDHS columns already pinned above,
#: and eight singletons.
#:
#: Trust was here too, with twelve columns -- one uniform `deleted_at`/`is_deleted`
#: pair across six tables. It is gone because NR-089 fixed it: the pair was
#: declared by `TrustSoftDeleteMixin` and the mixin was never mixed in. Mixing it
#: in took the budget from 377 to 365, the first reduction rather than
#: re-measurement.
DECLARED_COLUMN_DROPS_BY_DOMAIN = {
    "radiology": 231,
    "nhdw": 111,
    "fin": 10,
    "core/other": 9,
    "blood_bank": 2,
    "ecosystem": 1,
    "niam": 1,
}

#: Table-name prefixes, longest-match-wins is not needed because no prefix here
#: is a prefix of another.
_DOMAIN_PREFIXES = (
    "radiology_", "nhdw_", "pharmacy_", "nursing_", "hospital_", "trust_",
    "gov_", "ecosystem_", "fin_", "niam_", "national_", "blood_bank_",
    "ems_", "critical_care_", "biomedical_", "public_health_", "lims_",
)


def _domain(table: str) -> str:
    for prefix in _DOMAIN_PREFIXES:
        if table.startswith(prefix):
            return prefix.rstrip("_")
    return "core/other"


def _require_database() -> str:
    if not DATABASE_URL:
        pytest.skip("GULA_SCHEMA_DATABASE_URL / MIGRATION_DATABASE_URL not set")
    return DATABASE_URL


@pytest.fixture(scope="module")
def registry():
    """Exactly what `migrations/env.py` hands Alembic, by replaying that file."""
    from tests.test_alembic_metadata_registry import _load_registry

    saved = dict(os.environ)
    try:
        yield _load_registry()
    finally:
        os.environ.clear()
        os.environ.update(saved)


@pytest.fixture(scope="module")
def merged(registry):
    """Option A, constructed here rather than in `env.py`.

    Doing the merge inside the gate is what lets autogenerate execute while the
    application's declarative topology is left exactly as it is. If the merge is
    ever adopted for real, this fixture becomes a one-line import and the
    assertions below keep their meaning.
    """
    target = MetaData()
    duplicates: list[str] = []
    seen: set[str] = set()
    # NR-086 put seven of the registry's eighteen labels on one shared MetaData,
    # so walking by label would visit those 447 tables seven times and report six
    # spurious copies of each. Duplicate *table names* are the question; the same
    # object arriving twice is the topology, not a collision.
    visited: set[int] = set()
    for _label, metadata in registry:
        if id(metadata) in visited:
            continue
        visited.add(id(metadata))
        for name, table in metadata.tables.items():
            if name in seen:
                duplicates.append(name)
                continue
            seen.add(name)
            table.to_metadata(target)
    target.info["duplicates"] = duplicates
    return target


@pytest.fixture(scope="module")
def autogenerated(merged):
    """The real thing: Alembic autogenerate against a migrated PostgreSQL."""
    from alembic.autogenerate import produce_migrations
    from alembic.migration import MigrationContext

    engine = create_engine(_require_database())
    try:
        with engine.connect() as connection:
            context = MigrationContext.configure(
                connection,
                opts={"target_metadata": merged, "compare_type": False},
            )
            return produce_migrations(context, merged)
    finally:
        engine.dispose()


def _walk(ops):
    for op in getattr(ops, "ops", []):
        yield op
        yield from _walk(op)


def _operations(script) -> dict[str, list[tuple]]:
    found: dict[str, list[tuple]] = collections.defaultdict(list)
    for op in _walk(script.upgrade_ops):
        found[type(op).__name__].append((
            getattr(op, "table_name", None),
            getattr(op, "constraint_name", None)
            or getattr(op, "column_name", None)
            or getattr(op, "index_name", None),
        ))
    return found


# ── the capability itself ────────────────────────────────────────────────────

def test_every_cross_base_foreign_key_resolves_under_the_merge(merged) -> None:
    """NR-078's root cause, measured against the fix rather than described.

    310 foreign keys point at a table their own base does not own, and Alembic
    resolves every foreign key in `sorted_tables` before emitting an operation.
    Under one MetaData the count must be zero -- if it is not, the merge does
    not solve NR-078 and the conclusion in this file's docstring is wrong.
    """
    unresolved = sorted(
        (table.name, fk.parent.name, fk._table_key())
        for table in merged.tables.values()
        for fk in table.foreign_keys
        if fk._table_key() not in merged.tables
    )
    assert unresolved == [], (
        f"{len(unresolved)} foreign keys still do not resolve under a single "
        f"MetaData, so autogenerate cannot sort the schema: {unresolved[:10]}"
    )


def test_the_merge_has_no_duplicate_table_key(merged) -> None:
    """The blocker Option B could not clear, now cleared by Option A.

    Alembic refuses a multi-metadata target claiming one table twice. That was
    `national_facilities` alone -- NR-006's foreign-key anchor, column-identical
    to `NationalFacility`, not a rival entity. NR-086 put both bases on one
    MetaData, which made the anchor illegal as well as redundant, and deleted it.
    A duplicate appearing here again is a real ownership conflict and has to be
    decided before any topology change.
    """
    duplicates = set(merged.info.get("duplicates", []))
    assert duplicates == DECLARED_DUPLICATE_TABLE_KEYS, (
        "the set of table names claimed by more than one registered metadata "
        f"changed to {sorted(duplicates)}. Each is a canonical-ownership "
        "decision and none may be resolved by picking whichever import ran first"
    )


def test_autogenerate_actually_runs(autogenerated) -> None:
    """The assertion no previous guard made.

    `alembic revision --autogenerate` fails today with NoReferencedTableError.
    Under the merge it completes. If this ever raises, the gate has stopped
    measuring anything and every ledger below is vacuous.
    """
    operations = _operations(autogenerated)
    assert operations, "autogenerate produced no operations at all; it did not run"
    assert sum(len(v) for v in operations.values()) > 1000, (
        "autogenerate produced implausibly few operations; the comparison is "
        "probably running against an empty or unmigrated database"
    )


def test_autogenerate_is_deterministic(merged) -> None:
    """A diff that changes between runs cannot be reviewed operation by operation."""
    from alembic.autogenerate import produce_migrations
    from alembic.migration import MigrationContext

    shapes = []
    for _ in range(2):
        engine = create_engine(_require_database())
        try:
            with engine.connect() as connection:
                context = MigrationContext.configure(
                    connection, opts={"target_metadata": merged, "compare_type": False},
                )
                script = produce_migrations(context, merged)
        finally:
            engine.dispose()
        shapes.append({k: sorted(map(str, v)) for k, v in _operations(script).items()})
    assert shapes[0] == shapes[1], (
        "two autogenerate runs against the same database produced different "
        "operations; the diff cannot be reviewed or ratcheted"
    )


# ── the destructive boundary ─────────────────────────────────────────────────

def test_no_unexplained_table_drop_is_proposed(autogenerated) -> None:
    """Ten DROP TABLE proposals, and every one of them already has a reason.

    Cross-checked against `UNMAPPED_PHYSICAL_TABLES`, which is derived by
    subtracting mapped tables from physical ones -- a completely different
    route to the same list. An eleventh would mean a physical table lost its
    ORM owner, which is how a table gets dropped by accident.
    """
    proposed = {table for table, _ in _operations(autogenerated).get("DropTableOp", [])}
    unexplained = sorted(proposed - DECLARED_DROP_TABLE_PROPOSALS)
    assert unexplained == [], (
        "autogenerate proposes DROP TABLE for tables with no recorded reason: "
        f"{unexplained}. Map the table or record why it is intentionally "
        "unmapped; do not generate this migration"
    )
    resolved = sorted(DECLARED_DROP_TABLE_PROPOSALS - proposed)
    assert resolved == [], (
        "these tables are no longer proposed for DROP, which means they gained "
        f"an ORM owner; remove them from the ledger: {resolved}"
    )


def test_the_protected_column_drop_set_is_exactly_as_declared(autogenerated) -> None:
    """`patients.national_id` is proposed for DROP, and must never be acted on.

    Security Invariant #8 requires that column to hold encrypted national IDs.
    It is physical, it is indexed four ways, and the ORM maps only
    `national_id_hash` beside it. The same is true of `sndhs_health_id`,
    `identity_level`, `consent_flags` and `lab_orders.visit_id` -- the SNDHS
    Phase 1 surface, which CLAUDE.md gates behind `SNDHS_ENABLE_NATIONAL_ID`.

    Two directions matter and both are asserted. A column leaving this set means
    someone mapped it, which is the fix -- shrink the ledger. A column joining it
    means protected data just became invisible to the ORM and a DROP candidate.
    """
    proposed = set(_operations(autogenerated).get("DropColumnOp", []))
    relevant = {
        (table, column) for table, column in proposed
        if table in {t for t, _ in DECLARED_PROTECTED_DROP_COLUMNS}
    }
    assert relevant == DECLARED_PROTECTED_DROP_COLUMNS, (
        "the set of protected, physical, unmapped columns changed.\n"
        f"  newly proposed for DROP: {sorted(relevant - DECLARED_PROTECTED_DROP_COLUMNS)}\n"
        f"  no longer proposed:      {sorted(DECLARED_PROTECTED_DROP_COLUMNS - relevant)}\n"
        "A new entry means protected data became invisible to the ORM. A "
        "removed entry means it was mapped -- update the ledger."
    )


def test_the_destructive_budget_does_not_grow(autogenerated) -> None:
    """The ratchet on pre-existing drift.

    These 1367 operations are not a regression and not a plan: they are what
    the ORM and the database currently disagree about, measured for the first
    time. The number may fall as reconciliation proceeds. It may not rise.
    """
    operations = _operations(autogenerated)
    actual = {name: len(items) for name, items in operations.items() if "Drop" in name}
    grew = {
        name: (declared, actual.get(name, 0))
        for name, declared in DECLARED_DESTRUCTIVE_BUDGET.items()
        if actual.get(name, 0) > declared
    }
    assert grew == {}, (
        f"autogenerate now proposes more destructive operations (declared -> now): {grew}. "
        "Something was removed from the ORM while the database kept it"
    )
    appeared = sorted(set(actual) - set(DECLARED_DESTRUCTIVE_BUDGET))
    assert appeared == [], (
        f"a destructive operation type that has never been proposed appeared: {appeared}"
    )


def test_the_itemised_destructive_kinds_are_the_only_destructive_kinds(
    autogenerated,
) -> None:
    """Closes the gap between the budget and the whole diff.

    Three independent things have to agree, and each one catches a different
    way the headline figure can stop meaning what it says:

    * every kind the diff actually proposes is classified. A kind nobody has
      seen before fails here rather than being silently excluded by the
      `"Drop" in name` filter the budget uses;
    * the kinds marked destructive are exactly the budget's four keys, so the
      budget cannot name a kind this map calls harmless, or miss one it calls
      destructive;
    * the destructive counts still sum to the published 1367, so the docstring's
      headline and the budget below it cannot drift apart again the way 1379
      and 1367 did.
    """
    measured = {name: len(items) for name, items in _operations(autogenerated).items()}

    unclassified = sorted(set(measured) - set(DECLARED_OPERATION_KINDS))
    assert unclassified == [], (
        f"autogenerate proposed an operation kind nobody has classified: {unclassified}. "
        "Add each to DECLARED_OPERATION_KINDS as destructive (True) or not (False), "
        "and if destructive, give it a line in DECLARED_DESTRUCTIVE_BUDGET too."
    )

    marked_destructive = {
        name for name, destroys in DECLARED_OPERATION_KINDS.items() if destroys
    }
    assert marked_destructive == set(DECLARED_DESTRUCTIVE_BUDGET), (
        "the two ledgers disagree about what counts as destructive.\n"
        f"  marked destructive but unbudgeted: "
        f"{sorted(marked_destructive - set(DECLARED_DESTRUCTIVE_BUDGET))}\n"
        f"  budgeted but not marked:           "
        f"{sorted(set(DECLARED_DESTRUCTIVE_BUDGET) - marked_destructive)}"
    )

    published_total = sum(DECLARED_DESTRUCTIVE_BUDGET.values())
    assert published_total == 1367, (
        f"the budget now sums to {published_total}, not the 1367 this module's "
        "docstring publishes. Reconciliation should lower both together."
    )

    measured_destructive = sum(measured.get(name, 0) for name in marked_destructive)
    assert measured_destructive <= published_total, (
        f"{measured_destructive} destructive operations against a budget of "
        f"{published_total}. The budget is a ratchet: it may fall, not rise."
    )


def test_no_domain_grows_its_share_of_the_column_drops(autogenerated) -> None:
    """The aggregate budget cannot see redistribution. This can.

    `DropColumnOp: 377` stays 377 if radiology is reconciled by ten columns while
    ten new unmapped columns appear in trust. That is a defect arriving disguised
    as progress, and it is exactly the shape NR-079 warned about: a number is only
    worth the distance between it and what it is actually measuring.

    Demonstrated rather than argued. Mapping one radiology `lab_id` and unmapping
    one pharmacy column moves radiology 231 -> 230 and pharmacy 0 -> 1, and
    `TOTAL DropColumnOp` stays **377**. This test fails; the column half of the
    aggregate budget does not. (The budget did fail in that run, but on
    `DropIndexOp` -- the pharmacy column chosen happened to carry an index. Pick a
    column without one and the aggregate is silent, which is the whole point.)

    Per domain the counts may fall and may not rise. A domain appearing here that
    is not declared means physical columns in a new area just became invisible to
    the ORM.
    """
    counts: dict[str, int] = {}
    for table, _column in _operations(autogenerated).get("DropColumnOp", []):
        domain = _domain(table)
        counts[domain] = counts.get(domain, 0) + 1

    grew = sorted(
        f"{domain} ({count} > {DECLARED_COLUMN_DROPS_BY_DOMAIN.get(domain, 0)})"
        for domain, count in counts.items()
        if count > DECLARED_COLUMN_DROPS_BY_DOMAIN.get(domain, 0)
    )
    assert grew == [], (
        "autogenerate proposes dropping more columns in these domains than "
        "recorded, so physical columns there are newly unmapped. The aggregate "
        f"budget would not have caught this: {grew}"
    )

    emptied = sorted(
        domain for domain in DECLARED_COLUMN_DROPS_BY_DOMAIN
        if domain not in counts
    )
    assert emptied == [], (
        "these domains no longer propose any column drop, which means they were "
        f"reconciled; remove them so the ratchet keeps its grip: {emptied}"
    )
