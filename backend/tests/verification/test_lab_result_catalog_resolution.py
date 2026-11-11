"""IA-019 / IA-020 — every lab-result write path must consult the test catalog.

`LabResult.test_type_id` is nullable in the ORM and in the migrated database
(verified: `information_schema` reports `is_nullable=YES`, and no CHECK
constraint exists), so nothing at the schema level forces a write path to link a
result to its `TestType`. Of the four production paths that construct a
`LabResult`, only `app/routes/test_results.py` resolved the catalog. The other
three — order creation, analyzer ingestion and demo seeding — omitted
`test_type_id` entirely.

Two served consequences were measured, both silent:

IA-019  `GET /test-results/citizen/{health_id}` and `.../timeline` outer-join
        `TestType` and then filter `TestType.category == <category>`. For a row
        with `test_type_id IS NULL` that predicate is NULL, so the row is
        excluded. A category-filtered clinical history silently omits every
        result created by the order path or the analyzer. Proven in PostgreSQL:
        3 results stored, 1 returned.

IA-020  The catalog is also where reference ranges come from. Without it the
        analyzer path leaves `normal_range_low/high` NULL, never calls
        `get_flag`, and stores `flag = NULL`; the order path calls `get_flag`,
        which returns `"unknown"` *before* its critical check when ranges are
        absent. `LabResult.flag == "critical"` is what the critical-alert
        service, the statistics dashboards, the citizen portal and the
        compliance export all read, so a critically abnormal analyzer result is
        invisible to every one of them. `check_critical` needs only test name
        and value — data the analyzer route already holds.

The fix applies the resolution convention the platform had already established
in `test_results.py` (`test_code` exact, else `test_name` case-insensitive) to
all four paths, via one shared helper. It invents no clinical semantics: it
makes three paths behave the way the fourth already did.
"""
from __future__ import annotations

import ast
import pathlib

import pytest
from app.services.critical_alerts import CRITICAL_THRESHOLDS, check_critical
from app.services.interpretation import apply_critical_override, get_flag
from app.services.test_catalog import resolve_test_type

_BACKEND = pathlib.Path(__file__).resolve().parents[2]
_APP = _BACKEND / "app"

# Every production module that constructs a LabResult. The model definition
# itself is not a write path.
_WRITE_PATHS = (
    "app/services/order_service.py",
    "app/routes/device_results.py",
    "app/routes/test_results.py",
    "app/core/bootstrap/demo_data.py",
)


# ── the root cause, as pure functions ────────────────────────────────────────


def test_get_flag_returns_unknown_before_the_critical_check_when_ranges_are_absent():
    """Pins why a missing reference range hides a critical value.

    `get_flag` returns "unknown" on its first branch when either bound is None,
    so the `check_critical` call further down is unreachable for such a result.
    This is the behaviour the catalog fill exists to prevent, not a defect in
    `get_flag` itself.
    """
    assert get_flag(7.5, None, None, test_name="potassium") == "unknown"
    assert get_flag(500.0, None, None, test_name="glucose") == "unknown"
    # With ranges supplied, the same values are classified critical.
    assert get_flag(7.5, 3.5, 5.1, test_name="potassium") == "critical"


def test_check_critical_needs_only_a_test_name_and_a_value():
    """The analyzer route already holds everything this needs."""
    assert "potassium" in CRITICAL_THRESHOLDS
    alert = check_critical("potassium", 7.5)
    assert alert is not None
    assert alert["severity"] == "critical_high"
    assert check_critical("potassium", 4.0) is None


# ── the canonical resolver's contract ────────────────────────────────────────


class _Row:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class _Q:
    def __init__(self, rows):
        self._rows = rows
        self._pred = None

    def filter(self, pred):
        self._pred = pred
        return self

    def first(self):
        return self._rows.pop(0) if self._rows else None


class _StubSession:
    """Returns queued rows in order; records how many lookups were attempted."""

    def __init__(self, *results):
        self._queued = list(results)
        self.lookups = 0

    def query(self, _model):
        self.lookups += 1
        nxt = self._queued.pop(0) if self._queued else None
        return _Q([nxt] if nxt is not None else [])


def test_resolver_prefers_test_code_over_name():
    by_code = _Row(id=7, normal_range_low=3.5, normal_range_high=5.1, unit="mmol/L")
    db = _StubSession(by_code)
    low, high, unit, tt = resolve_test_type(db, "Potassium", "K", None, None, None)
    assert tt is by_code
    assert db.lookups == 1, "a matching test_code must not trigger the name fallback"
    assert (low, high, unit) == (3.5, 5.1, "mmol/L")


def test_resolver_falls_back_to_name_when_code_misses():
    by_name = _Row(id=9, normal_range_low=1.0, normal_range_high=2.0, unit="g/dL")
    db = _StubSession(None, by_name)
    low, high, unit, tt = resolve_test_type(db, "Potassium", "NOPE", None, None, None)
    assert tt is by_name
    assert db.lookups == 2
    assert (low, high, unit) == (1.0, 2.0, "g/dL")


def test_resolver_does_not_overwrite_caller_supplied_values():
    tt_row = _Row(id=1, normal_range_low=3.5, normal_range_high=5.1, unit="mmol/L")
    db = _StubSession(tt_row)
    low, high, unit, tt = resolve_test_type(db, "Potassium", "K", 1.0, 9.0, "custom")
    assert (low, high, unit) == (1.0, 9.0, "custom")
    assert tt is tt_row


def test_resolver_returns_none_when_the_catalog_has_no_match():
    db = _StubSession(None, None)
    low, high, unit, tt = resolve_test_type(db, "Unheard Of Assay", None, None, None, None)
    assert tt is None
    assert (low, high, unit) == (None, None, None)


# ── the guards: no write path may skip the catalog ───────────────────────────


def _calls_function(rel_path: str, func_name: str) -> bool:
    """True only when the module actually *calls* func_name.

    Substring matching is not enough: an ``import`` line contains the name, so a
    source scan passes even after every call site is deleted. This was found by
    the negative proof for IA-024 — removing the override call from the analyzer
    path left the string-matching guard green.
    """
    tree = ast.parse((_BACKEND / rel_path).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id == func_name:
            return True
        if isinstance(func, ast.Attribute) and func.attr == func_name:
            return True
    return False


def _lab_result_constructions(rel_path: str) -> list[ast.Call]:
    tree = ast.parse((_BACKEND / rel_path).read_text(encoding="utf-8"))
    return [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id == "LabResult"
    ]


@pytest.mark.parametrize("rel_path", _WRITE_PATHS)
def test_every_write_path_passes_test_type_id(rel_path):
    """A write path must make the link explicit, even if it resolves to None.

    Passing None after an honest catalog lookup is legitimate — a test the
    catalog does not carry has no TestType. Omitting the keyword entirely is
    not: it guarantees NULL without ever asking.
    """
    calls = _lab_result_constructions(rel_path)
    assert calls, f"{rel_path} no longer constructs a LabResult; update _WRITE_PATHS"
    for call in calls:
        kwargs = {kw.arg for kw in call.keywords if kw.arg}
        assert "test_type_id" in kwargs, (
            f"{rel_path}:{call.lineno} builds a LabResult without test_type_id, so the "
            "row is written with a NULL test-type link and drops out of every "
            "category-filtered query. See IA-019."
        )


@pytest.mark.parametrize("rel_path", _WRITE_PATHS)
def test_every_write_path_resolves_the_catalog(rel_path):
    """The link and the reference ranges come from the same lookup (IA-020)."""
    assert _calls_function(rel_path, "resolve_test_type"), (
        f"{rel_path} does not call resolve_test_type, so it cannot fill missing "
        "reference ranges and any critical value it stores is left unflagged."
    )


def test_there_is_exactly_one_catalog_resolver():
    """Reuse before build: the resolution convention lives in one place.

    Before this change the logic existed once, privately, inside a route module.
    A second copy would let the two drift, and the convention is what decides
    which TestType a free-text test name means.
    """
    definitions = []
    for path in sorted(_APP.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in (
                "resolve_test_type",
                "_fill_ranges_from_catalog",
            ):
                definitions.append(f"{path.relative_to(_APP.parent)}:{node.lineno}")
    assert len(definitions) == 1, f"expected one resolver, found: {definitions}"


# ── IA-024: criticality must not depend on a catalog entry existing ──────────


def _seeded_test_codes() -> set[str]:
    import re
    src = (_BACKEND / "app/core/startup_guard.py").read_text(encoding="utf-8")
    return set(re.findall(r'test_code="([^"]+)"', src))


def test_the_catalog_does_not_cover_every_critical_capable_test():
    """Pins the data gap that motivates the override (IA-024).

    The startup seeder creates a bounded TestType catalog; CRITICAL_THRESHOLDS is
    a separate, larger list. Tests in the second but not the first resolve to no
    TestType, so no reference range is available and `get_flag` cannot classify
    them — which is exactly when the override has to carry the criticality.

    This asserts the gap is non-empty, not that it has a particular size: closing
    it needs clinical reference data for each test, which is a decision for
    someone with clinical authority, not something to fill in from types.
    """
    uncatalogued = set(CRITICAL_THRESHOLDS) - _seeded_test_codes()
    assert uncatalogued, (
        "Every critical-capable test now has a catalog entry. If the catalog was "
        "extended with real clinical reference data, IA-024's data half is closed "
        "and this test should be replaced by one asserting the opposite."
    )
    # The cardiac, coagulation and sepsis markers are the ones that matter most.
    for marker in ("troponin", "inr", "calcium"):
        assert marker in uncatalogued, (
            f"{marker} left the uncatalogued set; re-derive IA-024's numbers."
        )


def test_override_escalates_a_critical_value_with_no_reference_range():
    """The case the analyzer produces: a value, a name, and no range."""
    assert get_flag(7.5, None, None, test_name="potassium") == "unknown"
    assert apply_critical_override("unknown", "potassium", 7.5) == "critical"
    assert apply_critical_override(None, "potassium", 7.5) == "critical"
    # A test with a threshold but no catalog entry — the IA-024 population.
    assert "troponin" in CRITICAL_THRESHOLDS
    th = CRITICAL_THRESHOLDS["troponin"]
    assert apply_critical_override(None, "troponin", th["critical_high"] + 1) == "critical"


def test_override_never_invents_a_classification():
    """It escalates to "critical" or leaves the flag exactly as it was."""
    # Normal value, threshold known -> unchanged.
    assert apply_critical_override("normal", "potassium", 4.0) == "normal"
    assert apply_critical_override(None, "potassium", 4.0) is None
    assert apply_critical_override("unknown", "potassium", 4.0) == "unknown"
    # Test the threshold table does not know -> unchanged, whatever the value.
    assert apply_critical_override("unknown", "Unheard Of Assay", 99999) == "unknown"
    # No value -> nothing to judge.
    assert apply_critical_override("unknown", "potassium", None) == "unknown"
    # It never downgrades an existing critical.
    assert apply_critical_override("critical", "potassium", 4.0) == "critical"
    # It never produces H, L or normal.
    for flag in (None, "unknown", "H", "L", "normal"):
        out = apply_critical_override(flag, "potassium", 7.5)
        assert out == "critical", out


@pytest.mark.parametrize("rel_path", (
    "app/services/order_service.py",
    "app/routes/device_results.py",
    "app/routes/test_results.py",
))
def test_every_clinical_write_path_applies_the_critical_override(rel_path):
    """Seeding is not a clinical path; the three clinical writers are."""
    assert _calls_function(rel_path, "apply_critical_override"), (
        f"{rel_path} stores a flag without consulting the critical-threshold "
        "table, so a critical value for an uncatalogued test is stored unflagged "
        "and is invisible to every consumer of flag == 'critical'. See IA-024."
    )


# ── the guard must also see raw SQL, not only ORM constructions ──────────────


def test_no_raw_sql_writes_lab_results_outside_the_known_dead_module():
    """An AST guard on `LabResult(...)` cannot see a text() INSERT.

    `app/reference/infrastructure/repositories.py` contains an
    `INSERT INTO lab_results` naming columns (`analyte`, `min_value`,
    `is_critical`, `flagged`, `performed_by`, …) that the table does not have, so
    it fails closed with UndefinedColumn and `app/reference` serves no route that
    reaches it. It is pinned here rather than removed, because a *new* raw writer
    would bypass every other guard in this file silently. See IA-025.
    """
    known_dead = {"app/reference/infrastructure/repositories.py"}
    offenders: set[str] = set()
    for path in sorted(_APP.rglob("*.py")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "INSERT INTO lab_results" in text:
            offenders.add(str(path.relative_to(_APP.parent)))
    assert offenders == known_dead, (
        "raw SQL writing lab_results changed. A new writer must set test_type_id "
        f"and the clinical flag like the ORM paths do. Found: {offenders}"
    )
