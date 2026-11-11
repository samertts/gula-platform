#!/usr/bin/env python3
"""GULA — unguarded setattr-loop mass-assignment detector.

Deterministic, AST-based (no LLM, no network, no DB access; whole-repo
scan in well under a second). Generalizes the verified defect first
found and fixed in app/nursing/services.py::update_task and closed again
this session in app/services/hospital_service.py::update_hospital: a
loop of the shape

    for k, v in data.items():
        setattr(target, k, v)

(or the "key, value" / "field, value" spelling) applies EVERY key in
`data` to the ORM instance with no field boundary. Whether this is
actually exploitable depends entirely on where `data` comes from and
whether an explicit allow-list already narrows the loop body -- this
detector cannot determine that from syntax alone, so it flags the
syntactic shape as a CANDIDATE and leaves classification (as Hospital's
own investigation did) to whoever reviews each hit:

    SAFE_BY_DESIGN       -- data is already a narrow, hand-built dict of
                            named server-derived values, not a raw
                            request payload
    SERVER_DERIVED       -- the loop body already checks each key against
                            an explicit allow-list/protected-fields set
                            before calling setattr
    INTERNAL_ONLY        -- data never originates from an HTTP request
                            (e.g. a fixed internal config dict)
    DEAD_OR_UNREACHABLE  -- the enclosing function has no live caller
    VULNERABLE           -- data flows from a request body/schema with no
                            independent field boundary at the ORM layer
    NEEDS_REVIEW         -- insufficient evidence to classify from this
                            scan alone

Do not treat a hit as VULNERABLE without reading the actual call site --
this is exactly what "avoid false-positive explosion" (this session's own
detector-quality bar) requires. This detector's job is to make the
repo-wide candidate list cheap to produce, not to replace that reading.

Usage:
    python3 scripts/setattr_mass_assignment_guard.py
    python3 scripts/setattr_mass_assignment_guard.py --json
    python3 scripts/setattr_mass_assignment_guard.py --self-test

Exit codes:
    0 -- no candidates found (or --self-test passed)
    1 -- at least one candidate found (or --self-test failed)
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
    loop_var: str
    target_expr: str
    guarded: bool  # loop body contains an `if` before setattr (weak signal, not proof of safety)
    snippet: str


def _find_setattr_loops(tree: ast.AST) -> list[tuple[ast.For, str]]:
    """Returns (for_node, target_expr) for every `for k, v in X.items(): ...
    setattr(target, k, v)` shaped loop, at any nesting depth inside the
    loop body (so an `if`-guarded setattr is still found)."""
    results = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.For):
            continue
        # for <k>, <v> in <dict>.items():
        if not (isinstance(node.target, ast.Tuple) and len(node.target.elts) == 2):
            continue
        key_name = node.target.elts[0]
        val_name = node.target.elts[1]
        if not (isinstance(key_name, ast.Name) and isinstance(val_name, ast.Name)):
            continue
        call = node.iter
        if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and call.func.attr == "items"):
            continue

        for inner in ast.walk(node):
            if (
                isinstance(inner, ast.Call)
                and isinstance(inner.func, ast.Name)
                and inner.func.id == "setattr"
                and len(inner.args) >= 3
            ):
                target_arg, key_arg, val_arg = inner.args[0], inner.args[1], inner.args[2]
                if (
                    isinstance(key_arg, ast.Name) and key_arg.id == key_name.id
                    and isinstance(val_arg, ast.Name) and val_arg.id == val_name.id
                ):
                    target_expr = ast.unparse(target_arg) if hasattr(ast, "unparse") else "?"
                    results.append((node, target_expr))
                    break
    return results


def _loop_is_conditionally_guarded(for_node: ast.For) -> bool:
    """Weak signal only: does the loop body contain an `if` anywhere
    before reaching setattr? A real allow-list check (`if k in
    ALLOWED_FIELDS`) looks like this; so does an unrelated, unrelated-key
    `if` that guards nothing. Reported for the reviewer, not treated as
    proof of safety."""
    return any(isinstance(n, ast.If) for n in ast.walk(for_node))


def scan_source(source: str, filename: str = "<string>") -> list[Hit]:
    hits: list[Hit] = []
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError:
        return hits
    lines = source.splitlines()
    for for_node, target_expr in _find_setattr_loops(tree):
        snippet = lines[for_node.lineno - 1].strip() if 0 < for_node.lineno <= len(lines) else ""
        hits.append(Hit(
            file=filename,
            line=for_node.lineno,
            loop_var=ast.unparse(for_node.target) if hasattr(ast, "unparse") else "?",
            target_expr=target_expr,
            guarded=_loop_is_conditionally_guarded(for_node),
            snippet=snippet,
        ))
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
        if "setattr(" not in source:
            continue  # cheap pre-filter before the AST parse
        rel = str(path.relative_to(REPO_ROOT))
        hits.extend(scan_source(source, rel))
    return hits


# ─── Self-test: positive + negative proof ──────────────────────────────────

_VULNERABLE_SHAPE = """
def update_thing(db, thing_id, data):
    thing = db.query(Thing).filter(Thing.id == thing_id).first()
    for k, v in data.items():
        setattr(thing, k, v)
    db.flush()
"""

_ALLOW_LISTED_SHAPE = """
_ALLOWED = {"name", "phone"}
def update_thing(db, thing_id, data):
    thing = db.query(Thing).filter(Thing.id == thing_id).first()
    for k, v in data.items():
        if k in _ALLOWED:
            setattr(thing, k, v)
    db.flush()
"""

_UNRELATED_LOOP_SHAPE = """
def summarize(data):
    total = 0
    for k, v in data.items():
        total += v
    return total
"""

_DIFFERENT_VAR_NAMES_SHAPE = """
def update_thing(db, thing_id, payload):
    thing = db.query(Thing).filter(Thing.id == thing_id).first()
    for field, value in payload.items():
        setattr(thing, field, value)
    db.flush()
"""


def run_self_test() -> bool:
    cases = [
        ("unguarded setattr loop (vulnerable shape)", _VULNERABLE_SHAPE, 1, False),
        ("allow-listed setattr loop (guarded, still flagged for review)", _ALLOW_LISTED_SHAPE, 1, True),
        ("unrelated .items() loop with no setattr", _UNRELATED_LOOP_SHAPE, 0, None),
        ("different variable names (field/value/payload)", _DIFFERENT_VAR_NAMES_SHAPE, 1, False),
    ]
    all_ok = True
    for name, source, expected_count, expected_guarded in cases:
        hits = scan_source(source, filename=f"<selftest:{name}>")
        ok = len(hits) == expected_count and (
            expected_guarded is None or (hits and hits[0].guarded == expected_guarded)
        )
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name}: expected {expected_count} hit(s), got {len(hits)}")
        all_ok = all_ok and ok
    return all_ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return 0 if run_self_test() else 1

    hits = scan_repo()

    if args.json:
        print(json.dumps([asdict(h) for h in hits], indent=2))
    else:
        if not hits:
            print("setattr_mass_assignment_guard: no candidates found.")
        else:
            print(f"setattr_mass_assignment_guard: {len(hits)} candidate(s) "
                  f"(each requires manual classification: SAFE_BY_DESIGN / "
                  f"SERVER_DERIVED / INTERNAL_ONLY / DEAD_OR_UNREACHABLE / "
                  f"VULNERABLE / NEEDS_REVIEW):\n")
            for h in hits:
                guard_note = "has an inner `if` (may be an allow-list, verify)" if h.guarded else "NO inner `if` at all"
                print(f"  {h.file}:{h.line} -- setattr({h.target_expr}, ...) -- {guard_note}")
                print(textwrap.indent(h.snippet, "      "))
                print()

    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
