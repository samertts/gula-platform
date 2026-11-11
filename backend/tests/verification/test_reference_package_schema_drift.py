"""The reference package's SQL targets columns that do not exist.

IA-075, found while closing the last two IA-059 entries. ``SQLResultRepository``
in ``app/reference/infrastructure/repositories.py`` leaves one abstract method
unimplemented (``list_by_patient_analyte``), so the class cannot be
instantiated. IA-070 taught that such a TypeError can be load-bearing, so
before implementing it I checked what it was holding back.

It is holding back queries written against a schema that does not exist.

``list_by_order`` SELECTs fourteen columns from ``lab_results``. **Nine of them
are not columns of that table** -- confirmed twice, against the live migrated
PostgreSQL schema and independently against the ORM metadata:

    queried      analyte, min_value, max_value, min_critical, max_critical,
                 is_critical, flagged, notes, performed_by
    real         clinical_engine_version, created_at, expires_at, flag, id,
                 normal_range_high, normal_range_low, order_id, test_name,
                 test_type_id, token, token_hash, unit, value, value_text,
                 version

The real table calls it ``test_name`` not ``analyte``, ``normal_range_low/high``
not ``min_value/max_value``, ``flag`` not ``flagged``, and has no critical
bounds, notes or performer columns at all. The same drift runs through the
sibling repositories: ``SQLPatientRepository`` queries ``name``,
``date_of_birth`` and ``address`` against a ``patients`` table whose columns are
``full_name``, ``birth_date`` and no address; ``SQLOrderRepository`` queries
``priority``, ``test_type``, ``notes`` and ``performed_by`` against
``lab_orders``, which has none of them.

SO THE MISSING METHOD WAS NOT IMPLEMENTED. Writing it would have meant a fourth
query against a fictional schema, and the two columns it needs --
``patient_id`` and ``analyte`` on ``lab_results`` -- do not exist, so there is
no faithful way to write it. Inventing them is what the standing brief forbids.

WHAT THIS COSTS. The caller is a clinical safety feature:
``app/reference/domain/safety.py`` performs a **delta check** -- "Compares
current result with previous results for the same patient/analyte. Returns True
if the change is suspicious" -- over the patient's last three results. Delta
checking is standard laboratory QC. It cannot run.

Reachability: latent. The reference package is not registered; its paths return
404 (recorded earlier in this audit). That is why none of this surfaced.

These tests pin the drift so it cannot be "fixed" by adding more queries
against the imagined shape, and so that the day someone registers the package
they find a failing test rather than a 500.
"""
from __future__ import annotations

import ast
import pathlib
import re

import pytest

REPOSITORIES = (
    pathlib.Path(__file__).resolve().parents[2]
    / "app" / "reference" / "infrastructure" / "repositories.py"
)

#: Columns the package's SQL asks for that the ORM does not define. Pinned as an
#: exact set: a new one fails, and removing one (by making the schema or the
#: query agree) also fails and forces this note to be updated with the repair.
KNOWN_PHANTOM_COLUMNS = {
    "lab_results": {
        "analyte", "min_value", "max_value", "min_critical", "max_critical",
        "is_critical", "flagged", "notes", "performed_by",
    },
    "patients": {"name", "date_of_birth", "address"},
    "lab_orders": {"priority", "test_type", "notes", "performed_by"},
}


def _orm_columns(table: str) -> set[str]:
    import app.models.lab_order
    import app.models.lab_result
    import app.models.patient
    from app.orm_topology import SHARED_METADATA

    assert table in SHARED_METADATA.tables, f"{table} is not in the ORM metadata"
    return {c.name for c in SHARED_METADATA.tables[table].columns}


@pytest.mark.parametrize("table", sorted(KNOWN_PHANTOM_COLUMNS))
def test_the_queried_columns_really_are_absent_from_the_orm(table):
    """The evidence, independent of any live database.

    Ratchets both ways. If a column appears -- because someone added it, or
    because the query was corrected -- this fails and the ledger above must be
    updated rather than the discrepancy quietly disappearing.
    """
    real = _orm_columns(table)
    phantom = KNOWN_PHANTOM_COLUMNS[table]

    now_present = sorted(phantom & real)
    assert not now_present, (
        f"{table}: {now_present} now exist(s). Either the schema gained them or "
        f"the query was fixed — update KNOWN_PHANTOM_COLUMNS and re-read IA-075."
    )


def test_the_real_column_names_are_what_the_queries_should_have_used():
    """Names the correct columns, so the repair is not guesswork later."""
    results = _orm_columns("lab_results")
    for expected in ("test_name", "normal_range_low", "normal_range_high", "flag", "unit"):
        assert expected in results, expected

    patients = _orm_columns("patients")
    assert "full_name" in patients
    assert "birth_date" in patients


def test_lab_results_cannot_support_a_patient_analyte_lookup():
    """Why list_by_patient_analyte was left unimplemented.

    The signature is ``(patient_id: str, analyte: str, limit: int = 5)``. Both
    of those columns are absent from ``lab_results``, so the query cannot be
    written faithfully — the patient is reachable only through
    ``lab_orders.patient_id``, and the analyte only as ``test_name``.
    """
    results = _orm_columns("lab_results")
    assert "patient_id" not in results
    assert "analyte" not in results
    # the indirection that a real implementation would have to go through
    assert "order_id" in results
    assert "patient_id" in _orm_columns("lab_orders")


def test_the_missing_abstract_method_was_not_implemented_against_a_phantom_schema():
    """The ratchet that matters: do not add a fourth broken query.

    If someone implements ``list_by_patient_analyte``, it must not reference the
    columns that do not exist. This fails if it does.
    """
    source = REPOSITORIES.read_text()
    tree = ast.parse(source)

    implementations = [
        n for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        and n.name == "list_by_patient_analyte"
    ]
    if not implementations:
        pytest.skip("still unimplemented, which is the documented IA-075 position")

    body = ast.get_source_segment(source, implementations[0]) or ""
    phantom_used = sorted(
        c for c in KNOWN_PHANTOM_COLUMNS["lab_results"]
        if re.search(rf"\b{c}\b", body)
    )
    assert not phantom_used, (
        f"list_by_patient_analyte references columns that do not exist: "
        f"{phantom_used}. lab_results has no patient_id and no analyte; the "
        f"patient is reachable only via lab_orders.patient_id and the analyte "
        f"as test_name."
    )


def test_the_delta_check_depends_on_the_unimplemented_method():
    """Records what the gap costs: a clinical QC feature cannot run."""
    safety = (
        pathlib.Path(__file__).resolve().parents[2]
        / "app" / "reference" / "domain" / "safety.py"
    )
    source = safety.read_text()
    assert "list_by_patient_analyte" in source
    assert "Delta check" in source or "delta check" in source.lower()
