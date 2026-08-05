#!/usr/bin/env python3
"""GULA Optimization Engine — top-level CLI launcher (GULA-OPTIMIZER-001).

Usage:
    python scripts/optimizer.py <command> [args]
    python scripts/optimizer.py run     # run the full optimization pipeline
    python scripts/optimizer.py check   # all self-checks (exit 1 on failure)
    python scripts/optimizer.py --help  # list every command

The Optimization Engine continuously improves the platform without changing
business behavior — performance, scalability, reliability, maintainability,
developer experience, and resource efficiency, always preserving
correctness. Every optimization is measured, verified, documented,
reversible, auditable, and safe. Commands are also reachable through the
Kernel: `python scripts/kernel.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.optimizer.cli import OPTIMIZER_COMMANDS

DOC = """GULA Optimization Engine (GULA-OPTIMIZER-001)

Usage:
    python scripts/optimizer.py <command> [args]

Commands:
    audit           Phase 0 — write OPTIMIZER_AUDIT_REPORT.md
    analyze         Phase 1 — measure + persist the performance baseline
    bottlenecks     Phase 2 — detect + persist bottlenecks
    architecture    Phase 3 — recommend + persist architecture optimizations
    resources       Phase 4 — recommend + persist resource optimizations
    dx              Phase 5 — score + persist developer experience
    debt            Phase 6 — detect + persist technical debt
    optimize        Phase 7 — run a safe optimization cycle (<metric>)
    evolve          Phase 8 — propose platform evolution
    validate        Phase 9 — run all optimization-quality checks
    report          Phase 10 — write OPTIMIZER_IMPLEMENTATION_REPORT.md
    run             Run the full optimization pipeline end-to-end
    check           Run all Optimizer self-checks (exit 1 on failure)
"""


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] in {"-h", "--help", "help"}:
        print(DOC)
        return 0
    command = argv[0]
    if command in OPTIMIZER_COMMANDS:
        return OPTIMIZER_COMMANDS[command]()
    short = f"optimizer-{command}"
    if short in OPTIMIZER_COMMANDS:
        return OPTIMIZER_COMMANDS[short]()
    print(f"Unknown command: {command}")
    print("Available: " + ", ".join(sorted(OPTIMIZER_COMMANDS)))
    return 2


if __name__ == "__main__":
    sys.exit(main())
