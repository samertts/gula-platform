"""Deployer CLI — GULA-DEPLOYER-001 commands.

Integrated into `scripts/kernel.py` so the Kernel remains the single entry
point, matching the Builder, Reviewer, and Orchestrator pattern.
"""

from __future__ import annotations

import sys

from scripts.deployer.core import (
    DeploymentRecord,
    DeploymentStatus,
    make_id,
)


def run_audit() -> int:
    """Phase 0 — write DEPLOYER_AUDIT_REPORT.md."""
    from .audit import run_audit as _audit

    path = _audit()
    print(f"[OK] {path.name} written")
    return 0


def run_architecture() -> int:
    """Phase 1 — describe the deployment topology."""
    from .architecture import build_topology, describe_targets

    print(describe_targets(build_topology()))
    return 0


def run_pipeline() -> int:
    """Phase 2 — print the pipeline for a version."""
    from .execution import build_pipeline

    version = sys.argv[2] if len(sys.argv) > 2 else "1.0.0"
    try:
        stages = build_pipeline(version)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 2
    print(f"pipeline for v{version}:")
    for stage in stages:
        print(f"  {stage}")
    return 0


def run_infrastructure() -> int:
    """Phase 3 — print the infrastructure management plan."""
    from .infrastructure import (
        certificate_spec,
        desired_network,
        manage_resources,
        render_plan,
        reverse_proxy_spec,
        secrets_spec,
    )

    resources = manage_resources()
    resources += [desired_network(), reverse_proxy_spec(), certificate_spec("gula.iq"), secrets_spec()]
    print(render_plan(resources))
    return 0


def run_health() -> int:
    """Phase 4 — validate all components and print the verdict."""
    from .health import run_validation, validation_summary

    checks = run_validation()
    for check in checks:
        print(f"  [{check.status.upper()}] {check.component:<16} "
              f"{check.endpoint} {check.latency_ms}ms")
    print(validation_summary(checks))
    return 1 if any(c.status == "fail" for c in checks) else 0


def run_rollback() -> int:
    """Phase 5 — show the rollback plan for the latest deployment."""
    from .knowledge import list_deployments
    from .rollback import capture_snapshot, rollback_plan

    deployments = list_deployments()
    if not deployments:
        print("No deployments registered. Run deployer-deploy first.")
        return 1
    latest = deployments[-1]
    snapshot = capture_snapshot(latest["deployment_id"], latest["version"])
    plan = rollback_plan(snapshot)
    print(f"rollback plan for {latest['version']}:")
    print(f"  snapshot {snapshot.snapshot_id} -> {', '.join(plan['order'])}")
    print("  verify after restore: True")
    return 0


def run_scaling() -> int:
    """Phase 6 — print scaling policies and decisions."""
    from .core import SERVICES
    from .scaling import default_policies, scale_decision

    policies = default_policies(SERVICES)
    for policy in policies:
        decision = scale_decision(policy, current=1, load=policy.threshold + 1)
        print(f"  [{policy.mode}] {policy.service:<12} min={policy.min_replicas} "
              f"max={policy.max_replicas} -> {decision['replicas']} ({decision['action']})")
    return 0


def run_observability() -> int:
    """Phase 7 — print the observability integration state."""
    from .observability import alert_rules, dashboard_links, observability_config

    configs = observability_config()
    for config in configs:
        state = "enabled" if config.enabled else "disabled"
        print(f"  {config.component:<13} {state:<9} {config.endpoint}")
    print(f"  alert rules: {len(alert_rules())} | dashboards: {len(dashboard_links(configs))}")
    return 0


def run_security() -> int:
    """Phase 8 — verify all security areas and print the verdict."""
    from .security import security_summary, verify_areas

    checks = verify_areas()
    for check in checks:
        mark = "PASS" if check.passed else "FAIL"
        print(f"  [{mark}] {check.area:<20} {check.finding}")
    print(security_summary(checks))
    return 1 if any(not c.passed for c in checks) else 0


def run_knowledge() -> int:
    """Phase 9 — print deployment knowledge state."""
    from .knowledge import lessons_learned, list_deployments, recovery_procedures

    deployments = list_deployments()
    print(f"deployment registry: {len(deployments)} deployment(s)")
    for dep in deployments:
        print(f"  {dep['deployment_id']}  {dep['version']:<12} {dep['environment']:<16} {dep['status']}")
    print("recovery procedures:")
    for step in recovery_procedures():
        print(f"  {step}")
    for lesson in lessons_learned(deployments):
        print(f"  lesson: {lesson}")
    return 0


def run_report() -> int:
    """Phase 10 — write DEPLOYER_IMPLEMENTATION_REPORT.md."""
    from .report import write_report

    write_report()
    print("[OK] DEPLOYER_IMPLEMENTATION_REPORT.md written")
    return 0


def _full_deploy(version: str, environment: str) -> int:
    """Run the complete deployment pipeline for a version/environment."""
    from .architecture import ENVIRONMENTS
    from .execution import build_pipeline, create_artifact, validate_version
    from .health import deployment_rejected, run_validation
    from .knowledge import (
        add_event,
        persist_record,
        recovery_procedures,
        register,
        write_runbook,
    )
    from .rollback import automatic_rollback, capture_snapshot
    from .security import deployment_blocked, verify_areas

    if not validate_version(version):
        print(f"REJECTED — invalid semantic version: {version}")
        return 1
    if environment not in ENVIRONMENTS:
        print(f"REJECTED — unknown environment: {environment}")
        return 1

    pipeline = build_pipeline(version)
    record = DeploymentRecord(
        deployment_id=make_id("DEP"),
        version=version,
        environment=environment,
    )
    add_event(record, "pipeline prepared", "; ".join(pipeline))

    artifact = create_artifact("gula-platform", version)
    record.artifacts.append(artifact.to_dict())
    record.status = DeploymentStatus.PACKAGED.value
    add_event(record, "artifact packaged", artifact.image)

    security = verify_areas()
    record.security = [c.to_dict() for c in security]
    if deployment_blocked(security):
        record.status = DeploymentStatus.FAILED.value
        add_event(record, "blocked", "security verification failed")
        persist_record(record)
        register(record.deployment_id, version, environment, record.status)
        print("SECURITY BLOCKED — deployment rejected before validation.")
        return 1

    checks = run_validation()
    record.validations = [c.to_dict() for c in checks]
    snapshot = capture_snapshot(record.deployment_id, version)
    record.snapshots.append(snapshot.to_dict())

    if deployment_rejected(checks):
        rollback = automatic_rollback(checks, snapshot)
        record.rollbacks.append(rollback)
        record.status = rollback["status"]
        add_event(record, "rolled back", rollback["reason"])
        persist_record(record)
        register(record.deployment_id, version, environment, record.status)
        print("HEALTH REJECTED — automatic rollback applied.")
        return 1

    record.status = DeploymentStatus.LIVE.value
    add_event(record, "deployed", f"{artifact.image} to {environment}")
    persist_record(record)
    register(record.deployment_id, version, environment, record.status)

    runbook = "\n".join(recovery_procedures())
    write_runbook(runbook)
    add_event(record, "runbook updated", recovery_procedures()[0])
    persist_record(record)

    print(f"DEPLOYMENT {record.deployment_id} — gula-platform:{version} -> {environment}")
    print(f"  artifacts: {len(record.artifacts)} | validations: {len(record.validations)}")
    print(f"  security: {len(record.security)} areas verified")
    print(f"  snapshot: {snapshot.snapshot_id} (rollback point)")
    print("  status: LIVE")
    return 0


def run_deploy() -> int:
    """Deploy a version to an environment end-to-end (the success criterion)."""
    version = sys.argv[2] if len(sys.argv) > 2 else "1.0.0"
    environment = sys.argv[3] if len(sys.argv) > 3 else "production"
    try:
        return _full_deploy(version, environment)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 2


def run_check() -> int:
    """Run all Deployer self-checks; exit 1 on any failure."""
    failures: list[str] = []

    from .architecture import build_topology
    from .audit import audit_systems
    from .execution import build_pipeline, validate_container
    from .health import deployment_rejected, run_validation
    from .rollback import automatic_rollback, capture_snapshot, verify_restore
    from .scaling import default_policies, scale_decision
    from .security import deployment_blocked, verify_areas

    # 1. Audit is deterministic and covers all components.
    items = audit_systems()
    if len(items) != 17:
        failures.append(f"audit expected 17 components got {len(items)}")

    # 2. Architecture covers all eight environments.
    if len(build_topology()) != 8:
        failures.append("topology must cover eight environments")

    # 3. Pipeline stages are deterministic and ordered.
    stages = build_pipeline("2.1.0")
    if len(stages) != 8:
        failures.append("pipeline must have eight stages")
    if "build" not in stages[0] or "deploy" not in stages[-1]:
        failures.append("pipeline ordering incorrect")

    # 4. Container validation flags insecure Dockerfiles.
    good = "FROM python:3.12\nUSER app\nHEALTHCHECK CMD curl -f http://localhost/\n"
    bad = "FROM python\n"
    if validate_container(good):
        failures.append("secure dockerfile flagged")
    if not validate_container(bad):
        failures.append("insecure dockerfile passed")

    # 5. Health validation rejects when a component is down.
    bad_checks = run_validation(healthy={"api", "database"})
    if not deployment_rejected(bad_checks):
        failures.append("health validation must reject missing components")

    # 6. Automatic rollback triggers on rejection and verifies restore.
    snapshot = capture_snapshot("DEP-1", "1.0.0")
    rollback = automatic_rollback(bad_checks, snapshot)
    if not rollback["rolled_back"]:
        failures.append("automatic rollback did not trigger")
    if not verify_restore(rollback):
        failures.append("rollback restore not verified")

    # 7. Scaling policies produce bounded decisions.
    for policy in default_policies(("backend", "worker")):
        decision = scale_decision(policy, current=1, load=999)
        if not (policy.min_replicas <= decision["replicas"] <= policy.max_replicas):
            failures.append(f"scaling decision out of bounds for {policy.service}")

    # 8. Security verification blocks when an area fails.
    blocked_checks = verify_areas(tls_enabled=False)
    if not deployment_blocked(blocked_checks):
        failures.append("security must block when an area fails")

    print("DEPLOYER SELF-CHECK")
    print("=" * 60)
    if failures:
        for failure in failures:
            print(f"  - {failure}")
        print("=" * 60)
        return 1
    for item in items:
        state = "present" if item.present else "absent"
        print(f"  [PASS] audit {item.name:<18} {state}")
    print("  [PASS] topology covers 8 environments")
    print("  [PASS] pipeline ordering deterministic")
    print("  [PASS] health rejects + rollback verified")
    print("  [PASS] scaling bounded + security blocks")
    print("=" * 60)
    print("RESULT: ALL DEPLOYER CHECKS PASSED")
    return 0


DEPLOYER_COMMANDS = {
    "deployer-audit": run_audit,
    "deployer-architecture": run_architecture,
    "deployer-pipeline": run_pipeline,
    "deployer-infrastructure": run_infrastructure,
    "deployer-health": run_health,
    "deployer-rollback": run_rollback,
    "deployer-scaling": run_scaling,
    "deployer-observability": run_observability,
    "deployer-security": run_security,
    "deployer-knowledge": run_knowledge,
    "deployer-report": run_report,
    "deployer-deploy": run_deploy,
    "deployer-check": run_check,
}
