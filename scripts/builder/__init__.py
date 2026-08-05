"""Builder Engine package (GULA-BUILDER-001).

The primary engineering execution system. Transforms a human objective into a
complete, verified, production-ready implementation.

Phases:
    audit       Phase 0 — repository audit (BUILDER_AUDIT_REPORT.md)
    analyzer    Phase 1 — mission type/complexity/risk estimation
    planner     Phase 2 — Program > Phase > Micro Phase > Task decomposition
    impact      Phase 3 — engineering surface impact analysis
    executor    Phase 4 — analyze > plan > validate > execute > ... > continue
    recovery    Phase 5 — checkpoint, analyze, retry, resume, continue
    knowledge   Phase 6 — search skills/playbooks/runbooks/ADR/registry/memory
    review      Phase 7 — self review across 8 quality areas
    report      Phase 8 — BUILDER_IMPLEMENTATION_REPORT.md
    cli         Builder CLI (integrated into scripts/kernel.py)
"""

from . import (
    analyzer,
    audit,
    executor,
    impact,
    knowledge,
    planner,
    recovery,
    report,
    review,
)

__all__ = [
    "analyzer",
    "audit",
    "executor",
    "impact",
    "knowledge",
    "planner",
    "recovery",
    "report",
    "review",
]
