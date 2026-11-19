#!/usr/bin/env python3
"""GULA — log_action() positional-argument-order guard.

Deterministic, AST-based detector (no LLM calls, no network, no database
access) generalizing a verified defect class first found and fixed in
app/nhdw/services.py this session: the shared audit helper

    log_action(db, action, resource_type, resource_id=None, user_id=None,
               user_role=None, lab_id=None, details=None, ip_address=None)

(backend/app/services/audit_service.py) has an easy-to-misalign
signature -- resource_type MUST be a string literal (a type tag like
"admission"/"patient_assignment"), and every parameter after resource_id
is easy to shift by one position because user_role sits between user_id
and lab_id where callers rarely need it. Two independently confirmed real
shapes this session:

  NHDW shape (6 positional args): resource_type position received the
  resource's own id (a non-literal expression) instead of a string tag,
  e.g. log_action(db, "nhdw.x", admission.id, lab_id, user_id, data) --
  admission.id lands in resource_type, lab_id lands in resource_id, and
  the details dict lands in user_role (crashes: no DBAPI can bind a raw
  dict to any column).

  Nursing shape (7 positional args): resource_type is correct, but the
  call supplies exactly 7 positional args assuming the next two slots
  are (lab_id, details) -- they are actually (user_role, lab_id), so
  lab_id lands in user_role and the details dict lands in lab_id.

This script finds every log_action(...) call site under backend/app/ and
flags any call shaped like either of the two confirmed defect classes:

  RULE_A: more than 2 positional args, and the 3rd positional arg
          (resource_type) is not a string literal.
  RULE_B: exactly 7 positional args with no keyword arguments (the
          Nursing shape -- lab_id/details are supplied positionally
          past resource_id/user_id with nothing marking where
          user_role should have gone).

A call using keyword arguments for user_id=/lab_id=/details= (the
convention this script's own fixes use) triggers neither rule, by
design -- keywords make the misalignment structurally impossible.

This is a DETECTOR, not an autofixer: every hit must still be read and
classified (SAFE_TO_FIX / NEEDS_REVIEW / FALSE_POSITIVE) before any
call site is changed, per this repo's own dead-code/repair discipline
(a hit's dict literal shape and surrounding code differ enough across
185 call sites that a blind, mechanical rewrite is not safe everywhere;
the NHDW/Nursing fixes were each still applied and verified by hand).

Usage:
    python3 scripts/log_action_arg_order_guard.py                # human report
    python3 scripts/log_action_arg_order_guard.py --json          # machine-readable
    python3 scripts/log_action_arg_order_guard.py --self-test      # positive+negative proof

Exit codes:
    0 -- no RULE_A/RULE_B hits (or --self-test passed)
    1 -- at least one hit found (or --self-test failed)
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
import textwrap
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_APP = REPO_ROOT / "backend" / "app"


@dataclass
class Hit:
    file: str
    line: int
    rule: str
    positional_arg_count: int
    snippet: str


def _is_log_action_call(node: ast.Call) -> bool:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id == "log_action"
    if isinstance(func, ast.Attribute):
        return func.attr == "log_action"
    return False


def _third_positional_is_string_literal(node: ast.Call) -> bool:
    if len(node.args) < 3:
        return True  # too few args for this rule to apply meaningfully
    third = node.args[2]
    return isinstance(third, ast.Constant) and isinstance(third.value, str)


def scan_source(source: str, filename: str = "<string>") -> list[Hit]:
    hits: list[Hit] = []
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError:
        return hits
    lines = source.splitlines()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not _is_log_action_call(node):
            continue
        n_pos = len(node.args)
        snippet = lines[node.lineno - 1].strip() if 0 < node.lineno <= len(lines) else ""

        if n_pos > 2 and not _third_positional_is_string_literal(node):
            hits.append(Hit(filename, node.lineno, "RULE_A_resource_type_not_literal", n_pos, snippet))
            continue  # one rule per call site is enough signal

        if n_pos == 7 and not node.keywords:
            hits.append(Hit(filename, node.lineno, "RULE_B_seven_positional_args", n_pos, snippet))

    return hits


def scan_repo() -> list[Hit]:
    hits: list[Hit] = []
    for path in sorted(BACKEND_APP.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if "log_action(" not in source:
            continue  # cheap pre-filter before the AST parse
        rel = str(path.relative_to(REPO_ROOT))
        hits.extend(scan_source(source, rel))
    return hits


# ─── Self-test: positive + negative proof (Section 11 of this session's ───
# ─── engineering directive: a detector is not trusted until it is shown  ───
# ─── to both catch the bad shape and leave the good shape alone).        ───

_BROKEN_NHDW_SHAPE = """
from app.services.audit_service import log_action
def f(db, lab_id, user_id, admission, data):
    log_action(db, "nhdw.admission.create", admission.id, lab_id, user_id, data)
"""

_BROKEN_NURSING_SHAPE = """
from app.services.audit_service import log_action
def f(db, lab_id, user_id, assignment):
    log_action(db, "ns.assign_patient", "patient_assignment", assignment.id, user_id, lab_id, {
        "nurse_id": 1,
    })
"""

_FIXED_SHAPE = """
from app.services.audit_service import log_action
def f(db, lab_id, user_id, admission, data):
    log_action(db, "nhdw.admission.create", "admission", None, user_id=user_id, lab_id=lab_id, details=data)
"""

_UNRELATED_CALL_SHAPE = """
def log_action(db, action, resource_type, resource_id=None, user_id=None,
                user_role=None, lab_id=None, details=None, ip_address=None):
    pass

def some_other_function_with_seven_args(a, b, c, d, e, f, g):
    pass
"""


def run_self_test() -> bool:
    cases = [
        ("broken NHDW shape", _BROKEN_NHDW_SHAPE, 1, "RULE_A_resource_type_not_literal"),
        ("broken Nursing shape", _BROKEN_NURSING_SHAPE, 1, "RULE_B_seven_positional_args"),
        ("fixed/keyword shape", _FIXED_SHAPE, 0, None),
        ("unrelated 7-arg call to a different function", _UNRELATED_CALL_SHAPE, 0, None),
    ]
    all_ok = True
    for name, source, expected_count, expected_rule in cases:
        hits = scan_source(source, filename=f"<selftest:{name}>")
        ok = len(hits) == expected_count and (
            expected_rule is None or (hits and hits[0].rule == expected_rule)
        )
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name}: expected {expected_count} hit(s)"
              f"{f' ({expected_rule})' if expected_rule else ''}, got {len(hits)} {[h.rule for h in hits]}")
        all_ok = all_ok and ok
    return all_ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", action="store_true", help="machine-readable JSON output")
    parser.add_argument("--self-test", action="store_true", help="run positive+negative proof only, no repo scan")
    args = parser.parse_args()

    if args.self_test:
        ok = run_self_test()
        return 0 if ok else 1

    hits = scan_repo()

    if args.json:
        print(json.dumps([asdict(h) for h in hits], indent=2))
    else:
        if not hits:
            print("log_action_arg_order_guard: no RULE_A/RULE_B hits found.")
        else:
            print(f"log_action_arg_order_guard: {len(hits)} candidate(s) found "
                  f"(each requires manual classification before any fix):\n")
            for h in hits:
                print(f"  [{h.rule}] {h.file}:{h.line} ({h.positional_arg_count} positional args)")
                print(textwrap.indent(h.snippet, "      "))
                print()

    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
