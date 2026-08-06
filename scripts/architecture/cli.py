"""PROGRAM-ALPHA — Architecture Constitution CLI.

Commands:
  architecture-scan         scan the repository for Shared Core reimplementation
  architecture-gate         run the full constitution gate (exit 1 on failure)
  architecture-country      run the country-agnostic design scan
  architecture-report       write ARCHITECTURE_CERTIFICATION.md
  architecture-constitution write ARCHITECTURE_CONSTITUTION.md
  architecture-docs         regenerate all master PROGRAM-ALPHA documents
  architecture-baseline     acknowledge the CURRENT findings as known debt
  architecture-check        full gate + certification verdict (CI hard gate)
"""

from __future__ import annotations

import argparse

from scripts.architecture.core import REPO_ROOT, scan
from scripts.architecture.gate import (
    _print_result,
    cmd_gate,
    load_baseline,
    run_all_gates,
    run_country_agnostic_scan,
    write_baseline,
)
from scripts.architecture.report import generate_certification, generate_constitution

_SCAN_ROOTS = (REPO_ROOT / "backend" / "app", REPO_ROOT / "shared")


def cmd_scan() -> int:
    findings = scan(_SCAN_ROOTS)
    known = {(f["rule_id"], f["path"]) for f in load_baseline()}
    print(f"constitution scan: {len(findings)} findings")
    for f in findings:
        status = "ACK" if (f.rule_id, f.path) in known else "NEW"
        print(f"  [{status}] {f.rule_id:<18} {f.path}")
    return 0


def cmd_gate_() -> int:
    return cmd_gate()


def cmd_country() -> int:
    findings = run_country_agnostic_scan()
    print(f"country-agnostic scan: {len(findings)} violations")
    for v in findings:
        print(f"  {v['path']}: {v['marker']}")
    return 0 if not findings else 1


def cmd_report() -> int:
    result = run_all_gates()
    path = generate_certification(result)
    print(f"wrote {path.name}")
    return 0


def cmd_constitution_doc() -> int:
    path = generate_constitution()
    print(f"wrote {path.name}")
    return 0


def cmd_docs() -> int:
    from scripts.architecture.docs import write_all

    for path in write_all():
        print(f"wrote {path.name}")
    return 0


def cmd_check() -> int:
    result = run_all_gates()
    _print_result(result)
    verdict = "PASS" if result["passed"] else "FAIL"
    print(f"architecture constitution: {verdict}")
    return 0 if result["passed"] else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="architecture", description=__doc__)
    parser.add_argument(
        "command",
        choices=["scan", "gate", "country", "report", "constitution", "docs", "baseline", "check"],
    )
    args = parser.parse_args(argv)
    return {
        "scan": cmd_scan,
        "gate": cmd_gate_,
        "country": cmd_country,
        "report": cmd_report,
        "constitution": cmd_constitution_doc,
        "docs": cmd_docs,
        "baseline": write_baseline,
        "check": cmd_check,
    }[args.command]()


ARCHITECTURE_COMMANDS = {
    "architecture-scan": cmd_scan,
    "architecture-gate": cmd_gate_,
    "architecture-country": cmd_country,
    "architecture-report": cmd_report,
    "architecture-constitution": cmd_constitution_doc,
    "architecture-docs": cmd_docs,
    "architecture-baseline": write_baseline,
    "architecture-check": cmd_check,
}


if __name__ == "__main__":
    raise SystemExit(main())
