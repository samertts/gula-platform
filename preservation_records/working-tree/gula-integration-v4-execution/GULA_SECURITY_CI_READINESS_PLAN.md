# GULA Security & CI Operational Readiness — Precise Test Plan

**Directive:** GULA-PBR-2026-11-19, §10 (Priority P2 — security/CI precise test plans)  \n**Repository:** `gula-integration` · **Branch:** `integration/gula-unification-v1`  \n**HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549` · **Date:** 2026-11-19  \n**Method:** read-only source/workflow inspection. **No CI workflow was executed, no runtime drill, no SAST/DAST/fuzz/load, no deployment.** This document is a *plan*, not a result.

---

## 1. Why this is a plan, not a result

This session is explicitly prohibited from CI execution, deployment, production/runtime operations and invented results. The 32 workflows present in `.github/workflows/` are **configuration evidence only**; workflow presence ≠ successful run. No PASS/FAIL is asserted for any workflow. Status is `NOT IMPLEMENTED` (execution) / `BLOCKED` (CI runner + owner authorization).

---

## 2. Access-control security — current read-only posture

| Control | Evidence | Status |
|---|---|---|
| Access-control test coverage | 45 dedicated `test_*.py` files (auth/rbac/permission/tenant/scope/guard) in `backend/tests` | `TESTED` (in-tree, scoped) |
| Canonical audit chain | 1 writer / 59 callers / 0 direct writes outside chain (`GULA_AUDIT_ARCHITECTURE_COMPLETENESS_REPORT.md`) | `INDEPENDENTLY VERIFIED` (prior awards, engineering scope) |
| SEC-004 unguarded operations | 56 live OpenAPI operations without declared security, documented 2026-11-17 | `BLOCKED` (per-route public-by-design vs remediate decision) |
| Role/tenant isolation | Dedicated suites (`test_*tenant_isolation.py`, `test_service_account_scopes.py`, `test_side_door_hardening.py`) exist | `TESTED` (scoped) |
| SAST/DAST/fuzz/load matrix | not executed this session | `NOT IMPLEMENTED` |

**SEC-004 remains the critical path.** It is a classification decision (public-by-design vs protect) requiring security-lead / owner sign-off; no autonomous change to those 56 operations is authorized.

---

## 3. Precise CI test plan (to execute only when authorized)

Each item states the exact command, required environment, expected artifact and owner gate. None was run.

| # | Gate | Command | Environment | Expected artifact | Owner gate |
|---|---|---|---|---|---|
| 1 | Constitution architecture gate | `python scripts/architecture.py architecture-check` | repo checkout, no DB | PASS report: 25 ack / 0 new | — (repo gate, safe when authorized) |
| 2 | Backend lint | `ruff check app tests` | backend venv | 379 baseline violations, no new | — |
| 3 | Frontend type/lint/test | `tsc --noEmit && npx vitest run && npx eslint .` | `frontend-v3` with deps | 0 TS errors, 122 vitest pass, 0 eslint errors | — |
| 4 | Backend full suite | `ENV=test RUNTIME_MODE=test PYTHONPATH=.:.. python -m pytest tests/ -q` | disposable PG16 + isolated Redis | clean 5166-collected run, no concurrent pytest | CI runner |
| 5 | Quality gate | `make validate --fast` | full checkout | regression gate vs baseline (no new failures) | — |
| 6 | Security static analysis | Semgrep (p/default + owasp-top-ten) + bandit | SAST tooling | clean on changed scope | security lead |
| 7 | Dependency audit | `npm audit` + `pip-audit` | network-enabled runner | 0 high/critical | security lead |
| 8 | W-017 strict gate | `STRICT_DATABASE_URL=<disposable PG16 clone> pytest tests -q` (872 tests, strict no-DDL conftest) | **A07/owner authorization + reconstructed `/tmp/opencode/strict-w1/` harness** | 872/872 + unchanged `sha256_manifest_full.txt` | A07 + owner (see `GULA_W017_STRICT_GATE_REASSESSMENT.md`) |
| 9 | Workflow dry-run | `act` or GitHub runner, per workflow | CI runner + secrets (owner-managed) | per-job logs | CI/DevOps owner |

Items 1–3, 5–7 are safe engineering gates once a runner is authorized. Items 4, 8, 9 require disposable PG16 / owner authorization / secrets and are `BLOCKED` in this session.

---

## 4. Precise operational/DR test plan (to execute only when authorized)

| Drill | Command / method | Required environment | Owner gate |
|---|---|---|---|
| DB backup → restore (same + fresh DB) | pg_dump/pg_restore round-trip on disposable PG16 | isolated PG16 clone | operations owner |
| PITR / RPO / RTO measurement | WAL archive replay, timed restore | PG16 + WAL archive + S3-compatible store | operations owner |
| Failover | promote standby in disposable topology | multi-node PG | operations owner |
| Redis / RabbitMQ / MinIO recovery | stop/start disposable services, verify outbox drain | full compose stack | operations owner |
| Clinical-alert outage / device partition | inject partition in disposable harness, verify durable outbox + alert delivery | disposable harness | clinical + operations owner |
| Offline device restart / interrupted sync | restart harness after mid-sync interruption | durable store (currently in-memory — see `GULA_OFFLINE_SYNC_REASSESSMENT.md`) | architecture + operations owner |

No drill was executed; no RPO/RTO number is asserted. Prior historical DR evidence (`DISASTER_RECOVERY_REPORT.md`) is preserved but not re-validated here.

---

## 5. Strict status and non-claims

| Item | Status |
|---|---|
| CI/operational test plans defined | `IMPLEMENTED` (planning only) |
| Any CI workflow execution this session | `NOT IMPLEMENTED` |
| Any runtime/DR drill this session | `NOT IMPLEMENTED` |
| W-017 strict gate fresh execution | `BLOCKED` (A07/owner + harness + PG16) |
| SEC-004 classification | `BLOCKED` (security-lead/owner decision) |

No `PRODUCTION READY`, no `INDEPENDENTLY VERIFIED`, no release/deployment/operational claim. No workflow run, no deployment, no secrets, no production DB/Redis, no PHI, no commit/push/merge/PR. Standing release decision **HOLD**; Stable v1.0.0 **NOT declared**; `production_ready_items = 0`.
