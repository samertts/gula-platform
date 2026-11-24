# GULA EXACT APPROVAL & RESOURCE REQUIREMENTS

**Directive:** GULA-OWNER-GATE-2026-11-20 §3D, §6, §7 and §9.6  
**Repository / branch:** `gula-integration` / `integration/gula-unification-v1` · **HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549` · **Date:** 2026-11-20  
**Purpose:** convert every remaining blocker into a bounded, independently approvable request. No request below is granted by this document. Nothing is bundled.

**Status vocabulary (exclusive):** `NOT IMPLEMENTED` · `IMPLEMENTED` · `TESTED` · `INTEGRATED` · `INDEPENDENTLY VERIFIED` · `PRODUCTION READY` · `BLOCKED`

---

## 1. W-017 strict gate fresh re-run (`OD-005`)

**Approval text (exact):**
> *"I authorize exactly one re-run of the W-017 strict 872-test gate under the unchanged 872/872 acceptance threshold, with the trigger recorded in `GOVERNANCE/GECS/CHANGE_CONTROL.md` and `DUPLICATE_PREVENTION.md`, QA Lead as executor, A07 as scope approver, and all artifacts captured under new evidence IDs. No threshold change, no test weakening, no production database, no `create_all()`, no `alembic stamp`."*

| Field | Requirement |
|---|---|
| Approvers (three separate signatures) | **A07** (Backend/API/DB) — scope; **QA Lead** — execution; **Program Director / project owner** — gate re-run and artifact capture (QA_AUDIT A09-004 P1, `:196`; SR-A09-06, `:300`) |
| Documented trigger | New schema-changing evidence — specifically an authorized ADR-A wave and/or NR-011 fix — appended to `GOVERNANCE/GECS/CHANGE_CONTROL.md` and `DUPLICATE_PREVENTION.md`. GECS forbids re-running a completed test without a trigger (`DUPLICATE_PREVENTION.md:32-38,45`) |
| Prior approvals noted, not reused | D-001 and D-003 are recorded as approved 2026-11-17 but **not implemented** (`DECISION_REGISTRY.md:17,19`); D-018 method constraints still hold (`:68`) |
| Exact environment | Disposable PostgreSQL **16.14** clone, revision `20261114_0006`, 433 tables, built **only** by Alembic; `STRICT_DATABASE_URL=<clone>` exported; strict `conftest.py` (PG only, savepoint isolation, no DDL) |
| Exact harness | Reconstruct `/tmp/opencode/strict-w1/` with `conftest.py`, `pytest.ini`, 53 byte-identical test modules; restore/regenerate and verify `sha256_manifest_full.txt` before use |
| Exact command(s) | `STRICT_DATABASE_URL=<clone> pytest tests -q`; then second pass with `--junitxml` (`EXECUTION_LEDGER.md:113-114`) |
| Artifacts to capture | `.exit` code, full log, `strict_run2.xml`, `baseline_sqlite.xml` control, before/after schema fingerprints, classification JSON; new IDs in `EVIDENCE_REGISTRY.md`; E-001…E-003 untouched |
| Known caveat to accept or fix first | Fixture write leak self-poisons 3 audit-chain failures (`W1_CHECKPOINT.md:141-143`) |
| Explicit boundary | No threshold reduction; no test skipped/weakened; no migration or test edited to obtain a pass; no operational DB; no Docker on production network; no PHI; no commit |
| Verification of result | Acceptance remains `872/872` twice with fingerprint delta = approved migrations only (`WORK_REGISTRY.md:40`, `W1_CHECKPOINT.md:179-180`) |
| Reversal | No repository state change; disposable environment destroyed after capture; new evidence is additive |
| Status | `BLOCKED` |

**Known unrecoverable gap:** all raw A09-004 P1 artifacts (`strict_run2.xml`, classification JSON, `.log`, manifest, harness) are absent on this host and in the repository (`GULA_W017_STRICT_GATE_REASSESSMENT.md` §5). The request does **not** ask to fabricate them; it asks to regenerate them under a documented trigger.

---

## 2. Exact-path commits (`OD-002`)

**Four separate approval texts — each independently scoped; one signature cannot cover another workstream.**

| # | Approver | Exact scope | Boundary | Status |
|---|---|---|---|---|
| 2.1 | `WS-1` owner (`AUDIT-POSITIONAL-001` / `SEC-001`) | `backend/app/lims/routes.py` hunks `L1`, `L2` only | No other hunk, no other path, no push/merge | `BLOCKED` |
| 2.2 | `WS-2` owner (`AUDIT-BYPASS-001` / `SEC-014`) | `backend/app/routes/ai.py` hunk `A1` (`log_action` import line), `A5`, `A6` only | `A1` shares a region with `WS-4`'s import — line-level staging required; no push/merge | `BLOCKED` |
| 2.3 | Team C / `WS-3` owner (`AUD-CLIN-001`, `AUD-CLIN-003`, `R-CLIN-003-A`) | `backend/app/lims/routes.py` hunks `L5`, `L6`, `L7` only | No other hunk, no other path, no push/merge | `BLOCKED` |
| 2.4 | `WS-4` owner (`S-09`, `S-12`) | `backend/app/lims/routes.py` hunks `L3`, `L4`; `backend/app/routes/ai.py` hunk `A1` (`require_ai_operator` import line), `A2`, `A3`, `A4` | Individual contributor not named in evidence; sign-off must come from the workstream owner; no push/merge | `BLOCKED` |

**SEC-015 acceptance/commit (`OD-001` → `OD-002` boundary):**
> *"I authorize an exact-path commit of `backend/app/services/audit_service.py`, `backend/tests/unit/test_audit_chain_integrity.py` and `backend/tests/test_compliance_integrity.py` only, after SEC-015 technical acceptance is recorded. No other path, no broad staging, no push, no merge, no deployment."* Approver: engineering owner. Status: `BLOCKED`.

| Field | Requirement |
|---|---|
| Required pre-check before any commit | `git diff --cached -U0` contains only approved hunks; `git diff --check` exit 0; protected MD5s exact; 20 `R100` renames intact; sibling HEAD unchanged |
| Required tests before any commit | Focused suites (13/13 chain, 11/11 positional, 3/3 bypass), related suites, positional-call AST guard; full suite if owner requires |
| Explicit boundary | No broad `git add`, no `git add -A`, no staging of the 264 untracked / 149 modified pre-existing paths, no destructive Git command, no force-push, no PR, no deployment |
| Reversal | One targeted `git revert` per workstream commit; renames and protected files never touched |
| Status | `BLOCKED` (all five approvals absent) |

---

## 3. Migration / DDL work order (`OD-003`, `OD-004`)

| Field | Requirement |
|---|---|
| Approval text (exact) | *"I approve ADR-A (domain-owned registries, all 19 bases visible to Alembic, context-by-context additive reversible revisions with disposable-PG16 upgrade/downgrade/re-upgrade proof, ship/no-ship record for 22 DORMANT and 20 UNUSED tables) and ADR-B option B1 (three reference tables are pre-existing baseline infrastructure excluded from `downgrade base`; one ORM owner for `national_facilities`). No bulk revision, no `create_all()`, no production DDL in this approval."* |
| Approvers | Program Director / Architect (ADR-A); Database owner (ADR-B) — two separate signatures |
| Exact scope | `backend/migrations/env.py` registration of `DocIntelBase`/`InsBase`; one new revision per domain context for the 261 `ACTIVE_REQUIRED` tables; P0 contexts first (51 unregistered-base tables, ≥20-ref tables, patient/claim-critical); ship/no-ship record; ADR-B ownership record |
| Required resources | Disposable PostgreSQL 16 instance; Alembic CLI; per-revision upgrade→downgrade→re-upgrade; schema fingerprint capture; no shared `gula-postgres`; no production connection string |
| Explicit boundary | No bulk baseline revision; no `create_all()`; no `alembic stamp`; no destructive migration; no data backfill from PHI; no deletion of dormant modules; no activation of unfinished functionality; no production DDL |
| Verification | Single Alembic head preserved; each revision independently reversible; strict round-trip proof per context; 354-row matrix updated without overwriting history |
| Reversal | One `git revert` per revision; `downgrade()` tested before merge |
| Status | `BLOCKED` |

---

## 4. Operational / DR drills (`OD-023`)

| Drill | Exact resource | Owner gate | Expected artifact | Status |
|---|---|---|---|---|
| Backup → restore (same + fresh DB) | Disposable PG16 instance isolated from shared services; `pg_dump`/`pg_restore` round-trip | Operations owner | Restore log, checksum comparison, timing | `BLOCKED` |
| PITR + RPO/RTO | PG16 + WAL archive + S3-compatible object store (self-hosted MinIO preferred) | Operations owner | Timed restore record, measured RPO/RTO — numbers recorded, never pre-asserted | `BLOCKED` |
| Failover | Disposable multi-node PG topology | Operations owner | Promotion log, reconnect evidence | `BLOCKED` |
| Redis recovery / outbox drain | Disposable Redis instance in isolation; stop/start; outbox consumer | Operations owner | Drain log, no-loss assertion | `BLOCKED` |
| RabbitMQ recovery | Disposable broker | Operations owner | Requeue/drain log | `BLOCKED` |
| MinIO recovery | Disposable object store | Operations owner | Bucket restore log | `BLOCKED` |
| Clinical-alert availability / network partition | Disposable harness; injected partition; durable outbox + delivery verification | Clinical Safety Owner + Operations owner | Delivery log with partition timeline | `BLOCKED` |
| Device restart / interrupted sync | Durable store required first (`OD-021`) — currently in-memory only | Architecture + Operations owner | Restart/replay record with payload preservation | `BLOCKED` |

**Exact boundary:** no production database, Redis, broker or object store; no real PHI; no simulated result labelled as an operational test; no RPO/RTO number asserted before measurement. **Approval text:** *"I authorize the listed drills in an isolated disposable environment with the named owners, and require new evidence IDs for each result. No production service, real patient data or invented RPO/RTO is authorized."* Status: `BLOCKED`.

---

## 5. CI/CD execution (`OD-024`)

| Group | Exact commands (from `GULA_SECURITY_CI_READINESS_PLAN.md` §3) | Resource | Boundary | Status |
|---|---|---|---|---|
| Safe once a runner is authorized | `python scripts/architecture.py architecture-check`; `ruff check app tests`; `tsc --noEmit && npx vitest run && npx eslint .`; `make validate --fast`; Semgrep (p/default + owasp-top-ten) + bandit; `npm audit` + `pip-audit` | CI runner, backend venv, `frontend-v3` deps, network for dependency audit | No deployment; no threshold change; capture logs | `BLOCKED` |
| Owner-gated | Full backend suite `ENV=test RUNTIME_MODE=test PYTHONPATH=.:.. python -m pytest tests/ -q` | Disposable PG16 + isolated Redis, no concurrent pytest | No production DB/Redis; no PHI | `BLOCKED` |
| Owner-gated | W-017 strict gate (§1 above) | A07 + owner + reconstructed harness | Unchanged 872/872 threshold | `BLOCKED` |
| Owner-gated | Per-workflow dry-run (`act` or GitHub runner) | CI runner + owner-managed secrets | No secret exposure; no production credentials | `BLOCKED` |

**Approval text:** *"I authorize execution of the named CI commands on an isolated runner with owner-managed secrets, with logs captured as new evidence. Workflow presence is not accepted as a pass, and no deployment is authorized."* Approver: DevOps owner. Status: `BLOCKED`.

---

## 6. Release authorization (`OD-025`)

**Approval text (exact):**
> *"I authorize HOLD to become GO and Stable v1.0.0 to be declared only after release criteria 2, 3, 4, 6, 8, 10, 11, 13, 15, 16 and 17 are individually cleared with recorded evidence and the D-020/D-021 verdicts are signed. Until then HOLD stands."*

| Field | Requirement |
|---|---|
| Approver | Program Director (single, non-delegable release decision) |
| Boundary | No self-declaration; no `PRODUCTION READY` by engineering; no deployment, no merge to protected branch, no version tag, no RC packet until criteria clear |
| Current status | `BLOCKED` — 10 criteria `BLOCKED`, 1 `NOT IMPLEMENTED`; `production_ready_items = 0` |
| Reversal | HOLD can be re-entered by owner decision at any time; historical evidence retained |

---

## 7. Universal boundary (applies to all six requests)

No modification to `gula-platform`; no destructive Git operation; no broad staging; no commit unless separately granted in §2; no push, merge, PR or deployment; no production DB/Redis/broker/object store; no real PHI; no secrets; no destructive migration; no `alembic stamp`; no `create_all()` masking; no deletion of failing tests; no reduction of security or coverage standards; no threshold change; no simulated drill presented as a real operational test; no self-awarded `INDEPENDENTLY VERIFIED` or `PRODUCTION READY`.

## 8. Non-claims

No approval in this document is granted. No resource was provisioned. No command above was executed under this directive. Standing decision **HOLD**; Stable v1.0.0 **NOT declared**; `production_ready_items = 0`.
