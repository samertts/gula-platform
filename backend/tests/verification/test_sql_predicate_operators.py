"""Python's boolean operators must never appear inside a SQL predicate.

``Model.attr`` is an ``InstrumentedAttribute``. It does not override ``__bool__``,
so Python's own operators do not build SQL — they evaluate the attribute for
truthiness and throw the expression away:

* ``not Model.attr``  -> the literal ``False``. SQLAlchemy folds the conjunction
  (``a AND b AND false`` is ``false``), so the statement compiles to
  ``WHERE false`` and **every other predicate in the call is eliminated**,
  including ``lab_id``. The query silently returns nothing.
* ``a and b``         -> ``b``. The left predicate is silently discarded.
* ``a or b``          -> ``a``. The right predicate is silently discarded.

The correct operators are ``~``, ``&`` and ``|`` (or ``sqlalchemy.not_``,
``and_``, ``or_``).

This construct had reached 28 call sites, 20 of them across the LIMS read
surface, one of which emptied the lab-approval queue so that no registered lab
could be activated. None of it raised: the queries ran and returned nothing.
A reviewer cannot see it, and a test that only asserts "no forbidden rows came
back" passes while the endpoint is dead — which is why this guard is static and
counts to zero rather than to a baseline.
"""

from __future__ import annotations

import ast
import pathlib

APP = pathlib.Path(__file__).resolve().parents[2] / "app"

# The methods that take SQL predicates. ``filter_by`` takes keywords, but a
# boolean operator in one of its values is wrong for exactly the same reason.
SQL_PREDICATE_CALLS = {"filter", "where", "filter_by", "having"}


def _offences() -> list[str]:
    found: list[str] = []
    for path in sorted(APP.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):  # pragma: no cover - the syntax gate owns this
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            name = fn.attr if isinstance(fn, ast.Attribute) else (
                fn.id if isinstance(fn, ast.Name) else "")
            if name not in SQL_PREDICATE_CALLS:
                continue
            for arg in list(node.args) + [kw.value for kw in node.keywords]:
                for sub in ast.walk(arg):
                    if isinstance(sub, ast.BoolOp):
                        which = "and (drops the left predicate)" if isinstance(sub.op, ast.And) \
                            else "or (drops the right predicate)"
                        found.append(
                            f"{path.relative_to(APP.parent)}:{sub.lineno} Python {which}"
                            f" -> use & / | : {ast.unparse(sub)[:100]}")
                    elif isinstance(sub, ast.UnaryOp) and isinstance(sub.op, ast.Not):
                        found.append(
                            f"{path.relative_to(APP.parent)}:{sub.lineno} Python not"
                            f" (compiles to WHERE false, eliminating every other predicate)"
                            f" -> use ~ : {ast.unparse(sub)[:100]}")
    return found


def test_the_sweep_actually_reaches_the_query_surface() -> None:
    """Guard against a guard that passes because it inspects nothing."""
    call_sites = 0
    for path in APP.rglob("*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                    and node.func.attr in SQL_PREDICATE_CALLS:
                call_sites += 1
    assert call_sites >= 500, (
        f"only {call_sites} SQL predicate calls found; the sweep is not reading the codebase"
    )


def test_no_python_boolean_operator_inside_a_sql_predicate() -> None:
    offences = _offences()
    assert not offences, (
        f"{len(offences)} SQL predicate(s) use a Python boolean operator, so the database "
        "never sees them:\n  " + "\n  ".join(offences)
    )
