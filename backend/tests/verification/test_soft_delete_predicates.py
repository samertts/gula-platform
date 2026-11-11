"""A double invert is not a stronger negation — it is no negation at all.

``~~Model.flag`` compiles to the bare column. SQLAlchemy eliminates the double
negation, so the predicate becomes ``WHERE flag`` — *exactly the rows the filter
was written to exclude*. On a soft-delete flag that means the query returns only
deleted records, and hands them to the caller as if they were current. That is
worse than the ``WHERE false`` class, which at least returned nothing.

47 such predicates existed across 15 files: pharmacy stock, dispense queue,
prescriptions and catalogues; national observations, encounters, documents,
schedules, partners, rules, observability and vital-sign references. Every one sat
on an ``is_deleted`` / ``is_revoked`` / ``is_quarantined`` / ``is_active`` flag, so
the intent was never ambiguous.

The first test proves the mechanism by compiling all three forms — it is the
claim, executed, not reasoned about. The second proves the construct is gone.

Scope of the evidence, stated plainly: these predicates live in modules that
cannot execute against the canonical schema (their tables are absent, or their
ORM cannot write to it), so this is compile-level and static evidence, not
REAL_HTTP. The defect lived at query construction, which is where it is proven.
"""

from __future__ import annotations

import pathlib

import pytest

from . import harness

APP = pathlib.Path(__file__).resolve().parents[2] / "app"


@pytest.mark.skipif(not harness.postgres_url(), reason="needs a database to bind a query")
def test_a_double_invert_is_no_negation() -> None:
    """``~~flag`` must compile identically to ``flag``, and differently from ``~flag``."""
    import app.main  # configures the mapped surface
    from app.lims import models as lims_models

    Session = harness.session_factory(pool_size=2)
    try:
        with Session() as session:
            def where(predicate: object) -> str:
                # The compiled statement puts WHERE on its own line.
                sql = " ".join(str(session.query(lims_models.Specimen.id).filter(predicate)).split())
                marker = sql.upper().rfind("WHERE ")
                assert marker != -1, f"no WHERE clause in compiled SQL: {sql}"
                return sql[marker:].strip()

            single = where(~lims_models.Specimen.is_deleted)
            double = where(~~lims_models.Specimen.is_deleted)
            bare = where(lims_models.Specimen.is_deleted)

        assert "NOT" in single, f"~flag should negate: {single}"
        assert double == bare, (
            "~~flag must be shown to be identical to no negation at all; "
            f"~~ gave {double!r}, bare gave {bare!r}"
        )
        assert double != single, (
            f"the double invert is not a negation: ~~ gave {double!r}, ~ gave {single!r}"
        )
    finally:
        harness.dispose(Session)


def test_no_double_invert_survives_in_a_predicate() -> None:
    offences: list[str] = []
    for path in sorted(APP.rglob("*.py")):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:  # pragma: no cover
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            if "~~" in line:
                offences.append(f"app/{path.relative_to(APP)}:{number} {line.strip()[:110]}")
    assert not offences, (
        "a double invert returns ONLY the rows the filter excludes; use a single ~:\n  "
        + "\n  ".join(offences)
    )
