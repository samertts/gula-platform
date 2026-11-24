# GULA OWNER DECISION PACKAGE — A / B / C / D

**Directive:** GULA-OWNER-GATE-2026-11-20 §3 and §9  
**Repository / branch:** `gula-integration` / `integration/gula-unification-v1` · **HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549`  
**Companion:** `GULA_OWNER_DECISION_REGISTER.md` (all decisions, all twelve fields) · **Date:** 2026-11-20  
**Method:** read-only evidence assembly. No code, test, index, configuration or Git state was changed by this package.

> **How to read this package.** Each decision below gives a concise explanation, the evidence, the recommended decision, the consequences of accepting or declining, and the exact implementation scope *after* approval. Nothing here is approved. All four decisions are `BLOCKED`. The standing release decision is **HOLD**; no Stable v1.0.0, no `PRODUCTION READY`.

---

## A. SEC-015 technical acceptance (`OD-001`)

### A.1 Concise explanation

`log_action()` on SQLite read its predecessor hash **after** `db.flush()`, so the newly inserted NULL-hash row became its own predecessor and every row chained to the genesis hash. `verify_audit_chain()` then reported `tampered` on an unmodified chain. The defect was a regression: commit `2cdc5479` had fixed the ordering; `f0b021bd3` restored the bad order; `2fb4fd11` timestamp canonicalization was already correct at HEAD and was preserved. The fix restores the pre-insert predecessor read, adds a zero-row `UPDATE` to acquire SQLite's transaction-scoped write reservation, and uses a PostgreSQL transaction-scoped advisory lock so two writers cannot read the same predecessor. The public `log_action()` contract, sequence handling, timestamp canonicalization, append-only trigger and tamper detection are unchanged.

### A.2 Evidence

| Element | Evidence |
|---|---|
| Root cause / regression | `GULA_SEC015_AUDIT_CHAIN_REMEDIATION_REPORT.md` §2; `git show 2cdc5479`, `git show 2fb4fd11`, `git show f0b021bd3` |
| SQLite serialization | Zero-row `UPDATE audit_logs SET id = id WHERE 1 = 0` before the predecessor read; write lock held to caller commit/rollback; no column values change |
| PostgreSQL serialization | `SELECT pg_advisory_xact_lock(0x47554C4155444954)` ("GULAUDIT", fits signed BIGINT) before predecessor read; released on commit/rollback |
| `READ COMMITTED` precondition | Report §3.1 and reviewer MEDIUM finding — no application caller overrides isolation; documented latent precondition, not introduced by this fix |
| Concurrency | 4-thread / 12-row single unbroken chain in PG16 harness; `PG_VERIFY_RESULT=PASS` (`sec015_pg_verify.log`); structural AST guard in both dialect branches |
| Tamper detection | Tampered-payload and tampered-predecessor tests in the 13-test focused suite; missing-predecessor boundary detection asserted as `broken_ids == [second_id]` after the LOW finding fix |
| Test results | Red `7 failed / 6 passed`; focused `13 passed`; related `73 passed`; PG16 `PASS`; full suite `5151 passed / 28 skipped / 0 failed, EXIT=0` (636.19 s); focused rerun after LOW fix `13 passed` |
| Independent review | Fresh-context reviewer session `ses_e0a984dadffemm3LClZf6oKOPo` — **VERDICT: PASS** (engineering scope); MEDIUM documented, LOW fixed empirically |
| Historical preservation | `5138 passed / 28 skipped / 0 failed, EXIT=0` retained from `/tmp/opencode/auditfix_full_suite_clean.log`; not overwritten |

### A.3 Recommended decision

**Accept the engineering evidence and record SEC-015 as `INDEPENDENTLY VERIFIED (engineering scope)`** — the award was made by the fresh-context reviewer, not by this package. Keep the exact-path commit `BLOCKED` (`OD-002` authority boundary) and keep `HOLD`. Acceptance is warranted because all listed evidence remains valid and the one fixable reviewer finding was corrected with a stronger assertion and a passing rerun.

### A.4 Consequences

| If accepted | If declined |
|---|---|
| One dated acceptance line in the decision register, release report and nine governance docs; zero code/test changes | Fix remains `INDEPENDENTLY VERIFIED` engineering evidence but unaccepted; no commit; `HOLD` unchanged either way |
| Criterion-4 sub-gate for SEC-015 recorded; criterion 4 stays `BLOCKED` because SEC-004 is open | No technical gain — the code fix and tests already exist in the working tree |
| Does **not** authorize commit, deployment, security certification, `PRODUCTION READY` or release | Does not remove the defect; it remains fixed in the working tree |

### A.5 Exact implementation scope after approval

1. Add one dated acceptance entry to `GULA_OWNER_DECISION_REGISTER.md` (`OD-001` status line).
2. Add one dated non-destructive note to `GULA_RELEASE_ACCEPTANCE_REPORT.md` and the nine governance docs.
3. No source edit, no test edit, no migration, no DDL, no Git staging/commit, no DB/Redis access.

---

## B. Change provenance and commit authorization (`OD-002`)

### B.1 Concise explanation

Two files hold 13 line-disjoint hunks from four independent workstreams. Every hunk has documentary ownership in-repository, and no hunk exists in any sibling worktree. Hunk-level separation is *technically* possible but does not unblock a commit — the positional-call AST guard validates the whole tree — and discarding another workstream's lines to enable a commit is prohibited. Both files remain `BLOCKED` for commit.

### B.2 Authorization matrix (all 13 hunks)

`Isolation = safe isolation possible` means the hunk is line-disjoint and could be patch-staged **without touching other work**. `Commit authorized` is `No` for every hunk: no owner sign-off exists and this directive forbids commits.

| File | Hunk | Change (new-side) | Owner / workstream | Verification status (pre-existing award) | Safe isolation | Commit authorized |
|---|---|---|---|---|---|---|
| `backend/app/lims/routes.py` | `L1` | `+344,9` — `create_department`: 8 positional `log_action` args → keywords | `WS-1` / `AUDIT-POSITIONAL-001` / `SEC-001` | `INDEPENDENTLY VERIFIED` (engineering scope, prior award) | Yes | **No** — `BLOCKED` |
| `backend/app/lims/routes.py` | `L2` | `+987,7→+995,7` — `order_fhir_bundle`: positional → keywords | `WS-1` / `AUDIT-POSITIONAL-001` | `INDEPENDENTLY VERIFIED` (prior award) | Yes | **No** — `BLOCKED` |
| `backend/app/lims/routes.py` | `L3` | `+1544→+1552` — `list_quality_indicators`: `Depends(get_current_user)` | `WS-4` / `S-12` | `IMPLEMENTED` / `TESTED` (5/5); no independent award located | Yes | **No** — `BLOCKED` |
| `backend/app/lims/routes.py` | `L4` | `+1560,0→+1569` — `evaluate_indicator`: `Depends(get_current_user)` | `WS-4` / `S-12` | `IMPLEMENTED` / `TESTED` (5/5); no independent award located | Yes | **No** — `BLOCKED` |
| `backend/app/lims/routes.py` | `L5` | `+2163,0→+2173,15` — `run_auto_validation`: persist all flags, commit only when `changed` | `WS-3` / `AUD-CLIN-003` | `INDEPENDENTLY VERIFIED` (prior Team C award) | Yes | **No** — `BLOCKED` |
| `backend/app/lims/routes.py` | `L6` | `+2167,0→+2192,24` — `run_auto_validation`: clear stale flags | `WS-3` / `R-CLIN-003-A` | `INDEPENDENTLY VERIFIED` (prior Team C award) | Yes | **No** — `BLOCKED` |
| `backend/app/lims/routes.py` | `L7` | `+2182→+2230,8` — `process_critical_alert`: commit on `notification_pending` | `WS-3` / `AUD-CLIN-001` | `INDEPENDENTLY VERIFIED` (prior Team C award) | Yes | **No** — `BLOCKED` |
| `backend/app/routes/ai.py` | `A1` | `+54,0→+55,2` — two imports on one region (`require_ai_operator` + `log_action`) | `WS-4` (`require_ai_operator`) + `WS-2` (`log_action`) | Mixed: `WS-4` `IMPLEMENTED`/`TESTED` (8/8); `WS-2` `INDEPENDENTLY VERIFIED` (prior award) | Partial — shared import region needs line-level care | **No** — `BLOCKED` |
| `backend/app/routes/ai.py` | `A2` | `+337→+339` — `/operations`: `Depends(require_ai_operator)` | `WS-4` / `S-09` | `IMPLEMENTED` / `TESTED` (8/8); no independent award located | Yes | **No** — `BLOCKED` |
| `backend/app/routes/ai.py` | `A3` | `+339→+341` — docstring "(operator-only)" | `WS-4` / `S-09` | `IMPLEMENTED` / `TESTED` (documentation accompanying guard) | Yes | **No** — `BLOCKED` |
| `backend/app/routes/ai.py` | `A4` | `+346→+348,5` — `/providers` multi-line guard decorator | `WS-4` / `S-09` | `IMPLEMENTED` / `TESTED` (8/8) | Yes | **No** — `BLOCKED` |
| `backend/app/routes/ai.py` | `A5` | `+644→+650,8` — `_emit_critical_alert` docstring documents `AUDIT-BYPASS-001` | `WS-2` / `AUDIT-BYPASS-001` | `INDEPENDENTLY VERIFIED` (prior award) | Yes | **No** — `BLOCKED` |
| `backend/app/routes/ai.py` | `A6` | `+646,16→+659,11` — direct `AuditLog(...)` → canonical `log_action(...)` | `WS-2` / `AUDIT-BYPASS-001` | `INDEPENDENTLY VERIFIED` (prior award) | Yes | **No** — `BLOCKED` |

**Workstream ownership evidence:** `WS-1` `GULA_AUDIT_POSITIONAL_FIX_REPORT.md:44,57,59`; `WS-2` `GULA_AUDIT_BYPASS_FIX_REPORT.md:15,29,40,51`; `WS-3` `GOVERNANCE/ADVERSARIAL_ASSURANCE/REMEDIATION_REGISTER.json:53-57,401-405` + `PHASE2_CLOSEOUT.md:26` + `INDEPENDENT_VERIFICATION_TEAM_C_PHASE2_REVERIFY.md:16,98-109`; `WS-4` `GOVERNANCE/PUBLIC_ENDPOINT_REGISTER.md:85-86` + `GOVERNANCE/REMEDIATION_STAGE_REPORT.md:44,46`. Contemporaneous separation statements are recorded in the positional fix report `:59` and the bypass fix report `:51,88`. Full manifest: `GULA_CHANGE_PROVENANCE_RESOLUTION_REPORT.md` §2–§5.

### B.3 Recommended decision

Keep both files `BLOCKED`. Require **four separate, scoped owner approvals** — `WS-1` (L1–L2), `WS-2` (A1 `log_action` import, A5–A6), `WS-3` (L5–L7), `WS-4` (L3–L4, A1 `require_ai_operator` import, A2–A4) — before any exact-path staging or commit. Do not extract one workstream by removing another's lines. Never bundle the four into one vague approval.

### B.4 Consequences

| If approvals are granted | If withheld |
|---|---|
| Per-workstream patch-level staging is possible; each commit must be independently revertible and followed by focused/related guard re-runs | All 13 hunks remain uncommitted but byte-intact; no work is lost; no provenance is misattributed |
| Whole-tree AST guard must still pass for each commit — staging a subset is not itself sufficient | SEC-001/SEC-014/SEC-015 commit claims remain `BLOCKED`; engineering evidence stands |
| Any owner may withhold its own workstream without affecting the others | HOLD unchanged in every case |

### B.5 Exact implementation scope after approval

1. Record each of the four signed approvals with file + hunk IDs in the provenance report.
2. `git add -p` only the approved hunks; verify with `git diff --cached -U0` that no other workstream's lines are staged.
3. Run `git diff --check`, the positional-call AST guard (`test_audit_positional_regression.py`), focused bypass/chain tests, and related suites.
4. One commit per signed workstream with a Conventional Commit message naming the workstream ID.
5. No merge, no push, no PR, no broad staging, no sibling-repo touch.

---

## C. Database ownership — ADR-A / ADR-B (`OD-003` / `OD-004`)

### C.1 Concise explanation

At HEAD, 19 declarative bases exist but only 17 are registered in `backend/migrations/env.py`; `DocIntelBase` (21 tables) and `InsBase` (30 tables) are invisible to Alembic autogenerate. The exact source-based discrepancy is **354** tables (not the historical 426 per-context measurement, which is preserved as older evidence). Of those 354: `261 ACTIVE_REQUIRED`, `51 OWNERSHIP_UNCLEAR`, `22 DORMANT`, `20 UNUSED`; 188 have FK declarations and 126 have enum columns. `national_facilities` has two ORM owners. Test-side `create_all()` currently masks these gaps.

### C.2 Evidence

`GULA_ORM_MIGRATION_COMPLETENESS_REPORT.md` §2 (19-base inventory), §3 (354 derivation and 426 reconciliation), §4 (all 354 classified rows), §6–§10 (ownership, backlog, decisions), §11 (historical contradictions retained); `GOVERNANCE/ADR_DECISION_REQUEST.md` ADR-A (A1–A4, recommendation A1+A3) and ADR-B (B1–B3, recommendation B1). Single Alembic head `20261119_0003`; no bulk DDL authorized. Full four-alternative comparison: `GULA_DATABASE_OWNERSHIP_PROPOSAL.md`.

### C.3 Recommended decision

- **ADR-A:** domain-owned metadata registries imported into a single Alembic metadata (Alternative 2), with all 19 bases registered so autogenerate is not blind (safe part of Alternative 1), the 261 active tables migrated **one context at a time** (Alternative 3), and the 42 dormant/unused tables declared non-shipping without deletion (Alternative 4). Reject a single bulk baseline revision and deploy-time `create_all()`.
- **ADR-B:** option **B1** — `facilities`, `organizations`, `national_facilities` are pre-existing baseline infrastructure excluded from `downgrade base` by design, with one named ORM owner for `national_facilities`.

### C.4 Consequences

| If approved | If declined |
|---|---|
| Authorizes a *work order*, not DDL: base registration, then per-context revisions with upgrade/downgrade/re-upgrade proof on disposable PG16 | Migration coverage remains `BLOCKED`; W-017 cannot legitimately reach `872/872`; schema drift persists |
| Domain isolation preserved through registries; dormant modules retained as strategic assets (GULA constitution) | `create_all()`-masked tests continue to hide the gap |
| Each revision independently revertible; single Alembic head maintained | No bulk migration, no data loss, no false pass — but no progress on criteria 3/6 |
| ADR-B avoids dropping tables that may hold national reference data | ADR-B tables stay undecided and excluded from `downgrade base` without a record |

### C.5 Exact implementation scope after approval

1. Register `DocIntelBase` and `InsBase` in `backend/migrations/env.py` (one file, one revert).
2. Author one additive, reversible revision per domain context, highest priority (`ACTIVE_REQUIRED`, ≥20 refs, patient/claim-critical) first.
3. For each: disposable PG16 `upgrade → downgrade → re-upgrade`, schema fingerprint, strict-schema test; no production DB.
4. Record ship/no-ship decision for all 22 DORMANT + 20 UNUSED tables (retain code; do not delete).
5. Record ADR-B B1 and re-point the single `national_facilities` owner in a separate reversible change.
6. Update the 354-row matrix with newly migrated rows; never overwrite historical versions.

---

## D. W-017 strict gate (`OD-005`)

### D.1 Concise explanation

W-017 asks whether the backend passes `872/872` against a PostgreSQL schema built **exclusively** by Alembic (no `create_all()`, no test-side DDL, no `alembic stamp`). Its recorded result is `753 passed / 119 failed / 0 skipped (872)` — `FAILED`. The numbers 119 and 753 are the failure and pass fractions of that single historical run; they are not two independent current measurements. The executable, strict `conftest.py`, 53 module copies, manifest and raw XML/log artifacts lived outside the repository and are absent. A fresh run requires a documented trigger, four approvals/resources and a reconstructed, hash-verified harness; the threshold stays `872/872`.

### D.2 Evidence

`GULA_W017_STRICT_GATE_REASSESSMENT.md` §1 (exact gate), §2 (re-run `BLOCKED`), §3 (read-only recomputation `119`), §4 (failure classification 83 + 24 + 12), §5 (raw artifact absent), §6 (119/753 reconciliation), §7 (seven-step unblock plan); `docs/parallel-program/qa/QA_AUDIT.md:196` A09-004 P1 and `:300` SR-A09-06; GECS `DUPLICATE_PREVENTION.md:32-38,45`.

### D.3 Recommended decision

Keep the gate `FAILED` and fresh re-execution `BLOCKED` until the exact authorization and resources in `GULA_EXACT_APPROVAL_RESOURCE_REQUIREMENTS.md` §1 are granted. On approval, execute the seven-step plan unchanged: record trigger → A07 + owner + QA Lead authorization → disposable PG16 clone (revision `20261114_0006`, 433 tables, Alembic-only) → reconstructed byte-identical harness → exact command twice with artifacts → classify → then revisit D-020/D-021. **No threshold change.**

### D.4 Consequences

| If authorized | If not |
|---|---|
| A fresh, artifact-backed result can supersede the historical `FAILED` record under a new evidence ID — it may still fail | Historical `FAILED` stands; no new evidence; no release gain |
| Requires an authorized schema change first (natural trigger) — `OD-003`/`OD-004` | No unauthorized gate run, no invented number |
| A pass alone does not grant release: D-020/D-021 and criteria 2,6,8,10,11,13,15,16,17 remain | HOLD unchanged |

### D.5 Exact implementation scope after approval

1. Append a documented trigger to `GOVERNANCE/GECS/CHANGE_CONTROL.md` / `DUPLICATE_PREVENTION.md`.
2. Provision a disposable PostgreSQL 16 clone built only by Alembic; export `STRICT_DATABASE_URL`.
3. Reconstruct `/tmp/opencode/strict-w1/` (strict `conftest.py`, `pytest.ini`, 53 copied modules) and re-verify `sha256_manifest_full.txt`.
4. Run `STRICT_DATABASE_URL=<clone> pytest tests -q`, then a second pass with `--junitxml`; capture exit code, full log, `strict_run2.xml`, `baseline_sqlite.xml`, before/after fingerprints, classification JSON.
5. Register new evidence IDs; retain E-001…E-003; never alter tests/migrations/threshold to obtain a pass; destroy the disposable environment afterward.

---

## 6. Sequencing and boundary

`OD-001` → `OD-002` → `OD-003`/`OD-004` → (`OD-003` implementation is the natural trigger for) `OD-005` → remaining architecture/operational/release decisions. Each decision is independent and separately reversible. No approval in this package permits a commit, a deployment, production DB/Redis access, real PHI, secrets, destructive migration, `alembic stamp`, `create_all()` masking, or a change to HOLD.

## 7. Non-claims

No owner approval is asserted; no acceptance is recorded. `INDEPENDENTLY VERIFIED` references are prior fresh-context reviewer awards reproduced verbatim, not self-awards. No `PRODUCTION READY`. No clinical/legal/regulatory/ministerial approval. No commit, push, merge, PR or deployment. Standing decision **HOLD**; Stable v1.0.0 **NOT declared**; `production_ready_items = 0`.
