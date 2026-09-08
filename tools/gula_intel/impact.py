"""Deterministic change impact and focused test selection.

The mapping is derived from repository structure, not guessed.  Every selected
test carries the reason it was selected, and paths with no known impact are
reported as NO_KNOWN_IMPACT rather than as safe.
"""
from __future__ import annotations

import dataclasses
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

DIRECT = "DIRECT_IMPACT"
INDIRECT = "INDIRECT_IMPACT"
POSSIBLE = "POSSIBLE_IMPACT"
NONE = "NO_KNOWN_IMPACT"

# Domain -> focused test paths that prove that domain.
DOMAIN_TESTS: dict[str, list[str]] = {
    "blood_bank": ["backend/tests/blood_bank/"],
    "clinical": ["backend/tests/blood_bank/"],  # the guard is proven through Blood Bank
    "migrations": ["backend/tests/migrations/"],
}


@dataclasses.dataclass
class Impact:
    path: str
    level: str
    domain: str
    reason: str
    tests: list[str]


def _domain_for(path: str) -> tuple[str, str, str]:
    p = path.replace("\\", "/")
    if p.startswith("backend/migrations/"):
        return "migrations", DIRECT, "changes the migration graph or its DDL"
    if p.startswith("backend/app/blood_bank/"):
        return "blood_bank", DIRECT, "changes Blood Bank domain code"
    if p.startswith("backend/app/clinical/"):
        return "clinical", DIRECT, "changes the shared clinical command guard used by many domains"
    if p.startswith("backend/tests/"):
        return "tests", DIRECT, "changes a test module"
    if p.startswith("backend/app/"):
        return "backend", POSSIBLE, "changes backend application code outside a mapped domain"
    if p.startswith("frontend-v3/") or p.startswith("frontend/"):
        return "frontend", POSSIBLE, "changes frontend code"
    if p.startswith("docs/"):
        return "docs", NONE, "documentation only"
    if p.startswith("tools/"):
        return "tooling", NONE, "engineering tooling only"
    return "unknown", POSSIBLE, "path not covered by a known mapping"


def analyse(paths: list[str]) -> list[Impact]:
    results: list[Impact] = []
    for path in sorted(set(paths)):
        domain, level, reason = _domain_for(path)
        tests = DOMAIN_TESTS.get(domain, [])
        if domain == "tests":
            tests = [str(pathlib.PurePath(path).parent) + "/"]
        results.append(Impact(path, level, domain, reason, tests))
    return results


def select_tests(paths: list[str]) -> dict[str, list[str]]:
    """Return {test path: [reasons]} — the minimum focused set, with justification."""
    selected: dict[str, list[str]] = {}
    for impact in analyse(paths):
        for test in impact.tests:
            selected.setdefault(test, []).append(f"{impact.path}: {impact.reason}")
    return selected


def unaffected_note(paths: list[str]) -> str:
    """State plainly which previously proven work remains valid and why."""
    domains = {analyse([p])[0].domain for p in paths}
    if domains <= {"docs", "tooling"}:
        return (
            "No application or migration path changed, so previously recorded "
            "verification remains valid; no suite needs re-running."
        )
    return "Application paths changed; the selected focused tests must be re-run."
