"""Deterministic development planner.

Given a set of changed paths, produce the plan a reviewer needs: what is
affected, what must be tested, what evidence is required, and how risky the
change is.  Every risk factor is explicit and reported, so the classification
can be argued with rather than trusted blindly.

The planner never emits "safe to deploy".  Deployment readiness is decided by
the production gate, not here.
"""
from __future__ import annotations

import dataclasses
from typing import Any

from . import detectors, impact, inventory

LOW, MODERATE, HIGH, CRITICAL = "LOW", "MODERATE", "HIGH", "CRITICAL"
_ORDER = {LOW: 0, MODERATE: 1, HIGH: 2, CRITICAL: 3}

# Each factor states its own weight and why it matters.
_FACTORS: list[tuple[str, str, str]] = [
    ("migration", "backend/migrations/", CRITICAL),
    ("shared_clinical_guard", "backend/app/clinical/", HIGH),
    ("clinical_domain", "backend/app/blood_bank/", HIGH),
    ("backend_app", "backend/app/", MODERATE),
    ("frontend", "frontend-v3/", MODERATE),
]


@dataclasses.dataclass
class Plan:
    changed: list[str]
    risk: str
    factors: list[dict[str, str]]
    affected_components: list[str]
    direct_dependencies: list[str]
    indirect_dependencies: list[str]
    required_tests: dict[str, list[str]]
    optional_tests: list[str]
    evidence_required: list[str]
    migration_implications: list[str]
    security_implications: list[str]
    clinical_safety_implications: list[str]
    known_blockers: list[dict[str, str]]
    architecture_decisions_required: list[dict[str, str]]
    minimum_safe_change_boundary: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def _risk(paths: list[str]) -> tuple[str, list[dict[str, str]]]:
    risk, factors = LOW, []
    for name, prefix, weight in _FACTORS:
        hits = [p for p in paths if p.replace("\\", "/").startswith(prefix)]
        if not hits:
            continue
        factors.append({"factor": name, "weight": weight, "matched": ", ".join(sorted(hits)[:4])})
        if _ORDER[weight] > _ORDER[risk]:
            risk = weight
    if not factors:
        factors.append({"factor": "no_mapped_risk_surface", "weight": LOW,
                        "matched": "no application, migration or frontend path changed"})
    return risk, factors


def plan(paths: list[str], *, include_open_blockers: bool = True) -> Plan:
    impacts = impact.analyse(paths)
    risk, factors = _risk(paths)
    touches_migration = any(f["factor"] == "migration" for f in factors)
    touches_clinical = any(
        f["factor"] in {"shared_clinical_guard", "clinical_domain"} for f in factors
    )

    blockers: list[dict[str, str]] = []
    decisions: list[dict[str, str]] = []
    if include_open_blockers:
        inv = inventory.collect()
        for result in detectors.run_all(inv):
            for finding in result.findings:
                entry = {"rule_id": finding.rule_id, "title": finding.title,
                         "severity": finding.severity.value, "evidence": finding.evidence}
                if finding.blocker:
                    blockers.append(entry)
                if finding.architecture_decision_required:
                    decisions.append(entry)

    evidence = ["focused test results", "py_compile of changed modules", "git diff --check"]
    migration_notes: list[str] = []
    if touches_migration:
        migration_notes = [
            "revision ids must remain unique and the graph must keep exactly one head",
            "a clean-database 'alembic upgrade head' proof is required before integration",
            "existing-database upgrade path must be proven separately or labelled NOT VERIFIED",
        ]
        evidence.append("clean-database migration proof on a disposable PostgreSQL")

    clinical: list[str] = []
    if touches_clinical:
        clinical = [
            "state transitions must stay reachable for every entity type that uses them",
            "idempotency, transaction boundary and audit behaviour must be re-proven",
        ]
        evidence.append("Blood Bank focused suite (the shared guard is proven through it)")

    security: list[str] = []
    if touches_clinical or touches_migration:
        security.append("authorization and tenant/facility scoping must not be weakened")

    return Plan(
        changed=sorted(set(paths)),
        risk=risk,
        factors=factors,
        affected_components=sorted({i.domain for i in impacts}),
        direct_dependencies=sorted({i.path for i in impacts if i.level == impact.DIRECT}),
        indirect_dependencies=sorted({i.path for i in impacts if i.level == impact.POSSIBLE}),
        required_tests=impact.select_tests(paths),
        optional_tests=(["backend/tests/"] if risk in {HIGH, CRITICAL} else []),
        evidence_required=evidence,
        migration_implications=migration_notes,
        security_implications=security,
        clinical_safety_implications=clinical,
        known_blockers=blockers,
        architecture_decisions_required=decisions,
        minimum_safe_change_boundary=(
            "restrict the change to the listed direct dependencies; widening it "
            "requires a stated justification"
        ),
        note=(
            "Risk is classified from the explicit factors above. This planner never "
            "reports deployment safety; the production gate decides that."
        ),
    )
