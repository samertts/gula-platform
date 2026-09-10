"""Deterministic architecture detectors.

Each rule has a stable id, a severity, a rationale and a verification method.
A rule that cannot run reports ``DETECTOR_EXISTS_NOT_RUN`` rather than silently
reporting success.
"""
from __future__ import annotations

import ast
import collections
import importlib
import os
import pathlib
import re
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    import sqlalchemy
    import sqlalchemy.types

from .inventory import MIGRATIONS, REPO_ROOT, Inventory
from .model import (
    CheckResult,
    DetectorState,
    Finding,
    Rule,
    Severity,
    stable_id,
)

RULES: dict[str, Rule] = {
    r.id: r
    for r in [
        Rule(
            id="GULA-MIG-001",
            category="migration-integrity",
            severity=Severity.P0,
            title="Duplicate Alembic revision identifier",
            rationale=(
                "Alembic resolves a repeated id to one file and silently ignores the "
                "other, so a migration can never run and its schema never exists."
            ),
            remediation="Give each migration a unique revision id and chain it so it still runs.",
            verification="tools/gula_intel + backend/tests/migrations/test_migration_graph_integrity.py",
        ),
        Rule(
            id="GULA-MIG-002",
            category="migration-integrity",
            severity=Severity.P0,
            title="Alembic graph does not have exactly one head",
            rationale="'alembic upgrade head' cannot choose a target, so a clean database cannot be built.",
            remediation="Add a merge revision joining the independent branches.",
            verification="tools/gula_intel + migration graph integrity tests",
        ),
        Rule(
            id="GULA-ARCH-001",
            category="source-of-truth",
            severity=Severity.P1,
            title="Physical table mapped by more than one app package",
            rationale=(
                "Two domains writing one table with different invariants breaks the "
                "single-source-of-truth rule and can diverge silently."
            ),
            remediation="Declare one owning domain; others consume a read model.",
            verification="tools/gula_intel inventory table-ownership scan",
            architecture_decision_required=True,
        ),
        Rule(
            id="GULA-STATE-001",
            category="clinical-state-machine",
            severity=Severity.P1,
            title="Duplicate key in a shared state-transition table",
            rationale=(
                "A repeated state name silently shadows the earlier entry, so a legal "
                "clinical transition can become impossible without any error."
            ),
            remediation="Key transitions per entity type, or merge the colliding sets deliberately.",
            verification="tools/gula_intel AST scan; flake8 F601",
        ),
        Rule(
            id="GULA-SCHEMA-001",
            category="data-integrity",
            severity=Severity.P0,
            title="Foreign key column type incompatible with its target primary key",
            rationale=(
                "PostgreSQL refuses the constraint, so the migration chain cannot "
                "complete and the schema cannot be built."
            ),
            remediation="Establish the canonical identity type for the domain, then align both sides.",
            verification="clean-database alembic upgrade head",
            architecture_decision_required=True,
        ),
        Rule(
            id="GULA-SCHEMA-002",
            category="data-integrity",
            severity=Severity.P0,
            title="ORM model disagrees with the migration-built schema",
            rationale=(
                "An ORM that declares a column the database does not have, or a type "
                "the database will not accept, cannot execute against the real schema. "
                "P0-2 survived undetected because the pharmacy tests built their schema "
                "from ORM metadata, so the ORM could not disagree with itself."
            ),
            remediation=(
                "Follow the physical schema: it is authoritative for current reality. "
                "Reconcile the model to it, or migrate the schema deliberately."
            ),
            verification=(
                "reflect a migration-built PostgreSQL database and compare every mapped "
                "column, with both sides rendered through the same dialect"
            ),
            architecture_decision_required=True,
        ),
        Rule(
            id="GULA-ARCH-002",
            category="schema-governance",
            severity=Severity.P1,
            title="Declarative base is not registered for migration autogeneration",
            rationale=(
                "alembic autogenerate compares the database against the metadata listed "
                "in migrations/env.py. A declarative base missing from that list is "
                "invisible: autogenerate will neither create its tables nor report drift "
                "in them, and it does so silently, because an empty diff is "
                "indistinguishable from an accurate one."
            ),
            remediation=(
                "Register the base in target_metadata, or retire it. Registering a base "
                "changes what autogenerate emits, so it is a deliberate schema decision "
                "and not a mechanical fix."
            ),
            verification=(
                "resolve every entry of migrations/env.py target_metadata to its MetaData "
                "object and compare by identity against the discovered declarative bases"
            ),
            architecture_decision_required=True,
        ),
        Rule(
            id="GULA-SCHEMA-003",
            category="data-integrity",
            severity=Severity.P0,
            title="Mapped ORM table has no physical table",
            rationale=(
                "Every query against the model fails with UndefinedTable, so the "
                "endpoints that use it cannot work at all. GULA-SCHEMA-002 compares "
                "columns and therefore skips these tables entirely -- a domain with no "
                "physical schema whatsoever produced zero drift findings and read as "
                "clean."
            ),
            remediation=(
                "Decide per table: migrate the schema deliberately, or retire the model. "
                "Do not create the table merely to satisfy the detector."
            ),
            verification=(
                "compare every mapped __tablename__ against the table names of a "
                "migration-built PostgreSQL database"
            ),
            architecture_decision_required=True,
        ),
        Rule(
            id="GULA-SCHEMA-004",
            category="data-integrity",
            severity=Severity.P0,
            title="Domain depends on another domain's missing table",
            rationale=(
                "A domain can be fully reconciled against its own schema and still be "
                "broken at runtime by a model it imports from elsewhere. Pharmacy was "
                "VERIFIED at 27/27 tables while writing ehr_medication_dispenses, which "
                "does not exist, so a sale carrying a patient id could not complete. "
                "Per-domain verification cannot see across a domain boundary."
            ),
            remediation=(
                "Resolve the owning domain's schema, or remove the cross-domain write. "
                "A domain is not verified while a persistence dependency is missing."
            ),
            verification=(
                "resolve each cross-package model import to its __tablename__ and test "
                "that name against the physical schema"
            ),
            architecture_decision_required=True,
        ),
    ]
}


def detect_duplicate_revisions(inv: Inventory) -> CheckResult:
    rule = RULES["GULA-MIG-001"]
    if not inv.migrations:
        return CheckResult(rule.id, DetectorState.NOT_RUN, note="no migrations directory")
    findings = [
        Finding(
            rule_id=rule.id,
            occurrence_id=stable_id(rule.id, revision),
            title=f"{rule.title}: {revision}",
            severity=rule.severity,
            category=rule.category,
            domain="platform/migrations",
            affected=sorted(meta["files"]),
            evidence=f"revision {revision} declared by {len(meta['files'])} files: {sorted(meta['files'])}",
        )
        for revision, meta in sorted(inv.migrations.items())
        if len(meta["files"]) > 1
    ]
    return CheckResult(
        rule.id,
        DetectorState.RAN_FOUND if findings else DetectorState.RAN_CLEAN,
        findings,
        note=f"{len(inv.migrations)} revisions scanned",
    )


def detect_multiple_heads(inv: Inventory) -> CheckResult:
    rule = RULES["GULA-MIG-002"]
    if not inv.migrations:
        return CheckResult(rule.id, DetectorState.NOT_RUN, note="no migrations directory")
    parents = {d for meta in inv.migrations.values() for d in meta["downs"]}
    heads = sorted(set(inv.migrations) - parents)
    findings = []
    if len(heads) != 1:
        findings.append(
            Finding(
                rule_id=rule.id,
                occurrence_id=stable_id(rule.id, *heads),
                title=f"{rule.title}: found {len(heads)}",
                severity=rule.severity,
                category=rule.category,
                domain="platform/migrations",
                affected=heads,
                evidence=f"heads = {heads}",
                blocker=True,
            )
        )
    return CheckResult(
        rule.id,
        DetectorState.RAN_FOUND if findings else DetectorState.RAN_CLEAN,
        findings,
        note=f"heads={heads}",
    )


def detect_table_ownership_conflicts(inv: Inventory) -> CheckResult:
    rule = RULES["GULA-ARCH-001"]
    if not inv.tables:
        return CheckResult(rule.id, DetectorState.NOT_RUN, note="no ORM tables discovered")
    findings = [
        Finding(
            rule_id=rule.id,
            occurrence_id=stable_id(rule.id, table),
            title=f"{rule.title}: {table}",
            severity=rule.severity,
            category=rule.category,
            domain="platform/data-ownership",
            affected=[f"app/{pkg}" for pkg in packages],
            evidence=f"table '{table}' mapped by packages {packages}",
            architecture_decision_required=True,
        )
        for table, packages in sorted(inv.tables.items())
        if len(packages) > 1
    ]
    return CheckResult(
        rule.id,
        DetectorState.RAN_FOUND if findings else DetectorState.RAN_CLEAN,
        findings,
        note=f"{len(inv.tables)} mapped tables scanned",
    )


def detect_duplicate_state_keys(inv: Inventory) -> CheckResult:
    rule = RULES["GULA-STATE-001"]
    if not inv.transition_tables:
        return CheckResult(rule.id, DetectorState.NOT_RUN, note="no state-machine modules found")
    findings = []
    for file, literals in sorted(inv.transition_tables.items()):
        for keys in literals:
            counts = collections.Counter(name for name, _ in keys)
            for name, count in sorted(counts.items()):
                if count <= 1:
                    continue
                lines = [lineno for key, lineno in keys if key == name]
                findings.append(
                    Finding(
                        rule_id=rule.id,
                        occurrence_id=stable_id(rule.id, file, name),
                        title=f"{rule.title}: '{name}' in {pathlib.Path(file).name}",
                        severity=rule.severity,
                        category=rule.category,
                        domain="clinical/state-machine",
                        affected=[file],
                        evidence=f"key '{name}' repeated at lines {lines} of one dict literal; the later entry wins",
                    )
                )
    return CheckResult(
        rule.id,
        DetectorState.RAN_FOUND if findings else DetectorState.RAN_CLEAN,
        findings,
        note=f"{len(inv.transition_tables)} transition tables scanned",
    )


_FK_RE = re.compile(
    r'sa\.Column\(\s*"(?P<col>[^"]+)"\s*,\s*sa\.(?P<type>String\(\d+\)|Integer\(\))'
    r'\s*,\s*sa\.ForeignKey\(\s*"(?P<target>[^"]+)"',
)
_PK_RE = re.compile(r'"(?P<table>[a-z_]+)",\s*\n\s*sa\.Column\(\s*"id"\s*,\s*sa\.(?P<type>String\(\d+\)|Integer\(\))')


def _family(sa_type: str) -> str:
    return "string" if sa_type.startswith("String") else "integer"


def detect_fk_type_mismatch() -> CheckResult:
    """Compare declared foreign-key column types against the target's declared id type."""
    rule = RULES["GULA-SCHEMA-001"]
    if not MIGRATIONS.is_dir():
        return CheckResult(rule.id, DetectorState.NOT_RUN, note="no migrations directory")
    pk_types: dict[str, str] = {}
    for path in sorted(MIGRATIONS.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        for match in _PK_RE.finditer(text):
            pk_types.setdefault(match.group("table"), match.group("type"))
    findings = []
    for path in sorted(MIGRATIONS.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        for match in _FK_RE.finditer(text):
            target_table = match.group("target").split(".")[0]
            declared = pk_types.get(target_table)
            # varchar(64) -> varchar(36) is accepted by PostgreSQL; only a change of
            # type family (character varying vs integer) makes the key unbuildable.
            if declared and _family(declared) != _family(match.group("type")):
                findings.append(
                    Finding(
                        rule_id=rule.id,
                        occurrence_id=stable_id(rule.id, path.name, match.group("col")),
                        title=f"{rule.title}: {match.group('col')} -> {match.group('target')}",
                        severity=rule.severity,
                        category=rule.category,
                        domain="platform/schema",
                        affected=[f"backend/migrations/versions/{path.name}"],
                        evidence=(
                            f"column '{match.group('col')}' is {match.group('type')} but "
                            f"{target_table}.id is declared {declared}"
                        ),
                        blocker=True,
                        architecture_decision_required=True,
                    )
                )
    return CheckResult(
        rule.id,
        DetectorState.RAN_FOUND if findings else DetectorState.RAN_CLEAN,
        findings,
        note=f"{len(pk_types)} primary-key types resolved",
    )





# Domains whose ORM has been reconciled to the physical schema. Drift here is a
# regression. Everything else is still measured and still reported -- this set
# records what has been *proven*, it never suppresses a finding. Scoping the
# detector to one domain was itself a way of reporting VERIFIED for an
# unexamined repository, which is the defect BATCH-1 exists to remove.
RECONCILED_DOMAINS: frozenset[str] = frozenset({"pharmacy"})


def _model_modules() -> list[str]:
    """Every module that can define a declarative base or mapped model.

    A scan rather than a curated list, so a new domain is measured the day it
    is written instead of the day someone remembers to enrol it. Importing
    ``base``/``models`` modules directly avoids booting the application, which
    would seed databases and register routes -- a detector must not mutate the
    system it reports on.
    """
    app = REPO_ROOT / "backend" / "app"
    names: set[str] = set()
    for path in app.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        stem, parent = path.stem, path.parent.name
        if stem in {"base", "models"} or parent == "models":
            rel = path.relative_to(app).with_suffix("")
            parts = [p for p in rel.parts if p != "__init__"]
            if parts:
                names.add("app." + ".".join(parts))
    return sorted(names)


def _load_orm_metadata() -> list[tuple[str, sqlalchemy.MetaData]]:
    """Discover every declarative base reachable from the model modules.

    Returns one entry per distinct ``MetaData`` object, labelled by the module
    that owns it. Modules that fail to import are surfaced by
    :func:`_unimportable_model_modules` rather than skipped silently: an
    unmeasured module is UNKNOWN, and UNKNOWN must never read as VERIFIED.
    """
    import sqlalchemy

    backend = REPO_ROOT / "backend"
    for path in (str(REPO_ROOT), str(backend)):
        if path not in sys.path:
            sys.path.insert(0, path)

    by_metadata: dict[int, tuple[str, sqlalchemy.MetaData]] = {}
    for module_name in _model_modules():
        try:
            module = importlib.import_module(module_name)
        except BaseException as exc:
            if isinstance(exc, KeyboardInterrupt):
                raise
            _UNIMPORTABLE[module_name] = f"{type(exc).__name__}: {exc}"
            continue
        for attr in dir(module):
            obj = getattr(module, attr, None)
            metadata = getattr(obj, "metadata", None)
            if not (isinstance(metadata, sqlalchemy.MetaData) and hasattr(obj, "registry")):
                continue
            label = f"{module_name}.{attr}"
            existing = by_metadata.get(id(metadata))
            # Many modules re-export the same base, so the first label seen is
            # arbitrary and often names a model rather than the base itself.
            # Prefer a declaring module (``...base``) and then the shortest path,
            # so findings are attributed to something a reader can act on.
            if existing is None or _better_base_label(label, existing[0]):
                by_metadata[id(metadata)] = (label, metadata)
    return sorted(by_metadata.values(), key=lambda pair: pair[0])


def _better_base_label(candidate: str, current: str) -> bool:
    """Whether ``candidate`` names a declarative base more usefully than ``current``."""
    def rank(label: str) -> tuple[int, int, str]:
        module = label.rsplit(".", 1)[0]
        declaring = 0 if module.endswith((".base", ".database")) else 1
        return (declaring, module.count("."), label)
    return rank(candidate) < rank(current)


_UNIMPORTABLE: dict[str, str] = {}


def _unimportable_model_modules() -> dict[str, str]:
    """Model modules that could not be imported during the last discovery."""
    return dict(_UNIMPORTABLE)


def _domain_of(label: str) -> str:
    """The domain package a base label belongs to (``app.ehr.base.EHRBase`` -> ``ehr``)."""
    parts = label.split(".")
    return parts[1] if len(parts) > 1 else label



# ── GULA-SCHEMA-002 ─────────────────────────────────────────────────────────


def _render(type_: sqlalchemy.types.TypeEngine[object]) -> str:
    """Render a type through the PostgreSQL dialect.

    Both sides must go through this. ``str(type)`` drops flags such as
    ``TIMESTAMP(timezone=True)``, which fabricates a mismatch between an ORM
    column and the very column it already matches -- 84 such false positives
    were produced before this was corrected during the P0-2 analysis.
    """
    from sqlalchemy.dialects import postgresql

    try:
        # postgresql.dialect() is untyped in SQLAlchemy's stubs.
        return str(type_.compile(dialect=postgresql.dialect()))  # type: ignore[no-untyped-call]
    except Exception:
        return str(type_)


def detect_orm_schema_drift(database_url: str | None = None) -> CheckResult:
    """Compare mapped ORM columns against a migration-built PostgreSQL schema.

    Requires a real migrated database. Without one the detector reports
    ``RAN_EVIDENCE_UNAVAILABLE``: an ORM cannot be checked against a schema
    that is not there, and reporting "no findings" would turn UNKNOWN into
    VERIFIED, which the platform forbids.
    """
    rule = RULES["GULA-SCHEMA-002"]
    url = database_url or os.environ.get("GULA_INTEL_DATABASE_URL")
    if not url:
        return CheckResult(
            rule.id,
            DetectorState.RAN_NO_EVIDENCE,
            note="set GULA_INTEL_DATABASE_URL to a migration-built database to compare",
        )

    try:
        import sqlalchemy
    except ImportError:
        return CheckResult(rule.id, DetectorState.NOT_RUN, note="sqlalchemy unavailable")

    try:
        metadatas = _load_orm_metadata()
    except BaseException as exc:
        # BaseException deliberately: importing the application evaluates its
        # configuration, and a missing production setting raises SystemExit,
        # which does not derive from Exception. A detector must never be able
        # to terminate the run it is reporting on.
        if isinstance(exc, KeyboardInterrupt):
            raise
        return CheckResult(
            rule.id, DetectorState.NOT_RUN, note=f"ORM metadata unavailable: {exc}"
        )
    if not metadatas:
        return CheckResult(rule.id, DetectorState.NOT_RUN, note="no ORM metadata discovered")

    try:
        engine = sqlalchemy.create_engine(url)
        inspector = sqlalchemy.inspect(engine)
        physical_tables = set(inspector.get_table_names())
    except Exception as exc:
        return CheckResult(
            rule.id, DetectorState.RAN_NO_EVIDENCE, note=f"database unreachable: {exc}"
        )

    findings: list[Finding] = []
    compared = 0
    drifted: set[str] = set()
    for label, metadata in metadatas:
        for table_name, table in sorted(metadata.tables.items()):
            if table_name not in physical_tables:
                # A model with no physical table is a different defect: it may be
                # a pending migration rather than drift, so it is not reported here.
                continue
            compared += 1
            physical = {c["name"]: c for c in inspector.get_columns(table_name)}
            mapped = {c.name: c for c in table.columns}

            for name in sorted(set(mapped) - set(physical)):
                drifted.add(table_name)
                findings.append(
                    Finding(
                        rule_id=rule.id,
                        occurrence_id=stable_id(rule.id, f"{table_name}.{name}.orm-only"),
                        title=f"{rule.title}: {table_name}.{name} exists only in the ORM",
                        severity=rule.severity,
                        category=rule.category,
                        domain=label,
                        affected=[f"{table_name}.{name}"],
                        evidence=(
                            f"{label} maps {table_name}.{name} "
                            f"({_render(mapped[name].type)}); the database has no such column"
                        ),
                    )
                )

            for name in sorted(set(mapped) & set(physical)):
                orm_col, pg_col = mapped[name], physical[name]
                orm_type, pg_type = _render(orm_col.type), _render(pg_col["type"])
                if orm_type != pg_type:
                    drifted.add(table_name)
                    findings.append(
                        Finding(
                            rule_id=rule.id,
                            occurrence_id=stable_id(rule.id, f"{table_name}.{name}.type"),
                            title=f"{rule.title}: {table_name}.{name} type",
                            severity=rule.severity,
                            category=rule.category,
                            domain=label,
                            affected=[f"{table_name}.{name}"],
                            evidence=f"ORM {orm_type} != physical {pg_type}",
                        )
                    )
                elif bool(orm_col.nullable) != bool(pg_col["nullable"]):
                    drifted.add(table_name)
                    # Reported only when the type agrees, so one column yields one
                    # finding rather than two for the same underlying disagreement.
                    findings.append(
                        Finding(
                            rule_id=rule.id,
                            occurrence_id=stable_id(rule.id, f"{table_name}.{name}.nullable"),
                            title=f"{rule.title}: {table_name}.{name} nullability",
                            severity=rule.severity,
                            category=rule.category,
                            domain=label,
                            affected=[f"{table_name}.{name}"],
                            evidence=(
                                f"ORM nullable={bool(orm_col.nullable)} != "
                                f"physical nullable={bool(pg_col['nullable'])}"
                            ),
                        )
                    )

    return CheckResult(
        rule.id,
        DetectorState.RAN_FOUND if findings else DetectorState.RAN_CLEAN,
        findings,
        note=(
            f"{compared} mapped tables compared against the database; "
            f"{compared - len(drifted)} match exactly, {len(drifted)} drift"
        ),
    )


# ── GULA-SCHEMA-003 / GULA-SCHEMA-004 ───────────────────────────────────────


def _physical_tables(url: str) -> set[str] | str:
    """Table names of a migration-built database, or a reason they are unavailable."""
    import sqlalchemy

    try:
        engine = sqlalchemy.create_engine(url)
        return set(sqlalchemy.inspect(engine).get_table_names())
    except Exception as exc:
        return f"database unreachable: {exc}"


def _schema_evidence(
    rule_id: str, database_url: str | None
) -> tuple[set[str], list[tuple[str, sqlalchemy.MetaData]]] | CheckResult:
    """Physical tables plus loaded ORM metadata, or the CheckResult explaining why not."""
    url = database_url or os.environ.get("GULA_INTEL_DATABASE_URL")
    if not url:
        return CheckResult(
            rule_id,
            DetectorState.RAN_NO_EVIDENCE,
            note="set GULA_INTEL_DATABASE_URL to a migration-built database to compare",
        )
    try:
        import sqlalchemy  # noqa: F401
    except ImportError:
        return CheckResult(rule_id, DetectorState.NOT_RUN, note="sqlalchemy unavailable")

    physical = _physical_tables(url)
    if isinstance(physical, str):
        return CheckResult(rule_id, DetectorState.RAN_NO_EVIDENCE, note=physical)

    try:
        metadatas = _load_orm_metadata()
    except BaseException as exc:
        if isinstance(exc, KeyboardInterrupt):
            raise
        return CheckResult(
            rule_id, DetectorState.NOT_RUN, note=f"ORM metadata unavailable: {exc}"
        )
    if not metadatas:
        return CheckResult(rule_id, DetectorState.NOT_RUN, note="no ORM metadata discovered")
    return physical, metadatas


def detect_orm_tables_without_physical_table(
    database_url: str | None = None,
) -> CheckResult:
    """Mapped tables that do not exist in a migration-built database.

    One finding per table, attributed to the base that maps it, so the output
    says which domain owns the decision.
    """
    rule = RULES["GULA-SCHEMA-003"]
    evidence = _schema_evidence(rule.id, database_url)
    if isinstance(evidence, CheckResult):
        return evidence
    physical, metadatas = evidence

    findings: list[Finding] = []
    mapped_total = 0
    per_domain: dict[str, list[int]] = {}
    for label, metadata in metadatas:
        domain = _domain_of(label)
        missing = sorted(set(metadata.tables) - physical)
        mapped_total += len(metadata.tables)
        counts = per_domain.setdefault(domain, [0, 0])
        counts[0] += len(metadata.tables)
        counts[1] += len(missing)
        for table_name in missing:
            findings.append(
                Finding(
                    rule_id=rule.id,
                    occurrence_id=stable_id(rule.id, table_name),
                    title=f"{rule.title}: {table_name}",
                    severity=rule.severity,
                    category=rule.category,
                    domain=label,
                    affected=[table_name],
                    evidence=(
                        f"{label} maps {table_name}; the migration-built database has "
                        f"no such table, so every query against it raises UndefinedTable"
                    ),
                )
            )

    total_missing = sum(counts[1] for counts in per_domain.values())
    whole_domains = sorted(d for d, c in per_domain.items() if c[0] and c[0] == c[1])
    note = (
        f"{mapped_total} mapped tables across {len(metadatas)} declarative bases; "
        f"{total_missing} have no physical table"
    )
    if whole_domains:
        note += f"; no schema at all for: {', '.join(whole_domains)}"
    unimportable = _unimportable_model_modules()
    if unimportable:
        note += f"; {len(unimportable)} model modules UNMEASURED (import failed)"
    return CheckResult(
        rule.id,
        DetectorState.RAN_FOUND if findings else DetectorState.RAN_CLEAN,
        findings,
        note=note,
    )


# ── GULA-ARCH-002 ───────────────────────────────────────────────────────────

# The canonical registry for schema generation. Every declarative base must be
# reachable from this list or alembic cannot see it.
ALEMBIC_ENV = pathlib.Path("backend/migrations/env.py")


def _registered_metadata_ids() -> tuple[set[int], str]:
    """MetaData objects listed in ``target_metadata``, resolved by identity.

    By identity rather than by name: several bases are re-exported under more
    than one name (``CareContinuumBase`` and ``CareContinuumAuditEntity`` share
    one MetaData), so a name comparison invents drift that is not there.
    """
    path = REPO_ROOT / ALEMBIC_ENV
    if not path.exists():
        return set(), f"{ALEMBIC_ENV} not found"
    tree = ast.parse(path.read_text(encoding="utf-8"))

    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            getattr(t, "id", None) == "target_metadata" for t in node.targets
        ):
            elements = getattr(node.value, "elts", [])
            for element in elements:
                value = getattr(element, "value", None)
                if isinstance(value, ast.Name):
                    names.add(value.id)

    imports: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("app"):
            for alias in node.names:
                imports[alias.asname or alias.name] = node.module

    ids: set[int] = set()
    unresolved: list[str] = []
    for name in sorted(names):
        module_name = imports.get(name)
        if module_name is None:
            unresolved.append(name)
            continue
        try:
            obj = getattr(importlib.import_module(module_name), name)
            ids.add(id(obj.metadata))
        except BaseException as exc:
            if isinstance(exc, KeyboardInterrupt):
                raise
            unresolved.append(f"{name} ({type(exc).__name__})")
    note = f"{len(ids)} of {len(names)} target_metadata entries resolved"
    if unresolved:
        note += f"; unresolved: {', '.join(unresolved)}"
    return ids, note


def detect_unregistered_declarative_bases() -> CheckResult:
    """Declarative bases that alembic autogenerate cannot see."""
    rule = RULES["GULA-ARCH-002"]
    try:
        import sqlalchemy  # noqa: F401
    except ImportError:
        return CheckResult(rule.id, DetectorState.NOT_RUN, note="sqlalchemy unavailable")

    try:
        bases = _load_orm_metadata()
    except BaseException as exc:
        if isinstance(exc, KeyboardInterrupt):
            raise
        return CheckResult(rule.id, DetectorState.NOT_RUN, note=f"ORM metadata unavailable: {exc}")
    if not bases:
        return CheckResult(rule.id, DetectorState.NOT_RUN, note="no ORM metadata discovered")

    registered, note = _registered_metadata_ids()
    if not registered:
        return CheckResult(rule.id, DetectorState.RAN_NO_EVIDENCE, note=note)

    findings: list[Finding] = []
    unregistered_tables = 0
    for label, metadata in bases:
        if id(metadata) in registered:
            continue
        unregistered_tables += len(metadata.tables)
        findings.append(
            Finding(
                rule_id=rule.id,
                occurrence_id=stable_id(rule.id, label),
                title=f"{rule.title}: {label}",
                severity=rule.severity,
                category=rule.category,
                domain=label,
                affected=[str(ALEMBIC_ENV), label],
                evidence=(
                    f"{label} maps {len(metadata.tables)} tables and is absent from "
                    f"target_metadata, so autogenerate reports no drift for any of them"
                ),
            )
        )

    return CheckResult(
        rule.id,
        DetectorState.RAN_FOUND if findings else DetectorState.RAN_CLEAN,
        findings,
        note=(
            f"{len(bases)} declarative bases discovered; {note}; "
            f"{len(findings)} unregistered covering {unregistered_tables} mapped tables"
        ),
    )


def _mapped_classes() -> dict[str, tuple[str, str]]:
    """Class name -> (table, owning domain), read from the loaded mappers.

    A name that is not a mapped model simply does not appear, so an import of
    an ordinary helper is never mistaken for a persistence dependency.
    """
    found: dict[str, tuple[str, str]] = {}
    for module_name in list(sys.modules):
        if not module_name.startswith("app."):
            continue
        module = sys.modules.get(module_name)
        if module is None:
            continue
        for attr in dir(module):
            obj = getattr(module, attr, None)
            table = getattr(obj, "__tablename__", None)
            if isinstance(table, str) and hasattr(obj, "__mapper__"):
                found.setdefault(attr, (table, module_name.split(".")[1]))
    return found


def detect_cross_domain_missing_dependency(
    database_url: str | None = None,
) -> CheckResult:
    """Cross-package model imports whose table does not exist.

    Static: each ``from app.<other>... import Model`` is resolved to the
    ``__tablename__`` its mapper carries, then tested against the physical
    schema. It does not boot the application, register routes or run a
    lifespan.

    It is not, however, free of side effects, and the claim should not be made:
    importing a model module can transitively import a package that builds a
    singleton at module scope, and ``app.ai`` seeds ``ai_model_registry`` from
    ``ModelRegistry()`` at import time. Recorded as MCM-P1-6.
    """
    rule = RULES["GULA-SCHEMA-004"]
    evidence = _schema_evidence(rule.id, database_url)
    if isinstance(evidence, CheckResult):
        return evidence
    physical, _metadatas = evidence

    class_to_table = _mapped_classes()
    app_root = REPO_ROOT / "backend" / "app"
    findings: list[Finding] = []
    checked = 0
    for path in sorted(app_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        rel = path.relative_to(app_root)
        consumer = rel.parts[0] if len(rel.parts) > 1 else rel.stem
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or not node.module:
                continue
            if not node.module.startswith("app.") or "." not in node.module[4:]:
                continue
            provider = node.module.split(".")[1]
            if provider == consumer:
                continue
            for alias in node.names:
                resolved = class_to_table.get(alias.name)
                if resolved is None:
                    continue
                table_name, _owner = resolved
                checked += 1
                if table_name in physical:
                    continue
                findings.append(
                    Finding(
                        rule_id=rule.id,
                        occurrence_id=stable_id(rule.id, f"{consumer}->{table_name}"),
                        title=f"{rule.title}: {consumer} -> {table_name}",
                        severity=rule.severity,
                        category=rule.category,
                        domain=f"backend/app/{consumer}",
                        affected=[str(rel), table_name],
                        evidence=(
                            f"{rel} imports {alias.name} from {node.module}, whose table "
                            f"{table_name} does not exist; {consumer} cannot be verified "
                            f"while {provider} has no schema for it"
                        ),
                    )
                )

    affected = sorted({f.domain for f in findings})
    return CheckResult(
        rule.id,
        DetectorState.RAN_FOUND if findings else DetectorState.RAN_CLEAN,
        findings,
        note=(
            f"{checked} cross-package model imports resolved; "
            f"{len(findings)} depend on a missing table"
            + (f"; consumers affected: {', '.join(affected)}" if affected else "")
        ),
    )


def run_all(inv: Inventory) -> list[CheckResult]:
    return [
        detect_duplicate_revisions(inv),
        detect_multiple_heads(inv),
        detect_table_ownership_conflicts(inv),
        detect_duplicate_state_keys(inv),
        detect_fk_type_mismatch(),
        detect_orm_schema_drift(),
        detect_orm_tables_without_physical_table(),
        detect_cross_domain_missing_dependency(),
        detect_unregistered_declarative_bases(),
    ]
