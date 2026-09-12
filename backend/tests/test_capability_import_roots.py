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

NR-058 then closed the rest of it: the five packages outside
`app/capabilities/` that still named the `backend` root — 73 import
statements across 25 files — so nothing under `app/` reaches the shadow tree
any more.

These tests hold the repaired state and stop it returning.
"""

from __future__ import annotations

import ast
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
CAPABILITIES = BACKEND / "app" / "capabilities"

# Packages outside `app/capabilities/` that still reach the shadow tree.
#
# Empty, and measured: NR-058 closed the five that were listed here
# (`national/task_engine`, `national/workflow_runtime`, `services/governance`,
# `services/reference`, `integration/connectors`) by rewriting 73 import
# statements across 25 files. Nothing under `app/` names the `backend` root any
# more, which is why this ledger is empty and the scan below no longer exempts
# `engineering` either — NR-056 closed that one.
#
# This ledger may shrink. It may never grow.
DECLARED_SHADOW_ROOT_PACKAGES: frozenset[str] = frozenset()


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


# The `backend.app` modules a real application start is still allowed to load.
#
# `shared/` lives at the repository root, outside `backend/`, and several of its
# modules import `backend.app._compat` for the `UTC` constant. That is a genuine
# second copy of that module — but `_compat` holds constants and no state: no
# engine, no session factory, no declarative base, no registry. Duplicating it
# costs nothing that can diverge. `backend` and `backend.app` are the namespace
# packages Python must create to reach it.
#
# Every other name is a defect, and the test below says why for each.
DECLARED_STATELESS_SHADOW_MODULES = frozenset({
    "backend",
    "backend.app",
    "backend.app._compat",
})


def test_a_real_application_start_loads_no_stateful_second_copy() -> None:
    """Behavioural, because the static check alone would not have caught the
    path that made this live: `factory.py` → capability package `__init__` →
    `capability.py`.

    Originally this asserted on the kernel alone. NR-058 showed why that was too
    narrow: `national/task_engine` and `national/workflow_runtime` were pulling
    in a second `app.database` — its own Engine and SessionLocal against the same
    URL, a connection pool outside the documented budget — and a second
    `NationalBase`, on which fifteen tables registered where neither Alembic's
    `target_metadata` nor `conftest`'s `create_all` could see them.

    Those three are what must never be duplicated: the kernel redirects
    registration, the database module splits the pool, and a declarative base
    hides tables from every schema gate the repository has.
    """
    import sys

    from app.factory import create_app

    create_app()

    loaded = {m for m in sys.modules if m.split(".")[0] == "backend"}
    offenders = sorted(loaded - DECLARED_STATELESS_SHADOW_MODULES)
    assert offenders == [], (
        "starting the application loaded a second copy of these modules; each "
        "carries state that then exists twice — a kernel registry nobody boots, "
        "a connection pool outside the budget, or a declarative base invisible "
        f"to Alembic and to conftest: {offenders}"
    )


def test_the_stateless_shadow_ledger_is_actually_stateless() -> None:
    """The exemption above is only defensible while it stays true.

    `_compat` is exempt because duplicating a constant cannot diverge. If it
    ever gains an engine, a session factory, a registry or a declarative base,
    the exemption has to be re-argued rather than inherited.
    """
    import ast

    source = (BACKEND / "app" / "_compat.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    stateful = sorted(
        node.id if isinstance(node, ast.Name) else node.attr
        for node in ast.walk(tree)
        if isinstance(node, (ast.Name, ast.Attribute))
        and (node.id if isinstance(node, ast.Name) else node.attr)
        in {"create_engine", "sessionmaker", "declarative_base", "registry", "MetaData"}
    )
    assert stateful == [], (
        "app/_compat.py has acquired state, so the second copy `shared/` loads "
        f"is no longer harmless: {stateful}"
    )


def test_the_shadow_root_ledger_does_not_grow() -> None:
    """The whole of `app/`, not just the capabilities.

    When this was written the ledger held five packages and the assertion was
    only that nothing had joined them. NR-058 emptied it, so the assertion is
    now absolute: no module under `app/` may name the `backend` root.
    """
    offenders: set[str] = set()
    for path in sorted((BACKEND / "app").rglob("*.py")):
        if "__pycache__" in path.parts:
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


def test_each_declared_shadow_package_still_has_the_defect() -> None:
    """A ledger entry that has been repaired should be deleted, not left to rot
    — otherwise the ledger slowly becomes a list of things that used to be true.

    Vacuous while the ledger is empty, and deliberately kept that way: it is
    what makes an entry added later expire on its own rather than becoming a
    permanent exemption. Written as one iterating test rather than a
    parametrized one so an empty ledger reports as a pass, not a skip — a skip
    in a gate's output is a place for a real failure to hide.
    """
    for package in sorted(DECLARED_SHADOW_ROOT_PACKAGES):
        base = BACKEND / package
        assert base.is_dir(), f"{package} no longer exists; remove it from the ledger"
        still = any(
            _imports_backend_root(f)
            for f in base.rglob("*.py") if "__pycache__" not in f.parts
        )
        assert still, f"{package} no longer uses the backend root; remove it from the ledger"
