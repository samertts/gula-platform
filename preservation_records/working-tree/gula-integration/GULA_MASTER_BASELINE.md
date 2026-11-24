# GULA MASTER BASELINE — WAVE 0

**Program:** Supreme Autonomous Completion & National Release Directive (2026-11-19)
**Repository:** `gula-integration` (target of this directive)
**Baseline method:** fresh, read-only examination on 2026-11-19. Prior checkpoints and reports were treated as *claims to be verified*, not as proof of current state.
**Status legend (exclusive):** `IMPLEMENTED` · `TESTED` · `INTEGRATED` · `INDEPENDENTLY VERIFIED` · `PRODUCTION READY` · `BLOCKED` · `NOT IMPLEMENTED`
**Release position:** **HOLD**. GULA Stable v1.0.0 is **NOT declared**. No `PRODUCTION READY` awarded anywhere in this baseline.

> **GULA-OWNER-GATE-2026-11-20 (additive cross-reference):** This baseline is preserved unchanged. Owner decisions `OD-001`…`OD-025` are prepared and `BLOCKED` in `GULA_OWNER_DECISION_REGISTER.md`; no owner-gated action was executed. Fresh baseline invariants (MD5s, 20 `R100` renames, sibling HEAD, HEAD `2206654`, `diff --check` 0) re-verified. HOLD stands.

---

## 1. Repository identity and protection state

| Item | Observed | Status |
|---|---|---|
| Worktree | `/home/samertts/workspace/projects/gula-integration` | `IMPLEMENTED` |
| Branch | `integration/gula-unification-v1` | `IMPLEMENTED` |
| HEAD | `2206654dc713ea2de8c564a3207dfe05fde23549` | `IMPLEMENTED` |
| Origin | `ssh://git@ssh.github.com:443/samertts/gula-platform.git` | `IMPLEMENTED` |
| Sibling repo (must not be modified) | `gula-platform` @ `f478676b6fc375338648dde46fbf076c015a3f91`, branch `remediate-security-001` | `IMPLEMENTED` (untouched) |
| Tracked files | 6,514 | `IMPLEMENTED` |
| Staged entries | 20 × `R100` renames, 0 content changes (`archive/legacy/workflow_runtime/`) | `IMPLEMENTED` (preserved) |
| Unstaged modified | 149 | `BLOCKED` for broad commit (mixed provenance — see §7) |
| Untracked | 264 | `BLOCKED` for broad commit (mixed provenance — see §7) |
| Commits / pushes / PRs / merges / deploys this directive | none | `IMPLEMENTED` (none performed) |

Protected MD5s re-verified by independent read-only agent (exact match to registry):

| Protected file | MD5 | Status |
|---|---|---|
| `GOVERNANCE/FINAL_DECISION.md` | `effdfeaf10234678d83b2668c4489552` | `IMPLEMENTED` (unchanged) |
| `GOVERNANCE/IDENTITY_REMEDIATION/MPI_FINAL_INDEPENDENT_AUDIT.md` | `1a02c01563c93b07a7cdb92c0462bf36` | `IMPLEMENTED` (unchanged) |
| `GOVERNANCE/IDENTITY_REMEDIATION/MPI_INDEPENDENT_AUDIT_FINDINGS.md` | `ea3969d09aaf7b0b28a065838b44a594` | `IMPLEMENTED` (unchanged) |

`status_registry.json → production_ready_items = 0` (`IMPLEMENTED`, unchanged).

---

## 2. Scale of the codebase (observed)

| Surface | Evidence | Status |
|---|---|---|
| Top-level directories | 56 (see `GULA_COMPONENT_INVENTORY.md`) | `IMPLEMENTED` |
| Backend Python modules (`backend/app/**/*.py`) | 2,045 | `IMPLEMENTED` |
| Backend route modules (`backend/app/routes/*.py`) | 63 (62 define `APIRouter`) | `IMPLEMENTED` |
| Application services (`backend/app/services/*.py`) | 46 top-level; 63 recursive | `IMPLEMENTED` |
| ORM model modules (`backend/app/**/models.py`) | 64 | `IMPLEMENTED` |
| Backend test files | 342 `test_*.py` under `backend/tests/`; 384 anywhere under `backend/` | `IMPLEMENTED` |
| Alembic revision modules | 111; **exactly 1 head** `20261119_0003`; 4 merge revisions; 0 duplicate revision IDs | `IMPLEMENTED` |
| ORM bases registered in `backend/migrations/env.py` | 17 (Base + 16 bounded-context bases) | `IMPLEMENTED` |
| Application factory | `backend/app/factory.py:1097` `create_app()` with 91 `include_router(...)` calls | `IMPLEMENTED` |
| Live OpenAPI (documented 2026-11-17) | 2,116 operations / 1,804 paths; 2,060 secured / 56 without declared security | `IMPLEMENTED` (documented figure) |
| CI workflows | 33 under `.github/workflows/` | `IMPLEMENTED` |
| ADR documents | 57 across the repo | `IMPLEMENTED` |
| Frontend unit/component test files | 15 under `frontend-v3/src/` | `IMPLEMENTED` |
| Frontend Playwright e2e specs | 13 under `frontend-v3/e2e/` | `IMPLEMENTED` |
| Contract export | `contracts/export/openapi.json` | `IMPLEMENTED` |

Note: `backend/.venv` does **not** exist in this worktree. Inventory/migration parsing used the Python 3.12 interpreter at `/home/samertts/workspace/projects/gula-platform/backend/.venv/bin/python`.

---

## 3. Migration and database integrity baseline

| Item | Evidence | Status |
|---|---|---|
| Care-continuum closure migration | `backend/migrations/versions/20261119_0003_care_continuum_closure.py` — 62 tables (45 `cc_*` + 17 `national_*`), 24 enum types, 44 `postgresql.ENUM(create_type=False)` columns | `IMPLEMENTED` |
| Its regression test | `backend/tests/migrations/test_care_continuum_closure_migration.py` — 7 static + 1 opt-in disposable-DB lifecycle test | `TESTED` |
| Disposable-DB full-chain e2e | upgrade → downgrade → re-upgrade: 435 → 497 → 435 → 497 target tables; 0 errors | `TESTED` |
| Team C independent review (engineering scope) | first `BLOCKED` on one P1 (`use_alter` FK silently omitted); after fix `INDEPENDENTLY VERIFIED` (A–G PASS, falsification proof) | `INDEPENDENTLY VERIFIED` |
| Migration coverage (documented) | 407/833 ORM tables (48.9%) covered; 426 missing; `ins_*` 30/30 unmigrated | `BLOCKED` |
| W-017 strict-schema gate (documented) | 753 passed / 119 failed on Alembic-only PG16 clone vs 872/872 under SQLite `create_all()` — figures preserved; `GULA_W017_STRICT_GATE_REASSESSMENT.md` reconciles 119 (failure) and 753 (pass) as the SAME 2026-11-17 run, both historical, fresh rerun `BLOCKED` (A07/owner + raw artifact absent) | `BLOCKED` |
| F-085 unregistered bases (documented) | `DocIntelBase` (21 classes), `InsBase` (30 classes) | `BLOCKED` |
| Production DB DDL / `alembic stamp` / `create_all()` masking | prohibited by directive; none performed | `IMPLEMENTED` (none performed) |

---

## 4. Test and gate baseline

| Item | Evidence | Status |
|---|---|---|
| Authoritative post-fix full suite | `5124 passed / 28 skipped / 0 failed, EXIT=0 (15m32s)` — `/tmp/opencode/final_tree_full_suite_p1_fixed.log` | `TESTED` |
| Authoritative full suite (post AUDIT-BYPASS-001 + benchmark fix) | `5138 passed / 28 skipped / 0 failed, EXIT=0 (12m13s)`, 203 pre-existing warnings, zero `FAILED`/`ERROR` — `/tmp/opencode/auditfix_full_suite_clean.log` (no concurrent pytest on this 2-CPU host) | `TESTED` |
| Care-continuum DB lifecycle | `1 passed (188s)` — `/tmp/opencode/cc_regression_p1_fixed.log` | `TESTED` |
| CI run in this session | not performed | `BLOCKED` |
| Local lint / syntax gates on scoped work | Ruff clean; `py_compile` OK | `TESTED` |

---

## 5. Governance baseline (as declared at reviewed HEAD)

| Item | Evidence | Status |
|---|---|---|
| Standing release decision | `GOVERNANCE/FINAL_DECISION.md:13` and `:361`: **HOLD — do not release to production** | `IMPLEMENTED` (decision recorded) |
| Security certification | `GOVERNANCE/FINAL_DECISION.md:46`: **NOT CERTIFIED** | `BLOCKED` |
| Acceptance criteria tally (18) | 1 `INDEPENDENTLY VERIFIED`, 2 `IMPLEMENTED`, 6 `TESTED`, 7 `BLOCKED`, 2 `NOT IMPLEMENTED` | `IMPLEMENTED` (recorded) |
| Owner-gated decisions | D-005…D-012 (ADR-C…J), D-020, D-021, MP-001, ODR-001…004 — all `PENDING_APPROVAL` / `BLOCKED` | `BLOCKED` |
| W1 decisions | D-001…D-004 recorded APPROVED by project owner 2026-11-17 in `GOVERNANCE/GECS/DECISION_REGISTRY.md:17-20` | `IMPLEMENTED` (recorded) |
| Official MoH / regulator / clinical / legal approval | no documentary evidence found | `NOT IMPLEMENTED` |

---

## 6. Fresh finding this baseline — P1 audit-integrity regression

| Field | Value |
|---|---|
| Finding ID | `AUDIT-POSITIONAL-001` |
| Component | Canonical audit service `backend/app/services/audit_service.py:184-193` and its positional callers |
| Evidence | Commit `aae20c89` (2026-08-13) inserted `lab_id` immediately before `details` in `log_action`'s signature. AST scan finds 50 total >2-positional calls across 8 files (49 mis-mapped + 1 canonical 8-arg call at `backend/app/lims/routes.py:985`, converted to keywords for a strict guard), authored 2026-07-14…16, before the signature change. All import the same canonical function. |
| Impact | Under the current signature, entity IDs land in `resource_type`, lab IDs land in `user_role`, and detail strings/dicts land in `lab_id`. The immutable, tamper-evident audit log is a protected GULA feature. |
| Affected files | `backend/app/nhdw/services.py` (24), `backend/app/nursing/coordination.py` (8), `backend/app/services/hospital_service.py` (5), `backend/app/lims/services.py` (4), `backend/app/nursing/services.py` (3), `backend/app/nhdw/offline.py` (2), `backend/app/nursing/medication.py` (2), `backend/app/lims/routes.py` (2) |
| Status (post-fix) | `INDEPENDENTLY VERIFIED` (engineering scope) — 50/50 calls converted to keyword arguments; fresh-context reviewer PASS on all 7 checks; focused 11/11; related 38/38; full suite 5134/28/1 (sole failure flaky CPU benchmark, isolated re-run passed). Commit `BLOCKED` by mixed provenance in `lims/routes.py`. Evidence: `GULA_AUDIT_POSITIONAL_FIX_REPORT.md`. |
| Detail note | Preserved at `/tmp/opencode/finding_audit_log_action_positional_regression.md` |

### 6b. Second fresh finding this session — P1 audit bypass (`AUDIT-BYPASS-001`)

| Field | Value |
|---|---|
| Finding ID | `AUDIT-BYPASS-001` (distinct from `AUDIT-POSITIONAL-001`) |
| Component | `backend/app/routes/ai.py::_emit_critical_alert` and canonical `backend/app/services/audit_service.py` |
| Evidence | AST/grep inventory of all audit write pathways. `_emit_critical_alert` (blame 2026-07-04) constructed `AuditLog(...)` directly; `AuditLog.chain_hash` has no default and `verify_audit_chain()` skips NULL-chain rows, so critical-result alerts were outside the tamper-evident chain. |
| Impact | Unchained, unverifiable audit records for critical clinical alerts; weakened non-repudiation and provenance for the most safety-relevant events. |
| Status (post-fix) | `INDEPENDENTLY VERIFIED` (engineering scope) — routed via canonical `log_action`; fresh-context reviewer verdict `INDEPENDENTLY VERIFIED (engineering scope)` (session `ses_e0ad74e7affewsQeqX0OxMTMvS`); focused 3/3, related 161/161; zero direct `AuditLog(...)` in any route module. Commit `BLOCKED` by mixed provenance in `routes/ai.py`. Evidence: `GULA_AUDIT_BYPASS_FIX_REPORT.md`. |
| Residual | SEC-015 SQLite multi-row chain linkage (regression of `2cdc5479` by `f0b021bd3`) FIXED and `INDEPENDENTLY VERIFIED` (engineering scope; `GULA_SEC015_AUDIT_CHAIN_REMEDIATION_REPORT.md`), commit `BLOCKED` (no-commit authority); production-PG path never affected. Shared-audit schema mismatch dormant `BLOCKED`. |

---

## 7. Known contradictions in the declared record (reported, not adjudicated)

These are recorded as *evidence inconsistencies*, not silently resolved, because several touch owner-gated decisions:

| Topic | Conflicting locations | Status |
|---|---|---|
| NR-011 | `FINAL_DECISION.md:168` OPEN vs `FINAL_ACCEPTANCE_REPORT.md:28` resolved in code (19/19 tests) vs `GOVERNANCE/IDENTITY_REMEDIATION/DATABASE_MIGRATION_READINESS.md:15` OPEN — not authorized | `BLOCKED` |
| ADR-A / D-001 | `ADR_DECISION_REQUEST.md:3,199,247` PENDING vs `DECISION_REGISTRY.md:17-20` APPROVED 2026-11-17 vs `status_registry.json:282-289` BLOCKED | `BLOCKED` |
| `hospital_*` unmigrated count | 12 (`RESUMPTION_STATUS.md:109-116`) vs 13 (`FINAL_REMEDIATION_AND_RELEASE_REPORT.md:116-119`) | `BLOCKED` |
| Full-suite count | 5124 authoritative vs 5117 in `FINAL_ACCEPTANCE_REPORT.md:57-58` / `MASTER_EXECUTION_STATUS.md:97,138,154`; registry still 4945 | `BLOCKED` |
| MIG-EXISTING | BLOCKED / NOT VERIFIED vs "NOT blocked" vs PARTIAL / NOT MET | `BLOCKED` |
| Rollback decision | "not a recorded decision" vs D-004 APPROVED | `BLOCKED` |
| HOLD line reference | lines 13 & 361 vs `RESUMPTION_STATUS.md:156` lines 13 & 40 | `IMPLEMENTED` (substantive HOLD unchanged) |

---

## 8. Scope boundaries of this baseline

- No production DB, production Redis, DDL, destructive migration, `alembic stamp`, or `create_all()` masking — `IMPLEMENTED` (none performed).
- No real patient data; synthetic data only — `IMPLEMENTED`.
- No sibling `gula-platform` modification — `IMPLEMENTED`.
- No `git reset --hard`, `git clean -fd`, history rewrite, force-push, `git add .`, `git add -A`, deletion of failing tests, or reduction of security/coverage standards — `IMPLEMENTED` (none performed).
- No merge to main/protected branch and no automatic deployment — `IMPLEMENTED` (none performed).
- Runtime service integration, restore/PITR/RPO/RTO and clinical-alert outage drills — `BLOCKED` (operational resources prohibited by directive).

---

## 9. Next decision

`BLOCKED` — `GULA_COMPLETION_PLAN.md` items (1) and (2) are done: all directive-required status files exist; `AUDIT-POSITIONAL-001` (`GULA_AUDIT_POSITIONAL_FIX_REPORT.md`) and `AUDIT-BYPASS-001` (`GULA_AUDIT_BYPASS_FIX_REPORT.md`) are fixed and `INDEPENDENTLY VERIFIED` (engineering scope). Both commits remain `BLOCKED` pending mixed-provenance sign-off (`lims/routes.py`, `routes/ai.py`). The flaky cosine benchmark fix is `TESTED` (threshold unchanged); the actual clean uncontended full-suite run passed (`5138 passed / 28 skipped / 0 failed, EXIT=0, 12m13s`, no concurrent pytest), confirming the earlier flake was environmental. Next: (3) continue Waves 1–12 in order within safe scope. Release, deployment and owner-gated decisions remain with their authorized owners.
