"""IA-026 — a partial PATCH must not blank the fields it does not mention.

`PATCH /results/{result_id}` declares every body field optional
(`UpdateResultRequest`: value, value_text, unit, normal_range_low,
normal_range_high — all `X | None = None`) and `update_result` passed all five
into a single `.update({...})`. So a caller correcting only the unit blanked the
value, the free-text value and both reference bounds, while the stored flag was
computed from `proposed_value = value if value is not None else result.value` —
the *old* value. Measured in PostgreSQL:

    BEFORE  Potassium | 7.5 | mmol/L | 3.5 | 5.1 | critical | v1
    PATCH   unit only
    AFTER   Potassium |     | mmol/L |     |     | critical | v2

A critically-flagged result with no value and no range, and an audit row reading
"Updated laboratory result with CAS version 1".

There is no way today to distinguish "field omitted" from "field explicitly
null" — both arrive as None — so nothing that works deliberately is lost by
treating absent as unchanged. Under the PERMANENT DATA RULE ("GULA does not
operationally delete data"), blanking a stored clinical value by omission is not
an operation the platform should offer at all.

The concurrency control in the same function is correct and is asserted here too,
so a future change cannot quietly trade optimistic locking for patch semantics.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

_BACKEND = pathlib.Path(__file__).resolve().parents[2]
_SERVICE = _BACKEND / "app/services/order_service.py"

_MUTABLE_FIELDS = (
    "value",
    "value_text",
    "unit",
    "normal_range_low",
    "normal_range_high",
)


def _update_result_fn() -> ast.FunctionDef:
    tree = ast.parse(_SERVICE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "update_result":
            return node
    raise AssertionError("update_result no longer exists in order_service.py")


def _update_call_payload() -> ast.AST:
    """The single argument handed to the `.update(...)` that writes the row."""
    fn = _update_result_fn()
    for node in ast.walk(fn):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "update"
            and node.args
        ):
            return node.args[0]
    raise AssertionError("update_result no longer calls .update(...)")


def test_the_update_payload_is_not_a_literal_of_every_field():
    """The defect shape: a dict literal naming all five mutable columns.

    A literal payload cannot express "leave this one alone", so every PATCH
    writes every field. The repair builds the payload conditionally, which makes
    it something other than a plain `ast.Dict` of all five keys.
    """
    payload = _update_call_payload()
    if not isinstance(payload, ast.Dict):
        return  # built conditionally — that is the fixed shape
    literal_keys = {
        k.value for k in payload.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)
    }
    blanked = sorted(set(_MUTABLE_FIELDS) & literal_keys)
    assert not blanked, (
        "update_result writes these columns unconditionally, so a PATCH that "
        f"omits them stores NULL over stored clinical data: {blanked}. See IA-026."
    )


@pytest.mark.parametrize("field", _MUTABLE_FIELDS)
def test_each_mutable_field_is_written_only_inside_its_own_guard(field):
    """Each column must be added to the payload only when the caller sent it.

    Asserted structurally: an ``if <field> is not None:`` whose body assigns
    ``updates[<field>]``. A bare ``is not None`` comparison elsewhere in the
    function (there are some, for the flag computation) does not satisfy this.
    """
    fn = _update_result_fn()
    guarded = False
    for node in ast.walk(fn):
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if not (
            isinstance(test, ast.Compare)
            and len(test.ops) == 1
            and isinstance(test.ops[0], ast.IsNot)
            and isinstance(test.left, ast.Name)
            and test.left.id == field
            and len(test.comparators) == 1
            and isinstance(test.comparators[0], ast.Constant)
            and test.comparators[0].value is None
        ):
            continue
        for stmt in node.body:
            if not isinstance(stmt, ast.Assign):
                continue
            for target in stmt.targets:
                if (
                    isinstance(target, ast.Subscript)
                    and isinstance(target.slice, ast.Constant)
                    and target.slice.value == field
                ):
                    guarded = True
    assert guarded, (
        f"`{field}` is not added to the update payload inside an "
        f"`if {field} is not None:` guard, so omitting it in a PATCH blanks the "
        "stored value. See IA-026."
    )


def test_optimistic_locking_and_lock_state_are_still_enforced():
    """NO DEFECT FOUND here — pinned so the patch fix cannot cost it.

    The write must stay a single atomic statement filtered on the caller's
    observed version AND on the order being unlocked, with a rollback and a
    409-shaped response when no row matches.
    """
    source = _SERVICE.read_text(encoding="utf-8")
    fn_src = ast.get_source_segment(source, _update_result_fn()) or ""
    assert "LabResult.version == expected_version" in fn_src
    assert "locked_at.is_(None)" in fn_src
    assert "LabResult.version + 1" in fn_src
    assert "db.rollback()" in fn_src
    assert '"status_code": 409' in fn_src


def test_the_flag_is_derived_from_the_value_that_will_be_stored():
    """The flag must not describe a value the update is about to discard."""
    source = _SERVICE.read_text(encoding="utf-8")
    fn_src = ast.get_source_segment(source, _update_result_fn()) or ""
    assert "proposed_value" in fn_src
    assert "apply_critical_override" in fn_src, (
        "the update path must consult the critical-threshold table (IA-024)"
    )
