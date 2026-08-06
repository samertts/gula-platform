#!/usr/bin/env python3
"""GULA Architecture Constitution — top-level CLI launcher (PROGRAM-ALPHA).

Usage:
    python scripts/architecture.py <command> [args]
    python scripts/architecture.py check    # full constitution gate (exit 1 on failure)
    python scripts/architecture.py --help   # list every command

Commands are also reachable through the Kernel: `python scripts/kernel.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.architecture.cli import ARCHITECTURE_COMMANDS

DOC = """GULA Architecture Constitution (PROGRAM-ALPHA)

Usage:
    python scripts/architecture.py <command> [args]

Commands:
    scan        scan backend/app + shared for Shared Core reimplementation
    gate        run the full constitution gate (exit 1 on violations)
    country     scan for country-specific hard-coding outside the national layer
    report      write ARCHITECTURE_CERTIFICATION.md
    constitution regenerate ARCHITECTURE_CONSTITUTION.md
    baseline    acknowledge the CURRENT finding set as known debt
    check       full gate, assert PASS (CI hard gate)
    policy      run the Architecture Policy Engine (human report, ADR-027)
    policy-json run the Architecture Policy Engine (JSON report)
    policy-baseline acknowledge CURRENT policy findings as known debt
"""


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] in {"-h", "--help", "help"}:
        print(DOC)
        return 0
    command = argv[0]
    if command in ARCHITECTURE_COMMANDS:
        return ARCHITECTURE_COMMANDS[command]()
    short = f"architecture-{command}"
    if short in ARCHITECTURE_COMMANDS:
        return ARCHITECTURE_COMMANDS[short]()
    print(f"Unknown command: {command}")
    print("Available: " + ", ".join(sorted(ARCHITECTURE_COMMANDS)))
    return 2


if __name__ == "__main__":
    sys.exit(main())
