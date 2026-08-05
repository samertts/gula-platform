"""Kernel Extensions package (GULA-KERNEL-EXT-001).

Phase 1 — Plugin SDK. Extends the Execution Kernel (GULA-KERNEL-001) with the
eight enterprise systems: Plugin SDK, Policy Engine, Compatibility Framework,
Migration Framework, Enterprise Event Bus, Workflow Engine, AI Marketplace,
and Continuous Evolution System. Every engine becomes a plugin; no engine may
bypass these systems.

Modules:
    plugin          Phase 1 — Plugin SDK (manifests, registry, lifecycle, sandbox)
    policy          Phase 2 — Policy Engine (versioned, composable policies)
    compatibility   Phase 3 — Compatibility Framework (matrices + detection)
    migration       Phase 4 — Migration Engine (schema/knowledge/policy/rollback)
    event_bus       Phase 5 — Enterprise Event Bus (loose coupling)
    workflow        Phase 6 — Workflow Engine (sequential/parallel/approval)
    marketplace     Phase 7 — AI Marketplace (catalogs + install)
    evolution       Phase 8 — Self Evolution Engine (RFC-only proposals)
    memory          Phase 9 — Enterprise AI Memory (multi-tier)
    health          Phase 10 — Health Engine (HEALTH/RISK/READINESS scores)
    cli             Extension CLI (integrated into scripts/kernel.py)
"""

from . import (
    compatibility,
    event_bus,
    evolution,
    marketplace,
    memory,
    migration,
    plugin,
    policy,
    workflow,
)

__all__ = ["compatibility", "event_bus", "evolution", "marketplace", "memory", "migration", "plugin", "policy", "workflow"]
