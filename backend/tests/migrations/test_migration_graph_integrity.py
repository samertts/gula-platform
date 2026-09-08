"""Structural invariants for the Alembic migration graph.

A duplicate revision id silently shadowed a migration for months: Alembic
resolved the id to one file and the other never ran, so the table it created was
missing from every database.  Multiple unmerged heads then made "alembic upgrade
head" impossible on a clean database.  These tests fail fast on both conditions.
"""
from __future__ import annotations

import ast
import collections
import pathlib

import pytest

VERSIONS = pathlib.Path(__file__).resolve().parents[2] / "migrations" / "versions"


def _module_level_assignment(tree: ast.Module, name: str):
    for node in tree.body:
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        if any(getattr(t, "id", None) == name for t in targets):
            try:
                return ast.literal_eval(node.value)
            except (ValueError, SyntaxError):
                return None
    return None


def _revisions() -> list[tuple[str, str]]:
    found = []
    for path in sorted(VERSIONS.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        revision = _module_level_assignment(tree, "revision")
        if revision:
            found.append((revision, path.name))
    return found


def test_revision_identifiers_are_unique() -> None:
    """A repeated id makes one migration unreachable and it silently never runs."""
    revisions = _revisions()
    assert revisions, "no migrations found"
    duplicates = {
        revision: [name for rev, name in revisions if rev == revision]
        for revision, count in collections.Counter(rev for rev, _ in revisions).items()
        if count > 1
    }
    assert not duplicates, f"duplicate Alembic revision ids: {duplicates}"


def test_migration_graph_has_exactly_one_head() -> None:
    """Multiple heads make 'alembic upgrade head' fail on a clean database."""
    parents: set[str] = set()
    revisions = []
    for path in sorted(VERSIONS.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        revision = _module_level_assignment(tree, "revision")
        if not revision:
            continue
        revisions.append(revision)
        down = _module_level_assignment(tree, "down_revision")
        if isinstance(down, (tuple, list)):
            parents.update(d for d in down if d)
        elif down:
            parents.add(down)
    heads = sorted(set(revisions) - parents)
    assert len(heads) == 1, f"expected exactly one Alembic head, found {heads}"


@pytest.mark.parametrize("required", ["clinical_command_receipts"])
def test_safety_critical_tables_are_created_by_a_migration(required: str) -> None:
    """The guarded clinical write path depends on this table existing."""
    creators = [
        path.name
        for path in VERSIONS.glob("*.py")
        if f'"{required}"' in path.read_text(encoding="utf-8")
        and "create_table" in path.read_text(encoding="utf-8")
    ]
    assert creators, f"no migration creates {required}"
