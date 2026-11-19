"""Every guarded operation's audit action must fit ``audit_logs.action``.

``ClinicalCommandGuard.complete`` and ``reject`` write ``f"clinical.{operation}"``
as the audit action, and ``audit_logs.action`` is ``varchar(50)``.  An operation
longer than 41 characters therefore makes the audit INSERT raise
``StringDataRightTruncation``, and because the guard re-raises after recording
the metric, the whole command fails with a 500.

That is how ``hospital.surgical_safety_checklist.complete`` (52 characters with
the prefix) made the WHO surgical safety checklist impossible to complete.  The
next longest operation in the platform, ``hospital.operation_theater.status_change``,
sits at 49 — one character of headroom — so this is a live edge, not a historical
one, and it is cheaper to fail here than in production.

This test is static on purpose: it needs no database, so it runs in the
syntax/lint tier rather than only where PostgreSQL is available.
"""

from __future__ import annotations

import ast
import pathlib

# ``audit_logs.action`` — see the base schema and every migration that has
# touched it; the guard prefix is applied in ``ClinicalCommandGuard.complete``.
ACTION_COLUMN_WIDTH = 50
GUARD_PREFIX = "clinical."
BUDGET = ACTION_COLUMN_WIDTH - len(GUARD_PREFIX)

APP = pathlib.Path(__file__).resolve().parents[2] / "app"


def _guarded_operations() -> dict[str, list[str]]:
    """Every ``operation="..."`` keyword literal, mapped to where it is written.

    Read with ``ast`` rather than a regex so a keyword spelled across lines, or a
    name that merely contains the word "operation", cannot skew the census.
    """
    found: dict[str, list[str]] = {}
    for path in sorted(APP.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):  # pragma: no cover - syntax gate covers this
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            for kw in node.keywords:
                if kw.arg != "operation":
                    continue
                if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    found.setdefault(kw.value.value, []).append(str(path.relative_to(APP.parent)))
    return found


def test_the_census_actually_found_the_guarded_surface() -> None:
    """A census that silently found nothing would make the width test vacuous."""
    operations = _guarded_operations()
    assert len(operations) >= 40, (
        f"expected the guarded operation surface, found only {sorted(operations)}"
    )
    assert "hospital.safety_checklist.complete" in operations, (
        "the repaired WHO checklist operation is missing; the census is not reading routes"
    )


def test_no_guarded_operation_overflows_the_audit_action_column() -> None:
    overflowing = {
        operation: sites
        for operation, sites in _guarded_operations().items()
        if len(operation) > BUDGET
    }
    assert not overflowing, (
        "these operations produce an audit action longer than "
        f"audit_logs.action({ACTION_COLUMN_WIDTH}), so the guard's audit write raises "
        "StringDataRightTruncation and the command fails with a 500: "
        + "; ".join(
            f"{op} ({len(GUARD_PREFIX) + len(op)} chars) in {', '.join(sorted(set(sites)))}"
            for op, sites in sorted(overflowing.items())
        )
    )
