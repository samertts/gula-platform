"""Extension CLI — GULA-KERNEL-EXT-001 commands.

Integrated into `scripts/kernel.py` so the Kernel remains the single entry
point. No ad-hoc scripts; every extension is reached through the Kernel.
"""

from __future__ import annotations

from ..core import Severity


def run_plugin() -> int:
    """Phase 1 — plugin registry snapshot + validation."""
    from ..core import ENGINE_REGISTRY
    from .plugin import PluginRegistry, manifest_from_engine

    registry = PluginRegistry()
    for name, meta in sorted(ENGINE_REGISTRY.items()):
        registry.register(manifest_from_engine(name, meta))

    print("PLUGIN SDK (GULA-KERNEL-EXT-001)")
    print(f"  plugins registered: {len(registry.list())}")
    print("  lifecycle: draft -> registered -> validated -> installed -> active")
    print("  isolation: sandbox | restricted | process | thread | embedded")
    for name, record in sorted(registry.snapshot().items()):
        print(f"  - {name} {record['version']} [{record['state']}]")
    return 0


def run_plugin_certify() -> int:
    """Phase 1 — certify every engine as a plugin."""
    from ..core import ENGINE_REGISTRY
    from .plugin import certify, manifest_from_engine

    failures = 0
    print("PLUGIN CERTIFICATION")
    for name, meta in sorted(ENGINE_REGISTRY.items()):
        findings = certify(manifest_from_engine(name, meta))
        hard = [f for f in findings if f.severity in {Severity.HIGH, Severity.CRITICAL}]
        if hard:
            failures += 1
            for finding in hard:
                print(f"  [FAIL] {name}: {finding.title} ({finding.detail})")
        else:
            print(f"  [PASS] {name} certified")
    return 1 if failures else 0


def run_policy() -> int:
    """Phase 2 — policy registry snapshot."""
    from .policy import PolicyEngine, default_policies

    engine = PolicyEngine()
    for policy in default_policies():
        engine.register(policy)
    policies = engine.search()
    print("POLICY ENGINE (GULA-KERNEL-EXT-001)")
    print(f"  policies active: {len(policies)}")
    for policy in policies:
        print(f"  - {policy.id} {policy.category:13s} {policy.action:4s} {policy.statement}")
    return 0


def run_policy_evaluate() -> int:
    """Phase 2 — evaluate a sample context; exit 1 if any policy is denied."""
    from .policy import PolicyEngine, default_policies

    engine = PolicyEngine()
    for policy in default_policies():
        engine.register(policy)
    context = {
        "content": "document body",
        "deployment_approval": "auto",
        "autonomy_level": "L6",
        "phase_files": 10,
        "phase_seconds": 120,
        "knowledge_verified": True,
        "bypass_quality": False,
        "has_rollback": True,
        "uses_paid_service": False,
        "constitution_change": "manual",
        "architecture_change": "manual",
        "removes_national_feature": False,
        "has_benchmark": False,
        "has_docs": True,
        "context_tokens": 1000,
        "simulated": True,
    }
    violations = engine.evaluate(context)
    print("POLICY EVALUATION")
    if not violations:
        print("  [PASS] no policy violations")
        return 0
    for violation in violations:
        print(f"  [{violation.verdict.upper()}] {violation.detail}")
    return 1 if any(v.verdict == "deny" for v in violations) else 0


def run_compat() -> int:
    """Phase 3 — render the engine contract compatibility matrix."""
    from ..core import ENGINE_REGISTRY
    from .compatibility import COMPAT_DIR, engine_matrix

    matrix = engine_matrix(ENGINE_REGISTRY)
    print("COMPATIBILITY MATRIX (GULA-KERNEL-EXT-001)")
    print(f"  contracts checked: {len(matrix.entries('contract'))}")
    for record in matrix.entries("contract"):
        status = "PASS" if record.compatible else "FAIL"
        print(f"  [{status}] {record.name} {record.to_version} {record.notes}")
    matrix.save(COMPAT_DIR + "engine_compatibility.json")
    return 0


def run_compat_check() -> int:
    """Phase 3 — exit 1 if any kernel contract is broken or unversioned."""
    from ..core import ENGINE_REGISTRY
    from .compatibility import CompatibilityError, engine_matrix

    try:
        matrix = engine_matrix(ENGINE_REGISTRY)
    except CompatibilityError as exc:
        print(f"COMPATIBILITY CHECK FAILED: {exc}")
        return 1
    broken = matrix.breaking()
    print("COMPATIBILITY CHECK (GULA-KERNEL-EXT-001)")
    if broken:
        for record in broken:
            print(f"  [BREAKING] {record.name}: {record.notes}")
        return 1
    print(f"  [PASS] {len(matrix.entries('contract'))} kernel contracts conformant")
    return 0


def run_migrate() -> int:
    """Phase 4 — migration plan registry snapshot."""
    from .migration import MIGRATION_DIR, MigrationEngine, _demo_plan

    engine = MigrationEngine()
    plan = _demo_plan()
    engine.register(plan)
    print("MIGRATION FRAMEWORK (GULA-KERNEL-EXT-001)")
    print(f"  plans: {len(engine.plans())}")
    for entry in engine.plans():
        breaking = " (breaking)" if engine.is_breaking(entry.id) else ""
        print(f"  - {entry.id} {entry.target} {entry.from_version} -> {entry.to_version}"
              f" [{entry.state}]{breaking}")
    engine.save(MIGRATION_DIR + "migration_plans.json")
    return 0


def run_migrate_run() -> int:
    """Phase 4 — execute the demo migration plan (reversible, audited)."""
    from .migration import MIGRATION_DIR, MigrationEngine, MigrationError, _demo_plan

    engine = MigrationEngine()
    plan = engine.register(_demo_plan())
    try:
        engine.execute(plan.id)
    except MigrationError as exc:
        print(f"MIGRATION EXECUTION FAILED: {exc}")
        return 1
    print("MIGRATION EXECUTION (GULA-KERNEL-EXT-001)")
    print(f"  [PASS] {plan.id} {plan.from_version} -> {plan.to_version} [{plan.state}]")
    print(f"  [PASS] rollback plan armed ({len(plan.rollback_steps)} steps)")
    engine.save(MIGRATION_DIR + "migration_plans.json")
    return 0


def run_event_bus() -> int:
    """Phase 5 — publish a demo event and show the audit trail."""
    from .event_bus import EVENT_JOURNAL, Event, EventBus

    bus = EventBus()
    bus.subscribe("migration.executed", "governor", lambda _ev: None)
    bus.subscribe("*", "audit", lambda _ev: None)
    event = Event(id="EVT-000001", name="migration.executed", publisher="ext-migrate",
                  payload={"plan": "MIGR-000001", "state": "executed"})
    deliveries = bus.publish(event)
    print("EVENT BUS (GULA-KERNEL-EXT-001)")
    print(f"  events emitted: {len(bus.events())}")
    print(f"  handlers matched: {len(deliveries)}")
    for delivery in deliveries:
        print(f"  [{delivery.status}] {delivery.event_id} -> {delivery.handler}")
    bus.save(EVENT_JOURNAL + "event_journal.json")
    return 0


def run_ext_check() -> int:
    failures: list[str] = []

    from ..core import ENGINE_REGISTRY
    from .plugin import (
        PluginRegistry,
        certify,
        manifest_from_engine,
    )

    registry = PluginRegistry()
    for name, meta in ENGINE_REGISTRY.items():
        try:
            registry.register(manifest_from_engine(name, meta))
        except Exception as exc:
            failures.append(f"plugin {name} failed registration: {exc}")

    for name, meta in ENGINE_REGISTRY.items():
        findings = certify(manifest_from_engine(name, meta))
        hard = [f for f in findings if f.severity in {Severity.HIGH, Severity.CRITICAL}]
        if hard:
            failures.append(f"plugin {name} failed certification")

    from .policy import PolicyEngine, default_policies

    try:
        policy_engine = PolicyEngine()
        for policy in default_policies():
            policy_engine.register(policy)
        if not policy_engine.search():
            failures.append("policy engine: no policies registered")
    except Exception as exc:
        failures.append(f"policy engine failed: {exc}")

    from .compatibility import engine_matrix

    try:
        compat_matrix = engine_matrix(ENGINE_REGISTRY)
        if compat_matrix.breaking():
            failures.append("compatibility: breaking contract changes detected")
    except Exception as exc:
        failures.append(f"compatibility check failed: {exc}")

    from .migration import MigrationEngine, _demo_plan

    try:
        migration_engine = MigrationEngine()
        plan = migration_engine.register(_demo_plan())
        migration_engine.execute(plan.id)
        if plan.state != "executed":
            failures.append("migration engine: demo plan did not execute")
    except Exception as exc:
        failures.append(f"migration engine failed: {exc}")

    from .event_bus import Event, EventBus

    try:
        bus = EventBus()
        bus.subscribe("migration.executed", "governor", lambda _ev: None)
        deliveries = bus.publish(Event(id="EVT-000002", name="migration.executed", publisher="ext-check"))
        if not deliveries:
            failures.append("event bus: no deliveries for demo event")
    except Exception as exc:
        failures.append(f"event bus failed: {exc}")

    print("KERNEL EXTENSION SELF-CHECK")
    print("=" * 60)
    if failures:
        for failure in failures:
            print(f"  - {failure}")
        print("=" * 60)
        return 1
    print("  [PASS] all engines register as plugins")
    print("  [PASS] all engines certified")
    print(f"  [PASS] {len(policy_engine.search())} policies registered")
    print(f"  [PASS] {len(compat_matrix.entries('contract'))} contracts compatible")
    print(f"  [PASS] migration demo executed ({plan.id} -> {plan.state})")
    print(f"  [PASS] event bus delivered ({len(deliveries)} handler(s))")
    print("=" * 60)
    print("RESULT: ALL KERNEL EXTENSION CHECKS PASSED")
    return 0


EXT_COMMANDS = {
    "ext-plugin": run_plugin,
    "ext-plugin-certify": run_plugin_certify,
    "ext-policy": run_policy,
    "ext-policy-evaluate": run_policy_evaluate,
    "ext-compat": run_compat,
    "ext-compat-check": run_compat_check,
    "ext-migrate": run_migrate,
    "ext-migrate-run": run_migrate_run,
    "ext-event-bus": run_event_bus,
    "ext-check": run_ext_check,
}
