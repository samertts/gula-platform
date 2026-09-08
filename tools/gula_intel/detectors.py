"""Deterministic architecture detectors.

Each rule has a stable id, a severity, a rationale and a verification method.
A rule that cannot run reports ``DETECTOR_EXISTS_NOT_RUN`` rather than silently
reporting success.
"""
from __future__ import annotations

import ast
import collections
import pathlib
import re

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


def run_all(inv: Inventory) -> list[CheckResult]:
    return [
        detect_duplicate_revisions(inv),
        detect_multiple_heads(inv),
        detect_table_ownership_conflicts(inv),
        detect_duplicate_state_keys(inv),
        detect_fk_type_mismatch(),
    ]
