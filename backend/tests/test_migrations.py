"""
GULA Platform — Migration Chain Integrity Tests
================================================
Pure Python tests (no DB required) that verify:
  1. Base migration (0000) exists and is the true root (down_revision=None)
  2. Migration chain has no gaps and no orphans (every revision is reachable)
  3. No two revisions share the same ID
  4. 0001 correctly points to 0000 (the root cause of the production crash)
  5. All migration files compile without syntax errors

These run in < 1s with zero external dependencies — safe to run anywhere.

Run:
  cd backend && python -m pytest tests/test_migrations.py -v
"""
import importlib.util
import pathlib
import re
import sys

MIGRATIONS_DIR = pathlib.Path(__file__).parent.parent / "migrations" / "versions"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _read_migration_meta(path: pathlib.Path) -> dict:
    """Extract revision/down_revision from a migration file without importing it."""
    src = path.read_text()
    # Accept both untyped declarations and valid typed declarations such as
    # `revision: str = ...` used by the NIAM migration series.
    rev_match = re.search(r'^revision(?:\s*:\s*[^=]+)?\s*=\s*["\']([^"\']+)["\']', src, re.M)
    down_match = re.search(r"^down_revision(?:\s*:\s*[^=]+)?\s*=\s*([^\n]+)", src, re.M)

    revision = rev_match.group(1) if rev_match else None

    down_raw = down_match.group(1).strip() if down_match else "None"
    # Preserve every parent so Alembic merge revisions are validated correctly.
    if down_raw.startswith("("):
        inner = down_raw.strip("() ")
        down_revisions = [p.strip().strip("\"'") for p in inner.split(",") if p.strip()]
        down_revision = down_revisions[0] if down_revisions else None
    elif down_raw == "None":
        down_revisions = []
        down_revision = None
    else:
        down_revision = down_raw.strip("\"'")
        down_revisions = [down_revision]

    return {
        "revision": revision,
        "down_revision": down_revision,
        "down_revisions": down_revisions,
        "path": str(path),
    }


def _load_all_migrations() -> list[dict]:
    migs = []
    for p in sorted(MIGRATIONS_DIR.glob("*.py")):
        if p.name == "__init__.py" or p.name.startswith("_"):
            continue
        meta = _read_migration_meta(p)
        if meta["revision"]:
            migs.append(meta)
    return migs


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_base_migration_exists():
    """20250322_0000 must exist — it is the bootstrap foundation."""
    paths = list(MIGRATIONS_DIR.glob("*0000*"))
    assert paths, (
        "Base migration 20250322_0000_create_base_schema.py not found. "
        "Fresh deploys will crash with NoSuchTableError."
    )


def test_base_migration_is_root():
    """0000 must have down_revision=None (it IS the root, nothing before it)."""
    paths = list(MIGRATIONS_DIR.glob("*0000*"))
    assert paths, "Base migration not found"
    meta = _read_migration_meta(paths[0])
    assert meta["down_revision"] is None, (
        f"Base migration {paths[0].name} has down_revision={meta['down_revision']!r}. "
        "It must be None — it is the root of the migration chain."
    )


def test_0001_points_to_0000():
    """Migration 0001 must point to 0000, not None.

    This was the root cause of the production crash: 0001 had down_revision=None
    and assumed create_all() had already run. After the Dockerfile fix that
    assumption was false, causing NoSuchTableError: lab_users on every fresh deploy.
    """
    # Match only the original 20250322_0001 — other dated "0001" migrations
    # (e.g. 20260407_0001, 20260413_0001) are downstream revisions.
    paths = list(MIGRATIONS_DIR.glob("20250322_0001*"))
    assert paths, "Migration 20250322_0001 not found"
    meta = _read_migration_meta(paths[0])
    assert meta["down_revision"] == "20250322_0000", (
        f"Migration 20250322_0001 has down_revision={meta['down_revision']!r}. "
        "It MUST point to '20250322_0000' so the base schema is created first."
    )


def test_no_duplicate_revision_ids():
    """Every revision ID must be unique — duplicates cause alembic to error."""
    migs = _load_all_migrations()
    seen: dict[str, str] = {}
    for m in migs:
        rev = m["revision"]
        assert rev not in seen, (
            f"Duplicate revision ID '{rev}' in:\n"
            f"  {seen[rev]}\n  {m['path']}"
        )
        seen[rev] = m["path"]


def test_chain_has_exactly_one_root():
    """Exactly one migration may have down_revision=None (the true root)."""
    migs = _load_all_migrations()
    roots = [m for m in migs if m["down_revision"] is None]
    assert len(roots) == 1, (
        f"Expected exactly 1 root migration (down_revision=None), found {len(roots)}:\n"
        + "\n".join(f"  {r['path']}" for r in roots)
    )
    # The root must be 0000
    assert "0000" in roots[0]["revision"], (
        f"Root migration is '{roots[0]['revision']}', expected '20250322_0000'. "
        "Make sure 20250322_0000 is the base and all others chain from it."
    )


def test_chain_has_no_orphans():
    """Every non-root migration must reference a revision that actually exists."""
    migs = _load_all_migrations()
    all_revisions = {m["revision"] for m in migs}
    for m in migs:
        for parent in m["down_revisions"]:
            assert parent in all_revisions, (
                f"Migration {m['path']} references down_revision='{parent}' "
                f"which does not exist. This would cause 'Can't locate revision' errors."
            )


def test_chain_has_single_head_after_merges():
    """All migration branches must converge to exactly one current head.

    A branch is valid when it is explicitly converged by an Alembic merge
    revision. Requiring every parent to have at most one child would reject
    legitimate merge histories and encourage rewriting published migrations.
    """
    migs = _load_all_migrations()
    all_revisions = {m["revision"] for m in migs}
    referenced_parents = {
        parent for migration in migs for parent in migration["down_revisions"]
    }
    heads = all_revisions - referenced_parents
    assert len(heads) == 1, (
        "Migration graph must converge to exactly one head; found "
        f"{len(heads)}: {sorted(heads)}"
    )


def test_all_migration_files_compile():
    """Every migration file must be valid Python (no syntax errors)."""
    errors = []
    for p in sorted(MIGRATIONS_DIR.glob("*.py")):
        if p.name == "__init__.py":
            continue
        try:
            compile(p.read_text(), str(p), "exec")
        except SyntaxError as e:
            errors.append(f"  {p.name}: {e}")
    assert not errors, "Syntax errors in migration files:\n" + "\n".join(errors)


def test_chain_reachable_from_root():
    """All migrations must be reachable by traversing the chain from the root."""
    migs = _load_all_migrations()
    by_down: dict[str | None, list[str]] = {}
    for m in migs:
        for parent in m["down_revisions"]:
            by_down.setdefault(parent, []).append(m["revision"])

    # Walk the chain from root
    roots = [m["revision"] for m in migs if m["down_revision"] is None]
    if not roots:
        return  # caught by another test

    visited: set[str] = set()
    queue = list(roots)
    while queue:
        current = queue.pop()
        if current in visited:
            continue
        visited.add(current)
        queue.extend(by_down.get(current, []))

    all_revs = {m["revision"] for m in migs}
    unreachable = all_revs - visited
    assert not unreachable, (
        "Unreachable migrations (not in the chain from root):\n"
        + "\n".join(f"  {r}" for r in sorted(unreachable))
    )
