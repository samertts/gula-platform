"""Builder CLI — GULA-BUILDER-001 commands.

Integrated into `scripts/kernel.py` so the Kernel remains the single entry
point. No ad-hoc scripts; every Builder command is reached through the Kernel.
"""

from __future__ import annotations


def run_audit() -> int:
    """Phase 0 — write BUILDER_AUDIT_REPORT.md."""
    from .audit import run_audit

    path = run_audit()
    print(f"[OK] {path.name} written")
    return 0


def run_analyze(objective: str = "Build Patient Management") -> int:
    """Phase 1 — classify and analyze an objective."""
    from .analyzer import analyze, describe

    analysis = analyze(objective)
    print("MISSION ANALYZER (GULA-BUILDER-001)")
    print(f"  objective:  {analysis.objective}")
    print(f"  mission_id: {analysis.mission_id}")
    print(f"  type:       {analysis.mission_type} — {describe(analysis.mission_type)}")
    print(f"  complexity: {analysis.complexity}")
    print(f"  risk:       {analysis.risk}")
    print(f"  cost:       {analysis.execution_cost}")
    print(f"  time:       ~{analysis.execution_time_minutes} minutes")
    print(f"  outputs:    {', '.join(analysis.outputs)}")
    print(f"  verify:     {analysis.verification_strategy}")
    print(f"  rollback:   {analysis.rollback_strategy}")
    return 0


def run_plan(objective: str = "Build Patient Management") -> int:
    """Phase 2 — decompose an objective into a budgeted plan."""
    from .planner import budget_violations, describe_plan, plan_mission

    _, plan = plan_mission(objective)
    print("MISSION PLANNER (GULA-BUILDER-001)")
    print(describe_plan(plan))
    violations = budget_violations(plan)
    if violations:
        print("  budget FAIL")
        for violation in violations:
            print(f"    - {violation}")
        return 1
    print("  [PASS] every task within 5 min / 50 files")
    return 0


def run_impact(objective: str = "Build Patient Management") -> int:
    """Phase 3 — determine the engineering surface impacted."""
    from .analyzer import analyze
    from .impact import analyze_impact, impact_summary

    analysis = analyze(objective)
    impact = analyze_impact(analysis)
    print("ENGINEERING ANALYZER (GULA-BUILDER-001)")
    print(f"  {impact_summary(impact)}")
    for area, values in {
        "modules": impact.affected_modules,
        "apis": impact.affected_apis,
        "database": impact.affected_database,
        "frontend": impact.affected_frontend,
        "tests": impact.affected_tests,
        "documentation": impact.affected_documentation,
        "deployment": impact.affected_deployment,
        "security": impact.affected_security,
        "knowledge": impact.affected_knowledge,
        "registry": impact.affected_registry,
    }.items():
        if values:
            print(f"  {area}: {', '.join(values)}")
    return 0


def run_execute() -> int:
    """Phase 4 — run a demo mission through the execution order."""
    from .executor import execute_mission, make_mission_id
    from .planner import EXECUTION_ORDER

    mid = make_mission_id()
    handlers = {
        step: lambda step=step, ctx=None: {
            "ok": True,
            "step": step,
            "tests_pass": step == "test",
            "ruff_clean": step in {"verify", "execute"},
        }
        for step in EXECUTION_ORDER
    }
    result = execute_mission(mid, handlers=handlers)
    print("EXECUTION ENGINE (GULA-BUILDER-001)")
    print(f"  mission: {mid}")
    print(f"  status:  {result.status}")
    print(f"  steps:   {len(result.completed_steps)}/{len(EXECUTION_ORDER)} completed")
    for trace in result.trace:
        print(f"    {trace}")
    return 0 if result.status == "completed" else 1


def run_recover() -> int:
    """Phase 5 — demonstrate checkpoint + retry + resume."""
    from .executor import execute_mission, make_mission_id

    mid = make_mission_id()
    checkpoints: list[str] = []

    def checkpoint_cb(step: str, context: dict) -> None:
        checkpoints.append(step)

    def failing(step: str, context: dict) -> dict:
        if step == "test":
            raise TimeoutError("transient timeout")
        return {"ok": True}

    result = execute_mission(mid, handlers={"test": failing}, checkpoint_callback=checkpoint_cb)
    print("FAILURE RECOVERY (GULA-BUILDER-001)")
    print(f"  mission:     {mid}")
    print(f"  status:      {result.status}")
    print(f"  failed step: {result.failed_step}")
    print(f"  error:       {result.error}")
    print(f"  checkpoints: {', '.join(checkpoints)}")
    return 0


def run_knowledge(query: str = "pytest import failure") -> int:
    """Phase 6 — search knowledge for reusable solutions."""
    from .knowledge import collect, reuse_summary

    references = collect(query)
    print("KNOWLEDGE INTEGRATION (GULA-BUILDER-001)")
    print(f"  query: {query}")
    print(f"  candidates ({len(references)}): {reuse_summary(references)}")
    for ref in references[:6]:
        print(f"    [{ref.source}] {ref.path} rel={ref.relevance:.2f}")
    return 0


def run_review() -> int:
    """Phase 7 — run the self-review against sample evidence."""
    from .review import can_continue, review, summary

    context = {
        "tests_run": True, "tests_pass": True,
        "ruff_clean": True, "typecheck_clean": True,
        "security_verified": True, "registry_updated": True,
        "docs_updated": True, "deploy_verified": True,
    }
    report = review("MSN-REVIEW", context)
    print("SELF REVIEW (GULA-BUILDER-001)")
    print(f"  verdict: {summary(report)}")
    for finding in report.findings:
        state = "PASS" if finding.passed else "FAIL"
        print(f"    [{finding.severity.value}] {finding.area:14s} {state}")
    return 0 if can_continue(report) else 1


def run_report() -> int:
    """Phase 8 — write a sample BUILDER_IMPLEMENTATION_REPORT.md."""
    from .report import ImplementationRecord, readiness, write_report

    record = ImplementationRecord(
        mission_id="MSN-BUILDER-001",
        objective="Build the GULA Builder Engine",
        mission_type="architecture",
        complexity="high",
        risk="moderate",
        completed_work=[
            "Audited the repository (Phase 0)",
            "Implemented Mission Analyzer (Phase 1)",
            "Implemented Mission Planner (Phase 2)",
            "Implemented Engineering Analyzer (Phase 3)",
            "Implemented Execution Engine (Phase 4)",
            "Implemented Failure Recovery (Phase 5)",
            "Implemented Knowledge Integration (Phase 6)",
            "Implemented Self Review (Phase 7)",
        ],
        created_files=[
            "scripts/builder/core.py",
            "scripts/builder/audit.py",
            "scripts/builder/analyzer.py",
            "scripts/builder/planner.py",
            "scripts/builder/impact.py",
            "scripts/builder/executor.py",
            "scripts/builder/recovery.py",
            "scripts/builder/knowledge.py",
            "scripts/builder/review.py",
            "scripts/builder/report.py",
        ],
        updated_files=["scripts/kernel/cli.py"],
        architecture=[
            "Builder Engine composes Kernel primitives (state, checkpoint, severity)",
            "Every phase is a deterministic, testable module",
        ],
        future_improvements=[
            "Teach the Builder to self-route work to the right engine",
            "Add per-mission telemetry to the Kernel observability suite",
        ],
        remaining_risks=["Builder missions still require a human-supplied objective"],
    )
    record.readiness_score = readiness(record)
    path = write_report(record)
    print(f"[OK] {path.name} written (readiness {record.readiness_score}/100)")
    return 0


def run_check() -> int:
    """Run all Builder self-checks; exit 1 on any failure."""
    failures: list[str] = []

    from .analyzer import analyze
    from .audit import audit_repository
    from .impact import analyze_impact
    from .knowledge import collect
    from .planner import budget_violations, plan_mission
    from .review import can_continue, review

    audit = audit_repository()
    if len(audit) < 8:
        failures.append(f"builder audit discovered {len(audit)} < 8 categories")

    analysis = analyze("Build Patient Management")
    if analysis.mission_type != "feature":
        failures.append(f"analyzer classified as {analysis.mission_type} (expected feature)")
    if not analysis.verification_strategy or not analysis.rollback_strategy:
        failures.append("analyzer missing verification or rollback strategy")

    mission_analysis, plan = plan_mission("Fix the login crash")
    if mission_analysis.mission_type != "bug":
        failures.append(f"planner/analyzer classified as {mission_analysis.mission_type} (expected bug)")
    if budget_violations(plan):
        failures.append(f"plan has {len(budget_violations(plan))} budget violations")

    impact = analyze_impact(analysis)
    if not impact.affected_registry:
        failures.append("impact analysis missing registry surface")

    references = collect("pytest import failure", include_memory=False)
    if not references:
        failures.append("knowledge integration found no reusable artifacts")

    review_report = review("MSN-CHECK", {
        "tests_run": True, "tests_pass": True,
        "ruff_clean": True, "typecheck_clean": True,
        "security_verified": True, "registry_updated": True,
        "docs_updated": True, "deploy_verified": True,
        "adr": True, "benchmark_pass": True, "skill_reused": True,
    })
    if not can_continue(review_report):
        failures.append("self review did not pass on clean evidence")

    print("BUILDER SELF-CHECK")
    print("=" * 60)
    if failures:
        for failure in failures:
            print(f"  - {failure}")
        print("=" * 60)
        return 1
    print("  [PASS] repository audit discovered 8 categories")
    print("  [PASS] mission analyzer classifies correctly")
    print("  [PASS] mission planner respects 5 min / 50 files")
    print("  [PASS] engineering analyzer detects surfaces")
    print("  [PASS] knowledge integration finds reusable artifacts")
    print("  [PASS] self review passes on clean evidence")
    print("=" * 60)
    print("RESULT: ALL BUILDER CHECKS PASSED")
    return 0


BUILDER_COMMANDS = {
    "builder-audit": run_audit,
    "builder-analyze": run_analyze,
    "builder-plan": run_plan,
    "builder-impact": run_impact,
    "builder-execute": run_execute,
    "builder-recover": run_recover,
    "builder-knowledge": run_knowledge,
    "builder-review": run_review,
    "builder-report": run_report,
    "builder-check": run_check,
}
