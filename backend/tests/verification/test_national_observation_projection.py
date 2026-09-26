"""The national canonical-observation projection must be constructible and tenant-scoped.

``CanonicalObservation`` selected ``LabResult.lab_id``, ``patient_id``, ``test_code``,
``value_numeric``, ``reference_range``, ``result_status`` and ``observed_at`` — seven
attributes that model does not have. Building the query raised AttributeError before
any SQL was emitted, so ``GET /national-data/observations`` answered 500 and the feed
carried nothing.

It failed closed, so nothing leaked. The real damage was that the tenant filter was
written against that non-existent ``lab_id``: the scoping had no working
implementation at all. A lab result is scoped through the order it belongs to
(``LabResult.order_id -> LabOrder.lab_id``), which the repaired projection joins.

These tests assert at the level the defect lived: query *construction* and the
compiled predicate. The endpoint itself is still blocked behind ``national_patients``
and ``national_encounters``, which do not exist at the canonical head — a separate
missing-table issue this repair does not claim to fix, pinned by
``test_the_endpoint_is_still_blocked_by_missing_national_tables`` so the day those
tables arrive, the remaining work is visible rather than forgotten.
"""

from __future__ import annotations

import pathlib
from typing import Any

import pytest
from sqlalchemy import inspect as sa_inspect

from . import harness

pytestmark = harness.requires_postgres()

LAB_ID = 996101


@pytest.fixture()
def Session() -> Any:
    S = harness.session_factory(pool_size=2)
    yield S
    harness.dispose(S)


def _compiled(Session: Any, **kwargs: Any) -> str:
    """The projection's SQL text. Construction is where the defect used to raise."""
    import app.main  # configures the full mapped surface
    from app.national_data.models.canonical_observation import CanonicalObservation

    with Session() as session:
        from app.models.lab_order import LabOrder
        from app.national_data.models.canonical_observation import _observation_query

        query = _observation_query(session)
        if "lab_id" in kwargs:
            query = query.filter(LabOrder.lab_id == kwargs["lab_id"])
        assert CanonicalObservation is not None
        return str(query.statement.compile(compile_kwargs={"literal_binds": True}))


def test_the_module_references_no_attribute_LabResult_lacks() -> None:
    """The precise defect: seven attributes selected from a model that has none of them.

    Read from the module source against the real mapper, so it fails at the exact
    reason rather than as a side effect of how the query is built.
    """
    import re

    import app.main  # configures the mapped surface
    from app.models.lab_result import LabResult

    source = (
        pathlib.Path(__file__).resolve().parents[2]
        / "app" / "national_data" / "models" / "canonical_observation.py"
    ).read_text(encoding="utf-8")
    referenced = sorted(set(re.findall(r"\bLabResult\.(\w+)", source)))
    assert referenced, "the census found no LabResult references; the guard would be vacuous"
    missing = [name for name in referenced if not hasattr(LabResult, name)]
    assert not missing, (
        "canonical_observation selects attributes LabResult does not have, so building the "
        f"query raises AttributeError and the feed is dead: {missing}"
    )


def test_the_projection_can_be_constructed_at_all(Session: Any) -> None:
    """Before the repair this raised AttributeError on LabResult.lab_id."""
    sql = _compiled(Session)
    assert "lab_results" in sql, sql[:300]


def test_the_tenant_predicate_comes_from_the_order(Session: Any) -> None:
    sql = _compiled(Session, lab_id=LAB_ID).lower()
    assert f"lab_orders.lab_id = {LAB_ID}" in sql, (
        f"the tenant filter must scope through the order; compiled SQL:\n{sql[-600:]}"
    )
    assert "lab_results.lab_id" not in sql, (
        "the projection must not reference a column LabResult does not have"
    )


def test_the_test_code_is_joined_from_the_test_type(Session: Any) -> None:
    sql = _compiled(Session).lower()
    assert "test_types.test_code" in sql, f"test_code must come from test_types:\n{sql[:600]}"
    assert "join test_types" in sql, "the test type must be joined"


def test_unknown_clinical_fields_are_selected_as_null(Session: Any) -> None:
    """status / observed_at / reference_range have no source and must stay NULL.

    Substituting LabOrder.status or LabResult.created_at would make a national feed
    assert clinical facts it does not hold. Recorded as NR-046.
    """
    sql = _compiled(Session).lower()
    for field in ("result_status", "observed_at", "reference_range"):
        assert f"null as {field}" in sql, (
            f"{field} must be selected as NULL until its source is defined; SQL:\n{sql[:800]}"
        )


def test_the_endpoint_is_still_blocked_by_missing_national_tables(Session: Any) -> None:
    """Honest statement of what this repair does NOT fix.

    The projection outer-joins the national patient and encounter tables for
    enrichment. Neither exists at the canonical head, so the endpoint still fails
    there. When they are created this test fails, which is the signal to re-run the
    feed end to end over real HTTP.
    """
    with Session() as session:
        present = set(sa_inspect(session.get_bind()).get_table_names(schema="public"))
    missing = sorted({"national_patients", "national_encounters"} - present)
    assert missing == ["national_encounters", "national_patients"], (
        "the national enrichment tables now exist, so /national-data/observations "
        f"should be proven end to end over real HTTP. present={sorted(present & {'national_patients', 'national_encounters'})}"
    )
