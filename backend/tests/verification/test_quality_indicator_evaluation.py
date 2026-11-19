"""The ISO 15189 / CAP quality indicator surface must not fake conformance.

Three defects, all measured before they were changed.

1. ``GET /lims/quality/indicators`` publishes the ISO 15189 and the CAP
   catalogues together, but ``evaluate_iso_15189_indicator`` consulted only
   ``ISO_15189_INDICATORS``.  Every one of the four CAP ids therefore raised
   ``ValueError``, which the route converted into ``404 "Resource not found"`` --
   denying the existence of an indicator the sibling endpoint had just returned.

2. A percentage indicator accepted any float.  ``-500`` against a ``< 2%`` target
   scored ``"passed"``: a negative specimen rejection rate reported as
   conformant.  The spec dicts already declare ``"measure": "percentage"``, so
   the bound is read from the data rather than invented here.

3. The comparison fell back to ``meets_target = True`` whenever the target string
   carried no ASCII ``<`` or ``>``.  STATED PRECISELY, because it matters: all
   ten ISO targets do carry an operator today, so that branch was NOT reachable
   and this was a latent trap rather than a live defect.  An indicator added with
   a Unicode ``≤`` or a bare ``"95%"`` would have become a quality indicator that
   can only ever report "passed" -- which in an accreditation context is the
   worst available failure mode.  It now fails closed.

Also: these were the only 2 of this module's 69 routes with no authenticated
caller.  The reference data is published and the evaluation is stateless, so
guarding them is a consistency repair, not a disclosure fix -- and the tests say
so rather than claiming a leak was closed.
"""

from __future__ import annotations

import contextlib

import pytest
from app.lims.quality import (
    CAP_INDICATORS,
    ISO_15189_INDICATORS,
    IndicatorNotEvaluable,
    IndicatorValueOutOfRange,
    evaluate_iso_15189_indicator,
)

from tests.verification import harness

# ---------------------------------------------------------------------------
# The evaluator
# ---------------------------------------------------------------------------


def test_a_cap_indicator_is_recognised_rather_than_denied():
    """Defect 1. Every published id must be *known*, even if not comparable."""
    for indicator_id in CAP_INDICATORS:
        with pytest.raises(IndicatorNotEvaluable):
            evaluate_iso_15189_indicator(indicator_id, 50.0)


def test_an_unknown_indicator_is_still_a_different_answer():
    """The repair must not blur 'not evaluable' into 'does not exist'."""
    with pytest.raises(ValueError) as excinfo:
        evaluate_iso_15189_indicator("no-such-indicator", 50.0)
    # Not the not-evaluable type -- the route maps these to 404 and 422.
    assert not isinstance(excinfo.value, IndicatorNotEvaluable)


def test_every_published_cap_target_is_genuinely_prose():
    """Guards the premise of defect 1 rather than assuming it.

    If someone later gives a CAP indicator a real threshold, this fails and the
    catalogue should then be evaluable -- which is the outcome we would want.
    """
    for spec in CAP_INDICATORS.values():
        target = spec["target"]
        numeric = target.replace("%", "").replace("<", "").replace(">", "").strip()
        with pytest.raises(ValueError):
            float(numeric)


@pytest.mark.parametrize("bad_value", [-500.0, -0.1, 100.1, 1e9])
def test_a_percentage_indicator_rejects_an_impossible_value(bad_value):
    """Defect 2. -500% must not be scored at all, let alone as passed."""
    with pytest.raises(IndicatorValueOutOfRange):
        evaluate_iso_15189_indicator("specimen_rejection_rate", bad_value)


@pytest.mark.parametrize(
    ("value", "expected"),
    [(0.0, "passed"), (1.9, "passed"), (2.0, "passed"), (2.1, "failed"), (100.0, "failed")],
)
def test_a_less_than_target_still_scores_correctly(value, expected):
    """The repair must not break the comparison it exists to protect."""
    result = evaluate_iso_15189_indicator("specimen_rejection_rate", value)
    assert result["status"] == expected
    assert result["target"] == "< 2%"


@pytest.mark.parametrize(
    ("value", "expected"),
    [(100.0, "passed"), (95.0, "passed"), (94.9, "failed"), (0.0, "failed")],
)
def test_a_greater_than_target_still_scores_correctly(value, expected):
    result = evaluate_iso_15189_indicator("tat_emergency", value)
    assert result["status"] == expected


def test_no_iso_indicator_can_only_ever_pass():
    """Defect 3, as a standing guard rather than a claim about today.

    For every ISO indicator, some value in range must fail. An indicator that
    passes at both extremes cannot discriminate and is not measuring anything.
    """
    unfalsifiable = []
    for indicator_id, spec in ISO_15189_INDICATORS.items():
        outcomes = set()
        for value in (0.0, 50.0, 100.0):
            with contextlib.suppress(IndicatorNotEvaluable, IndicatorValueOutOfRange):
                outcomes.add(evaluate_iso_15189_indicator(indicator_id, value)["status"])
        if outcomes and "failed" not in outcomes:
            unfalsifiable.append(f"{indicator_id} (target {spec['target']!r})")

    assert unfalsifiable == [], (
        "these indicators cannot fail for any in-range value, so they certify "
        "conformance unconditionally:\n  " + "\n  ".join(unfalsifiable)
    )


def test_a_target_without_a_numeric_comparison_fails_closed():
    """The removed ``else True``: absent an operator, refuse rather than pass."""
    from app.lims.quality import _parse_target

    for prose in ("95%", "≤ 2%", "100% of required PT events", "as low as possible"):
        with pytest.raises(IndicatorNotEvaluable):
            _parse_target(prose)


# ---------------------------------------------------------------------------
# The HTTP boundary
# ---------------------------------------------------------------------------
#
# These go through the real app so the authorization dependency is actually
# resolved. Neither route touches the database, but the harness is still the
# right entry point: it is what leaves the real authentication dependency in
# place when the actor is None.

_ROUTES_REQUIRE_POSTGRES = harness.requires_postgres()


@pytest.fixture
def Session():
    factory = harness.session_factory()
    yield factory
    harness.dispose(factory)


@_ROUTES_REQUIRE_POSTGRES
def test_both_quality_routes_refuse_an_unauthenticated_caller(Session):
    """They were this module's only 2 anonymous routes out of 69."""
    with harness.client(Session, None) as api:
        listed = api.get("/lims/quality/indicators")
        evaluated = api.post(
            "/lims/quality/indicators/specimen_rejection_rate/evaluate?value=1.0"
        )

    assert listed.status_code == 401, listed.text
    assert evaluated.status_code == 401, evaluated.text


@_ROUTES_REQUIRE_POSTGRES
def test_an_authenticated_caller_still_gets_an_evaluation(Session):
    """Guarding must not disable the capability."""
    actor = harness.Actor(user_id=1, lab_id=1, role="lab_manager")
    with harness.client(Session, actor) as api:
        response = api.post(
            "/lims/quality/indicators/specimen_rejection_rate/evaluate?value=1.0"
        )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "passed"


@_ROUTES_REQUIRE_POSTGRES
def test_a_cap_indicator_answers_422_not_404(Session):
    """The listing publishes it, so denying its existence was the defect."""
    actor = harness.Actor(user_id=1, lab_id=1, role="lab_manager")
    with harness.client(Session, actor) as api:
        listed = api.get("/lims/quality/indicators")
        response = api.post(
            "/lims/quality/indicators/proficiency_testing/evaluate?value=50.0"
        )

    # The id really is advertised by the sibling route.
    assert "proficiency_testing" in [row["id"] for row in listed.json()["cap"]]
    assert response.status_code == 422, response.text
    assert "cannot be evaluated numerically" in response.json()["detail"]


@_ROUTES_REQUIRE_POSTGRES
def test_an_impossible_percentage_answers_400_not_passed(Session):
    actor = harness.Actor(user_id=1, lab_id=1, role="lab_manager")
    with harness.client(Session, actor) as api:
        response = api.post(
            "/lims/quality/indicators/specimen_rejection_rate/evaluate?value=-500"
        )

    assert response.status_code == 400, response.text
    assert "passed" not in response.text


@_ROUTES_REQUIRE_POSTGRES
def test_an_unknown_indicator_still_answers_404(Session):
    actor = harness.Actor(user_id=1, lab_id=1, role="lab_manager")
    with harness.client(Session, actor) as api:
        response = api.post("/lims/quality/indicators/not-a-real-one/evaluate?value=1")

    assert response.status_code == 404, response.text
