"""GULA Kernel CLI — single entry point for all 19 phases.

Usage:
    python scripts/kernel.py audit       Phase 0  — write KERNEL_AUDIT_REPORT.md
    python scripts/kernel.py state       Phase 1  — print execution state snapshot
    python scripts/kernel.py autonomy    Phase 2  — autonomy level map
    python scripts/kernel.py contract    Phase 3  — engine contract validation
    python scripts/kernel.py schedule    Phase 4  — mission schedule report
    python scripts/kernel.py resources   Phase 5  — system resource snapshot
    python scripts/kernel.py locks       Phase 6  — lock manager snapshot
    python scripts/kernel.py context     Phase 7  — context engine stats
    python scripts/kernel.py decisions   Phase 8  — decision history
    python scripts/kernel.py knowledge   Phase 9  — knowledge health
    python scripts/kernel.py safety      Phase 10 — safety preflight
    python scripts/kernel.py simulate    Phase 11 — run a mission simulation
    python scripts/kernel.py quality     Phase 12 — quality gate results
    python scripts/kernel.py observe     Phase 13 — observability suite
    python scripts/kernel.py recover     Phase 14 — recovery plan
    python scripts/kernel.py debt        Phase 15 — technical debt scan
    python scripts/kernel.py registry    Phase 16 — engine registry matrices
    python scripts/kernel.py diagnose    Phase 17 — self diagnostics
    python scripts/kernel.py report      Phase 18 — write the three enterprise reports
    python scripts/kernel.py check       Run all Kernel self-checks (exit 1 on failure)
"""

from __future__ import annotations

import sys

from . import report
from .core import REPO_ROOT

_AUDIT_PATH = REPO_ROOT / "KERNEL_AUDIT_REPORT.md"


def run_audit() -> int:
    from . import audit

    findings = audit.audit_findings()
    subsystems = audit.scan_subsystems()
    _AUDIT_PATH.write_text(audit.render_audit_markdown(findings, subsystems), encoding="utf-8")
    print(f"[OK] KERNEL_AUDIT_REPORT.md written ({len(findings)} findings)")
    return 0


def run_state() -> int:
    from . import state

    summary = state.snapshot_summary(state.load_state())
    for key, value in summary.items():
        print(f"{key}: {value}")
    return 0


def run_autonomy() -> int:
    from . import autonomy

    print("AUTONOMY LEVELS")
    for level, name in autonomy.ACTION_REQUIREMENTS.items():
        print(f"  {level} -> {name}")
    return 0


def run_contract() -> int:
    from . import contract
    from .core import ENGINE_REGISTRY

    violations = contract.contract_violations(ENGINE_REGISTRY)
    print("ENGINE CONTRACT")
    if violations:
        for violation in violations:
            print(f"  [FAIL] {violation}")
        return 1
    print(f"  [PASS] all {len(ENGINE_REGISTRY)} engines conform to the Kernel contract")
    return 0


def run_schedule() -> int:
    from . import scheduler
    from .core import Task

    tasks = [
        Task("simulate", "demo", "simulation", dependencies=["build"]),
        Task("build", "demo", "builder", dependencies=[]),
        Task("review", "demo", "reviewer", dependencies=["build"]),
        Task("deploy", "demo", "deployer", dependencies=["review"]),
    ]
    plan = scheduler.mission_schedule("demo", tasks)
    print("MISSION SCHEDULE")
    print(f"  critical path: {' -> '.join(plan['critical_path'])}")
    print(f"  execution graph: {plan['execution_graph']}")
    print(f"  status: {plan['status']}")
    return 0


def run_resources() -> int:
    from . import resource

    load = resource.monitor_system()
    print("SYSTEM RESOURCE SNAPSHOT")
    for key, value in load.to_dict().items():
        print(f"  {key}: {value}")
    return 0


def run_locks() -> int:
    from . import locks

    manager = locks.LockManager()
    snapshot = manager.snapshot()
    print(f"LOCK MANAGER (currently {len(snapshot)} locks)")
    for resource, lock in snapshot.items():
        print(f"  {resource}: held by {lock['owner']} ({lock['lock_type']})")
    return 0


def run_context() -> int:
    from . import context

    engine = context.ContextEngine()
    stats = engine.cache_stats()
    print("CONTEXT ENGINE")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    return 0


def run_decisions() -> int:
    from . import decisions

    records = decisions.load_history()
    print(f"DECISION HISTORY ({len(records)} records)")
    for record in records[-5:]:
        print(f"  {record.decision.decision_id}: {record.decision.status} (risk={record.risk})")
    return 0


def run_knowledge() -> int:
    from scripts.governor.knowledge_governance import KnowledgeItem

    from . import knowledge

    artifacts = [
        knowledge.KnowledgeArtifact(KnowledgeItem("KNOW-1", "Deployment runbook", "runbook", "approved", 0.9, "content a")),
        knowledge.KnowledgeArtifact(KnowledgeItem("KNOW-2", "Deployment runbook", "runbook", "draft", 0.4, "content b")),
    ]
    health = knowledge.health_check(artifacts)
    print("KNOWLEDGE HEALTH")
    for key, value in health.items():
        print(f"  {key}: {value}")
    return 0


def run_safety() -> int:
    from . import safety

    print("SAFETY PREFLIGHT")
    assessment = safety.assess_action("breaking_api_change")
    print(f"  breaking_api_change: allowed={assessment.allowed} requires_approval={assessment.requires_approval}")
    command = safety.assess_command("git push --force")
    print(f"  git push --force: allowed={command.allowed}")
    return 0


def run_simulate() -> int:
    from . import simulation

    steps = [
        {"kind": "file", "name": "write config", "path": "config.yml", "content": "x"},
        {"kind": "db", "name": "insert patient", "table": "patients", "row": {"id": 1}},
        {"kind": "assert", "name": "verify", "pass": True},
    ]
    result = simulation.simulate_mission("demo-sim", steps)
    print(result.summary)
    return 0 if result.passed else 1


def run_quality() -> int:
    from . import quality

    results = quality.run_quality_gates()
    print("QUALITY GATES")
    for gate in results:
        print(f"  {gate.name}: {'PASS' if gate.passed else 'FAIL'}")
    failing = quality.failed(results)
    return 1 if failing else 0


def run_observe() -> int:
    from . import observability

    suite = observability.ObservabilitySuite()
    suite.metrics.record("missions", 1)
    suite.audit.record("kernel", "check", "observe")
    suite.timeline.event("kernel.check")
    export = suite.export()
    print("OBSERVABILITY")
    print(f"  metrics: {len(export['metrics'])}")
    print(f"  audit: {len(export['audit'])}")
    print(f"  timeline: {len(export['timeline'])}")
    return 0


def run_recover() -> int:
    from . import recovery

    counters = __import__("scripts.governor.loop_protection", fromlist=["LoopCounters"]).LoopCounters("demo")
    plan = recovery.plan_recovery("demo", "transient", counters)
    print("RECOVERY PLAN")
    for key, value in plan.items():
        print(f"  {key}: {value}")
    return 0


def run_debt() -> int:
    from . import debt

    findings = debt.large_modules([]) + debt.todo_density([])
    print(f"TECHNICAL DEBT (static scan: {len(findings)} findings)")
    return 0


def run_registry() -> int:
    from . import registry

    print(registry.render_matrices())
    return 0


def run_diagnose() -> int:
    from . import diagnostics

    audits = diagnostics.audit_components()
    print("SELF DIAGNOSTICS")
    for audit in audits:
        print(f"  {audit.component}: {audit.health}")
    return 0


def run_report() -> int:
    paths = report.write_enterprise_report()
    for path in paths:
        print(f"[OK] {path}")
    return 0


def run_check() -> int:
    """Run all Kernel self-checks; exit 1 on any failure."""
    from . import audit, contract, diagnostics, quality, safety
    from .core import ENGINE_REGISTRY, Severity

    failures: list[str] = []

    violations = contract.contract_violations(ENGINE_REGISTRY)
    if violations:
        failures.extend(violations)

    gates = quality.run_quality_gates()
    failing = quality.failed(gates)
    if failing:
        failures.append(f"failed quality gates: {', '.join(failing)}")

    assessment = safety.assess_action("unauthorized_deployment")
    if assessment.allowed:
        failures.append("safety engine allowed unauthorized deployment")

    diagnostics_findings = diagnostics.run_diagnostics(ENGINE_REGISTRY)
    high = [
        d for d in diagnostics_findings
        if d.severity in {Severity.CRITICAL, Severity.HIGH}
    ]
    if high:
        failures.append(f"diagnostics found {len(high)} high/critical findings")

    audit_findings = audit.audit_findings()
    audit_high = [f for f in audit_findings if f.severity == Severity.HIGH]
    if audit_high:
        failures.append(f"audit found {len(audit_high)} high findings")

    print("KERNEL SELF-CHECK")
    print("=" * 60)
    if failures:
        for failure in failures:
            print(f"  - {failure}")
        print("=" * 60)
        return 1
    print("  [PASS] engine contracts conform (16 fields)")
    print("  [PASS] all 9 quality gates pass")
    print("  [PASS] safety engine blocks unauthorized actions")
    print("  [PASS] diagnostics clean")
    print("  [PASS] audit clean")
    print("=" * 60)
    print("RESULT: ALL KERNEL CHECKS PASSED")
    return 0


def _ext_commands() -> dict[str, object]:
    """Lazily import the extension CLI (GULA-KERNEL-EXT-001)."""
    from .ext import cli as ext_cli

    return ext_cli.EXT_COMMANDS


def _builder_commands() -> dict[str, object]:
    """Lazily import the Builder CLI (GULA-BUILDER-001)."""
    from scripts.builder import cli as builder_cli

    return builder_cli.BUILDER_COMMANDS


def _reviewer_commands() -> dict[str, object]:
    """Lazily import the Reviewer CLI (GULA-REVIEWER-001)."""
    from scripts.reviewer import cli as reviewer_cli

    return reviewer_cli.REVIEWER_COMMANDS


def _orchestrator_commands() -> dict[str, object]:
    """Lazily import the Orchestrator CLI (GULA-ORCHESTRATOR-001)."""
    from scripts.orchestrator import cli as orchestrator_cli

    return orchestrator_cli.ORCHESTRATOR_COMMANDS


def _deployer_commands() -> dict[str, object]:
    """Lazily import the Deployer CLI (GULA-DEPLOYER-001)."""
    from scripts.deployer import cli as deployer_cli

    return deployer_cli.DEPLOYER_COMMANDS


def _learner_commands() -> dict[str, object]:
    """Lazily import the Learner CLI (GULA-LEARNER-001)."""
    from scripts.learner import cli as learner_cli

    return learner_cli.LEARNER_COMMANDS


def _optimizer_commands() -> dict[str, object]:
    """Lazily import the Optimizer CLI (GULA-OPTIMIZER-001)."""
    from scripts.optimizer import cli as optimizer_cli

    return optimizer_cli.OPTIMIZER_COMMANDS


COMMANDS = {
    "audit": run_audit,
    "state": run_state,
    "autonomy": run_autonomy,
    "contract": run_contract,
    "schedule": run_schedule,
    "resources": run_resources,
    "locks": run_locks,
    "context": run_context,
    "decisions": run_decisions,
    "knowledge": run_knowledge,
    "safety": run_safety,
    "simulate": run_simulate,
    "quality": run_quality,
    "observe": run_observe,
    "recover": run_recover,
    "debt": run_debt,
    "registry": run_registry,
    "diagnose": run_diagnose,
    "report": run_report,
    "check": run_check,
    "ext-plugin": _ext_commands()["ext-plugin"],
    "ext-plugin-certify": _ext_commands()["ext-plugin-certify"],
    "ext-policy": _ext_commands()["ext-policy"],
    "ext-policy-evaluate": _ext_commands()["ext-policy-evaluate"],
    "ext-compat": _ext_commands()["ext-compat"],
    "ext-compat-check": _ext_commands()["ext-compat-check"],
    "ext-migrate": _ext_commands()["ext-migrate"],
    "ext-migrate-run": _ext_commands()["ext-migrate-run"],
    "ext-event-bus": _ext_commands()["ext-event-bus"],
    "ext-workflow": _ext_commands()["ext-workflow"],
    "ext-marketplace": _ext_commands()["ext-marketplace"],
    "ext-evolution": _ext_commands()["ext-evolution"],
    "ext-memory": _ext_commands()["ext-memory"],
    "ext-health": _ext_commands()["ext-health"],
    "ext-check": _ext_commands()["ext-check"],
    "builder-audit": _builder_commands()["builder-audit"],
    "builder-analyze": _builder_commands()["builder-analyze"],
    "builder-plan": _builder_commands()["builder-plan"],
    "builder-impact": _builder_commands()["builder-impact"],
    "builder-execute": _builder_commands()["builder-execute"],
    "builder-recover": _builder_commands()["builder-recover"],
    "builder-knowledge": _builder_commands()["builder-knowledge"],
    "builder-review": _builder_commands()["builder-review"],
    "builder-report": _builder_commands()["builder-report"],
    "builder-check": _builder_commands()["builder-check"],
    "reviewer-audit": _reviewer_commands()["reviewer-audit"],
    "reviewer-review": _reviewer_commands()["reviewer-review"],
    "reviewer-area": _reviewer_commands()["reviewer-area"],
    "reviewer-gate": _reviewer_commands()["reviewer-gate"],
    "reviewer-report": _reviewer_commands()["reviewer-report"],
    "reviewer-check": _reviewer_commands()["reviewer-check"],
    "reviewer-verify": _reviewer_commands()["reviewer-verify"],
    "reviewer-architecture": _reviewer_commands()["reviewer-architecture"],
    "reviewer-code": _reviewer_commands()["reviewer-code"],
    "reviewer-security": _reviewer_commands()["reviewer-security"],
    "reviewer-tests": _reviewer_commands()["reviewer-tests"],
    "reviewer-deployment": _reviewer_commands()["reviewer-deployment"],
    "reviewer-documentation": _reviewer_commands()["reviewer-documentation"],
    "reviewer-performance": _reviewer_commands()["reviewer-performance"],
    "reviewer-knowledge": _reviewer_commands()["reviewer-knowledge"],
    "orchestrator-audit": _orchestrator_commands()["orchestrator-audit"],
    "orchestrator-mission": _orchestrator_commands()["orchestrator-mission"],
    "orchestrator-classify": _orchestrator_commands()["orchestrator-classify"],
    "orchestrator-plan": _orchestrator_commands()["orchestrator-plan"],
    "orchestrator-route": _orchestrator_commands()["orchestrator-route"],
    "orchestrator-checkpoint": _orchestrator_commands()["orchestrator-checkpoint"],
    "orchestrator-resume": _orchestrator_commands()["orchestrator-resume"],
    "orchestrator-status": _orchestrator_commands()["orchestrator-status"],
    "orchestrator-history": _orchestrator_commands()["orchestrator-history"],
    "orchestrator-report": _orchestrator_commands()["orchestrator-report"],
    "orchestrator-check": _orchestrator_commands()["orchestrator-check"],
    "deployer-audit": _deployer_commands()["deployer-audit"],
    "deployer-architecture": _deployer_commands()["deployer-architecture"],
    "deployer-pipeline": _deployer_commands()["deployer-pipeline"],
    "deployer-infrastructure": _deployer_commands()["deployer-infrastructure"],
    "deployer-health": _deployer_commands()["deployer-health"],
    "deployer-rollback": _deployer_commands()["deployer-rollback"],
    "deployer-scaling": _deployer_commands()["deployer-scaling"],
    "deployer-observability": _deployer_commands()["deployer-observability"],
    "deployer-security": _deployer_commands()["deployer-security"],
    "deployer-knowledge": _deployer_commands()["deployer-knowledge"],
    "deployer-report": _deployer_commands()["deployer-report"],
    "deployer-deploy": _deployer_commands()["deployer-deploy"],
    "deployer-check": _deployer_commands()["deployer-check"],
    "learner-audit": _learner_commands()["learner-audit"],
    "learner-extract": _learner_commands()["learner-extract"],
    "learner-skill": _learner_commands()["learner-skill"],
    "learner-playbook": _learner_commands()["learner-playbook"],
    "learner-runbook": _learner_commands()["learner-runbook"],
    "learner-memory": _learner_commands()["learner-memory"],
    "learner-patterns": _learner_commands()["learner-patterns"],
    "learner-improve": _learner_commands()["learner-improve"],
    "learner-quality": _learner_commands()["learner-quality"],
    "learner-search": _learner_commands()["learner-search"],
    "learner-report": _learner_commands()["learner-report"],
    "learner-learn": _learner_commands()["learner-learn"],
    "learner-check": _learner_commands()["learner-check"],
    "optimizer-audit": _optimizer_commands()["optimizer-audit"],
    "optimizer-analyze": _optimizer_commands()["optimizer-analyze"],
    "optimizer-bottlenecks": _optimizer_commands()["optimizer-bottlenecks"],
    "optimizer-architecture": _optimizer_commands()["optimizer-architecture"],
    "optimizer-resources": _optimizer_commands()["optimizer-resources"],
    "optimizer-dx": _optimizer_commands()["optimizer-dx"],
    "optimizer-debt": _optimizer_commands()["optimizer-debt"],
    "optimizer-optimize": _optimizer_commands()["optimizer-optimize"],
    "optimizer-evolve": _optimizer_commands()["optimizer-evolve"],
    "optimizer-validate": _optimizer_commands()["optimizer-validate"],
    "optimizer-report": _optimizer_commands()["optimizer-report"],
    "optimizer-run": _optimizer_commands()["optimizer-run"],
    "optimizer-check": _optimizer_commands()["optimizer-check"],
}


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] in {"-h", "--help", "help"}:
        print(__doc__)
        return 0
    command = argv[0]
    if command not in COMMANDS:
        print(f"Unknown command: {command}")
        print("Available: " + ", ".join(sorted(COMMANDS)))
        return 2
    return COMMANDS[command]()


if __name__ == "__main__":
    sys.exit(main())
