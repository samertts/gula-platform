#!/usr/bin/env python3
"""Static detector: mutating routes that take a resource id but show no
textual evidence of a tenant/ownership scope check.

This is Detector Category B from the F5 authorization sweep: "target-resource
mutation without scope check" (see F5 — can_manage_user() in
backend/app/security/rbac.py used to let a lab-scoped admin manage a user in
any other lab, because the hierarchy check alone was mistaken for
authorization). This detector looks for the same *shape* of bug elsewhere:
a role/permission gate that says nothing about which lab/tenant/resource the
caller may act on.

Method: for every POST/PUT/PATCH/DELETE route handler in
backend/app/routes/*.py whose path contains a resource-id path parameter
(``{foo_id}`` where foo != lab), search the function's own source text for
any of a small set of known scope-check idioms. A handler with a resource id
and none of these idioms is reported as a CANDIDATE — not a confirmed
finding. This is a heuristic textual scan, not a data-flow or type analysis;
it proves absence of a *pattern*, not absence of a *check* (see Known false
negatives below), so every hit needs a human to read the function before it
is treated as a real defect.

Known false positives (a hit here is very likely NOT a bug):
  - Endpoints intentionally scoped to platform-wide roles only (master_admin/
    ministry_admin), where "any tenant" is correct by design.
  - Endpoints scoped by something other than lab_id (e.g. current_user.id
    for "my own resource", or a different tenant column this detector
    doesn't know the name of).
  - Endpoints whose scope check lives in a shared dependency (e.g. a
    Depends(...) helper) rather than inline in the function body — this
    detector only reads the decorated function's own source.

Known false negatives (a real bug here could still show 0 hits):
  - A scope check using a variable name this detector doesn't recognize
    (e.g. ``org_id``, ``facility_id``) is invisible to the LAB_ID_INDICATORS
    pattern list below; run with --extra-indicator to widen it ad hoc.
  - A function that merely *mentions* lab_id in a comment or an unrelated
    query (e.g. reading it for an audit log) is enough to suppress a hit,
    even if the actual mutation itself is unscoped. This detector proves
    "some lab_id-shaped text exists in this function," not that it is used
    correctly as a comparison feeding an authorization decision.

Regression fixtures: see
backend/tests/test_detect_missing_tenant_scope.py for one deliberately
vulnerable (positive) and one deliberately safe (negative) fixture, run
through this module's own scan function directly.
"""
from __future__ import annotations

import argparse
import ast
import pathlib
import re
import sys

MUTATING_METHODS = {"post", "put", "patch", "delete"}

# Path params that look like a specific resource, not the tenant/lab itself.
_RESOURCE_ID_PARAM = re.compile(r"\{(?!lab_id\})(\w+_id)\}")

# Textual idioms that indicate SOME tenant/ownership scoping is present.
# Deliberately broad (substring-level) — this is a recall-favoring heuristic,
# not a precise one; see the module docstring's false-positive/negative notes.
SCOPE_INDICATORS = (
    "require_own_lab",
    "can_manage_user",
    "can_manage_role",
    ".lab_id ==",
    "== current_user.lab_id",
    "current_user.lab_id ==",
    "lab_id=current_user.lab_id",
    "platform_roles",
    "require_permission",  # possession-based, but common enough to not re-litigate here
)


class RouteHit:
    __slots__ = ("file", "line", "func", "method", "path")

    def __init__(self, file: str, line: int, func: str, method: str, path: str) -> None:
        self.file = file
        self.line = line
        self.func = func
        self.method = method
        self.path = path

    def __repr__(self) -> str:  # pragma: no cover - debug convenience only
        return f"{self.file}:{self.line} {self.method.upper()} {self.path} ({self.func})"


def _decorator_route_info(dec: ast.expr) -> tuple[str, str] | None:
    """Return (method, path) for a @router.<method>("path", ...) decorator, else None."""
    if not isinstance(dec, ast.Call):
        return None
    func = dec.func
    if not isinstance(func, ast.Attribute):
        return None
    method = func.attr.lower()
    if method not in MUTATING_METHODS:
        return None
    if not dec.args:
        return None
    first = dec.args[0]
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        return method, first.value
    return None


def scan_source(source: str, filename: str = "<string>") -> list[RouteHit]:
    """Scan one Python module's source for candidate unscoped mutations.

    Exposed as a function (not just a CLI) so tests can feed it a fixture
    string directly without touching the filesystem.
    """
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError:
        return []

    hits: list[RouteHit] = []
    lines = source.splitlines()

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        route_info = None
        for dec in node.decorator_list:
            route_info = _decorator_route_info(dec)
            if route_info:
                break
        if route_info is None:
            continue
        method, path = route_info

        if not _RESOURCE_ID_PARAM.search(path):
            continue  # no specific-resource id in the path at all

        start = node.lineno - 1
        end = getattr(node, "end_lineno", None) or (start + 1)
        body_source = "\n".join(lines[start:end])

        if any(indicator in body_source for indicator in SCOPE_INDICATORS):
            continue  # some scope-check idiom present — not a hit

        hits.append(RouteHit(filename, node.lineno, node.name, method, path))

    return hits


def scan_directory(root: pathlib.Path) -> list[RouteHit]:
    hits: list[RouteHit] = []
    for path in sorted(root.glob("*.py")):
        if path.name == "__init__.py":
            continue
        hits.extend(scan_source(path.read_text(), filename=str(path)))
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--routes-dir",
        default="backend/app/routes",
        help="directory of route modules to scan (default: backend/app/routes)",
    )
    args = parser.parse_args()

    root = pathlib.Path(args.routes_dir)
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2

    hits = scan_directory(root)
    if not hits:
        print("No candidates found.")
        return 0

    print(f"{len(hits)} candidate(s) — mutating route, resource id in path, "
          f"no recognized scope-check idiom in the function body:\n")
    for hit in hits:
        print(f"  {hit}")
    print(
        "\nEach of these is a CANDIDATE, not a confirmed finding — read the "
        "function (and any Depends(...) it uses) before treating it as a "
        "bug. See this script's module docstring for known false "
        "positives/negatives."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
