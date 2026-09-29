"""NR-086b — one module, one import path.

``backend/`` has no ``__init__.py``, so with both the repo root and ``backend/``
on the path, ``app.x`` and ``backend.app.x`` are two *different* module objects
for the same file, each with its own module-level state. 54 files inside
``backend/app/`` imported their own package by the second name, which put 36
duplicate modules in the assembled app, 11 of them live under both names at once
-- including ``app.config``, ``app.database`` and ``app.kernel.integration``.

The consequence was not theoretical. ``app.kernel.integration`` keeps the kernel
in a module-level ``_kernel_instance``, so after the platform called
``init_kernel()`` on the canonical module, ``get_kernel()`` on the duplicate
raised ``RuntimeError: Kernel not initialized`` -- and the duplicate is what all
ten generated capability modules imported.

Those capabilities were unreachable anyway for a second reason from the same
generator: nine of the ten ``__init__.py`` files carried a bare
``from <cap>.capability import ...``, which resolves to no top-level package. One,
``fhir_interoperability``, used the relative form and was the only importable
capability in the tree -- and is the evidence for which form is correct here,
rather than a preference.

What survived by accident and is asserted here so it keeps surviving: the ORM
escaped, because ``database.py`` and the base modules import ``orm_topology``
absolutely, so both copies of ``Base`` still shared the one ``SHARED_METADATA``.
Had they not, NR-074's whole closure would have been silently undone.
"""

from __future__ import annotations

import importlib
import pathlib
import sys

import pytest

_APP = pathlib.Path(__file__).resolve().parents[2] / "app"
_SHADOW_PREFIX = "backend.app"

#: The one module still reached by both names, pinned with its reason rather than
#: swept into the fix, because the honest repair is not a rename.
#:
#: ``app/_compat.py`` is imported as ``backend.app._compat`` by 40 files OUTSIDE
#: ``backend/app/`` -- most of ``shared/``, four files in
#: ``services/device_bridge/``, and ``scripts/self_heal.py``. Renaming those to
#: ``app._compat`` would close this set and leave the real problem untouched:
#: ``shared/`` is a lower layer than ``app`` and should not import from it at all,
#: under either name. Whether ``shared`` grows its own compatibility shim, or
#: simply uses ``datetime.UTC``, is a layering decision and is registered
#: separately rather than taken here.
#:
#: The duplication is benign in effect today -- the module binds one constant --
#: which is exactly why it must be pinned: a second module reached this way that
#: held real state would be the kernel defect again.
KNOWN_SHADOWED: set[str] = {"backend.app._compat"}


@pytest.fixture(scope="module")
def assembled() -> None:
    """Import the platform exactly as a worker does."""
    importlib.import_module("app.main")


def _shadowed_modules() -> list[str]:
    return sorted(
        name
        for name in sys.modules
        if name.startswith(_SHADOW_PREFIX + ".")
        and name[len("backend."):] in sys.modules
    )


def test_no_module_is_loaded_under_two_names(assembled: None) -> None:
    """A module loaded twice has its singletons, config and caches twice over.

    Pinned as an exact set, not a count and not a subset: a swap — this one
    closed while another appears — must fail, because the next one may hold
    state rather than a constant.
    """
    assert set(_shadowed_modules()) == KNOWN_SHADOWED, (
        f"modules live under both app.* and backend.app.*: {_shadowed_modules()}, "
        f"expected exactly {sorted(KNOWN_SHADOWED)}. Each copy has its own "
        "module-level state, so a singleton initialised through one is invisible "
        "through the other — which is how the capability tree acquired a second "
        "kernel that could never be initialised."
    )


def test_no_source_file_under_app_imports_its_own_package_by_the_shadow_name() -> None:
    """Static companion to the runtime check, so a new one fails before it runs."""
    offenders: dict[str, list[str]] = {}
    for path in sorted(_APP.rglob("*.py")):
        if "__pycache__" in str(path):
            continue
        hits = [
            line.strip()
            for line in path.read_text().splitlines()
            if line.strip().startswith(("from backend.", "import backend."))
        ]
        if hits:
            offenders[str(path.relative_to(_APP.parent))] = hits
    assert offenders == {}, f"files importing their own package as backend.app.*: {offenders}"


def test_the_kernel_is_one_instance_through_every_module_that_reaches_it(assembled: None) -> None:
    """The defect's sharpest form: the capability tree held a second kernel."""
    integration = importlib.import_module("app.kernel.integration")
    integration.init_kernel()
    kernel = integration.get_kernel()
    assert kernel is not None

    from app.capabilities.workflow_engine import capability

    assert capability.get_kernel is integration.get_kernel, (
        "a capability imported get_kernel from a second copy of the module"
    )
    assert capability.get_kernel() is kernel


def test_every_capability_package_imports(assembled: None) -> None:
    """Nine of ten raised ModuleNotFoundError at their own ``__init__``.

    ``fhir_interoperability`` is the positive control: it was importable before
    the repair too, so a probe that reported everything broken would be wrong.
    """
    names = sorted(
        p.name for p in _APP.joinpath("capabilities").iterdir()
        if p.is_dir() and not p.name.startswith("__")
    )
    assert len(names) == 10, f"the capability tree changed: {names}"
    failures: dict[str, str] = {}
    for name in names:
        try:
            importlib.import_module(f"app.capabilities.{name}")
        except Exception as exc:  # the failure itself is the finding
            failures[name] = f"{type(exc).__name__}: {exc}"
    assert failures == {}, f"capability packages that cannot be imported: {failures}"


def test_the_capability_generator_emits_a_relative_import() -> None:
    """The generator is the root cause; fixing only its output would regress."""
    source = _APP.joinpath("engineering", "generators", "capability.py").read_text()
    assert "from .capability import {cap_cap}Capability" in source, (
        "the generator's __init__ template no longer emits a relative import; "
        "a bare 'from {cap}.capability import ...' resolves to no package"
    )
    assert "backend.app." not in source, (
        "the generator bakes the shadow prefix into the code it emits"
    )


def test_both_copies_of_Base_would_still_share_one_metadata() -> None:
    """NR-074's closure must not depend on which name a module was imported by.

    Asserted directly rather than assumed: ``orm_topology`` is imported
    absolutely by every base, so the shared namespace is a property of the file
    and not of the import path that reached it.
    """
    topology = importlib.import_module("app.orm_topology")
    for module_name, base_attr in (
        ("app.database", "Base"),
        ("app.national.base", "NationalBase"),
        ("app.ehr.base", "EHRBase"),
    ):
        base = getattr(importlib.import_module(module_name), base_attr)
        assert base.metadata is topology.SHARED_METADATA, (
            f"{module_name}.{base_attr} is not on the shared MetaData"
        )
