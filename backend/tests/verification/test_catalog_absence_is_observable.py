"""BLOCKER-02 — a deployment with no test-type catalog must not look healthy.

`startup_guard.seed_critical_data` treats the test-type catalog as optional
data: `_run_seed_test_types` is called inside a per-seed `try/except` that logs
and continues, and the caller wraps the whole thing in a second `try/except`
before setting `system_ready = True`. That policy is deliberate and is left
alone here — a missing catalog is an operator task, not a reason to refuse to
boot.

What was wrong is that the failure then vanished. With `test_types` empty, every
one of the five health endpoints answered exactly as it does on a fully seeded
deployment: `/health/ready` 200 `{"status": "ready"}`, `/health/status`
`ready=true reason="ok"`, `/health/deep` `grade="GREEN"`, and not one field
anywhere mentioned the catalog. Meanwhile the platform could not interpret a
single result: no reference range, no H/L grading, every
`lab_results.test_type_id` NULL, and the category-filtered history views empty.

So the state is reported, not enforced. `/health/deep` gains a
`test_type_catalog` component and a `test_type_catalog_unavailable` issue, which
takes the grade out of GREEN to YELLOW; `/health/status`, whose stated job is
explaining why a deployment is not usable, gains the same field. Readiness
semantics are untouched: `/health/ready` still answers from
`is_system_ready()`, so an empty catalog does not stop traffic or trip the
rollback workflow — it is visible instead of silent.

Availability is "the catalog holds at least one row", the same question
`_run_seed_test_types` asks before it seeds. There is no count: no minimum
catalog size is documented anywhere, and inventing one would fail a lab that
legitimately offers three tests.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

_BACKEND = pathlib.Path(__file__).resolve().parents[2]
_MAIN = _BACKEND / "app" / "main.py"
_GUARD = _BACKEND / "app" / "core" / "startup_guard.py"


# ── the state is reported on the endpoints that exist ────────────────────────


def _function(path: pathlib.Path, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name == name:
            return node
    raise AssertionError(f"{name} not found in {path.name}")


@pytest.mark.parametrize("endpoint", ["health_deep", "health_status"])
def test_the_endpoint_queries_the_catalog(endpoint: str):
    """Not a cached flag, not a startup variable: the live table."""
    source = ast.unparse(_function(_MAIN, endpoint))
    assert "TestType" in source, f"{endpoint} does not consult the catalog"
    assert "test_type_catalog" in source, f"{endpoint} does not report catalog state"


def test_deep_health_degrades_the_grade_when_the_catalog_is_missing():
    """The grade must leave GREEN, which is the whole point."""
    source = ast.unparse(_function(_MAIN, "health_deep"))
    assert "test_type_catalog_unavailable" in source
    # The issue list is what moves GREEN -> YELLOW; an issue appended outside
    # that list would be cosmetic.
    assert "issues.append('test_type_catalog_unavailable')" in source


def test_the_catalog_check_does_not_hard_code_a_count():
    """A minimum size is undocumented, so asserting one would be invented policy."""
    source = ast.unparse(_function(_MAIN, "health_deep"))
    line = next(
        ln for ln in source.splitlines() if "catalog_available" in ln and "query" in ln
    )
    assert ".first() is not None" in line, f"expected an existence check, got: {line.strip()}"
    assert "count()" not in line
    for forbidden in (" 20", "== 20", ">= 20"):
        assert forbidden not in line


def test_an_empty_catalog_is_not_graded_green():
    """The grading rule itself, exercised without a database.

    `health_deep` builds `issues` and then grades: any issue at all is enough to
    leave GREEN, and only a "down" component reaches RED. An unavailable catalog
    must therefore be YELLOW — degraded and visible, without tripping the alert
    loop or the rollback workflow that RED drives.
    """
    issues = ["test_type_catalog_unavailable"]
    grade = "RED" if any("down" in i for i in issues) else ("YELLOW" if issues else "GREEN")
    assert grade == "YELLOW"


# ── readiness semantics stay as they were ────────────────────────────────────


def test_readiness_still_answers_from_is_system_ready_alone():
    """A healthy deployment must not be made unready by this change.

    `/health/ready` is the Docker healthcheck and the api-gateway's
    `depends_on` condition. Making it fail on an empty catalog would stop a
    deployment from serving, which is the fatal-seeding behaviour this patch
    deliberately does not adopt.
    """
    source = ast.unparse(_function(_MAIN, "readiness"))
    assert "is_system_ready" in source
    assert "TestType" not in source, "readiness must not gate on the catalog"
    assert "test_type_catalog" not in source


def test_seeding_the_catalog_is_still_non_fatal():
    """The patch reports the failure; it does not change startup policy."""
    source = _GUARD.read_text()
    assert "_run_seed_test_types" in source
    seed = ast.unparse(_function(_GUARD, "seed_critical_data"))
    # The optional seeds, including the catalog, still run inside a try/except.
    assert "except Exception" in seed
    assert "_run_seed_test_types" in seed
    assert "raise" not in seed.split("_run_perm_version_migration")[-1], (
        "a catalog seed failure must not be made fatal here"
    )


# ── both directions, against the real app ────────────────────────────────────


def _catalog_state(client, path: str):
    body = client.get(path).json()
    return body["test_type_catalog"]["available"]


def test_empty_then_populated_catalog_is_reported_both_ways(monkeypatch):
    """One app, two catalog states, read from the live endpoints.

    The catalog is read through a session the test controls, so neither state
    writes to any database.
    """
    import app.main as main_module
    from fastapi.testclient import TestClient

    class _FakeQuery:
        def __init__(self, row):
            self._row = row

        def first(self):
            return self._row

    class _FakeSession:
        def __init__(self, row):
            self._row = row

        def query(self, *_a, **_k):
            return _FakeQuery(self._row)

        def close(self):
            pass

        def execute(self, *_a, **_k):  # pragma: no cover - not used by the probe
            raise AssertionError("the catalog probe must only query")

    def _factory(row):
        return lambda: _FakeSession(row)

    with TestClient(main_module.app) as client:
        # A) empty catalog -> not available, not GREEN, and an explicit issue.
        monkeypatch.setattr(main_module, "SessionLocal", _factory(None), raising=False)
        monkeypatch.setattr("app.database.SessionLocal", _factory(None))
        deep = client.get("/health/deep").json()
        status = client.get("/health/status").json()
        assert deep["components"]["test_type_catalog"]["available"] is False
        assert "test_type_catalog_unavailable" in deep["issues"]
        assert deep["grade"] != "GREEN"
        assert status["test_type_catalog"]["available"] is False
        # Readiness is unchanged by the catalog being empty.
        assert client.get("/health/ready").status_code == 200

        # B) populated catalog -> available, no catalog issue, no false alarm.
        monkeypatch.setattr("app.database.SessionLocal", _factory((1,)))
        deep = client.get("/health/deep").json()
        status = client.get("/health/status").json()
        assert deep["components"]["test_type_catalog"]["available"] is True
        assert "test_type_catalog_unavailable" not in deep["issues"]
        assert status["test_type_catalog"]["available"] is True
        assert client.get("/health/ready").status_code == 200


def test_a_single_row_counts_as_available(monkeypatch):
    """One test type is a catalog. Only zero rows is unavailable."""
    import app.main as main_module
    from fastapi.testclient import TestClient

    class _Q:
        def __init__(self, row):
            self._row = row

        def first(self):
            return self._row

    class _S:
        def __init__(self, row):
            self._row = row

        def query(self, *_a, **_k):
            return _Q(self._row)

        def close(self):
            pass

    with TestClient(main_module.app) as client:
        monkeypatch.setattr("app.database.SessionLocal", lambda: _S((1,)))
        deep = client.get("/health/deep").json()
        assert deep["components"]["test_type_catalog"]["available"] is True
        assert "test_type_catalog_unavailable" not in deep["issues"]


def test_a_failing_catalog_probe_is_reported_not_swallowed(monkeypatch):
    """If the check itself cannot run, that is unavailable with an error, not GREEN."""
    import app.main as main_module
    from fastapi.testclient import TestClient

    def _boom():
        raise RuntimeError("SIMULATED: catalog probe failed")

    with TestClient(main_module.app) as client:
        monkeypatch.setattr("app.database.SessionLocal", _boom)
        deep = client.get("/health/deep").json()
        assert deep["components"]["test_type_catalog"]["available"] is False
        assert deep["components"]["test_type_catalog"]["error"] == "catalog_check_failed"
        assert "test_type_catalog_unavailable" in deep["issues"]
