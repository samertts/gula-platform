#!/usr/bin/env python3
"""GULA Learning Engine — top-level CLI launcher (GULA-LEARNER-001).

Usage:
    python scripts/learner.py <command> [args]
    python scripts/learner.py learn    # run the full learning pipeline
    python scripts/learner.py check    # all self-checks (exit 1 on failure)
    python scripts/learner.py --help   # list every command

The Learning Engine transforms every completed mission into permanent
engineering knowledge. It never develops features and never deploys
software — it continuously improves platform intelligence by extracting
knowledge, generating skills/playbooks/runbooks, evolving memory and the
knowledge graph, detecting patterns, proposing improvements, verifying
quality, and powering search. Commands are also reachable through the
Kernel: `python scripts/kernel.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.learner.cli import LEARNER_COMMANDS

DOC = """GULA Learning Engine (GULA-LEARNER-001)

Usage:
    python scripts/learner.py <command> [args]

Commands:
    audit        Phase 0 — write LEARNER_AUDIT_REPORT.md
    extract      Phase 1 — extract knowledge from a mission/deployment
    skill        Phase 2 — generate a reusable skill
    playbook     Phase 3 — generate a playbook (<kind>)
    runbook      Phase 4 — generate a runbook (<kind>)
    memory       Phase 5 — evolve memory + knowledge graph
    patterns     Phase 6 — detect recurring patterns
    improve      Phase 7 — propose engine improvements
    quality      Phase 8 — run all knowledge-quality checks
    search       Phase 9 — build index or search (<query> | --build)
    report       Phase 10 — write LEARNER_IMPLEMENTATION_REPORT.md
    learn        Run the full learning pipeline end-to-end
    check        Run all Learner self-checks (exit 1 on failure)
"""


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] in {"-h", "--help", "help"}:
        print(DOC)
        return 0
    command = argv[0]
    if command in LEARNER_COMMANDS:
        return LEARNER_COMMANDS[command]()
    short = f"learner-{command}"
    if short in LEARNER_COMMANDS:
        return LEARNER_COMMANDS[short]()
    print(f"Unknown command: {command}")
    print("Available: " + ", ".join(sorted(LEARNER_COMMANDS)))
    return 2


if __name__ == "__main__":
    sys.exit(main())
