"""NR-050 — a capability must not load the application a second time.

`backend/` is not a package (no `__init__.py`), but `backend.app.x` still
resolves wherever the repository root is on `sys.path` — under pytest, in CI,
and in the container, which copies the application twice (`COPY backend
./backend` alongside `COPY backend/app ./app`). When it resolves it produces a
**different module object for the same file**, with its own module-level
globals.

That is not cosmetic here. `app/kernel/integration.py` holds `_kernel_instance`
as a module-level global, so a capability importing
`backend.app.kernel.integration` would register itself into a second kernel
with a second registry — one that `factory.py` never boots. Registration would
succeed and reach nobody.

It was live, not hypothetical: `factory.py` imports
`app.capabilities.fhir_interoperability.models`, which executes that package's
`__init__`, which imports its `capability.py`, which named the `backend.app`
root. Every application start loaded the shadow kernel.

These tests hold the repaired state and stop it returning.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
CAPABILITIES = BACKEND / "app" / "capabilities"

# Modules outside `app/capabilities/` that still reach the shadow tree. They are
# NOT NR-050's to repair: `national/task_engine` and `national/workflow_runtime`
# use the `backend.app.` root throughout, for their own internal references as
# well as for `database` and `config`, so correcting them is a package-wide
# change with its own review. Recorded as NR-058.
#
# This ledger may shrink. It may never grow.
DECLARED_SHADOW_ROOT_PACKAGES = frozenset({
    "app/national/task_engine",
    "app/national/workflow_runtime",
    "app/services/governance",
    "app/services/reference",
    "app/integration/connectors",
})


def _imports_backend_root(path: Path) -> bool:
    """True if this module names `backend` as an import root, by AST."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.level == 0
            and node.module
            and node.module.split(".")[0] == "backend"
        ):
            return True
        if isinstance(node, ast.Import) and any(
            a.name.split(".")[0] == "backend" for a in node.names
        ):
            return True
    return False


def _capability_modules() -> list[Path]:
    return sorted(
        p for p in CAPABILITIES.rglob("*.py") if "__pycache__" not in p.parts
    )


def test_capability_modules_are_discovered() -> None:
    """Guard the guard: a scan that finds nothing proves nothing."""
    assert len(_capability_modules()) >= 200


def test_no_capability_module_loads_the_application_through_a_second_root() -> None:
    """The NR-050 repair, held.

    Ten `capability.py` files named `backend.app.kernel.integration`. Only
    `fhir_interoperability` was reachable enough to execute it, and that was
    enough to put a second kernel in every running process.
    """
    offenders = sorted(
        str(p.relative_to(BACKEND)) for p in _capability_modules()
        if _imports_backend_root(p)
    )
    assert offenders == [], (
        "these capability modules import through the `backend` root and would "
        f"bind to a second copy of the application: {offenders}"
    )


def test_a_real_application_start_does_not_load_a_second_kernel() -> None:
    """Behavioural, because the static check alone would not have caught the
    path that made this live: `factory.py` → capability package `__init__` →
    `capability.py`.

    Asserted on the kernel specifically — that is the module whose duplication
    silently redirects capability registration.
    """
    import sys

    from app.factory import create_app

    create_app()

    shadow_kernel = sorted(
        m for m in sys.modules if m.startswith("backend.app.kernel")
    )
    assert shadow_kernel == [], (
        "starting the application loaded a second copy of the kernel; a "
        f"capability registering through it would reach nobody: {shadow_kernel}"
    )


def test_the_shadow_root_ledger_does_not_grow() -> None:
    """The rest of the shadow tree is NR-058's, not NR-050's.

    This does not assert the ledger is empty — it is not, and pretending
    otherwise would be manufacturing green. It asserts that no package outside
    the declared set has joined it.
    """
    offenders: set[str] = set()
    for path in sorted((BACKEND / "app").rglob("*.py")):
        if "__pycache__" in path.parts or "engineering" in path.parts:
            continue
        if not _imports_backend_root(path):
            continue
        rel = str(path.relative_to(BACKEND))
        if not any(rel.startswith(pkg) for pkg in DECLARED_SHADOW_ROOT_PACKAGES):
            offenders.add(rel)

    assert offenders == set(), (
        "a new module reaches the application through the `backend` root: "
        f"{sorted(offenders)}"
    )


@pytest.mark.parametrize("package", sorted(DECLARED_SHADOW_ROOT_PACKAGES))
def test_each_declared_shadow_package_still_has_the_defect(package: str) -> None:
    """A ledger entry that has been repaired should be deleted, not left to rot
    — otherwise the ledger slowly becomes a list of things that used to be
    true."""
    base = BACKEND / package
    if not base.is_dir():
        pytest.fail(f"{package} no longer exists; remove it from the ledger")
    still = any(
        _imports_backend_root(p)
        for p in base.rglob("*.py") if "__pycache__" not in p.parts
    )
    assert still, f"{package} no longer uses the backend root; remove it from the ledger"
