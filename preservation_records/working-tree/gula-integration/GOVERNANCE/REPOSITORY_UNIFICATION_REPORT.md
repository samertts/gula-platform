# Repository Unification Report (Interim — Phase 2 RECONCILE)

**Program:** GULA Stable v1.0.0
**Goal:** Converge the local lineage (`remediate-security-001`, `f478676b`, 858 commits) with `origin/main` (`2827c1ff`) into one maintainable codebase without losing valid work, without rewriting history, and without touching production data.
**Branch:** `integration/gula-unification-v1` (base `origin/main`). Main repo and `main` branch untouched.
**Date:** 2026-11-15
**Status:** **IN PROGRESS — reconciliation complete; backend code merge in progress; workflow integration (CR-1) executed and verified; database round trip repaired and verified; full backend suite PASS; frontend suites and existing-DB rehearsal not run; not certified.**

## 1. Safety posture

- `main` is protected; no commit has been made to it. All work is on `integration/gula-unification-v1` in the `gula-integration` worktree.
- Full recovery backup at `$HOME/GULA_RECOVERY_BACKUP_20261114_190243` (bundle + patches, checksums verified).
- Only disposable databases (`gula_unify_scratch`, `gula_unify_tail`, `gula_unify_full`, `gula_unify_downgrade`) were written (container `gula-postgres`, effective address `172.18.0.3:5432`). The live `gula` database was never touched.
- All reconciliation/repair changes remain uncommitted on the integration branch for review; no production branch was modified.
- Unrelated histories were confirmed (no merge base); no history was rewritten.

## 2. What was reconciled

| Dimension | Result |
|---|---|
| Repositories | Local 7,527 files vs origin/main 6,465; rename-aware diff 6,329 paths, 6,991 raw rows |
| Migrations | Local 57 vs remote 101 revisions; 50 common, 51 remote-only, 7 local-only; 8 diverged files adjudicated |
| Workspace collision | Decided: remote architecture canonical; local workspace/citizen-verification tables retired; 3 unique tables forwarded |
| Magic-number/index drift | 15 authorization indexes restored; 200 FK indexes preserved |
| Backend code | 1,102 M / 338 remote-only / 233 local-only — inventoried by subsystem |
| Security package | 158 local-only files, 0 runtime imports; coverage mapped module-by-module |
| Governance/tooling | `.ai`, `.opencode`, `.omm`, `.agents`, 204 script files inventoried for preservation |

## 3. Deliverables produced

| Document | Purpose |
|---|---|
| `GOVERNANCE/MIGRATION_RECONCILIATION_MATRIX.md` | Per-file migration adjudication + workspace decision + forward plan |
| `GOVERNANCE/DATABASE_COMPATIBILITY_REPORT.md` | Forward migrations, validation evidence, NR-003 fix, NR-009 blocker, risk analysis |
| `GOVERNANCE/CODE_RECONCILIATION_INVENTORY.md` | Backend/frontend/scripts merge inventory + high-risk conflicts |
| `GOVERNANCE/LOCAL_FEATURES_PRESERVATION.md` | Every local-only capability and its preservation method |
| `GOVERNANCE/SECURITY_COVERAGE_MATRIX.md` | Local security modules vs remote runtime controls + carry-forward list |
| `GOVERNANCE/UNIFICATION_BLOCKERS.md` | Consolidated blocker register + critical path |
| `GOVERNANCE/evidence/*` | Machine-readable matrices, index-target proof, tail harness results |
| `backend/migrations/versions/20261114_0001..0006_*.py` | Forward-only migration chain |

## 4. Verification evidence

| Check | Result |
|---|---|
| Migration graph (107 revisions) | **PASS** — single head `20261114_0006`, 0 missing, 0 cycles |
| Forward migration compile | **PASS** |
| Fresh `upgrade 20260815_0022` (disposable PG16) | **PASS** — 405 tables |
| Fresh `upgrade 20260815_0023` | **PASS** after NR-003 identity fix |
| Fresh `upgrade head` | **PASS** — 433 tables, `alembic_version = 20261114_0006` (NR-009 conditional FK) |
| `downgrade base` → `upgrade head` | **PASS** after NR-010 repairs — 3 ambiguous reference tables intentionally remain (`DATABASE_COMPATIBILITY_REPORT.md` §4.3/§9.7) |
| Isolated tail (upgrade → reverse downgrade → re-upgrade) | **PASS** — 13/13 tables, 5/5 spot indexes, widening verified |
| 200 FK-index migration | **STATIC PASS** (all 108 target tables present) |
| Backend code merge | **IN PROGRESS** — 7 subsystems ported and tested (§4.1); service extractions/tests remain |
| Merged-feature tests | **402 PASS** (domain 71, PDF 13, professional 12, communication 198, Telegram 98, workflow 10); search-service scaffold 1 PASS / 1 env-only failure |
| Full backend suite | **PASS** — 3135 passed, 27 skipped, 0 failed; 577.65s; exit 0 (`/tmp/opencode/full_suite_integration_2.log`) |
| Ruff (scoped to changed files) | **0 findings introduced** — 37 remaining: 20 capability-pattern baseline (E402/N801/N999) + 17 pre-existing in untouched lines; 4 introduced findings fixed |
| Mypy (scoped: workflows, domain_platform, communication) | **NOT CLEAN** — 71 pre-existing errors in ported local modules (32 domain_platform, 35 communication, 4 workflows); `id=...` is the NIAM placeholder resolved by `_ensure_identity_id` |
| Security certification | **NOT CERTIFIED** |

### 4.1 Backend code merge progress (uncommitted)

| Subsystem | Status | Verification |
|---|---|---|
| `workflows` (CR-1) | **EXECUTED / VERIFIED** — remote `national/workflow_runtime`, duplicate `identity/workflows/{engine,models}`, `platform/workflow.py` archived; canonical engine/routes/security/database wired | `create_app()` boot PASS (125 routes); 10/10 regression tests; single mount; 401 unauthenticated; SQLite DB integration PASS |
| Preserved local workflow tests | **UPDATED + PASS** — imports re-pointed from archived `app.identity.workflows.models` to canonical `app.workflows.models` | 3/3 `TestWorkflowModels` tests pass in full suite |
| Blood-bank clinical transition | **FIXED + PASS** — added `verified -> in_progress` to the canonical transition map | Transfusion regression test passes; full suite PASS |
| `search_service` | **PORTED** — capability package + router; document-intelligence consumer re-pointed; duplicates removed | imports OK (5 routes); scaffold 1 PASS / 1 env-only fail (kernel not initialized) |
| `pdf_generator` (national document PDF) | **PORTED** | 13/13 tests; operation id/summary pinned (OpenAPI-compatible) |
| `domain_platform` + `scripts/domains` | **PORTED** — 19 app files, governance engine, migration already forward-ported | 71/71 tests; 16 routes |
| `professional_registry` | **PORTED** — 5 files; 37 local-only `AuditAction` members unioned; router included once | 12/12 tests; 7 routes |
| `communication` experience + providers | **PORTED** — shared + app trees, model, router; local `shared/circuit_breaker.py` superset adopted; `signxml` installed (declared dependency) | 198/198 communication tests |
| Telegram notifications (`platform`, `notifications`, `shared`) | **PORTED** — remote hardened `platform/routes.py` kept (no port); `send_ntfy` preserved in `shared/notifications` | 98/98 tests |
| Local service extractions (9) | **PARTIAL** — 9 service modules + 9 test files ported; **5 routes delegate** (dashboard, stats, quality_control, metrics, mobile); **4 routes not wired** (admin 1 037 LOC, test_results 731, labs 231, samples 217) and their service twins are imported by no route | unit tests per service |
| Frontend (`frontend-v3`) | **MERGED** (CR-2) — typecheck 0, lint 0, vitest 16 files / 56 tests, build 3.41 s, `npm audit --omit=dev` 0 | `FRONTEND_INTEGRATION_REPORT.md` |

## 5. Risks

1. **MIG-EXISTING** remains NOT VERIFIED: only empty disposable databases were exercised; no upgrade rehearsal from a supported existing snapshot. Downgrade residuals (`facilities`, `organizations`, `national_facilities`) block a clean-schema claim.
2. The backend merge is large; 7 subsystems are ported and the full backend suite passes (3135 passed), but the local service extractions, remaining preserved gates, and frontend merge remain. Silent behaviour change is still possible outside tested scope.
3. Remote and local share 50 migration ids with content differences resolved only semantically; the converged schema has not yet been compared against a real existing database.
4. Ported local modules are not mypy-clean (71 scoped errors) and carry pre-existing ruff findings; no new ruff findings were introduced. These must be baselined or fixed, not masked.
5. CR-2 frontend merge and CR-3 security human review are still open.

## 6. Next actions (critical path)

1. Commit-review the uncommitted merge (workflow, ported subsystems, NR-010 repairs) per Program Director instruction; keep changes uncommitted until approved.
2. Finish backend code merge: local service extractions (9 services), preserved tests, remaining reconciliation items.
3. Rehearse the existing-database upgrade path (MIG-EXISTING) from a supported prior snapshot, then decide the residual-table disposition.
4. Merge `frontend-v3` per CR-2; run `tsc`, ESLint, Vite build, unit tests.
5. Produce the final unification report and request human certification.

## 7. Explicit non-claims

This report does **not** claim repository unification is complete, that the platform is production-ready, or that security/migration safety is certified. AI cannot certify clinical safety, security, migration safety or production readiness (`GOVERNANCE/AI_AGENT_RULES.md`).

---
_Interim report. Update after code merge and full verification._
