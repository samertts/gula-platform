#!/usr/bin/env python3
"""GULA Architect Engine — top-level CLI launcher (GULA-ARCHITECT-001).

Usage:
    python scripts/architect.py <command> [args]
    python scripts/architect.py run     # run the full architect pipeline
    python scripts/architect.py check   # all self-checks (exit 1 on failure)
    python scripts/architect.py --help  # list every command

The Enterprise Autonomous Architecture & Strategic Decision Engine makes,
documents, and reviews architectural decisions for the GULA national
healthcare platform. It never writes production features. Commands are also
reachable through the Kernel: `python scripts/kernel.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.architect.cli import ARCHITECT_COMMANDS

DOC = """GULA Architect Engine (GULA-ARCHITECT-001)

Usage:
    python scripts/architect.py <command> [args]

Commands:
    audit           Phase 0 — write ARCHITECT_AUDIT_REPORT.md
    model           Phase 1 — build + persist the system model
    decisions       Phase 2 — record + persist architectural decisions
    dependencies    Phase 3 — scan + persist dependency findings
    evolution       Phase 4 — build + persist the evolution roadmap
    risk            Phase 5 — build + persist the risk register
    review          Phase 6 — review a candidate design (<name>)
    simulation      Phase 7 — persist scale projections (100 -> 1M)
    coordination    Phase 8 — persist AI coordination contracts
    health          Phase 9 — measure + persist architecture health
    report          Phase 10 — write ARCHITECT_IMPLEMENTATION_REPORT.md
    run             Run the full architect pipeline end-to-end
    check           Run all Architect self-checks (exit 1 on failure)
"""


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] in {"-h", "--help", "help"}:
        print(DOC)
        return 0
    command = argv[0]
    if command in ARCHITECT_COMMANDS:
        return ARCHITECT_COMMANDS[command]()
    short = f"architect-{command}"
    if short in ARCHITECT_COMMANDS:
        return ARCHITECT_COMMANDS[short]()
    print(f"Unknown command: {command}")
    print("Available: " + ", ".join(sorted(ARCHITECT_COMMANDS)))
    return 2


if __name__ == "__main__":
    sys.exit(main())
