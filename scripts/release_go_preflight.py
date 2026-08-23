#!/usr/bin/env python3
"""Validate the structural evidence required before a human GULA GO decision.

This utility is deliberately default-deny. It can establish only that the
release evidence register is complete and internally consistent; it never
asserts clinical acceptance or substitutes for an authorized human decision.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_EVIDENCE_PATH = Path("docs/GO_LAUNCH_EVIDENCE_MANIFEST.json")
DEFAULT_MIGRATIONS_PATH = Path("backend/migrations/versions")

REQUIRED_GATES = (
    "ci",
    "backend_regression",
    "security",
    "migration",
    "android_release",
    "uat",
)
REQUIRED_SIGNATURES = (
    "lims_authorizer",
    "clinical_recipient",
    "privacy_security",
    "platform_engineer",
    "clinical_safety_lead",
)


@dataclass(frozen=True)
class PreflightReport:
    status: str
    migration_heads: tuple[str, ...]
    failures: tuple[str, ...]
    warnings: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "migration_heads": list(self.migration_heads),
            "failures": list(self.failures),
            "warnings": list(self.warnings),
        }


def _literal_strings(node: ast.AST) -> tuple[str, ...]:
    """Return string values from a migration assignment without evaluating code."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return (node.value,)
    if isinstance(node, (ast.Tuple, ast.List)):
        values: list[str] = []
        for item in node.elts:
            values.extend(_literal_strings(item))
        return tuple(values)
    return ()


def migration_heads(migrations_dir: Path) -> tuple[str, ...]:
    """Calculate Alembic heads from literal revision/down_revision assignments."""
    revisions: set[str] = set()
    parents: set[str] = set()

    for path in sorted(migrations_dir.glob("*.py")):
        if path.name == "__init__.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        revision_values: tuple[str, ...] = ()
        parent_values: tuple[str, ...] = ()
        for statement in tree.body:
            if isinstance(statement, ast.Assign):
                names = {target.id for target in statement.targets if isinstance(target, ast.Name)}
                value = statement.value
            elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                names = {statement.target.id}
                value = statement.value
            else:
                continue
            if "revision" in names:
                revision_values = _literal_strings(value)
            if "down_revision" in names:
                parent_values = _literal_strings(value)
        if len(revision_values) != 1:
            raise ValueError(
                f"{path}: migration must have exactly one literal revision assignment",
            )
        revisions.add(revision_values[0])
        parents.update(parent_values)

    if not revisions:
        raise ValueError(f"No migration revisions found in {migrations_dir}")
    return tuple(sorted(revisions - parents))


def _required_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value.strip().upper() != "PENDING"


def evaluate_manifest(
    manifest: dict[str, Any],
    heads: tuple[str, ...],
) -> PreflightReport:
    """Validate evidence fields while retaining human authority over the GO decision."""
    failures: list[str] = []
    warnings: list[str] = []

    release = manifest.get("release")
    if not isinstance(release, dict):
        failures.append("release section is missing")
    else:
        for field in ("candidate_sha", "target_branch", "recorded_at"):
            if not _required_text(release.get(field)):
                failures.append(f"release.{field} is required")

    gates = manifest.get("gates")
    if not isinstance(gates, dict):
        failures.append("gates section is missing")
        gates = {}
    for gate_name in REQUIRED_GATES:
        gate = gates.get(gate_name)
        if not isinstance(gate, dict):
            failures.append(f"gates.{gate_name} is required")
            continue
        if gate.get("status") != "PASS":
            failures.append(f"gates.{gate_name}.status must be PASS")
        for field in ("owner", "recorded_at", "evidence"):
            if not _required_text(gate.get(field)):
                failures.append(f"gates.{gate_name}.{field} is required")

    migration_gate = gates.get("migration")
    if isinstance(migration_gate, dict):
        expected = migration_gate.get("expected_head")
        observed = migration_gate.get("observed_heads")
        if len(heads) != 1:
            failures.append(f"Alembic must have exactly one head; found {list(heads)}")
        if not _required_text(expected) or expected != (heads[0] if len(heads) == 1 else None):
            failures.append("migration.expected_head does not match the repository head")
        if observed != list(heads):
            failures.append("migration.observed_heads does not match the repository heads")

    signatures = manifest.get("signatures")
    if not isinstance(signatures, dict):
        failures.append("signatures section is missing")
        signatures = {}
    for role in REQUIRED_SIGNATURES:
        signature = signatures.get(role)
        if not isinstance(signature, dict):
            failures.append(f"signatures.{role} is required")
            continue
        if signature.get("decision") != "APPROVED":
            failures.append(f"signatures.{role}.decision must be APPROVED")
        for field in ("name", "signed_at", "evidence"):
            if not _required_text(signature.get(field)):
                failures.append(f"signatures.{role}.{field} is required")

    if not failures:
        warnings.append(
            "Evidence is structurally complete. An authorized release authority must still issue the GO decision.",
        )
        status = "HUMAN_GO_DECISION_REQUIRED"
    else:
        status = "NO_GO"

    return PreflightReport(
        status=status,
        migration_heads=heads,
        failures=tuple(failures),
        warnings=tuple(warnings),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE_PATH)
    parser.add_argument("--migrations-dir", type=Path, default=DEFAULT_MIGRATIONS_PATH)
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable report")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        manifest = json.loads(args.evidence.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError("Evidence manifest must be a JSON object")
        report = evaluate_manifest(manifest, migration_heads(args.migrations_dir))
    except (OSError, ValueError, json.JSONDecodeError, SyntaxError) as exc:
        report = PreflightReport(
            status="NO_GO",
            migration_heads=(),
            failures=(str(exc),),
            warnings=(),
        )

    if args.json:
        sys.stdout.write(
            json.dumps(report.as_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )
    else:
        lines = [
            f"RELEASE_GO_PREFLIGHT: {report.status}",
            f"Alembic heads: {', '.join(report.migration_heads) or 'unavailable'}",
            *(f"FAIL: {failure}" for failure in report.failures),
            *(f"WARNING: {warning}" for warning in report.warnings),
        ]
        sys.stdout.write("\n".join(lines) + "\n")

    return 0 if report.status == "HUMAN_GO_DECISION_REQUIRED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
