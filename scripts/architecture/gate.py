"""PROGRAM-ALPHA — Architecture Constitution gate (Phase 7 enforcement).

The gate is the CI-level mechanism that makes the constitution permanent:

    gate() = constitution scan (new findings fail) + domain certification +
             workspace binding + country-agnostic scan.

Findings already present in the committed baseline are acknowledged debt
(migrate them, never grow them). Any finding NOT in the baseline is a hard
failure — this is the property that makes future PRs automatically fail when
they introduce duplicated infrastructure.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from scripts.architecture.core import (
    REPO_ROOT,
    ConstitutionFinding,
    scan,
)

STATE_DIR = REPO_ROOT / ".ai" / "core" / "architecture"
BASELINE_PATH = STATE_DIR / "constitution_baseline.json"

_SCAN_ROOTS = (
    REPO_ROOT / "backend" / "app",
    REPO_ROOT / "shared",
)

# Country-specific hard-coding markers are only allowed inside the national
# layer (backend/app/national, backend/app/nhdw, backend/app/national_data).
# Administrative hierarchy terms (governorate, directorate) are NOT markers:
# they are the constitutional national platform hierarchy.
_COUNTRY_MARKERS = (
    r"\bi_qar\b",
    r"\bdinar\b",
    r"['\"](?:i)?raq['\"]",
)


def load_baseline() -> list[dict[str, str]]:
    if not BASELINE_PATH.exists():
        return []
    data = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    return data.get("findings", [])


def load_country_baseline() -> list[dict[str, str]]:
    if not BASELINE_PATH.exists():
        return []
    data = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    return data.get("country_findings", [])


def baseline_fingerprint() -> set[tuple[str, str]]:
    return {(f["rule_id"], f["path"]) for f in load_baseline()}


def country_baseline_fingerprint() -> set[tuple[str, str]]:
    return {(f["path"], f["marker"]) for f in load_country_baseline()}


def new_findings(findings: list[ConstitutionFinding]) -> list[ConstitutionFinding]:
    known = baseline_fingerprint()
    return [f for f in findings if (f.rule_id, f.path) not in known]


def new_country_findings(findings: list[dict[str, str]]) -> list[dict[str, str]]:
    known = country_baseline_fingerprint()
    return [f for f in findings if (f["path"], f["marker"]) not in known]


def run_constitution_gate() -> dict[str, Any]:
    findings = scan(_SCAN_ROOTS)
    unknown = new_findings(findings)
    by_rule: dict[str, list[str]] = {}
    for f in findings:
        by_rule.setdefault(f.rule_id, []).append(f.path)
    return {
        "total_findings": len(findings),
        "baseline_acknowledged": len(findings) - len(unknown),
        "new_findings": [f.to_dict() for f in unknown],
        "by_rule": by_rule,
        "passes": not unknown,
    }


def run_country_agnostic_scan() -> list[dict[str, str]]:
    """Find country-specific hard-coding outside the national layer."""
    import re

    from scripts.architecture.core import iter_source_files

    violations: list[dict[str, str]] = []
    for path, rel in iter_source_files((REPO_ROOT / "backend" / "app",)):
        if rel.startswith(("backend/app/national", "backend/app/nhdw", "backend/app/national_data")):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for marker in _COUNTRY_MARKERS:
            if re.search(marker, text, re.IGNORECASE):
                violations.append({"path": rel, "marker": marker})
                break
    return violations


def run_domain_gate() -> dict[str, Any]:
    """Delegate to the Domain Platform Framework certification (Phase 7)."""
    _backend = REPO_ROOT / "backend"
    if str(_backend) not in sys.path:
        sys.path.insert(0, str(_backend))
    from app.domain_platform.certification import DomainCertificationEngine
    from app.domain_platform.isolation import IsolationValidator
    from app.domain_platform.manifest import (
        CANONICAL_DOMAINS,
        assert_no_cross_domain_administration,
    )

    domains = list(CANONICAL_DOMAINS.values())
    isolation = IsolationValidator(domains).run()
    certs = DomainCertificationEngine(isolation_report=isolation).certify_all(domains)
    passed = sum(1 for c in certs if c.passed)
    total = len(certs)
    return {
        "domains_total": total,
        "domains_passed": passed,
        "isolation_passes": isolation.passes,
        "cross_domain_admin": assert_no_cross_domain_administration(),
        "certified": passed == total and isolation.passes,
    }


def run_all_gates() -> dict[str, Any]:
    constitution = run_constitution_gate()
    domain = run_domain_gate()
    country = run_country_agnostic_scan()
    new_country = new_country_findings(country)
    passed = constitution["passes"] and domain["certified"] and not new_country
    return {
        "constitution": constitution,
        "domain": domain,
        "country_agnostic": {
            "findings": country,
            "new_findings": new_country,
            "passes": not new_country,
        },
        "passed": passed,
        "verdict": "PASS" if passed else "FAIL",
    }


def cmd_gate(report_only: bool = False) -> int:
    result = run_all_gates()
    _print_result(result)
    return 0 if result["passed"] else 1


def _print_result(result: dict[str, Any]) -> None:
    c = result["constitution"]
    d = result["domain"]
    ca = result["country_agnostic"]
    print(f"Architecture Constitution gate: {result['verdict']}")
    print(f"  Shared Core scan: {c['total_findings']} findings "
          f"({c['baseline_acknowledged']} acknowledged, {len(c['new_findings'])} new)")
    for f in c["new_findings"]:
        print(f"    NEW: {f['rule_id']:<18} {f['path']}")
    print(f"  Domain certification: {d['domains_passed']}/{d['domains_total']} "
          f"({(d['isolation_passes'] and 'isolation PASS') or 'isolation FAIL'})")
    print(f"  Country-agnostic: {'PASS' if ca['passes'] else str(len(ca['new_findings'])) + ' NEW violations'}")
    for v in ca["new_findings"]:
        print(f"    NEW: {v['path']}: {v['marker']}")


def write_baseline() -> int:
    """Acknowledge the CURRENT full finding set as known debt. Use only when
    intentionally accepting new debt (never to hide a regression)."""
    findings = scan(_SCAN_ROOTS)
    country = run_country_agnostic_scan()
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "note": "Known Shared Core reimplementation + country-hardening debt "
                "awaiting migration (MASTER_REMAINING_WORK.md). Do not grow "
                "this list.",
        "findings": [f.to_dict() for f in findings],
        "country_findings": country,
    }
    BASELINE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"baseline written: {BASELINE_PATH} ({len(findings)} findings, "
          f"{len(country)} country findings acknowledged)")
    return 0


if __name__ == "__main__":
    sys.exit(cmd_gate())
