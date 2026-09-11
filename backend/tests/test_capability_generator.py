"""NR-053 — the capability generator, proved by generating and importing.

NR-050 found three defects in `app/engineering/generators/capability.py`, each of
which shipped 267 modules deep into `app/capabilities/` and made nine of its ten
packages unimportable:

* **D1** — the generated `__init__.py` said `from <package>.capability import …`,
  a bare top-level import that resolves against nothing. One character.
* **D2** — generated modules imported `backend.app.…`, a root that exists only
  where the repository root happens to be on `sys.path`. True under pytest and
  in CI, false for a plain interpreter rooted at `backend/`.
* **D3** — the entity template declared a defaulted `id` ahead of the caller's
  required fields, so any capability with a required field raised
  `TypeError: non-default argument 'x' follows default argument 'id'`.

These tests do not read the generator's source looking for strings. They **run
it**, into a temporary directory, and then import what came out — which is the
only evidence that actually distinguishes a fixed generator from a fixed
docstring. The existing tree is untouched: nothing here writes to `app/`, and
the disposition of those ten packages remains NR-050's decision.
"""

from __future__ import annotations

import importlib
import py_compile
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
from app.engineering.generators.capability import (
    CapabilityGenerator,
    CapabilitySpec,
    EntityField,
)

BACKEND = Path(__file__).resolve().parents[1]


def _generate(tmp_path: Path, spec: CapabilitySpec) -> Path:
    """Generate one capability into a temporary directory and return its root."""
    CapabilityGenerator(target_dir=tmp_path).generate(spec=spec)
    package = tmp_path / spec.name
    assert package.is_dir(), f"the generator produced no package at {package}"
    return package


def _import_generated(package: Path, module: str = ""):
    """Import a generated module by making its parent a package root.

    The generated package is written outside `app/`, so it is imported here as a
    top-level package. That is deliberate: it checks the generated code on its
    own terms rather than borrowing the application's import graph.
    """
    root = str(package.parent)
    sys.path.insert(0, root)
    try:
        name = package.name + (f".{module}" if module else "")
        for cached in [k for k in sys.modules if k == package.name or k.startswith(package.name + ".")]:
            del sys.modules[cached]
        return importlib.import_module(name)
    finally:
        sys.path.remove(root)


# ── Specs covering the generator's code paths ────────────────────────────────


def _minimal() -> CapabilitySpec:
    return CapabilitySpec(
        name="nr053_minimal",
        description="A capability with no entities, to cover the scaffold-only path.",
        domain="infrastructure",
        layer="application",
        owner="platform-architecture",
        commands=["do_thing"],
        queries=["get_thing"],
        events=["ThingHappened"],
        permissions=["nr053.read"],
    )


def _with_entities() -> CapabilitySpec:
    """The path that produces domain / application / infrastructure layers.

    `required=True` on the first two fields is the whole point: that is the
    combination D3 could not express.
    """
    return CapabilitySpec(
        name="nr053_entities",
        description="A capability with required and defaulted entity fields.",
        domain="clinical",
        layer="application",
        owner="platform-architecture",
        entities=[
            EntityField(name="record_id"),
            EntityField(name="title"),
            EntityField(name="note", required=False),
        ],
        commands=["create_record"],
        queries=["get_record"],
        events=["RecordCreated"],
        permissions=["nr053.write"],
    )


# ── Phase 3: fresh generation ────────────────────────────────────────────────


def test_a_minimal_capability_generates_compiles_and_imports(tmp_path) -> None:
    package = _generate(tmp_path, _minimal())

    for source in package.rglob("*.py"):
        py_compile.compile(str(source), doraise=True)

    module = _import_generated(package)
    assert hasattr(module, "Nr053_minimalCapability")


def test_a_capability_with_entities_generates_every_layer(tmp_path) -> None:
    package = _generate(tmp_path, _with_entities())

    for expected in (
        "domain/entities.py", "domain/repository.py",
        "application/service.py", "infrastructure/repository.py",
        "routes.py", "contract.py", "capability.py", "dto.py",
    ):
        assert (package / expected).is_file(), f"{expected} was not generated"

    for source in package.rglob("*.py"):
        py_compile.compile(str(source), doraise=True)


# ── Phase 4: one regression guard per defect, behavioural ────────────────────


def test_d1_the_generated_package_imports_through_its_own_name(tmp_path) -> None:
    """D1. The `__init__` used a bare top-level import, so the package could not
    be imported by any route at all — which is what made nine of the ten
    packages in `app/capabilities/` dead.

    Proved by importing, not by grepping. The assertion on the source afterwards
    is a second, weaker check that names the shape for a future reader.
    """
    package = _generate(tmp_path, _minimal())

    module = _import_generated(package)
    assert module.__name__ == "nr053_minimal"

    init = (package / "__init__.py").read_text(encoding="utf-8")
    assert "from .capability import" in init
    assert f"from {package.name}.capability import" not in init


def test_d2_no_generated_module_imports_the_backend_app_root(tmp_path) -> None:
    """D2. `backend.app.…` resolves only where the repository root is on
    `sys.path`; the application's root is `app`.

    Both specs are generated because the offending string reached three
    different templates — the routes, the capability, and (through
    `module_path`) the infrastructure repository, the unit test and the
    descriptor metadata.
    """
    offenders: list[str] = []
    for spec in (_minimal(), _with_entities()):
        package = _generate(tmp_path / spec.name, spec)
        for source in package.rglob("*"):
            if source.suffix not in {".py", ".md", ".json", ".xml"}:
                continue
            if "backend.app" in source.read_text(encoding="utf-8", errors="ignore"):
                offenders.append(str(source.relative_to(tmp_path)))
    assert offenders == [], f"generated files still name the backend.app root: {offenders}"


def test_d3_an_entity_with_required_fields_is_a_constructible_dataclass(tmp_path) -> None:
    """D3. The template put the defaulted `id` first, so a required field after
    it raised TypeError at class-creation time.

    The class is imported and instantiated here: a dataclass whose field order is
    wrong fails when the module is *executed*, so importing it is the proof. The
    required fields must still be required, and `id` must still default — the
    fix was ordering, not semantics.
    """
    package = _generate(tmp_path, _with_entities())

    entities = _import_generated(package, "domain.entities")
    entity_cls = entities.Nr053_entities

    instance = entity_cls(record_id="r-1", title="A title")
    assert instance.record_id == "r-1"
    assert instance.title == "A title"
    assert instance.id, "id lost its default"
    assert instance.note is None, "the optional field lost its default"
    assert instance.created_at is not None

    with pytest.raises(TypeError):
        entity_cls()  # required fields are still required

    source = (package / "domain" / "entities.py").read_text(encoding="utf-8")
    assert source.index("record_id") < source.index("id: str = field"), (
        "the defaulted id is ahead of a required field again"
    )


def test_the_generated_package_imports_without_the_repository_root(tmp_path) -> None:
    """The environment D2 actually broke.

    A generated capability legitimately depends on the application — it imports
    `app.kernel.integration` and `app.security.dependencies`, and should. What it
    must not depend on is *which* of the two roots happens to be on `sys.path`.

    So this subprocess is given `backend/` (the application root) and the
    generated package's parent, and deliberately **not** the repository root.
    That is the environment where `backend.app.…` raises and `app.…` resolves,
    and it is the one a plain `python -m` from `backend/` provides.
    """
    package = _generate(tmp_path, _with_entities())

    result = subprocess.run(
        [sys.executable, "-c", textwrap.dedent(f"""
            import sys
            sys.path.insert(0, {str(package.parent)!r})
            import {package.name}
            from {package.name}.domain.entities import Nr053_entities
            row = Nr053_entities(record_id="r-1", title="t")
            assert row.id and row.note is None
            print("OK")
        """)],
        capture_output=True, text=True, cwd=str(tmp_path),
        env={
            "PATH": "/usr/bin:/bin:/usr/local/bin",
            "PYTHONPATH": str(BACKEND),
            "RUNTIME_MODE": "test",
            "FEATURE_BACKGROUND_TASKS": "false",
            "ENV": "test",
            "DATABASE_URL": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-key-not-for-production-" + "x" * 32,
            "ENCRYPTION_KEY": "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=",
            "NID_HMAC_KEY": "a" * 64,
            "REDIS_URL": "",
        },
    )
    assert result.returncode == 0, (
        "the generated package does not import with only the application root on "
        f"sys.path — which is exactly what D2 broke:\n{result.stderr[-2000:]}"
    )
    assert "OK" in result.stdout


def test_the_generator_itself_imports_without_the_repository_root(tmp_path) -> None:
    """The generator carried D2 in its own head, too.

    It imported `backend.app.engineering.generators.base`, so the tool that
    writes capabilities could only be loaded from one of the two roots. Checked
    in a subprocess rooted at `backend/` alone.
    """
    result = subprocess.run(
        [sys.executable, "-c",
         "import app.engineering.generators.capability as g; print(g.CapabilityGenerator.__name__)"],
        capture_output=True, text=True, cwd=str(BACKEND),
        env={"PATH": "/usr/bin:/bin:/usr/local/bin", "PYTHONPATH": str(BACKEND)},
    )
    assert result.returncode == 0, f"the generator still needs the repository root:\n{result.stderr}"
    assert "CapabilityGenerator" in result.stdout


# ── Phase 3 item 10: the generated descriptor satisfies the contract ─────────


def test_the_generated_descriptor_points_at_the_module_it_generated(tmp_path) -> None:
    """`module_path` is the field PROGRAM-EXT-001 requires so a descriptor can be
    checked against reality. A descriptor naming a root that does not resolve is
    the reason all 52 existing capabilities fail that check.
    """
    package = _generate(tmp_path, _minimal())

    descriptor_files = [*package.rglob("*.json"), package / "capability.py"]
    text = "\n".join(
        p.read_text(encoding="utf-8") for p in descriptor_files if p.is_file()
    )
    assert "app.capabilities.nr053_minimal" in text or "nr053_minimal" in text
    assert "backend.app.capabilities" not in text
