"""Deterministic architecture detectors.

Each rule has a stable id, a severity, a rationale and a verification method.
A rule that cannot run reports ``DETECTOR_EXISTS_NOT_RUN`` rather than silently
reporting success.
"""
from __future__ import annotations

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





_ORM_MODULES: tuple[tuple[str, str, str], ...] = (
    # (label, module, attribute holding the declarative base)
    ("backend/app/pharmacy", "app.pharmacy.models", "PharmacyBase"),
)


def _load_orm_metadata() -> list[tuple[str, sqlalchemy.MetaData]]:
    """Import the declarative bases this detector knows how to compare.

    Deliberately an explicit list rather than a scan. A model package is added
    here once its ORM has been reconciled to the physical schema, so the
    detector reports real drift rather than the known, tracked divergence of a
    package still awaiting reconciliation.
    """
    backend = REPO_ROOT / "backend"
    for path in (str(REPO_ROOT), str(backend)):
        if path not in sys.path:
            sys.path.insert(0, path)

    loaded: list[tuple[str, sqlalchemy.MetaData]] = []
    for label, module_name, base_attr in _ORM_MODULES:
        module = importlib.import_module(module_name)
        base = getattr(module, base_attr, None)
        if base is None:
            base_module = importlib.import_module(module_name.rsplit(".", 1)[0] + ".base")
            base = getattr(base_module, base_attr)
        loaded.append((label, base.metadata))
    return loaded



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


def run_all(inv: Inventory) -> list[CheckResult]:
    return [
        detect_duplicate_revisions(inv),
        detect_multiple_heads(inv),
        detect_table_ownership_conflicts(inv),
        detect_duplicate_state_keys(inv),
        detect_fk_type_mismatch(),
        detect_orm_schema_drift(),
    ]
