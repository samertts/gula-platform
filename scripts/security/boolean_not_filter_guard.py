#!/usr/bin/env python3
"""GULA — Python `not` applied to a SQLAlchemy column, inside a query
filter, detector.

Deterministic, AST-based (no LLM, no network, no DB access; whole-repo
scan in well under a second). Generalizes the verified defect first
found and fixed in app/services/hospital_service.py::_get_entity this
session, then confirmed to recur in app/radiology/pacs.py (3 sites),
app/pharmacy/routes.py, and app/routes/admin.py.

THE BUG
-------
    db.query(Model).filter(Model.id == x, not Model.is_deleted)

Python evaluates `not Model.is_deleted` immediately, at query-*build*
time, not at SQL-*execution* time. A bare column attribute
(`Model.is_deleted`) has no `__bool__` override, so `bool(Model.column)`
is always `True` (default object truthiness) and `not Model.column` is
always the literal Python `False`. Confirmed directly:

    >>> bool(Foo.is_deleted)
    True
    >>> not Foo.is_deleted
    False

`.filter(False)` compiles to `WHERE 0 = 1` -- the query unconditionally
matches ZERO ROWS, regardless of what data actually exists. The correct
SQLAlchemy idiom is `~Model.is_deleted` (the library's boolean-NOT
operator on a column expression), which already appears correctly
dozens of times elsewhere in this same codebase.

WHAT THIS DETECTS
------------------
A `not <attribute access>` expression that appears as a direct argument
to a call to a method literally named `.filter(` or `.filter_by(`
(the two SQLAlchemy Query methods this shape has been found inside).
This is deliberately narrow: it does NOT flag `not obj.field` in an
ordinary `if` statement or boolean expression outside a `.filter(...)`
call, because that is completely different and correct Python (e.g.
`app/routes/demo.py`'s `elif not user.is_active or ...` negates an
already-fetched instance's real runtime boolean value -- checked and
confirmed NOT a bug during this detector's construction).

Every hit is a near-certain defect, not merely a candidate requiring
manual classification (unlike scripts/setattr_mass_assignment_guard.py's
"CANDIDATE" model) -- there is no legitimate reason to apply Python's
`not` to a bare SQLAlchemy column/attribute expression inside a filter
call. Still printed with file:line and the exact snippet so a reviewer
can confirm before fixing.

Usage:
    python3 scripts/security/boolean_not_filter_guard.py
    python3 scripts/security/boolean_not_filter_guard.py --json
    python3 scripts/security/boolean_not_filter_guard.py --self-test

Exit codes:
    0 -- no hits found (or --self-test passed)
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

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_APP = REPO_ROOT / "backend" / "app"

_FILTER_METHODS = {"filter", "filter_by"}


@dataclass
class Hit:
    file: str
    line: int
    expr: str
    snippet: str


def _is_not_of_attribute(node: ast.expr) -> bool:
    """True for `not <attribute access>`, e.g. `not Model.is_deleted` or
    `not model.is_deleted` -- a UnaryOp(Not) whose operand is an
    ast.Attribute (never a plain ast.Name, which would be a normal
    Python boolean variable, not a column expression)."""
    return (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, ast.Not)
        and isinstance(node.operand, ast.Attribute)
    )


def _find_bad_filter_args(tree: ast.AST) -> list[tuple[ast.expr, int]]:
    """Returns (bad_arg_node, containing_call_lineno) for every
    `.filter(...)`/`.filter_by(...)` call with a `not <attribute>` among
    its positional arguments."""
    results = []
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in _FILTER_METHODS
        ):
            continue
        for arg in node.args:
            if _is_not_of_attribute(arg):
                results.append((arg, node.lineno))
    return results


def scan_source(source: str, filename: str = "<string>") -> list[Hit]:
    hits: list[Hit] = []
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError:
        return hits
    lines = source.splitlines()
    for arg, lineno in _find_bad_filter_args(tree):
        arg_line = arg.lineno if hasattr(arg, "lineno") else lineno
        snippet = lines[arg_line - 1].strip() if 0 < arg_line <= len(lines) else ""
        hits.append(Hit(
            file=filename,
            line=arg_line,
            expr=ast.unparse(arg) if hasattr(ast, "unparse") else "?",
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
        if ".filter(" not in source and ".filter_by(" not in source:
            continue  # cheap pre-filter before the AST parse
        rel = str(path.relative_to(REPO_ROOT))
        hits.extend(scan_source(source, rel))
    return hits


# ─── Self-test: positive + negative proof ──────────────────────────────────

_VULNERABLE_SHAPE = """
def get_entity(db, entity_id):
    return db.query(Model).filter(Model.id == entity_id, not Model.is_deleted).first()
"""

_VULNERABLE_MULTILINE_SHAPE = """
def get_share(db, share_id):
    return db.query(ImageShare).filter(
        ImageShare.id == share_id,
        not ImageShare.is_revoked,
    ).first()
"""

_VULNERABLE_SOLE_ARG_SHAPE = """
def list_active(db):
    return db.query(Lab).filter(not Lab.is_active).all()
"""

_CORRECT_TILDE_SHAPE = """
def get_entity(db, entity_id):
    return db.query(Model).filter(Model.id == entity_id, ~Model.is_deleted).first()
"""

_CORRECT_IF_STATEMENT_SHAPE = """
def check(user, lab):
    if not user.is_active or user.lab_id != lab.id:
        raise ValueError("inactive")
"""

_CORRECT_BOOLEAN_VARIABLE_SHAPE = """
def maybe_skip(should_include):
    if not should_include:
        return None
"""


def run_self_test() -> bool:
    cases = [
        ("not-attribute as one of several filter() args (vulnerable)", _VULNERABLE_SHAPE, 1),
        ("not-attribute in a multi-line filter() call (vulnerable)", _VULNERABLE_MULTILINE_SHAPE, 1),
        ("not-attribute as the sole filter() arg (vulnerable)", _VULNERABLE_SOLE_ARG_SHAPE, 1),
        ("correct ~Model.column usage", _CORRECT_TILDE_SHAPE, 0),
        ("not on an instance attribute inside a plain if-statement", _CORRECT_IF_STATEMENT_SHAPE, 0),
        ("not on a plain boolean variable", _CORRECT_BOOLEAN_VARIABLE_SHAPE, 0),
    ]
    all_ok = True
    for name, source, expected_count in cases:
        hits = scan_source(source, filename=f"<selftest:{name}>")
        ok = len(hits) == expected_count
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
            print("boolean_not_filter_guard: no candidates found.")
        else:
            print(f"boolean_not_filter_guard: {len(hits)} hit(s) -- each is a near-certain "
                  f"defect (a `not <attribute>` inside .filter()/.filter_by() always "
                  f"evaluates to the literal False, matching zero rows unconditionally). "
                  f"Fix: replace `not X.field` with `~X.field`.\n")
            for h in hits:
                print(f"  {h.file}:{h.line} -- {h.expr}")
                print(textwrap.indent(h.snippet, "      "))
                print()

    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
