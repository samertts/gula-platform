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
    print("=" * 60)
    print("RESULT: ALL KERNEL EXTENSION CHECKS PASSED")
    return 0


EXT_COMMANDS = {
    "ext-plugin": run_plugin,
    "ext-plugin-certify": run_plugin_certify,
    "ext-policy": run_policy,
    "ext-policy-evaluate": run_policy_evaluate,
    "ext-check": run_ext_check,
}
