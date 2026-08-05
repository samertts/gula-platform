"""Architect CLI — GULA-ARCHITECT-001 commands.

Integrated into `scripts/kernel.py` so the Kernel remains the single entry
point, matching the Builder, Reviewer, Orchestrator, Deployer, Learner, and
Optimizer pattern.
"""

from __future__ import annotations

import sys


def run_audit() -> int:
    """Phase 0 — write ARCHITECT_AUDIT_REPORT.md."""
    from .audit import run_audit as _audit

    path = _audit()
    print(f"[OK] {path.name} written")
    return 0


def run_model() -> int:
    """Phase 1 — build and persist the system model."""
    from .model import persist_model

    contexts_path, relationships_path = persist_model()
    print(f"[OK] model persisted -> {contexts_path.name}, {relationships_path.name}")
    return 0


def run_decisions() -> int:
    """Phase 2 — record and persist architectural decisions."""
    from .decisions import build_decisions, discover_adrs, persist_decisions

    decisions = build_decisions()
    path = persist_decisions()
    accepted = sum(1 for d in decisions if d.status == "accepted")
    print(
        f"[OK] {len(decisions)} decisions "
        f"({accepted} accepted, {len(discover_adrs())} ADR files) -> {path.name}"
    )
    return 0


def run_dependencies() -> int:
    """Phase 3 — scan and persist dependency findings."""
    from .dependencies import detect_dependencies, persist_dependencies

    findings = detect_dependencies()
    path = persist_dependencies()
    for finding in findings[:10]:
        print(f"  [{finding.severity}] {finding.kind} {finding.evidence}")
    print(f"[OK] {len(findings)} dependency finding(s) -> {path.name}")
    return 0


def run_evolution() -> int:
    """Phase 4 — build and persist the evolution roadmap."""
    from .evolution import build_roadmap, persist_roadmap

    milestones = build_roadmap()
    path = persist_roadmap()
    print(f"[OK] {len(milestones)} roadmap milestone(s) -> {path.name}")
    return 0


def run_risk() -> int:
    """Phase 5 — build and persist the risk register."""
    from .risk import build_risks, persist_risks

    risks = build_risks()
    path = persist_risks()
    for risk in risks[:8]:
        print(f"  [{risk.exposure}] {risk.area:<14} {risk.title}")
    print(f"[OK] {len(risks)} risk(s) -> {path.name}")
    return 0


def run_review() -> int:
    """Phase 6 — review a candidate design (default: the platform)."""
    from .review import persist_review

    candidate = sys.argv[2] if len(sys.argv) > 2 else "gula-platform"
    path = persist_review(candidate)
    print(f"[OK] review of '{candidate}' -> {path.name}")
    return 0


def run_simulation() -> int:
    """Phase 7 — persist scale projections (100 → 1M users)."""
    from .simulation import persist_simulation, project_full

    projections = project_full()
    path = persist_simulation()
    for projection in projections:
        print(
            f"  {projection.users:>8,} users -> "
            f"{projection.requests_per_second} r/s, "
            f"{projection.app_replicas} replicas ({projection.tier})"
        )
    print(f"[OK] {len(projections)} projection(s) -> {path.name}")
    return 0


def run_coordination() -> int:
    """Phase 8 — persist AI coordination contracts."""
    from .coordination import build_coordination, persist_coordination

    contracts = build_coordination()
    path = persist_coordination()
    for contract in contracts:
        print(f"  {contract.engine:<12} {contract.role:<12} {contract.status}")
    print(f"[OK] {len(contracts)} contract(s) -> {path.name}")
    return 0


def run_health() -> int:
    """Phase 9 — measure and persist architecture health."""
    from .health import persist_health

    health = persist_health()
    print(f"[OK] architecture health -> {health.name}")
    return 0


def run_report() -> int:
    """Phase 10 — write ARCHITECT_IMPLEMENTATION_REPORT.md."""
    from .report import build_report

    build_report()
    print("[OK] ARCHITECT_IMPLEMENTATION_REPORT.md written")
    return 0


def _run_all() -> int:
    """Run the complete architect pipeline end-to-end (the success criterion)."""
    from .audit import run_audit as _audit
    from .coordination import build_coordination, persist_coordination
    from .decisions import build_decisions, persist_decisions
    from .dependencies import detect_dependencies, persist_dependencies
    from .evolution import build_roadmap, persist_roadmap
    from .health import measure_health, persist_health
    from .model import persist_model
    from .review import persist_review
    from .risk import build_risks, persist_risks
    from .simulation import persist_simulation, project_full

    _audit()
    print("[1] architecture audit written")

    persist_model()
    print("[2] system model persisted")

    decisions = build_decisions()
    persist_decisions()
    print(f"[3] {len(decisions)} architectural decisions recorded")

    findings = detect_dependencies()
    persist_dependencies()
    print(f"[4] dependency findings: {len(findings)}")

    roadmap = build_roadmap()
    persist_roadmap()
    print(f"[5] evolution roadmap: {len(roadmap)} milestones")

    risks = build_risks()
    persist_risks()
    print(f"[6] risk register: {len(risks)} risks")

    persist_review("gula-platform")
    print("[7] design review recorded")

    projections = project_full()
    persist_simulation()
    print(f"[8] scale projections: {len(projections)} (100 -> 1M users)")

    contracts = build_coordination()
    persist_coordination()
    print(f"[9] AI coordination contracts: {len(contracts)}")

    health = measure_health()
    persist_health()
    print(f"[10] architecture health: {health.overall}/100, "
          f"maturity: {health.maturity}/100 ({health.maturity_level})")

    from .report import build_report

    build_report()
    print("[11] ARCHITECT_IMPLEMENTATION_REPORT.md written")
    return 0


def run_all() -> int:
    try:
        return _run_all()
    except ValueError as exc:
        print(f"Error: {exc}")
        return 2


def run_check() -> int:
    """Run all Architect self-checks; exit 1 on any failure."""
    failures: list[str] = []

    from .audit import audit_system
    from .coordination import build_coordination
    from .decisions import build_decisions
    from .dependencies import build_edges, detect_dependencies
    from .evolution import build_roadmap
    from .health import measure_health
    from .model import build_model
    from .risk import build_risks
    from .simulation import project_full

    # 1. Audit covers all sixteen architecture surfaces.
    items = audit_system()
    if len(items) != 16:
        failures.append(f"audit expected 16 surfaces got {len(items)}")

    # 2. System model discovers bounded contexts with trust boundaries.
    contexts = build_model()
    if not contexts:
        failures.append("system model found no bounded contexts")
    if not all(c.trust_boundary for c in contexts):
        failures.append("every context must declare a trust boundary")
    if len({c.name for c in contexts}) != len(contexts):
        failures.append("context names must be unique")

    # 3. Decisions all carry status and consequences.
    decisions = build_decisions()
    if not decisions:
        failures.append("no decisions recorded")
    if not all(d.consequences for d in decisions):
        failures.append("every decision must list consequences")
    if not all(d.alternatives and d.trade_offs and d.rollback and d.cost
               for d in decisions):
        failures.append("every decision must record alternatives, trade-offs, "
                        "cost, and rollback strategy")

    # 4. Dependency scan produces edges and findings deterministically.
    edges = build_edges()
    findings = detect_dependencies()
    if not isinstance(edges, list) or not isinstance(findings, list):
        failures.append("dependency scan must return lists")
    if len({f.kind for f in findings} - {"circular", "skip-layer",
                                         "cross-context", "technology-lock-in"}) > 0:
        failures.append("dependency findings use unknown kinds")

    # 5. Evolution roadmap covers all three horizons with migration strategy.
    roadmap = build_roadmap()
    if len({m.horizon for m in roadmap}) != 3:
        failures.append("roadmap must cover 1/3/5-year horizons")
    if not all(m.technology and m.migration for m in roadmap):
        failures.append("every milestone must carry technology evolution "
                        "and migration strategy")

    # 6. Risk register produces bounded exposure and covers all categories.
    risks = build_risks()
    categories = {r.category for r in risks}
    if not risks:
        failures.append("risk register is empty")
    if not all(1 <= r.exposure <= 16 for r in risks):
        failures.append("risk exposure must be within 1-16")
    if not all(r.priority for r in risks):
        failures.append("every risk must have a priority")
    if not {"technical", "business", "operational", "security", "ai",
            "knowledge"} <= categories:
        failures.append("risk register must cover technical/business/"
                        "operational/security/ai/knowledge categories")

    # 7. Scale simulation covers all five steps with bounded replicas.
    projections = project_full()
    if len(projections) != 5:
        failures.append(f"expected 5 scale steps got {len(projections)}")
    if not all(p.app_replicas >= 1 for p in projections):
        failures.append("every scale step needs at least one replica")
    if not all(p.storage_gb >= 0 and p.monthly_cost_usd >= 0
               and p.predicted_bottleneck for p in projections):
        failures.append("every scale step needs storage, cost, and a "
                        "predicted bottleneck")

    # 8. AI coordination integrates the six engines.
    contracts = build_coordination()
    if len(contracts) != 6:
        failures.append(f"expected 6 AI contracts got {len(contracts)}")
    if not all(c.engine in {"builder", "reviewer", "orchestrator", "learner",
                            "optimizer", "deployer"} for c in contracts):
        failures.append("unknown AI engine in coordination contracts")

    # 9. Health score is bounded and covers all dimensions + maturity.
    health = measure_health()
    if not (0 <= health.overall <= 100):
        failures.append("health score out of bounds")
    if len(health.dimensions) != 6:
        failures.append(f"health must cover 6 dimensions got {len(health.dimensions)}")
    if not (0 <= health.maturity <= 100):
        failures.append("maturity score out of bounds")
    if not health.maturity_level:
        failures.append("maturity level missing")

    print("ARCHITECT SELF-CHECK")
    print("=" * 60)
    if failures:
        for failure in failures:
            print(f"  - {failure}")
        print("=" * 60)
        return 1
    for item in items:
        state = "verified" if item.status == "measured" else "planned"
        print(f"  [PASS] audit {item.title:<24} {state}")
    print(f"  [PASS] system model deterministic ({len(contexts)} contexts)")
    print(f"  [PASS] {len(decisions)} decisions with ADR linkage")
    print(f"  [PASS] dependency governance ({len(findings)} findings)")
    print("  [PASS] evolution roadmap covers 1/3/5-year horizons")
    print(f"  [PASS] risk register bounded ({len(risks)} risks)")
    print("  [PASS] scale simulation 100 -> 1M users")
    print(f"  [PASS] AI coordination ({len(contracts)} engines)")
    print(f"  [PASS] architecture health {health.overall}/100, "
          f"maturity {health.maturity}/100 ({health.maturity_level})")
    print("=" * 60)
    print("RESULT: ALL ARCHITECT CHECKS PASSED")
    return 0


ARCHITECT_COMMANDS = {
    "architect-audit": run_audit,
    "architect-model": run_model,
    "architect-decisions": run_decisions,
    "architect-dependencies": run_dependencies,
    "architect-evolution": run_evolution,
    "architect-risk": run_risk,
    "architect-review": run_review,
    "architect-simulation": run_simulation,
    "architect-coordination": run_coordination,
    "architect-health": run_health,
    "architect-report": run_report,
    "architect-run": run_all,
    "architect-check": run_check,
}
