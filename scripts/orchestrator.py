#!/usr/bin/env python3
"""GULA Orchestrator Engine — top-level CLI launcher (GULA-ORCHESTRATOR-001).

Usage:
    python scripts/orchestrator.py <command> [args]
    python scripts/orchestrator.py mission "Build Patient Management"
    python scripts/orchestrator.py check   # all self-checks (exit 1 on failure)
    python scripts/orchestrator.py --help  # list every command

The Orchestrator is the executive brain. It transforms a single human
objective into a managed workflow: classify → plan → route → schedule →
execute → verify → deploy → learn → report. It coordinates the Builder
(execution) and Reviewer (verification) engines without writing code or
reviewing directly. Commands are also reachable through the Kernel:
`python scripts/kernel.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.orchestrator.cli import ORCHESTRATOR_COMMANDS

DOC = """GULA Orchestrator Engine (GULA-ORCHESTRATOR-001)

Usage:
    python scripts/orchestrator.py <command> [args]

Commands:
    audit      Phase 0 — write ORCHESTRATOR_AUDIT_REPORT.md
    mission    Classify + plan + route + schedule a single objective
    classify   Classify an objective (type, priority, complexity, risk)
    plan       Classify + plan a mission
    route      Classify + plan + route + schedule a mission
    checkpoint Report checkpoint state for a mission
    resume     Resume a mission from its latest checkpoint
    status     Regenerate MISSION_STATUS.md for the latest mission
    history    List registered missions (optional search query)
    report     Phase 10 — write ORCHESTRATOR_IMPLEMENTATION_REPORT.md
    check      Run all Orchestrator self-checks (exit 1 on failure)
"""


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] in {"-h", "--help", "help"}:
        print(DOC)
        return 0
    command = argv[0]
    if command in ORCHESTRATOR_COMMANDS:
        return ORCHESTRATOR_COMMANDS[command]()
    short = f"orchestrator-{command}"
    if short in ORCHESTRATOR_COMMANDS:
        return ORCHESTRATOR_COMMANDS[short]()
    print(f"Unknown command: {command}")
    print("Available: " + ", ".join(sorted(ORCHESTRATOR_COMMANDS)))
    return 2


if __name__ == "__main__":
    sys.exit(main())
