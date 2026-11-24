#!/usr/bin/env python3
"""Generate one Markdown decision record per registry entry (stdlib only)."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "DECISION_RECORDS"
DATE = "2026-11-15"


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def record_markdown(item: dict) -> str:
    identity = item["identity"]
    technical = item["technical"]
    legal = item["legal"]
    security = item["security"]
    gula = item["gula"]
    decision = item["decision"]
    evaluation = item["evaluation"]
    rid = identity["registry_id"]
    did = decision["decision_id"]
    return f"""# {did} — {identity["name"]}

**Registry ID:** {rid}
**Decision ID:** {did}
**Decision:** {decision["decision"]}
**Status:** {decision["status"]}
**Date:** {decision["date"]}
**Owner:** GLOSI Program (proposed)
**GULA ADR:** N/A

## 1. Context

{identity["description"]}

GULA domain: **{gula["domain"]}**; candidate component: **{gula["component"]}**; architecture layer: **{gula["architecture_layer"]}**.

Expected benefit: {gula["expected_benefits"]}

## 2. Decision

Proposed status: **{decision["decision"]}**. {decision["rationale"]}

This is a non-binding research decision. It does not authorize code import, dependency addition, database change, or production use.

## 3. Evidence

- Official source: {identity["official_url"]}
- Last verified version: {technical["latest_verified_version"]}
- License: {legal["license"]} (review status: {legal["review_status"]})
- Security review: {security["security_review_status"]}
- Tests: registry structural validation and GLOSI quality tests only
- Estimated integration cost: {gula["estimated_integration_cost"]}
- Evidence snapshot: `GLOSI/REPORTS/evidence/phase3_source_verification.json`

Evaluation state: **{evaluation["status"]}** with **{evaluation["confidence"]}** confidence. No dimension score or total score has been assigned.

## 4. Conditions

- No adoption until a COMPLETE evaluation exists.
- Named technical, security, and legal reviewers must complete review.
- A GULA ADR is required before any approved adoption or integration.
- Unknown or incompatible licensing blocks adoption.
- A critical security finding blocks adoption regardless of score.
- The component must remain replaceable and self-hostable.

## 5. Alternatives Considered

- Maintain the current GULA status quo.
- Re-implement a narrower capability internally.
- Defer the source to a later research batch.

Alternatives have not been formally scored; this record only preserves the proposed study/monitor decision.

## 6. Risks and Mitigation

| Risk | Likelihood | Impact | Control |
|---|---|---|---|
| {gula["operational_risks"]} | UNKNOWN | UNKNOWN | Complete technical/security/legal review before approval |
| Unverified license obligations | UNKNOWN | High | Legal review; no adoption while license is unknown or unverified |
| Hidden security defects | UNKNOWN | High | CVE/SBOM review and security testing |
| Maintenance or abandonment | UNKNOWN | Medium | Monitor releases and `pushed_at`; keep replacement path |

## 7. Rollback

The decision is non-binding and has no runtime effect. It can be withdrawn by updating the registry decision status and superseding this record; no GULA rollback is required.

## 8. Reviewers

| Role | Name | Date | Result |
|---|---|---|---|
| Technical | UNASSIGNED | — | NOT REVIEWED |
| Security | UNASSIGNED | — | NOT REVIEWED |
| Legal | UNASSIGNED | — | NOT REVIEWED |
| Clinical Safety (if applicable) | UNASSIGNED | — | NOT REVIEWED |

## 9. References

- `GLOSI/REGISTRY/registry.json`
- `GLOSI/REPORTS/PHASE_3_INITIAL_RESEARCH_BATCH_1.md`
- `GLOSI/SECURITY_AND_LICENSE_POLICY.md`
- `GLOSI/INTEGRATION_POLICY.md`
- `GLOSI/DECISION_RECORDS/README.md`
"""


def main() -> None:
    registry = json.loads((ROOT / "REGISTRY" / "registry.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    for item in registry["records"]:
        path = OUT / f"{item['decision']['decision_id']}-{_slug(item['identity']['name'])}.md"
        path.write_text(record_markdown(item), encoding="utf-8")
    print(f"wrote {len(registry['records'])} decision records to {OUT}")  # noqa: T201


if __name__ == "__main__":
    main()
