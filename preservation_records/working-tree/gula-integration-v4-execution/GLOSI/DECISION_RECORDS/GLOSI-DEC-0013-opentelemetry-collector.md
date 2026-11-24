# GLOSI-DEC-0013 — OpenTelemetry Collector

**Registry ID:** GLOSI-0013
**Decision ID:** GLOSI-DEC-0013
**Decision:** MONITOR
**Status:** PROPOSED
**Date:** 2026-11-15
**Owner:** GLOSI Program (proposed)
**GULA ADR:** N/A

## 1. Context

Vendor-neutral telemetry collector for traces, metrics, and logs, supporting OTLP and multiple exporters.

GULA domain: **Observability**; candidate component: **Tracing/metrics pipeline**; architecture layer: **Infrastructure / observability**.

Expected benefit: Vendor-neutral telemetry export, local deployment, and reduced lock-in.

## 2. Decision

Proposed status: **MONITOR**. Recorded as an existing baseline dependency; no new integration. Version and deployment evidence remain UNKNOWN.

This is a non-binding research decision. It does not authorize code import, dependency addition, database change, or production use.

## 3. Evidence

- Official source: https://github.com/open-telemetry/opentelemetry-collector
- Last verified version: v0.165.0
- License: Apache-2.0 (review status: NOT_REVIEWED)
- Security review: NOT_REVIEWED
- Tests: registry structural validation and GLOSI quality tests only
- Estimated integration cost: UNKNOWN
- Evidence snapshot: `GLOSI/REPORTS/evidence/phase3_source_verification.json`

Evaluation state: **PARTIAL** with **LOW** confidence. No dimension score or total score has been assigned.

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
| GULA already uses OpenTelemetry SDK; collector deployment/version must be verified separately. | UNKNOWN | UNKNOWN | Complete technical/security/legal review before approval |
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
