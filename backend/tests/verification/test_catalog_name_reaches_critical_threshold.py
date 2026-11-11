"""BLOCKER-01 — a result reported under the catalog's own name must still be critical.

`GET /test-types` is the catalog an integrating client reads, and it publishes
`test_name` verbatim: "Glucose (Fasting)". `CRITICAL_THRESHOLDS` is keyed by
analyte — "glucose" — and `check_critical` derived its key from the test name
alone, so "Glucose (Fasting)" normalised to "glucose_(fasting)" and matched
nothing. The documented `critical_low` of 40 was then never consulted, and
`get_flag` fell through to its generic rule, `normal_low * 0.5` = 35 for the
seeded 70-100 range.

The consequence, measured on real PostgreSQL through the real write path before
the fix: a glucose of 35.1-40.0 mg/dL — severe hypoglycaemia — was stored with
`flag = "L"`. `LabResult.flag == "critical"` is what the critical-alert feed,
the citizen portal's `critical_flags`, the statistics `critical_count` and the
FHIR interpretation all select on, so the result was absent from every one of
them. A client that ignored the catalog and sent the bare name "Glucose" got
"critical" correctly; the platform punished catalog-faithful clients only.

The reconciliation uses an identity the catalog already assigns rather than a
new naming rule: `test_types.test_code` is "glucose" on the very row whose
`test_name` is "Glucose (Fasting)", and that is the vocabulary
`CRITICAL_THRESHOLDS` is written in. Of the 20 seeded rows, 13 reach a threshold
row by code against 8 by name, and each of those 13 codes names the same analyte
as its own test name, so no result is mapped to a different clinical concept.
The lookup tries the name first and the code only as a fallback, so every caller
that resolved before resolves identically.

No threshold moved. `critical_low` is still 40, the generic bound is still
`normal_low * 0.5`, and the tests below pin both.
"""
from __future__ import annotations

import ast
import pathlib

import pytest
from app.services.critical_alerts import CRITICAL_THRESHOLDS, check_critical
from app.services.interpretation import apply_critical_override, get_flag

from .harness import committed, dispose, requires_postgres, session_factory

_BACKEND = pathlib.Path(__file__).resolve().parents[2]

# The seeded Glucose row, as app/core/startup_guard.py writes it.
_GLUCOSE_NAME = "Glucose (Fasting)"
_GLUCOSE_CODE = "glucose"
_GLUCOSE_LOW = 70
_GLUCOSE_HIGH = 100


def _stored_flag(
    name: str,
    value: float | None,
    low: float | None,
    high: float | None,
    code: str | None,
) -> str | None:
    """The flag the four write paths compute, in their exact order."""
    flag = "unknown"
    if value is not None and low is not None and high is not None:
        flag = get_flag(value, low, high, test_name=name, test_code=code)
    return apply_critical_override(flag, name, value, code)


# ── the two numbers the fix must not move ────────────────────────────────────


def test_the_documented_glucose_thresholds_are_unchanged():
    """A fix that lowered critical_low to reach 35.1 would be a different claim."""
    assert CRITICAL_THRESHOLDS["glucose"]["critical_low"] == 40
    assert CRITICAL_THRESHOLDS["glucose"]["critical_high"] == 500


def test_the_generic_fallback_bound_is_unchanged():
    """`normal_low * 0.5` still decides criticality for a test with no threshold row.

    "Vitamin D" has no row in CRITICAL_THRESHOLDS under either its name or its
    catalog code, so only the generic rule can classify it.
    """
    assert "vitamin_d" not in CRITICAL_THRESHOLDS
    assert get_flag(10.0, 20, 100, test_name="Vitamin D", test_code="vitamin_d") == "critical"
    assert get_flag(10.1, 20, 100, test_name="Vitamin D", test_code="vitamin_d") == "L"


# ── the defect, as a pure function ───────────────────────────────────────────


@pytest.mark.parametrize("value", [35.1, 37.5, 39.9, 40.0])
def test_catalog_name_reaches_the_documented_threshold(value: float):
    """The window that was graded "L": above the generic bound, at or below 40."""
    assert value > _GLUCOSE_LOW * 0.5, "a value inside the generic bound proves nothing"
    assert check_critical(_GLUCOSE_NAME, value, _GLUCOSE_CODE) is not None
    assert (
        _stored_flag(_GLUCOSE_NAME, value, _GLUCOSE_LOW, _GLUCOSE_HIGH, _GLUCOSE_CODE)
        == "critical"
    )


def test_the_bare_name_still_works_without_a_code():
    """The path that was already correct must stay correct."""
    assert check_critical("Glucose", 37.5) is not None
    assert _stored_flag("Glucose", 37.5, _GLUCOSE_LOW, _GLUCOSE_HIGH, None) == "critical"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (30.0, "critical"),  # below the generic bound — was already critical
        (34.9, "critical"),
        (35.0, "critical"),  # exactly the generic bound
        (35.1, "critical"),  # the window — regressed to "L" before the fix
        (40.0, "critical"),  # the documented critical_low
        (40.1, "L"),         # above it: low, not critical
        (45.0, "L"),
        (85.0, "normal"),
        (150.0, "H"),
        (500.0, "critical"), # the documented critical_high
    ],
)
def test_boundary_sweep_under_the_catalog_name(value: float, expected: str):
    """Pins the whole curve, so a fix cannot shift a boundary to pass the window."""
    assert (
        _stored_flag(_GLUCOSE_NAME, value, _GLUCOSE_LOW, _GLUCOSE_HIGH, _GLUCOSE_CODE)
        == expected
    )


@pytest.mark.parametrize(
    ("name", "code", "low", "high", "value", "expected"),
    [
        # Urea / ALT / AST: the key miss was real, but the generic rule already
        # fired at or before the documented threshold, so these never lost a
        # criticality. They must not change.
        ("Urea (BUN)", "urea", 15, 45, 250.0, "critical"),
        ("Urea (BUN)", "urea", 15, 45, 60.0, "H"),
        ("Urea (BUN)", "urea", 15, 45, 30.0, "normal"),
        ("Urea (BUN)", "urea", 15, 45, 10.0, "L"),
        ("ALT (SGPT)", "alt", 0, 40, 1200.0, "critical"),
        ("ALT (SGPT)", "alt", 0, 40, 60.0, "H"),
        ("AST (SGOT)", "ast", 0, 40, 1200.0, "critical"),
        ("AST (SGOT)", "ast", 0, 40, 20.0, "normal"),
        # Potassium's name already matched its key; the fallback must not disturb it.
        ("Potassium", "potassium", 3.5, 5.0, 7.0, "critical"),
        ("Potassium", "potassium", 3.5, 5.0, 2.0, "critical"),
        ("Potassium", "potassium", 3.5, 5.0, 4.0, "normal"),
        ("Potassium", "potassium", 3.5, 5.0, 5.5, "H"),
    ],
)
def test_the_other_thresholds_are_untouched(
    name: str, code: str, low: float, high: float, value: float, expected: str,
):
    assert _stored_flag(name, value, low, high, code) == expected


# ── the fallback's own limits ────────────────────────────────────────────────


def test_the_code_is_a_fallback_and_never_an_override():
    """A name that resolves wins, so no existing caller's answer can change.

    "Potassium" resolves by name. Handing it an unrelated code must not move the
    classification: the name's own thresholds decide.
    """
    by_name = check_critical("Potassium", 7.0)
    assert by_name is not None
    assert check_critical("Potassium", 7.0, "glucose") == by_name


def test_a_code_with_no_threshold_row_changes_nothing():
    """7 of the 20 seeded rows have no threshold row under name or code."""
    for code in ("cholesterol", "triglycerides", "vitamin_d", "rbc", "mcv", "ldl", "hdl"):
        assert code not in CRITICAL_THRESHOLDS
    assert check_critical("LDL Cholesterol", 400.0, "ldl") is None
    assert check_critical("Total Cholesterol", 900.0, "cholesterol") is None


def test_no_value_and_no_name_are_still_handled():
    assert check_critical(_GLUCOSE_NAME, 37.5, None) is None  # unresolved: as before
    assert apply_critical_override("L", _GLUCOSE_NAME, None, _GLUCOSE_CODE) == "L"
    assert apply_critical_override("L", None, 37.5, _GLUCOSE_CODE) == "L"
    assert get_flag(37.5, None, None, test_name=_GLUCOSE_NAME, test_code=_GLUCOSE_CODE) == (
        "unknown"
    )


def test_the_override_still_only_ever_escalates():
    """It must not be able to produce H, L or normal, or undo a criticality."""
    assert apply_critical_override("critical", _GLUCOSE_NAME, 85.0, _GLUCOSE_CODE) == "critical"
    assert apply_critical_override("normal", _GLUCOSE_NAME, 85.0, _GLUCOSE_CODE) == "normal"
    assert apply_critical_override("H", _GLUCOSE_NAME, 150.0, _GLUCOSE_CODE) == "H"


def test_every_code_that_reaches_a_threshold_row_names_the_same_analyte():
    """The clinical-safety precondition for using test_code as the key.

    Read from the seeder rather than asserted by hand, so adding a catalog row
    whose code collides with a different analyte's thresholds fails here.
    """
    source = (_BACKEND / "app" / "core" / "startup_guard.py").read_text()
    rows: list[tuple[str, str]] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "TestType":
            kw = {k.arg: k.value for k in node.keywords}
            if "test_code" in kw and "test_name" in kw:
                rows.append(
                    (ast.literal_eval(kw["test_code"]), ast.literal_eval(kw["test_name"])),
                )
    assert len(rows) >= 20, "the seeded catalog shrank; re-check this mapping"

    # The analyte each code is allowed to mean, read off its own test name.
    for code, name in rows:
        if code not in CRITICAL_THRESHOLDS:
            continue
        head = name.split("(")[0].strip().lower().replace(" ", "_").replace("-", "_")
        aliases = {
            "glucose": {"glucose"},
            "urea": {"urea"},
            "alt": {"alt"},
            "ast": {"ast"},
            "wbc": {"white_blood_cells"},
            "hemoglobin": {"hemoglobin"},
            "platelets": {"platelets"},
            "creatinine": {"creatinine"},
            "tsh": {"tsh"},
            "potassium": {"potassium"},
            "sodium": {"sodium"},
            "hba1c": {"hba1c"},
            "uric_acid": {"uric_acid"},
        }
        assert code in aliases, f"catalog code {code!r} reaches thresholds but is unreviewed"
        assert head in aliases[code] or head == code, (
            f"catalog code {code!r} would read {name!r} as a different analyte"
        )


# ── the call sites, so a path cannot quietly stop passing the code ───────────


def _calls_passing_code(path: str, callee: str) -> int:
    """How many calls to `callee` in `path` carry a test_code argument."""
    tree = ast.parse((_BACKEND / path).read_text())
    found = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
        if name != callee:
            continue
        has_kw = any(k.arg == "test_code" for k in node.keywords)
        # get_flag takes value/low/high/name positionally in these call sites;
        # apply_critical_override takes flag/name/value then the code.
        positional = len(node.args) >= (5 if callee == "get_flag" else 4)
        if has_kw or positional:
            found += 1
    return found


@pytest.mark.parametrize(
    "path",
    [
        "app/routes/test_results.py",
        "app/routes/device_results.py",
        "app/services/order_service.py",
    ],
)
def test_every_write_path_passes_the_resolved_code(path: str):
    """A path that drops the argument silently reintroduces the defect."""
    assert _calls_passing_code(path, "apply_critical_override") >= 1, (
        f"{path} calls apply_critical_override without a test_code"
    )


def test_get_flag_receives_the_code_on_every_write_path():
    for path in (
        "app/routes/test_results.py",
        "app/routes/device_results.py",
        "app/services/order_service.py",
    ):
        assert _calls_passing_code(path, "get_flag") >= 1, (
            f"{path} calls get_flag without a test_code"
        )


# ── the stored flag, on real PostgreSQL ──────────────────────────────────────


@requires_postgres()
def test_the_flag_committed_to_postgresql_is_critical():
    """The claim is about `lab_results.flag` in the database, not a return value.

    Everything is created inside one transaction and rolled back, so the
    verification database keeps no probe rows.
    """
    Session = session_factory()
    try:
        with Session() as db:
            from sqlalchemy import text

            lab = db.execute(
                text("INSERT INTO labs(name) VALUES('BLOCKER01 PROOF') RETURNING id"),
            ).scalar()
            patient = db.execute(
                text(
                    "INSERT INTO patients(lab_id, full_name, phone) "
                    "VALUES(:l, 'BLOCKER01 PROOF', '0000000000') RETURNING id",
                ),
                {"l": lab},
            ).scalar()
            order = db.execute(
                text(
                    "INSERT INTO lab_orders(patient_id, lab_id) "
                    "VALUES(:p, :l) RETURNING id",
                ),
                {"p": patient, "l": lab},
            ).scalar()
            db.execute(
                text(
                    "INSERT INTO test_types(test_code, test_name, unit, "
                    "normal_range_low, normal_range_high) "
                    "VALUES(:c, :n, 'mg/dL', :lo, :hi)",
                ),
                {"c": _GLUCOSE_CODE, "n": _GLUCOSE_NAME, "lo": _GLUCOSE_LOW, "hi": _GLUCOSE_HIGH},
            )
            db.flush()

            from app.services.test_catalog import resolve_test_type

            stored: dict[float, tuple[str | None, int | None]] = {}
            for index, value in enumerate((35.1, 40.0)):
                low, high, unit, tt = resolve_test_type(
                    db, _GLUCOSE_NAME, None, None, None, None,
                )
                assert tt is not None, "the catalog name must resolve"
                flag = _stored_flag(_GLUCOSE_NAME, value, low, high, tt.test_code)
                row = db.execute(
                    text(
                        "INSERT INTO lab_results(order_id, test_type_id, test_name, "
                        "value, unit, normal_range_low, normal_range_high, flag, token) "
                        "VALUES(:o, :tt, :n, :v, :u, :lo, :hi, :f, :tok) RETURNING id",
                    ),
                    {
                        "o": order, "tt": tt.id, "n": _GLUCOSE_NAME, "v": value,
                        "u": unit, "lo": low, "hi": high, "f": flag,
                        "tok": f"blocker01-proof-{index}",
                    },
                ).scalar()
                db.flush()
                read_back = db.execute(
                    text("SELECT flag, test_type_id FROM lab_results WHERE id = :i"),
                    {"i": row},
                ).first()
                stored[value] = (read_back[0], read_back[1])

            assert stored[35.1][0] == "critical", f"35.1 stored as {stored[35.1][0]!r}"
            assert stored[40.0][0] == "critical", f"40.0 stored as {stored[40.0][0]!r}"
            assert stored[35.1][1] is not None, "the result must stay linked to its TestType"

            # The consumers select on flag == 'critical'; both rows must be there.
            visible = db.execute(
                text(
                    "SELECT count(*) FROM lab_results lr "
                    "JOIN lab_orders lo ON lo.id = lr.order_id "
                    "WHERE lo.lab_id = :l AND lr.flag = 'critical'",
                ),
                {"l": lab},
            ).scalar()
            assert visible == 2, "an under-flagged row is invisible to the alert feed"

            db.rollback()

        # Nothing survived the rollback.
        leaked = committed(
            Session,
            "SELECT count(*) AS n FROM labs WHERE name = 'BLOCKER01 PROOF'",
        )
        assert leaked[0]["n"] == 0, "the probe must not persist rows"
    finally:
        dispose(Session)
