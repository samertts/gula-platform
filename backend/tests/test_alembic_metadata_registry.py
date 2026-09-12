"""Fail-closed guards on the metadata Alembic actually sees.

BATCH-2.5 closed one instance of a hazard: four bases were registered for
autogeneration while resolving to an EMPTY MetaData, so autogenerate would have
compared zero mapped tables against a populated database and proposed dropping
all 74 of their physical tables.

BATCH-2.6 measured the general case. "Registered" is not the same as
"complete": IdentityBase held 39 tables while 48 of its own were never
imported. Across the registry, 64 physical tables were mapped by no registered
metadata at all. Empty was merely the extreme end of that spectrum.

These guards therefore assert the whole invariant, not the empty case:

  * no registered metadata is empty;
  * every physical table is mapped, except a pinned, named list;
  * every foreign key names a table that exists somewhere, except a pinned list;
  * exactly one table name is claimed by two registered metadata.

Each pinned set is an assertion of a *known defect*. When one is fixed the guard
fails, which is the signal to close the finding and tighten the pin — never to
widen it.

The import graph is read from ``backend/migrations/env.py`` itself rather than
restated here. A second list would drift from the first, and drift is the defect
this file exists to catch.
"""
from __future__ import annotations

import ast
import importlib
import os
import sys
from contextlib import suppress
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_PY = REPO_ROOT / "backend" / "migrations" / "env.py"

# This guard needs a real database migrated to head, and DATABASE_URL cannot
# supply it: backend/tests/conftest.py pins that variable to in-memory SQLite
# for the whole suite, and app.config rewrites it again from backend/.env. Both
# happen before this module's fixtures run, so a value read from DATABASE_URL
# would silently describe a different database than the caller named.
# GULA_SCHEMA_DATABASE_URL is owned by this guard, following the same
# convention as GULA_INTEL_DATABASE_URL.
def _schema_database_url() -> str:
    """The database this module inspects, migrated to head.

    DATABASE_URL cannot supply it: conftest pins that variable to in-memory
    SQLite for the whole suite. GULA_SCHEMA_DATABASE_URL is this guard's own
    variable; MIGRATION_DATABASE_URL is the one CI already exports for the
    migrated PostgreSQL service, so the guard runs there without the workflow
    having to name a second variable for the same database.
    """
    return (os.environ.get("GULA_SCHEMA_DATABASE_URL")
            or os.environ.get("MIGRATION_DATABASE_URL", ""))


SCHEMA_DATABASE_URL = _schema_database_url()

# Physical tables mapped by no ORM class anywhere (NR-030), each with its
# BATCH-2.7 disposition. Every entry is a DROP candidate for a single-MetaData
# autogenerate, so the list is an explicit, named exclusion — never a silent one.
UNMAPPED_PHYSICAL_TABLES = frozenset({
    # KEEP_PHYSICAL_NO_ORM — Financial Engine Phase A is schema-only by design
    # (CLAUDE.md). Writing models for these would be adding Phase B logic.
    "fin_ads_campaigns", "fin_ads_clicks", "fin_ads_conversions",
    "fin_clinical_behavior", "fin_fraud_logs", "fin_market_benchmarks",
    # KEEP_PHYSICAL_NO_ORM — deliberately raw SQL in app/core/idempotency.py,
    # a request hot path that does not want an ORM round trip.
    "idempotency_keys",
    # (BATCH-3 resolved the two nursing entries that stood here.
    # ClinicalChecklist and EscalationRecord named nursing_checklists and
    # nursing_escalations, tables no migration creates; they now name the real
    # tables, so both left this list and the shared-MetaData DROP set with
    # them. No table entered either.)
    # CREATE_ORM — 34 columns and 6 foreign keys, and the only radiology table
    # of eighteen with no model. Mechanical, but not authorised in BATCH-2.7.
    "radiology_ai_analysis_jobs",
    # BLOCKED — a parallel UUID-keyed audit surface from SNDHS Phase 1 whose
    # promised service (app/services/sndhs_audit.py) was never written.
    "sndhs_audit_logs",
    # BLOCKED — the clinical episode anchor. Its model is part of adopting
    # Visit as canonical, which waits on the clinical owner.
    "visits",
})

# Foreign keys naming a table that is neither mapped nor physical (NR-029).
#
# Empty since BATCH-2.7. The three declarations that populated it named the ORM
# *class* rather than its __tablename__ — IdentityAuthority is
# niam_gov_authorities, UserSession is niam_sessions — while the migrations had
# written the real names all along and PostgreSQL already enforced both foreign
# keys. Repointing the ORM closed it with no migration and no schema change.
PHANTOM_FK_TARGETS: frozenset[str] = frozenset()

# Registered metadata holding zero tables (NR-024).
EMPTY_REGISTERED_BASES = frozenset({"CitizenPlatformBase"})

# One table name claimed by two registered metadata (NR-006).
TABLE_NAME_COLLISIONS = frozenset({"national_facilities"})


def _load_registry() -> list[tuple[str, object]]:
    """Replay env.py's model imports and return its labelled target_metadata.

    env.py runs the migration at module scope, so it cannot be imported. Its
    import statements and its ``target_metadata`` list are read instead, which
    keeps this guard honest: it measures what Alembic is handed, not what a
    second list claims.
    """
    os.environ["RUNTIME_MODE"] = "migration"
    for key, value in {
        "ENV": "migration",
        "SECRET_KEY": "alembic-migration-key-" + "x" * 48,
        "ENCRYPTION_KEY": "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=",
        "NID_HMAC_KEY": "a" * 64,
        "REDIS_URL": "",
        "BASE_URL": "http://localhost:8000",
    }.items():
        os.environ.setdefault(key, value)
    for path in (str(REPO_ROOT), str(REPO_ROOT / "backend")):
        if path not in sys.path:
            sys.path.insert(0, path)

    tree = ast.parse(ENV_PY.read_text(encoding="utf-8"), filename=str(ENV_PY))
    namespace: dict[str, object] = {}

    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("app."):
                    importlib.import_module(alias.name)
        elif isinstance(node, ast.ImportFrom) and (node.module or "").startswith("app"):
            module = importlib.import_module(node.module)
            for alias in node.names:
                namespace[alias.asname or alias.name] = getattr(module, alias.name)
        elif isinstance(node, ast.For) and isinstance(node.iter, ast.List):
            # env.py also imports a batch of domain models through a loop over a
            # list of module names, guarded by suppress(ImportError). Replaying
            # only the static import statements would miss them and report their
            # tables as unmapped, which is the opposite of the truth.
            for element in node.iter.elts:
                if isinstance(element, ast.Constant) and str(element.value).startswith("app."):
                    with suppress(ImportError):
                        importlib.import_module(element.value)

    namespace["import_all_models"]()  # type: ignore[operator]

    for node in tree.body:
        if (isinstance(node, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "target_metadata" for t in node.targets)
                and isinstance(node.value, ast.List)):
            registry = []
            for element in node.value.elts:
                label = ast.unparse(element)           # e.g. "PharmacyBase.metadata"
                base = label.rsplit(".", 1)[0]
                registry.append((base, namespace[base].metadata))
            return registry

    raise AssertionError("env.py no longer assigns a target_metadata list")


@pytest.fixture(scope="module")
def registry():
    """Load env.py's metadata, then put the environment back as it was.

    _load_registry() sets RUNTIME_MODE=migration and other alembic-mode
    variables so app.config will import. Those are process-global: leaving them
    set changes how the application behaves for every test that runs after this
    module, which showed up as a blood-bank test failing only when this file ran
    first. The imports themselves are idempotent and are left in place.
    """
    saved = dict(os.environ)
    try:
        yield _load_registry()
    finally:
        os.environ.clear()
        os.environ.update(saved)


@pytest.fixture(scope="module")
def mapped(registry) -> set[str]:
    return {name for _, metadata in registry for name in metadata.tables}


def test_no_registered_metadata_is_empty(registry) -> None:
    """The BATCH-2.5 hazard, guarded permanently.

    An empty registered metadata is worse than an unregistered one: autogenerate
    compares zero mapped tables against a populated database and proposes
    dropping every table the base owns.
    """
    empty = {label for label, metadata in registry if not metadata.tables}
    assert empty <= set(EMPTY_REGISTERED_BASES), (
        "a base is registered for autogeneration but maps no tables, so "
        "autogenerate would propose dropping its physical tables: "
        + ", ".join(sorted(empty - set(EMPTY_REGISTERED_BASES)))
    )
    assert empty == set(EMPTY_REGISTERED_BASES), (
        "NR-024 appears resolved; tighten this guard rather than leaving it "
        "asserting a defect that no longer exists"
    )


def test_every_foreign_key_names_a_table_that_exists(registry, mapped) -> None:
    """A foreign key to a table no model defines cannot resolve in any design."""
    phantom: dict[str, int] = {}
    for _, metadata in registry:
        for table in metadata.tables.values():
            for fk in table.foreign_keys:
                target = fk.target_fullname.rsplit(".", 1)[0]
                if target not in mapped:
                    phantom[target] = phantom.get(target, 0) + 1

    unexpected = set(phantom) - set(PHANTOM_FK_TARGETS) - UNMAPPED_PHYSICAL_TABLES
    assert not unexpected, (
        f"foreign keys name tables that exist nowhere: {sorted(unexpected)}. "
        "Define the model or remove the reference; do not delete the foreign key "
        "to silence this."
    )


def test_exactly_one_table_name_is_claimed_by_two_registered_metadata(registry) -> None:
    """NR-006, and the single blocker for a canonical shared MetaData."""
    owners: dict[str, list[str]] = {}
    for label, metadata in registry:
        for name in metadata.tables:
            owners.setdefault(name, []).append(label)
    collisions = {name for name, labels in owners.items() if len(labels) > 1}
    assert collisions == set(TABLE_NAME_COLLISIONS), (
        f"the set of table names blocking a shared MetaData changed: {sorted(collisions)}"
    )


@pytest.mark.skipif(
    not SCHEMA_DATABASE_URL,
    reason="GULA_SCHEMA_DATABASE_URL is not configured; this guard needs a database migrated to head",
)
def test_every_physical_table_is_mapped_by_a_registered_metadata(mapped) -> None:
    """The general form of the hazard: an unmapped physical table is a DROP candidate.

    Requires a database migrated to head. Measured there: 64 physical tables were
    mapped by nothing until env.py imported the modules that declare them, and
    twelve remain mapped by no ORM class at all.
    """
    from sqlalchemy import create_engine, inspect

    engine = create_engine(SCHEMA_DATABASE_URL)
    try:
        physical = set(inspect(engine).get_table_names()) - {"alembic_version"}
    finally:
        engine.dispose()

    if not physical:
        pytest.skip("database has no tables; not migrated to head")

    unmapped = physical - mapped
    unexpected = unmapped - UNMAPPED_PHYSICAL_TABLES
    assert not unexpected, (
        f"physical tables mapped by no registered metadata: {sorted(unexpected)}. "
        "Autogenerate would propose DROP TABLE for each. Import the module that "
        "declares them, or add them to UNMAPPED_PHYSICAL_TABLES with a reason."
    )
    resolved = UNMAPPED_PHYSICAL_TABLES - unmapped
    assert not resolved, (
        f"these tables are now mapped: {sorted(resolved)}. Remove them from "
        "UNMAPPED_PHYSICAL_TABLES so the guard keeps its meaning."
    )


@pytest.mark.skipif(
    not SCHEMA_DATABASE_URL,
    reason="GULA_SCHEMA_DATABASE_URL is not configured; this guard needs a database migrated to head",
)
def test_a_shared_metadata_would_not_drop_an_unlisted_table(registry, mapped) -> None:
    """Condition E: the destructive half of the single-MetaData architecture.

    BATCH-2.6 measured what a combined MetaData would emit against a database at
    head: 5,101 operations including 76 DROP TABLE. Importing the modules that
    were never imported cut that to the named list above. This guard is the one
    that would have caught the original hazard: it asserts that the set of
    tables a shared MetaData would propose dropping is exactly the set someone
    has written down and justified.

    It deliberately does not build the shared MetaData — that architecture is
    blocked (NR-006) — it measures the same quantity the architecture would act
    on.
    """
    from sqlalchemy import create_engine, inspect

    engine = create_engine(SCHEMA_DATABASE_URL)
    try:
        physical = set(inspect(engine).get_table_names()) - {"alembic_version"}
    finally:
        engine.dispose()

    if not physical:
        pytest.skip("database has no tables; not migrated to head")

    would_drop = physical - mapped
    assert would_drop == set(UNMAPPED_PHYSICAL_TABLES), (
        "the set of tables a shared MetaData would DROP no longer matches the "
        f"reviewed list. Unexpected: {sorted(would_drop - UNMAPPED_PHYSICAL_TABLES)}; "
        f"no longer at risk: {sorted(UNMAPPED_PHYSICAL_TABLES - would_drop)}"
    )


# ── NR-078 — the guard above asks the weaker half of the question ────────────
#
# `PHANTOM_FK_TARGETS` asks whether a foreign key names a table that exists
# **somewhere** across the registry. SQLAlchemy asks something stricter: it
# resolves a ForeignKey inside the MetaData that owns the *referring* table. A
# declaration pointing at a table owned by a different declarative base names a
# table that exists, passes that guard, and still cannot resolve.
#
# Measured across the registry env.py actually hands Alembic: **310** foreign
# keys are in that state, across five bases. NR-075 -- the five on
# `niam_citizen_relationships` that stop `POST /admin/citizen-relationships`
# from inserting a row -- is 1.6% of the class.
#
# The consequence is larger than any one endpoint, and it is a defect in the
# measuring instrument rather than in the thing measured. Alembic's
# `sorted_tables` resolves every foreign key before it emits a single
# operation, so:
#
#     $ alembic revision --autogenerate -m "anything"
#     sqlalchemy.exc.NoReferencedTableError: Foreign key associated with column
#     'ehr_allergies.citizen_id' could not find table 'national_citizens'
#
# **`alembic revision --autogenerate` cannot run against this repository at
# all.** It is the command CLAUDE.md's migration policy names as the way to make
# any schema change, and it has no working path. Nothing detected that, because
# every guard in this file reasons about what autogenerate *would* propose and
# none of them has ever asked autogenerate to propose it.
#
# The ledger is per-base and may shrink. It may never grow, and no base may
# appear. Closing it is a declarative-base topology decision (share MetaData, or
# drop the ORM-level ForeignKey and keep the physical constraint) with a real
# risk of autogenerate then proposing to DROP constraints PostgreSQL is
# enforcing today, so it is measured here and decided by a human.
UNRESOLVABLE_CROSS_BASE_FKS = {
    "CareContinuumBase": 214,
    "EHRBase": 70,
    "DataPlatformBase": 13,
    "TrustBase": 8,
    "IdentityBase": 5,
}


def _cross_base_foreign_keys(registry) -> list[tuple[str, str, str, str]]:
    """(base, table, column, target) for each FK its own MetaData cannot see."""
    found: list[tuple[str, str, str, str]] = []
    for label, metadata in registry:
        own = set(metadata.tables)
        for table in metadata.tables.values():
            for fk in table.foreign_keys:
                target = fk._table_key()
                if target not in own:
                    found.append((label, table.name, fk.parent.name, target))
    return found


def test_the_cross_base_foreign_key_scan_still_finds_the_surface(registry) -> None:
    """Guard the guard: finding none would ratchet nothing."""
    found = _cross_base_foreign_keys(registry)
    assert len(found) >= 250, (
        f"only {len(found)} cross-base foreign keys found; the scan has drifted "
        "and every count below would be understated"
    )


def test_no_base_gains_a_foreign_key_its_own_metadata_cannot_resolve(registry) -> None:
    """The ratchet. A new one is an INSERT that will fail on flush."""
    import collections

    counts = collections.Counter(row[0] for row in _cross_base_foreign_keys(registry))
    appeared = sorted(set(counts) - set(UNRESOLVABLE_CROSS_BASE_FKS))
    assert appeared == [], (
        "these declarative bases now declare a foreign key to a table owned by "
        "another base. SQLAlchemy resolves foreign keys inside the referring "
        f"table's own MetaData, so those rows cannot be INSERTed: {appeared}"
    )
    widened = {
        base: (declared, counts.get(base, 0))
        for base, declared in UNRESOLVABLE_CROSS_BASE_FKS.items()
        if counts.get(base, 0) > declared
    }
    assert widened == {}, (
        f"cross-base foreign keys were added (declared -> now): {widened}"
    )


def test_the_cross_base_foreign_key_ledger_does_not_rot(registry) -> None:
    """A base that resolved its foreign keys must leave the ledger."""
    import collections

    counts = collections.Counter(row[0] for row in _cross_base_foreign_keys(registry))
    resolved = sorted(
        base for base, declared in UNRESOLVABLE_CROSS_BASE_FKS.items()
        if counts.get(base, 0) < declared
    )
    assert resolved == [], (
        "these bases now declare fewer unresolvable foreign keys than the "
        "ledger claims; lower the numbers so the ratchet keeps its grip: "
        f"{ {b: (UNRESOLVABLE_CROSS_BASE_FKS[b], counts.get(b, 0)) for b in resolved} }"
    )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "NR-078: `alembic revision --autogenerate` cannot run. Alembic sorts "
        "every registered MetaData before emitting an operation, and 310 "
        "cross-base foreign keys cannot resolve. Fixing it is a declarative-base "
        "topology decision, so this is held as a strict xfail: it fails loudly "
        "the moment autogenerate starts working, which is the signal to close "
        "NR-078 and NR-075 rather than to delete this test."
    ),
)
def test_alembic_can_sort_every_registered_metadata(registry) -> None:
    """The capability every other guard in this file assumes and none exercises.

    `alembic.autogenerate` reaches `MetaData.sorted_tables` on each registered
    metadata before it compares anything. This is that step, isolated: if it
    raises, no autogenerate diff exists to reason about, and a guard that asks
    "what would autogenerate propose?" is asking about something that never
    runs.
    """
    for label, metadata in registry:
        try:
            assert metadata.sorted_tables is not None
        except Exception as exc:  # the failure is the measurement
            raise AssertionError(
                f"{label}.metadata cannot be sorted, so autogenerate cannot "
                f"produce a diff: {exc}"
            ) from exc
