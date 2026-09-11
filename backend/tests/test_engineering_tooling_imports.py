"""NR-056 — the engineering tooling imports through the root the package actually has.

`backend/` is not a package: it has no `__init__.py`, and `backend/pyproject.toml`
publishes `include = ["app*"]`. So `backend.app.…` never resolves from an
installed distribution — only from an interpreter that happens to have the
repository root on `sys.path`. `tests/conftest.py` puts it there (for the
unrelated `shared` package) and CI exports it too, which is exactly why
seventeen generator modules and the whole productivity CLI could sit broken
behind a green test suite.

That is the trap these tests are built to avoid. Anything that asserts
importability runs in a **subprocess rooted at `backend/` with no PYTHONPATH at
all**, so `app` resolves the way the installed package provides it and
`backend.app` resolves not at all. Importing these modules inside the pytest
process would prove nothing: this process can import both roots.

NR-053 repaired the same defect in `generators/capability.py`; NR-056 is the
rest of the family plus `productivity/cli.py`, which loads all of them.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
ENGINEERING = BACKEND / "app" / "engineering"

# The root that does not exist. Kept as a tuple so the guard reads the same way
# whether the offender wrote `from backend.app.x import y` or `import backend.app.x`.
INVALID_ROOT = "backend"


# ── Package-level discovery, so a generator added tomorrow is covered too ─────


def _module_paths() -> list[Path]:
    return sorted(
        p for p in ENGINEERING.rglob("*.py") if "__pycache__" not in p.parts
    )


def _dotted(path: Path) -> str:
    parts = path.relative_to(BACKEND).with_suffix("").parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _imported_roots(path: Path) -> set[str]:
    """First segment of every module this file imports, by AST — not by string.

    Deliberately AST and not a grep: a string search cannot tell an import from
    a docstring, a comment, or a template that legitimately mentions a path.
    """
    roots: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom):
            # level > 0 is a relative import and has no root to check.
            if node.level == 0 and node.module:
                roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
    return roots


def _is_generator_module(path: Path) -> bool:
    """A generator is a module that builds on BaseGenerator.

    Detected structurally — an import of the name, or a class that subclasses it
    — rather than by filename, because the family is spread over eleven
    subpackages under three different naming conventions (`cqrs/generator.py`,
    `generators/module.py`, `docs/adr.py`).
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module
            and any(a.name == "BaseGenerator" for a in node.names)
        ):
            return True
        if isinstance(node, ast.ClassDef) and any(
            isinstance(b, ast.Name) and b.id == "BaseGenerator" for b in node.bases
        ):
            return True
    return False


GENERATOR_MODULES = [p for p in _module_paths() if _is_generator_module(p)]
CLI_MODULE = ENGINEERING / "productivity" / "cli.py"


def _env_without_the_repository_root() -> dict[str, str]:
    """The parent environment minus the one variable under test.

    Inheriting and subtracting, rather than building an env from scratch: a
    hand-built env drops `LD_LIBRARY_PATH`, which the hosted Python in CI needs
    to start at all, so the test would fail for a reason that has nothing to do
    with imports. PYTHONPATH is what CI uses to put the repository root on
    sys.path, and removing it is the whole point.
    """
    return {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}


def _import_in_real_environment(dotted: str) -> subprocess.CompletedProcess[str]:
    """Import one module in a process rooted at backend/ and nothing else.

    No PYTHONPATH, no sys.path insertion, no importlib trickery: `cwd` alone
    supplies the package root for `python -c`, which is precisely the
    environment the finding reproduced in and the one a deployed backend runs
    in.
    """
    return subprocess.run(
        [sys.executable, "-c", f"import {dotted}; print('IMPORT_OK')"],
        capture_output=True,
        text=True,
        cwd=str(BACKEND),
        env=_env_without_the_repository_root(),
    )


# ── A. every generator module imports ────────────────────────────────────────


def test_the_generator_family_is_discovered_at_all() -> None:
    """Guard the guard: a discovery bug that finds nothing would make every
    parametrised test below vacuously pass."""
    assert len(GENERATOR_MODULES) >= 18, (
        f"only {len(GENERATOR_MODULES)} generator modules discovered under "
        f"{ENGINEERING}; the detector has probably stopped matching"
    )


@pytest.mark.parametrize("path", GENERATOR_MODULES, ids=_dotted)
def test_every_generator_module_imports_without_the_repository_root(path: Path) -> None:
    result = _import_in_real_environment(_dotted(path))
    assert result.returncode == 0, (
        f"{_dotted(path)} does not import with only the application root on "
        f"sys.path:\n{result.stderr[-1500:]}"
    )


# ── B. the CLI imports ───────────────────────────────────────────────────────


def test_the_productivity_cli_imports_without_the_repository_root() -> None:
    """The acceptance criterion of NR-056, and its exact reproduction command."""
    result = _import_in_real_environment("app.engineering.productivity.cli")
    assert result.returncode == 0, (
        "cd backend && python3 -c 'import app.engineering.productivity.cli' still "
        f"fails:\n{result.stderr[-1500:]}"
    )
    assert "IMPORT_OK" in result.stdout


def test_the_cli_can_load_every_generator_it_advertises() -> None:
    """Importing the CLI only proves its *module-level* imports resolve.

    Eighteen of its twenty-seven imports are inside subcommand handlers, so they
    were invisible to an import check while `gula generate tests`, `adr`,
    `diagram`, `ci`, `docker`, `compose` and `kubernetes` would all still have
    raised ModuleNotFoundError at call time. This resolves each deferred target
    for real.
    """
    tree = ast.parse(CLI_MODULE.read_text(encoding="utf-8"))
    deferred = sorted({
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module
        and node.module.startswith("app.")
    })
    assert len(deferred) >= 20, f"expected the CLI's full import set, found {deferred}"

    program = "\n".join(f"import {m}" for m in deferred) + "\nprint('IMPORT_OK')"
    result = subprocess.run(
        [sys.executable, "-c", program],
        capture_output=True, text=True, cwd=str(BACKEND),
        env=_env_without_the_repository_root(),
    )
    assert result.returncode == 0, (
        f"a module the CLI imports lazily does not resolve:\n{result.stderr[-1500:]}"
    )


# ── C. the generators still work ─────────────────────────────────────────────


def test_a_repaired_generator_still_generates(tmp_path: Path) -> None:
    """Imports resolving is not the same as the tool working.

    CQRSGenerator is a representative of the ten `<subpackage>/generator.py`
    modules the repair touched; it was chosen because it needs no application
    state to run.
    """
    from app.engineering.cqrs.generator import CQRSGenerator, CQRSSpec

    result = CQRSGenerator(target_dir=tmp_path).generate(
        spec=CQRSSpec(name="nr056_probe", commands=["do_thing"], queries=["get_thing"])
    )

    assert result.success, result.errors
    assert result.files_created, "the generator reported success but wrote nothing"


# ── E + Phase 6. the architecture guard ──────────────────────────────────────


def test_no_engineering_module_imports_through_the_nonexistent_backend_root() -> None:
    """One guard for the whole family, by package discovery rather than filename.

    `backend` is not an importable package — no `__init__.py`, and the
    distribution publishes `app*`. Any module naming it as an import root is
    relying on the repository root being on `sys.path`, which is true under
    pytest and false in production. This is the defect NR-053 fixed once and
    NR-056 fixed seventeen more times; the guard is what stops it returning a
    nineteenth.
    """
    offenders = sorted(
        _dotted(p) for p in _module_paths() if INVALID_ROOT in _imported_roots(p)
    )
    assert offenders == [], (
        "these engineering modules import through the non-existent `backend` "
        f"root and will not load outside a repository checkout: {offenders}"
    )
