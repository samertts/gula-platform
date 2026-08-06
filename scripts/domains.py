#!/usr/bin/env python3
"""GULA Domain Platform Framework — top-level CLI launcher (PROGRAM-STABLE-004).

Usage:
    python scripts/domains.py <command> [args]
    python scripts/domains.py check     # full pipeline self-check (exit 1 on failure)
    python scripts/domains.py --help    # list every command

The permanent Domain Platform Framework enforces Domain Sovereignty for every
current and future GULA healthcare module: Domain Blueprint, Shared Core
consumption, Domain isolation, cross-domain contracts, lifecycle, workspace
binding, and certification. Commands are also reachable through the Kernel:
`python scripts/kernel.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.domains.cli import DOMAINS_COMMANDS

DOC = """GULA Domain Platform Framework (PROGRAM-STABLE-004)

Usage:
    python scripts/domains.py <command> [args]

Commands:
    audit       resolve the canonical Domains from source
    isolate     run the Phase 3 isolation scan (exit 1 on findings)
    certify     run the Phase 7 certification (exit 1 if not certified)
    docs        regenerate the 7 official DOMAIN_*.md documents
    report      run the full pipeline + write state/DATA.json + docs
    check       full pipeline, assert certification PASS
"""


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] in {"-h", "--help", "help"}:
        print(DOC)
        return 0
    command = argv[0]
    if command in DOMAINS_COMMANDS:
        return DOMAINS_COMMANDS[command]()
    short = f"domain-{command}"
    if short in DOMAINS_COMMANDS:
        return DOMAINS_COMMANDS[short]()
    print(f"Unknown command: {command}")
    print("Available: " + ", ".join(sorted(DOMAINS_COMMANDS)))
    return 2


if __name__ == "__main__":
    sys.exit(main())
