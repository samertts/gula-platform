#!/usr/bin/env python3
"""GULA Deployment Engine — top-level CLI launcher (GULA-DEPLOYER-001).

Usage:
    python scripts/deployer.py <command> [args]
    python scripts/deployer.py deploy 1.4.0 production
    python scripts/deployer.py check    # all self-checks (exit 1 on failure)
    python scripts/deployer.py --help   # list every command

The Deployment Engine transforms verified software into a production-ready,
observable, secure, and recoverable platform. It never develops application
features; it only deploys, validates, secures, monitors, scales, and
recovers production systems. Commands are also reachable through the Kernel:
`python scripts/kernel.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.deployer.cli import DEPLOYER_COMMANDS

DOC = """GULA Deployment Engine (GULA-DEPLOYER-001)

Usage:
    python scripts/deployer.py <command> [args]

Commands:
    audit           Phase 0 — write DEPLOYER_AUDIT_REPORT.md
    architecture    Phase 1 — describe the deployment topology
    pipeline        Phase 2 — print the pipeline for a version
    infrastructure  Phase 3 — print the infrastructure management plan
    health          Phase 4 — validate all components
    rollback        Phase 5 — show the rollback plan
    scaling         Phase 6 — print scaling policies
    observability   Phase 7 — print the observability integration state
    security        Phase 8 — verify all security areas
    knowledge       Phase 9 — print deployment knowledge state
    report          Phase 10 — write DEPLOYER_IMPLEMENTATION_REPORT.md
    deploy          Deploy a version end-to-end (deploy <version> [env])
    check           Run all Deployer self-checks (exit 1 on failure)
"""


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] in {"-h", "--help", "help"}:
        print(DOC)
        return 0
    command = argv[0]
    if command in DEPLOYER_COMMANDS:
        return DEPLOYER_COMMANDS[command]()
    short = f"deployer-{command}"
    if short in DEPLOYER_COMMANDS:
        return DEPLOYER_COMMANDS[short]()
    print(f"Unknown command: {command}")
    print("Available: " + ", ".join(sorted(DEPLOYER_COMMANDS)))
    return 2


if __name__ == "__main__":
    sys.exit(main())
