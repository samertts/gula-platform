# GULA SECURITY & OPERATIONAL READINESS ASSESSMENT — v2

**Directive:** GULA-OWNER-GATE-2026-11-20 §4.3–§4.4 · **Decision IDs:** `OD-006`–`OD-008`, `OD-023`, `OD-024`, `OD-025`  
**Repository / branch:** `gula-integration` / `integration/gula-unification-v1` · **HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549` · **Date:** 2026-11-20  
**Supersedes for assessment purposes:** `GULA_SECURITY_CI_READINESS_PLAN.md` (2026-11-19), which remains preserved as the original test plan. **Evidence base:** `GULA_SECURITY_AND_RISK_REGISTER.md`, `GULA_SECURITY_CI_READINESS_PLAN.md`, `GULA_SEC015_AUDIT_CHAIN_REMEDIATION_REPORT.md`, `GULA_W017_STRICT_GATE_REASSESSMENT.md`, `GULA_OFFLINE_SYNC_REASSESSMENT.md`.

**Status vocabulary (exclusive):** `NOT IMPLEMENTED` · `IMPLEMENTED` · `TESTED` · `INTEGRATED` · `INDEPENDENTLY VERIFIED` · `PRODUCTION READY` · `BLOCKED`

**Method:** read-only source/report inspection and adversarial-evidence review. **No CI workflow ran, no SAST/DAST/fuzz/load tool ran, no runtime/DR drill was simulated or executed, no DB/Redis/service was contacted, no deployment occurred.** Security certification remains **NOT CERTIFIED** (`GOVERNANCE/FINAL_DECISION.md:46`). HOLD unchanged; no `PRODUCTION READY`.

---

## 1. Security posture — adversarial verification status

### 1.1 Access control and identity surface

| Control | Evidence | Strict status | Boundary / residual |
|---|---|---|---|
| Identity / NIAM authorization probes | `GULA_SECURITY_AND_RISK_REGISTER.md:21` — 13/13 bypass probes, 57+ step-up probes, 10 B4 probes; prior Team C awards | `TESTED` / `INDEPENDENTLY VERIFIED` (named scopes, prior awards) | B4 R-1…R-4, B5 forged-DB-row gap, endpoint residuals R-01…R-11 remain documented |
| Passkeys / TOTP / recovery codes / step-up | Identity suites under `backend/app/identity/*` and `GOVERNANCE/ADVERSARIAL_ASSURANCE/*` (see SEC-006); not individually re-executed or re-awarded in this pass | `TESTED` (scoped, by existing in-tree evidence); fresh independent award `BLOCKED` | No new independent verification commissioned here; no production claim |
| Session lifecycle | `GULA_SECURITY_AND_RISK_REGISTER.md:21` (replay / impersonation probes) | `TESTED` (scoped) | Concurrent-session and workspace-binding behaviour requires fresh review for any new change |
| Tenant isolation | Dedicated suites `test_*tenant_isolation.py`, `test_service_account_scopes.py`, `test_side_door_hardening.py` (`GULA_SECURITY_CI_READINESS_PLAN.md` §2) | `TESTED` (scoped) | Per-service re-verification not performed here |
| Consent / guardian access / break-glass | `gov_break_glass_policies`, `gov_approval_policies`, `gov_canonical_mappings` in ORM matrix; ADR-D/E open | `BLOCKED` | Policy models exist (observational signal) but no release verdict: ADR-D real-principal rule and ADR-E public access model undecided (`OD-015`, `OD-016`) |
| Role/permission matrix | 45 dedicated `test_*.py` auth/rbac/permission/tenant/scope/guard files (`GULA_SECURITY_CI_READINESS_PLAN.md` §2) | `TESTED` (scoped) | Not a programme-wide attack matrix |
| Public / unguarded operations | SEC-004: 56 live OpenAPI operations without declared security (2060 secured / 2116 total) | `BLOCKED` | Critical path: per-route public-by-design vs remediate (`OD-006`) |

### 1.2 Audit integrity chain

| Control | Evidence | Strict status |
|---|---|---|
| Canonical chained writer | 1 writer (`log_action`), 59 callers, 0 direct `AuditLog(...)` writes outside chain (`GULA_AUDIT_ARCHITECTURE_COMPLETENESS_REPORT.md`) | `INDEPENDENTLY VERIFIED` (prior awards, engineering scope) |
| SEC-001 positional-argument regression | 50/50 calls converted to keywords; focused 11/11, related 38/38 | `INDEPENDENTLY VERIFIED` (prior fresh-context award); commit `BLOCKED` (`OD-002`) |
| SEC-014 critical-alert bypass | Direct `AuditLog` → `log_action`; focused 3/3, related 161/161 | `INDEPENDENTLY VERIFIED` (prior fresh-context award); commit `BLOCKED` (`OD-002`) |
| SEC-015 SQLite chain linkage | Pre-insert predecessor read; SQLite write reservation; PG advisory xact lock; focused 13/13; related 73/73; disposable PG16 PASS; full suite `5151 / 28 / 0` | `INDEPENDENTLY VERIFIED` (prior fresh-context award, engineering scope); acceptance `OD-001`, commit `BLOCKED` |
| Tamper detection | Payload/predecessor tamper tests and missing-predecessor boundary detection in the 13-test suite | `TESTED` |
| Known limitations | PG `READ COMMITTED` precondition; pre-commit anchor write (pre-existing); `shared/audit/service.py` schema mismatch separately `BLOCKED` | `BLOCKED` (residual) |
| Full SAST / DAST / fuzz / load matrix | Not executed | `NOT IMPLEMENTED` / `BLOCKED` (tooling + owner) |

### 1.3 Security verdict boundary

Security certification is explicitly **NOT CERTIFIED**. D-020 (`OD-007`) requires a named security lead + Program Director verdict. No finding is reclassified by this assessment; SEC-002/003/004/010/011/012/013 remain open. No `PRODUCTION READY` is awarded.

---

## 2. Operational readiness — assessment, not execution

Every row below is an **assessment of evidence availability**, never a claim that a drill passed. No simulated result is presented as an operational test.

| Capability | Evidence available | Strict status | Exact blocker |
|---|---|---|---|
| CI execution (33 workflows) | Workflow files present; no run this session | `NOT IMPLEMENTED` (execution) / `BLOCKED` | CI runner + DevOps authorization (`OD-024`); presence ≠ success |
| PostgreSQL migration verification (strict gate) | W-017 `753 passed / 119 failed / 0 skipped (872)` historical, `FAILED`; rerun `BLOCKED` | `BLOCKED` | A07 + owner authorization, raw A09-004 artifact absent, harness missing, disposable PG16 (`OD-005`) |
| Backup → restore (same + fresh DB) | `DATABASE_RECOVERY_REPORT.md` historical; not re-validated | `NOT IMPLEMENTED` (this assessment) | Authorized disposable PG16 + operations owner (`OD-023`) |
| PITR / RPO / RTO measurement | No live measurement; no number asserted | `NOT IMPLEMENTED` | WAL archive + S3-compatible store + timed restore, operations owner |
| Failover | No multi-node topology exercised | `NOT IMPLEMENTED` | Disposable multi-node PG, operations owner |
| Redis recovery / outbox drain | In-memory fallback exists in code; no recovery drill | `NOT IMPLEMENTED` | Full disposable compose stack, operations owner |
| RabbitMQ recovery | Not exercised | `NOT IMPLEMENTED` | Disposable broker, operations owner |
| MinIO recovery | Not exercised | `NOT IMPLEMENTED` | Disposable object store, operations owner |
| Clinical-alert availability / device partition | Durable outbox code exists (AUD-CLIN-001); no injected partition | `NOT IMPLEMENTED` | Disposable harness + clinical and operations owner |
| Network interruption / device disconnection | Three in-memory offline engines; synthetic harness only | `NOT IMPLEMENTED` (durable) / `TESTED` (simulation) | Durable store contract (`OD-021`) + operational environment (`OD-023`) |
| Restore-driven release criterion 10 | `FINAL_ACCEPTANCE_REPORT.md:23` | `NOT IMPLEMENTED` | Authorized staging; never invent RPO/RTO |

---

## 3. Exact executable plans (unchanged, to run only when authorized)

The nine CI gates and seven operational drills are specified command-by-command, environment-by-environment and artifact-by-artifact in `GULA_SECURITY_CI_READINESS_PLAN.md` §3–§4. Safe-on-authorization items: constitution gate, ruff, TypeScript/Vitest/ESLint, `make validate --fast`, Semgrep/bandit, dependency audits. Owner-gated items: full backend suite on disposable PG16, W-017 strict gate, workflow execution with secrets, and all DR/availability drills. **None was run in this assessment.**

---

## 4. Adversarial boundaries honoured

- No duplication of central engines: audit, identity, notification and workflow remain canonical; no new engine introduced.
- No security control weakened; no threshold lowered; no failing test deleted; no simulated drill relabelled as real.
- No production DB/Redis, real PHI, secrets, deployment, commit, push, merge or PR.
- No self-award: prior `INDEPENDENTLY VERIFIED` awards are reproduced from their originating reports, not granted here.

---

## 5. Strict status and non-claims

| Object | Status |
|---|---|
| This assessment (documentary artifact) | `IMPLEMENTED` |
| Any CI workflow execution this directive | `NOT IMPLEMENTED` |
| Any runtime/DR drill this directive | `NOT IMPLEMENTED` |
| W-017 fresh strict-gate execution | `BLOCKED` |
| SEC-004 classification | `BLOCKED` |
| Security certification (D-020) | `BLOCKED` |
| Overall operational readiness | `NOT IMPLEMENTED` / `BLOCKED` |

No `PRODUCTION READY`. No release, deployment or operational claim. Standing decision **HOLD**; Stable v1.0.0 **NOT declared**; `production_ready_items = 0`.
