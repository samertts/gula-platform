"""PROGRAM-BETA-COMMIT-0.2 — Architecture Policy Engine governance runner.

Runs the Policy Engine (ADR-027) in repository mode against the canonical
Domains and the canonical Dormancy source, then exposes:

  * ``run_policy_gate()`` — the machine-readable gate section consumed by
    the Architecture Constitution gate and CI;
  * ``cmd_policy()`` / ``cmd_policy_json()`` — human + JSON reports;
  * ``write_policy_baseline()`` — acknowledge the current finding set as
    known debt (never to hide a regression).

The engine is the single governance entry point: enabling any future policy
in the registry automatically joins this gate, certification (check 10) and
CI without touching this module.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from scripts.architecture.core import REPO_ROOT

POLICY_BASELINE_PATH = REPO_ROOT / ".ai" / "core" / "policies" / "policy_baseline.json"


def _backend_on_path() -> None:
    backend = REPO_ROOT / "backend"
    if str(backend) not in sys.path:
        sys.path.insert(0, str(backend))


def _context() -> Any:
    from app.domain_platform.dormancy import load_default_dormancy_source
    from app.domain_platform.manifest import CANONICAL_DOMAINS
    from app.domain_platform.policies import PolicyContext

    return PolicyContext(
        domains=list(CANONICAL_DOMAINS.values()),
        dormancy_source=load_default_dormancy_source(),
    )


def run_policy_engine() -> Any:
    """Run every enabled policy against the canonical repository context."""
    _backend_on_path()
    from app.domain_platform.policies import PolicyBaseline, PolicyEngine, build_default_registry

    baseline = PolicyBaseline.load(POLICY_BASELINE_PATH)
    return PolicyEngine(registry=build_default_registry(), baseline=baseline).run(_context())


def run_policy_gate() -> dict[str, Any]:
    report = run_policy_engine()
    return {
        "report": report.to_dict(),
        "verdict": report.verdict,
        "passes": report.verdict == "PASS",
    }


def cmd_policy() -> int:
    report = run_policy_engine()
    print(report.render_markdown())
    print(f"policy verdict: {report.verdict}")
    return 0 if report.verdict == "PASS" else 1


def cmd_policy_json() -> int:
    report = run_policy_engine()
    print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    return 0 if report.verdict == "PASS" else 1


def write_policy_baseline() -> int:
    """Acknowledge the CURRENT findings as known debt (ADR-027 waivers)."""
    report = run_policy_engine()
    from app.domain_platform.policies import PolicySeverity

    waivers: list[dict[str, Any]] = []
    for result in report.results:
        for finding in result.findings:
            if finding.severity in (
                PolicySeverity.MINOR,
                PolicySeverity.MAJOR,
                PolicySeverity.CRITICAL,
            ):
                waivers.append(
                    {
                        "policy": result.policy,
                        "code": finding.code,
                        "path": finding.path,
                        "rationale": "acknowledged architecture debt (ADR-027)",
                    }
                )
    POLICY_BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "note": "Acknowledged Architecture Policy Engine findings (ADR-027). "
                "Do not grow this list.",
        "waivers": waivers,
    }
    POLICY_BASELINE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(
        f"policy baseline written: {POLICY_BASELINE_PATH} "
        f"({len(waivers)} finding(s) acknowledged)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(cmd_policy())
