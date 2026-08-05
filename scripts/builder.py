#!/usr/bin/env python3
"""GULA Builder Engine — top-level CLI launcher (GULA-BUILDER-001).

Usage:
    python scripts/builder.py <command>
    python scripts/builder.py check     # all self-checks (exit 1 on failure)
    python scripts/builder.py --help    # list every command

The Builder is the primary engineering execution system. It transforms a
human objective into a complete, verified, production-ready implementation.
Commands are also reachable through the Kernel: `python scripts/kernel.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.builder.cli import BUILDER_COMMANDS

DOC = """GULA Builder Engine (GULA-BUILDER-001)

Usage:
    python scripts/builder.py <command> [objective]

Commands:
    audit      Phase 0 — write BUILDER_AUDIT_REPORT.md
    analyze    Phase 1 — classify and analyze an objective
    plan       Phase 2 — decompose an objective into a budgeted plan
    impact     Phase 3 — engineering surface impact analysis
    execute    Phase 4 — run a demo mission through the execution order
    recover    Phase 5 — demonstrate checkpoint + retry + resume
    knowledge  Phase 6 — search knowledge for reusable solutions
    review     Phase 7 — run the self-review
    report     Phase 8 — write BUILDER_IMPLEMENTATION_REPORT.md
    check      Run all Builder self-checks (exit 1 on failure)
"""


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] in {"-h", "--help", "help"}:
        print(DOC)
        return 0
    command = argv[0]
    if command in BUILDER_COMMANDS:
        return BUILDER_COMMANDS[command]()
    short = f"builder-{command}"
    if short in BUILDER_COMMANDS:
        return BUILDER_COMMANDS[short]()
    print(f"Unknown command: {command}")
    print("Available: " + ", ".join(sorted(BUILDER_COMMANDS)))
    return 2


if __name__ == "__main__":
    sys.exit(main())
