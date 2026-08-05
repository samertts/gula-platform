#!/usr/bin/env python3
"""GULA Reviewer Engine — top-level CLI launcher (GULA-REVIEWER-001).

Usage:
    python scripts/reviewer.py <command> [area]
    python scripts/reviewer.py check     # all self-checks (exit 1 on failure)
    python scripts/reviewer.py --help    # list every command

The Reviewer is the independent verification authority. It reviews Builder
outputs and the repository itself across eight areas, producing deterministic
PASS / PASS WITH WARNINGS / REJECT verdicts. It never writes production code.
Commands are also reachable through the Kernel: `python scripts/kernel.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.reviewer.cli import REVIEWER_COMMANDS

DOC = """GULA Reviewer Engine (GULA-REVIEWER-001)

Usage:
    python scripts/reviewer.py <command> [area]

Commands:
    audit      Phase 0 — write REVIEWER_AUDIT_REPORT.md
    review     Run all eight area reviews and persist the verdict
    area       Review one area (e.g. `reviewer.py area security`)
    gate       Run the review and return 0 (pass) / 1 (reject)
    report     Phase 10 — write REVIEWER_IMPLEMENTATION_REPORT.md
    check      Run all Reviewer self-checks (exit 1 on failure)
    <area>     Review a single area directly (architecture, code, security,
               tests, deployment, documentation, performance, knowledge)
"""


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] in {"-h", "--help", "help"}:
        print(DOC)
        return 0
    command = argv[0]
    if command in REVIEWER_COMMANDS:
        return REVIEWER_COMMANDS[command]()
    short = f"reviewer-{command}"
    if short in REVIEWER_COMMANDS:
        return REVIEWER_COMMANDS[short]()
    print(f"Unknown command: {command}")
    print("Available: " + ", ".join(sorted(REVIEWER_COMMANDS)))
    return 2


if __name__ == "__main__":
    sys.exit(main())
