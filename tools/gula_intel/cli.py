"""Developer-facing entry point: read-only by default.

    python3 -m gula_intel.cli health
    python3 -m gula_intel.cli findings
    python3 -m gula_intel.cli inspect
    python3 -m gula_intel.cli impact <path> [<path> ...]
    python3 -m gula_intel.cli tests-for <path> [<path> ...]

No subcommand mutates the repository or a database.  ``--write-state`` is the
single opt-in that persists recurrence memory.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

from . import detectors, impact, inventory, planner, registry
from .model import Health, Severity


def _commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True,
            cwd=str(inventory.REPO_ROOT),
        ).stdout.strip()[:12]
    except (subprocess.SubprocessError, OSError):
        return "unknown"


def _health(results: list) -> Health:
    if any(f.blocker for r in results for f in r.findings):
        return Health.BLOCKED
    if any(r.detector_state.name.startswith("RAN") is False for r in results):
        return Health.UNKNOWN  # a detector that did not run cannot imply health
    severities = {f.severity for r in results for f in r.findings}
    if Severity.P0 in severities:
        return Health.UNHEALTHY
    if severities:
        return Health.DEGRADED
    return Health.HEALTHY


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gula-intel", description=__doc__)
    parser.add_argument("command", choices=["health", "findings", "inspect", "impact", "tests-for", "plan"])
    parser.add_argument("paths", nargs="*")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--write-state", action="store_true", help="persist recurrence memory")
    args = parser.parse_args(argv)

    if args.command == "plan":
        if not args.paths:
            parser.error("plan requires at least one path")
        print(_render(planner.plan(args.paths).to_dict()))
        return 0

    if args.command in {"impact", "tests-for"}:
        if not args.paths:
            parser.error(f"{args.command} requires at least one path")
        if args.command == "impact":
            rows = [vars(i) for i in impact.analyse(args.paths)]
            payload = {"impact": rows, "note": impact.unaffected_note(args.paths)}
        else:
            payload = {"selected_tests": impact.select_tests(args.paths),
                       "note": impact.unaffected_note(args.paths)}
        print(json.dumps(payload, indent=2, ensure_ascii=False) if args.json else _render(payload))
        return 0

    inv = inventory.collect()
    if args.command == "inspect":
        payload = inv.summary()
        print(json.dumps(payload, indent=2, ensure_ascii=False) if args.json else _render(payload))
        return 0

    results = detectors.run_all(inv)
    commit = _commit()
    reconciled = registry.reconcile(results, registry.load_state(), commit)
    if args.write_state:
        registry.save_state(reconciled)

    payload = {
        "commit": commit,
        "health": _health(results).value,
        "inventory": inv.summary(),
        "checks": [r.to_dict() for r in results],
        "transitions": reconciled["transitions"],
        "production_ready": False,
        "production_ready_reason": "blockers remain unresolved; see findings",
    }
    if args.command == "health":
        payload.pop("checks")
    print(json.dumps(payload, indent=2, ensure_ascii=False) if args.json else _render(payload))
    return 0


def _render(payload: dict) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    sys.exit(main())
