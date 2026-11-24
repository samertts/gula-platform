# Master Remediation Plan — GULA Stable v1.0.0

**Document:** `MASTER_REMEDIATION_PLAN.md`
**Repository:** `gula-integration`, branch `integration/gula-unification-v1`, HEAD `2206654dc713ea2de8c564a3207dfe05fde23549`
**Date:** 2026-11-19
**Companion:** `MASTER_EXECUTION_STATUS.md` (status/evidence), `FINAL_ACCEPTANCE_REPORT.md` (18 criteria).

This plan distinguishes work already executed from work that is gated. It does **not** authorize
any protected decision change, production claim, commit, push, PR, merge, deploy, or operational
data access.

## 1. Executed and verified at engineering scope

| Item | Remediation | Verification | Status |
|---|---|---|---|
| AUD-SEC-001/002/003, AUD-API-002, AUD-ARCH-003 | Phase 1 control-plane authz, JWT account domain, staged privileged login, OAuth2 token usability, single authz authority | Team C + `4913 passed / 0 failed` | `INDEPENDENTLY VERIFIED` (engineering) |
| AUD-SEC-007, AUD-API-001, AUD-PRV-001, AUD-SEC-004, AUD-PRV-003, AUD-CLIN-003 | Phase 2 Tier A: async actor lock, standards endpoint, NID PHI scoping, Bearer logout revocation, force_create guard, critical flag persistence | Team C + re-verification + `4947 passed / 0 failed` | `INDEPENDENTLY VERIFIED` (engineering) |
| NIAM step-up prerequisite | Own-account MFA evidence, server-side binding, fail-closed, 300s freshness, replay/state/concurrency guards | 37 adversarial tests, final tree 4984/0, gates, Team C 57+ probes | `INDEPENDENTLY VERIFIED` (engineering scope) |

## 2. Active gate — step-up → B4

1. **Done:** authoritative final-tree full-suite result recorded (`/tmp/opencode/step_up_final_full_suite.log`, `4984 passed / 0 failed`).
2. **Done:** fresh-context Team C verdict awarded `INDEPENDENTLY VERIFIED` at engineering scope
   (`GOVERNANCE/ADVERSARIAL_ASSURANCE/INDEPENDENT_VERIFICATION_TEAM_C_STEP_UP.md`).
3. No defect found (57+ probes, zero real bypasses); no re-verification cycle required.
4. Present to owner for explicit step-up approval and B4 authorization. **B4 stays `BLOCKED` until then.**

## 3. Owner-gated remediations (no engineering execution)

| ID | Required decision | Engineering posture |
|---|---|---|
| B1 `AUD-SEC-005` | Per-action patient-route permission/consent map | Not implemented; avoid piecemeal patching |
| B2 `AUD-PRV-002` | Who may break glass; consent wiring policy | Not implemented; fail-closed logging only if authorized |
| B3 `AUD-PRV-005` | Minor/guardian backfill and fail-closed policy | Not implemented; no data mutation |
| B5 `AUD-SEC-008` | Delegation of synthetic Health Core facade to canonical authority | Not implemented — would create second authority |
| B4 `AUD-SEC-006` residual | Cross-account administration model + step-up approval | Not implemented; surface untouched |
| ADR-A / ADR-B | ORM↔migration gap ownership (340 slots / 82 tables / 664 columns), 3 ambiguous tables | No DDL; no `create_all`/`stamp` shortcuts |
| AUD-API-002 / AUD-ARCH-003 | Ratification for any production claim | Engineering verdict alone is insufficient |

## 4. Operational evidence gates (outside safe lane)

- Disposable-DB restore / PITR drill with recorded RPO/RTO (`NOT IMPLEMENTED`).
- Runtime clinical-alert failure drill (broker outage, retry, escalation, DLQ, dedup) without
  claiming practitioner delivery (`BLOCKED`).
- 18-service runtime/integration inventory and frontend build re-run (`NOT IMPLEMENTED` / historical).
- Clean-environment reproducibility, Docker build, CI pipeline (`BLOCKED`).

## 5. Execution rules (binding)

- One owning agent per modification scope; no two agents edit the same file concurrently.
- Small tests after each fix; targeted after each group; full suite after each phase closure.
- No test deletion, skip, or threshold weakening. No `git add .` / `git add -A`; no broad commits.
- Every status bound to a specific command/exit code/report; no generic-green-suite awards.
- Never self-award `INDEPENDENTLY VERIFIED` or `PRODUCTION READY`.
- Re-check invariant table in `MASTER_EXECUTION_STATUS.md` §1 before any sensitive operation.

**Plan decision:** continue only the safe lane (final-suite recording, Team C reconciliation,
scoped failure-mode test coverage). Everything in §3–§4 stays explicitly gated.
