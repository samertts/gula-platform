"""Regression coverage for the complete SQLite Alembic round-trip."""
from __future__ import annotations

import os
from pathlib import Path
import sqlite3
import subprocess
import sys


HEAD_REVISION = "20260820_0008"


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "backend" / "alembic.ini").exists():
            return parent
    raise AssertionError("Could not locate the repository root")


def _run_alembic(backend_dir: Path, database_url: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment.update(
        {
            "DATABASE_URL": database_url,
            "MIGRATION_DATABASE_URL": database_url,
            "PYTHONPATH": str(backend_dir.parent),
        }
    )
    return subprocess.run(
        [sys.executable, "-m", "alembic", *arguments],
        cwd=backend_dir,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def _revision_rows(database_path: Path) -> list[str]:
    with sqlite3.connect(database_path) as connection:
        return [row[0] for row in connection.execute("SELECT version_num FROM alembic_version")]


def test_sqlite_alembic_upgrade_and_downgrade_round_trip(tmp_path: Path) -> None:
    repo_root = _repo_root()
    backend_dir = repo_root / "backend"
    database_path = tmp_path / "alembic-roundtrip.sqlite"
    database_url = f"sqlite:///{database_path}"

    upgrade = _run_alembic(backend_dir, database_url, "upgrade", "head")
    assert upgrade.returncode == 0, upgrade.stdout + upgrade.stderr
    assert _revision_rows(database_path) == [HEAD_REVISION]

    downgrade = _run_alembic(backend_dir, database_url, "downgrade", "base")
    assert downgrade.returncode == 0, downgrade.stdout + downgrade.stderr
    assert _revision_rows(database_path) == []
