"""The FHIR Observation must not assert more than the record supports.

Four defects, all measured on real PostgreSQL through the production builder
before the fix, all in one function that already held the data it needed:

IA-028 (P1, clinical misrepresentation)
    ``status`` was the literal ``"final"`` for every result. GULA tracks
    verification on the order — a doctor or admin verifying a result sets
    ``lab_orders.status = "validated"`` and locks the row — so a result on a
    ``pending`` or ``completed`` order had been verified by nobody, and a result
    whose order was ``cancelled`` had been withdrawn. All three were published
    as ``final``, which is the one claim a consuming EHR is entitled to act on.

IA-029 (P1, non-conformant terminology)
    ``interpretation`` published the raw internal flag under the URI
    ``.../v3-ObservationInterpretation``. That system defines ``H``, ``L``,
    ``N``, ``HH``, ``LL``, ``AA`` — not ``critical``, ``normal`` or
    ``unknown``. Three of the five values GULA writes were codes that do not
    exist in the system they were published under.

IA-030 (P2, hardcoded version)
    ``meta.versionId`` was the literal ``"1"`` while ``lab_results.version`` is
    the optimistic-lock counter incremented on every mutation, so an amended
    result was published as version 1 and a FHIR client's concurrency and cache
    logic had nothing real to work with.

IA-031 (P2, cross-tenant existence oracle)
    ``GET /fhir/Observation/{id}`` answered 404 for an unknown id but 403 for one
    belonging to another laboratory, so iterating ids revealed another lab's
    result count and id range. Every sibling FHIR read route in the module
    already answered 404 for both; Observation was the only exception.

Why the suite did not catch any of it: eight test files reference Observation and
not one asserted ``status``, ``interpretation`` or ``meta.versionId``. The
builder was covered for the fields that were right.
"""
from __future__ import annotations

import ast
import pathlib

import pytest
from app.fhir.terminology import (
    interpretation_code,
    interpretation_concept,
    observation_status,
)

_BACKEND = pathlib.Path(__file__).resolve().parents[2]
_ROUTES = _BACKEND / "app" / "routes" / "ehr_fhir.py"

_INTERPRETATION_SYSTEM = "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation"

# The complete code set v3-ObservationInterpretation defines for the subset GULA
# can produce. Anything outside this must never be emitted under that URI.
_VALID_INTERPRETATION_CODES = frozenset({"H", "L", "N", "HH", "LL", "AA"})

# Every value the platform writes to lab_results.flag. Sourced from the three
# producers: get_flag, apply_critical_override, and the analyzer path's None.
_ALL_INTERNAL_FLAGS = ("critical", "H", "L", "normal", "unknown", None, "")

# Every value lab_orders.status can hold, per domain/order_state.py.
_ALL_ORDER_STATUSES = ("pending", "completed", "validated", "cancelled")


# ── IA-028 status ────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("order_status", "expected"),
    [
        ("pending", "preliminary"),
        ("completed", "preliminary"),
        ("validated", "final"),
        ("cancelled", "cancelled"),
    ],
)
def test_status_follows_the_order_state(order_status: str, expected: str):
    assert observation_status(order_status) == expected


def test_only_a_validated_order_may_be_called_final():
    """The whole point: 'final' is a claim, and it needs the verification behind it."""
    finals = [s for s in _ALL_ORDER_STATUSES if observation_status(s) == "final"]
    assert finals == ["validated"]


def test_a_cancelled_order_is_published_as_cancelled():
    """A withdrawn result must not be presented as a usable one."""
    assert observation_status("cancelled") == "cancelled"


@pytest.mark.parametrize("unknown", [None, "", "  ", "nonsense", "FINAL_ish"])
def test_an_unrecognised_order_state_is_never_final(unknown):
    """Fail safe in the clinical direction: never claim final without evidence."""
    assert observation_status(unknown) == "preliminary"


def test_status_is_case_insensitive_but_not_permissive():
    assert observation_status("VALIDATED") == "final"
    assert observation_status(" validated ") == "final"
    assert observation_status("validated_pending") == "preliminary"


# ── IA-029 interpretation ────────────────────────────────────────────────────


@pytest.mark.parametrize("flag", _ALL_INTERNAL_FLAGS)
def test_no_flag_ever_produces_a_code_outside_the_system(flag):
    """The invariant. Every emitted code must exist in the declared system."""
    code = interpretation_code(flag, 37.5, 70, 100)
    assert code is None or code in _VALID_INTERPRETATION_CODES, (
        f"flag {flag!r} produced {code!r}, which v3-ObservationInterpretation "
        "does not define"
    )


@pytest.mark.parametrize(
    ("flag", "value", "low", "high", "expected"),
    [
        ("H", 150.0, 70, 100, "H"),
        ("L", 50.0, 70, 100, "L"),
        ("normal", 85.0, 70, 100, "N"),
        # "critical" has no single code: the system distinguishes direction, and
        # direction is a fact already in the data.
        ("critical", 37.5, 70, 100, "LL"),
        ("critical", 650.0, 70, 100, "HH"),
        ("critical", 70.0, 70, 100, "LL"),    # at the bound, inclusive
        ("critical", 100.0, 70, 100, "HH"),
        # No bound to decide direction -> the system's own code for exactly that.
        ("critical", 37.5, None, None, "AA"),
        ("critical", None, 70, 100, "AA"),
        # A value strictly inside the range that is nonetheless flagged critical
        # (the medical threshold table can do this) has no derivable direction.
        ("critical", 85.0, 70, 100, "AA"),
    ],
)
def test_the_interpretation_mapping(flag, value, low, high, expected):
    assert interpretation_code(flag, value, low, high) == expected


@pytest.mark.parametrize("flag", ["unknown", None, "", "   "])
def test_an_unclassifiable_flag_emits_nothing_rather_than_a_fake_code(flag):
    """GULA's "unknown" means the platform could not classify. There is no code
    for that, so the element is omitted. A fabricated code would be worse than
    an absent optional element."""
    assert interpretation_code(flag, 85.0, 70, 100) is None
    assert interpretation_concept(flag, 85.0, 70, 100) is None


def test_the_concept_declares_the_system_and_an_official_display():
    concept = interpretation_concept("critical", 37.5, 70, 100)
    assert concept is not None
    coding = concept["coding"][0]
    assert coding["system"] == _INTERPRETATION_SYSTEM
    assert coding["code"] == "LL"
    assert coding["display"] == "Critical low"


def test_the_internal_flag_survives_as_text_so_nothing_is_lost():
    """The repair must not discard GULA's own vocabulary — it moves it to `text`,
    which is free text, instead of publishing it as a code."""
    for flag, expected_code in (("critical", "LL"), ("normal", "N"), ("H", "H")):
        concept = interpretation_concept(flag, 37.5, 70, 100)
        assert concept is not None
        assert concept["coding"][0]["code"] == expected_code
        assert concept["text"] == flag


def test_the_display_matches_the_code_for_every_code_we_can_emit():
    """A display that contradicts its code is its own defect."""
    cases = {
        "H": ("H", 150.0, 70, 100),
        "L": ("L", 50.0, 70, 100),
        "N": ("normal", 85.0, 70, 100),
        "LL": ("critical", 37.5, 70, 100),
        "HH": ("critical", 650.0, 70, 100),
        "AA": ("critical", 85.0, 70, 100),
    }
    expected_displays = {
        "H": "High", "L": "Low", "N": "Normal",
        "HH": "Critical high", "LL": "Critical low", "AA": "Critical abnormal",
    }
    for code, args in cases.items():
        concept = interpretation_concept(*args)
        assert concept is not None
        assert concept["coding"][0]["code"] == code
        assert concept["coding"][0]["display"] == expected_displays[code]


# ── the builder, read from the source so a literal cannot creep back ─────────


def _observation_builder() -> str:
    for node in ast.walk(ast.parse(_ROUTES.read_text())):
        if isinstance(node, ast.FunctionDef) and node.name == "_lab_result_to_observation":
            return ast.unparse(node)
    raise AssertionError("_lab_result_to_observation not found")


def test_the_builder_does_not_hardcode_status():
    source = _observation_builder()
    assert "observation_status(order.status)" in source
    assert "'status': 'final'" not in source


def test_the_builder_does_not_hardcode_the_version():
    """IA-030. versionId must come from the optimistic-lock counter."""
    source = _observation_builder()
    assert "result.version" in source
    assert "'versionId': '1'" not in source


def test_the_builder_routes_interpretation_through_the_mapping():
    source = _observation_builder()
    assert "interpretation_concept(" in source
    # The old call published result.flag directly as the code.
    assert "_codeable_concept(result.flag, result.flag" not in source


def test_the_builder_still_publishes_a_reference_range_and_a_value():
    """Positive control: the fields that were already correct must stay.

    A test suite that only forbids things passes on an empty builder.
    """
    source = _observation_builder()
    for required in (
        "'resourceType': 'Observation'",
        "observation_code(result.test_name)",
        "referenceRange",
        "valueQuantity",
        "effectiveDateTime",
        "issued",
        "subject",
    ):
        assert required in source, f"the builder stopped emitting {required}"


# ── IA-031 the existence oracle ──────────────────────────────────────────────


def test_a_cross_tenant_observation_is_not_distinguishable_from_a_missing_one():
    """403 told the caller the id exists in another laboratory. 404 does not."""
    for node in ast.walk(ast.parse(_ROUTES.read_text())):
        if isinstance(node, ast.FunctionDef) and node.name == "fhir_read_observation":
            source = ast.unparse(node)
            break
    else:  # pragma: no cover
        raise AssertionError("fhir_read_observation not found")
    assert "status_code=403" not in source, (
        "a 403 here distinguishes 'exists in another lab' from 'does not exist'"
    )
    assert source.count("status_code=404") >= 2, (
        "both the missing and the cross-tenant case must answer 404"
    )
    # Positive control: the tenant predicate must still be there. Answering 404
    # for everything would also pass the assertions above.
    assert "LabOrder.lab_id == current_user.lab_id" in source
