"""The workflow capability admits it cannot run, instead of pretending.

IA-058. ``app/platform/workflow.py`` called ``WorkflowRuntimeService()`` with
none of its eight required repository arguments, so every one of its four
methods raised ``TypeError: ... missing 8 required positional arguments``.
Meanwhile the module registered itself into ``PlatformRegistry`` at import
time, so ``GET /platform/capabilities`` advertised all four as available.

The repair does not wire the repositories, for two measured reasons:

* ``SagaLogRepository`` has no implementation --
  ``app/national/workflow_runtime/infrastructure/repository.py`` provides seven
  ``SQLAlchemy*`` repositories, and the eighth exists only as an ABC.
* No migration creates any of the eight tables the subsystem needs. Each was
  checked individually against ``migrations/versions/``: zero creating
  migrations.

Wiring seven of eight would convert a TypeError into ``no such table`` -- the
same unavailability in a different costume.

RATCHET BOTH WAYS. The dangerous "fix" here is not a regression to TypeError;
it is someone making the tests pass by returning ``None`` or ``[]``, which
would turn an outage into a successful empty answer. These tests assert the
raise, assert the two shapes that must NOT be returned, and assert that the
capability listing and the runtime error cannot drift apart.
"""
from __future__ import annotations

import inspect

import pytest


def test_every_entry_point_raises_rather_than_returning_a_plausible_answer():
    from app.platform.workflow import WorkflowRuntimeUnavailable, WorkflowService

    service = WorkflowService()
    calls = (
        ("start", lambda: service.start("any_type", {})),
        ("cancel", lambda: service.cancel("exec-1")),
        ("get_status", lambda: service.get_status("exec-1")),
        ("get_tasks", lambda: service.get_tasks("exec-1")),
    )
    for name, call in calls:
        with pytest.raises(WorkflowRuntimeUnavailable, match="is not wired") as caught:
            call()
        assert name in str(caught.value), f"the error does not say which operation: {caught.value}"


def test_get_status_does_not_answer_none_and_get_tasks_does_not_answer_empty():
    """The two fake successes this defect invites.

    ``get_status`` returning ``None`` is its documented "no such execution"
    answer, and ``get_tasks`` returning ``[]`` is indistinguishable from an
    execution with no steps. Either would report a normal, empty result while
    the subsystem is in fact unable to run.
    """
    from app.platform.workflow import WorkflowService

    service = WorkflowService()

    for name in ("get_status", "get_tasks"):
        source = inspect.getsource(getattr(WorkflowService, name))
        body = source.split('"""')[-1] if '"""' in source else source
        executable = [
            line.strip() for line in body.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        assert not any(line in ("return None", "return []") for line in executable), (
            f"{name} has a live `return None`/`return []`; that reports an "
            f"empty result for an unavailable subsystem:\n{source}"
        )


def test_the_capability_listing_says_the_workflow_capability_is_unavailable():
    import app.platform.workflow
    from app.platform import PlatformRegistry

    workflow_caps = [c for c in PlatformRegistry.get_capabilities() if c["module"] == "workflow"]

    assert len(workflow_caps) == 4, [c["name"] for c in workflow_caps]
    for cap in workflow_caps:
        assert cap["available"] is False, cap
        assert "not wired" in cap["unavailable_reason"], cap


def test_the_listed_reason_is_the_same_string_the_error_carries():
    """One source of truth, so the listing and the failure cannot diverge."""
    import app.platform.workflow
    from app.platform import PlatformRegistry
    from app.platform.workflow import (
        UNAVAILABLE_REASON,
        WorkflowRuntimeUnavailable,
        WorkflowService,
    )

    listed = {
        c["unavailable_reason"]
        for c in PlatformRegistry.get_capabilities()
        if c["module"] == "workflow"
    }
    assert listed == {UNAVAILABLE_REASON}

    with pytest.raises(WorkflowRuntimeUnavailable) as caught:
        WorkflowService().start("any_type", {})
    assert UNAVAILABLE_REASON in str(caught.value)


def test_an_unavailable_module_cannot_be_registered_without_a_reason():
    """The control. A bare `available=False` would be an unactionable outage."""
    from app.platform import PlatformRegistry

    with pytest.raises(ValueError, match="without a reason"):
        PlatformRegistry.register("ia058_probe", object(), available=False)


def test_health_distinguishes_unavailable_from_registered():
    import app.platform.workflow
    from app.platform import PlatformRegistry

    # The ratchet: assert both states appear, or the test would also pass if
    # health() simply returned "unavailable" for everything. A probe supplies
    # the available side, rather than depending on which of the other 14
    # platform modules this process happened to import.
    PlatformRegistry.register("ia058_available_probe", object())

    health = PlatformRegistry.health()
    assert health["workflow"] == "unavailable", health["workflow"]
    assert health["ia058_available_probe"] == "registered", health


def test_get_capabilities_does_not_hand_out_registry_state():
    """It used to mutate the stored dicts and return references to them."""
    from app.platform import PlatformRegistry

    first = PlatformRegistry.get_capabilities()
    first[0]["name"] = "mutated-by-caller"
    second = PlatformRegistry.get_capabilities()

    assert all(c["name"] != "mutated-by-caller" for c in second), (
        "a caller editing a returned capability edited the registry"
    )


def test_no_platform_module_constructs_a_service_it_cannot_construct():
    """Keep the family closed. IA-058 was 4 sites in 1 of 15 platform modules.

    A zero-argument call to an imported class whose ``__init__`` has required
    parameters can only raise, so it is a defect wherever it appears.
    """
    import ast
    import importlib
    import pathlib

    platform_dir = pathlib.Path(__file__).resolve().parents[2] / "app" / "platform"
    offenders, scanned = [], 0

    for path in sorted(platform_dir.glob("*.py")):
        if path.name == "__init__.py":
            continue
        tree = ast.parse(path.read_text())
        imports: dict[str, tuple[str, str]] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.level == 1:
                    module = f"app.platform.{node.module}"
                elif node.level == 2:
                    module = f"app.{node.module}"
                else:
                    module = node.module
                for alias in node.names:
                    imports[alias.asname or alias.name] = (module, alias.name)

        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
                continue
            name = node.func.id
            if node.args or node.keywords or not name[:1].isupper() or name not in imports:
                continue
            scanned += 1
            module, attr = imports[name]
            try:
                cls = getattr(importlib.import_module(module), attr)
            except Exception:
                continue
            if not inspect.isclass(cls):
                continue
            try:
                parameters = list(inspect.signature(cls.__init__).parameters.values())[1:]
            except (TypeError, ValueError):
                continue
            required = [
                p.name for p in parameters
                if p.default is inspect.Parameter.empty
                and p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
            ]
            if required:
                offenders.append(f"app/platform/{path.name}:{node.lineno} {name}() needs {required}")

    # positive control: a scan that finds nothing to check proves nothing
    assert scanned >= 3, f"the scan only examined {scanned} constructions; it has gone blind"
    assert not offenders, "\n".join(offenders)
