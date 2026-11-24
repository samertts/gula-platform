# GULA OWNER DECISION REGISTER — GULA-OWNER-GATE-2026-11-20

**Directive:** GULA-OWNER-GATE-2026-11-20 (post-SEC-015 verification / national platform completion)  
**Repository / branch:** `gula-integration` / `integration/gula-unification-v1`  
**Fresh baseline HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549` · **Sibling HEAD:** `f478676b6fc375338648dde46fbf076c015a3f91`  
**Date:** 2026-11-20  
**Method:** read-only evidence assembly from existing reports and source; no code changed, no file staged, no commit/push/merge/PR/deploy, no DB/Redis operation, no owner-gated action executed.

**Status vocabulary (exclusive):** `NOT IMPLEMENTED` · `IMPLEMENTED` · `TESTED` · `INTEGRATED` · `INDEPENDENTLY VERIFIED` · `PRODUCTION READY` · `BLOCKED`

**Authority rule:** this register *prepares* decisions. It never self-awards `INDEPENDENTLY VERIFIED` or `PRODUCTION READY`, and never converts `HOLD` to `GO`. Every decision below is `BLOCKED` until the named owner records an explicit, scoped approval; only an owner-recorded decision may change from `BLOCKED` to `ACCEPTED`. Standing release decision remains **HOLD** (`GOVERNANCE/FINAL_DECISION.md`, protected MD5 `effdfeaf10234678d83b2668c4489552`). Stable v1.0.0 is **NOT declared**; `production_ready_items = 0`.

> **GULA-AUDIT-COMPREHENSIVE-REVIEW — OD-001 OWNER ACCEPTANCE (2026-11-20, additive):** The owner explicitly recorded: “OD-001: ACCEPTED. The owner explicitly accepts the third independent SEC-015 F-01 review verdict (PASS) and authorizes recording OD-001 as ACCEPTED. This acceptance applies to the defined SEC-015/F-01 engineering scope only.” Reference: `GULA_SEC015_F01_INDEPENDENT_REVIEW_3_REPORT.md` (MD5 `329049ee6bed006901660e43b2d4b995`, 171 lines), verdict **PASS** for the defined engineering scope only. This acceptance does not authorize commit (`OD-002`), merge, release, deployment, `PRODUCTION READY`, or HOLD→GO; it does not accept `OD-002`…`OD-025`. Earlier statements recording OD-001 as `BLOCKED` are historical and are superseded by §8 for OD-001 only.

> **GULA-MASTER-COMPLETION-2026-11-20 — SEC-015 REVIEW-2 synchronization (additive, no status changed):** The mandated second independent adversarial review was located and verified: `GULA_SEC015_ADVERSARIAL_REVIEW_2_REPORT.md` (MD5 `f2b44ae6b23ffbbb3f65344aa2126134`), verdict **PASS WITH CONDITIONS**. It reproduced an audit-chain fork under PostgreSQL `REPEATABLE READ` and `SERIALIZABLE` (Finding F-01, **MEDIUM**) and found no isolation-level enforcement anywhere in `backend/app`. Review-2 explicitly does **not** award `INDEPENDENTLY VERIFIED`, does not resolve F-01, and contains no explicit owner acceptance text. **OD-001 therefore remains `BLOCKED`.** No source/test/migration/config file was changed in this synchronization: `backend/app/services/audit_service.py` MD5 remains `40c2598a02319b00c0351ddc689f7ed7`. F-01 is prepared for explicit R4 review in `GULA_SEC015_F01_REMEDIATION_PACKAGE.md`. The `/tmp/opencode/sec015_*` raw logs cited below were removed by temporary-directory cleanup and are historical references only (Review-2 §10.1). Standing decision **HOLD**; Stable v1.0.0 **not declared**.

---

## 1. Protection invariants re-verified at this baseline

| Invariant | Status | Evidence |
|---|---|---|
| Protected MD5s unchanged | `IMPLEMENTED` | `FINAL_DECISION.md` `effdfeaf…`; `MPI_FINAL_INDEPENDENT_AUDIT.md` `1a02c015…`; `MPI_INDEPENDENT_AUDIT_FINDINGS.md` `ea3969d0…` |
| 20 staged `R100` renames preserved | `IMPLEMENTED` | `git diff --cached --name-status` = 20 × `R100`, staged total 20 |
| Sibling `gula-platform` untouched | `IMPLEMENTED` | HEAD `f478676b6fc375338648dde46fbf076c015a3f91` |
| `git diff --check` clean | `IMPLEMENTED` | exit 0 at baseline |
| Pre-existing modified/untracked work preserved byte-for-byte | `IMPLEMENTED` | no broad staging, no checkout/reset/revert performed |
| No commit / push / merge / PR / deployment | `IMPLEMENTED` | no Git write, no deploy operation performed |
| No production DB/Redis, PHI, secrets, DDL, `alembic stamp`, `create_all()` masking | `IMPLEMENTED` | none performed |

---

## 2. Priority owner decisions (directive §3 — A, B, C, D)

### OD-001 — Decision A: SEC-015 technical acceptance

| Field | Record |
|---|---|
| **Decision ID** | `OD-001` (owner decision A) |
| **Description** | Accept or reject the SEC-015 SQLite multi-row audit-chain linkage remediation as the authoritative engineering fix, and authorize only the *acceptance record* — not a commit, not a release. |
| **Why it matters** | The audit chain is the tamper-evidence backbone of a national health platform. SEC-015 was a regression of an earlier correct fix: `f0b021bd3` restored a predecessor read *after* insert, so SQLite chains self-referenced to genesis and `verify_audit_chain()` reported `tampered` on valid data. Acceptance must rest on reproducible evidence, not on a test workaround. |
| **Evidence** | Root cause (`2cdc5479` fix → `f0b021bd3` regression) and exact mechanism in `GULA_SEC015_AUDIT_CHAIN_REMEDIATION_REPORT.md` §2; SQLite zero-row `UPDATE` write reservation + pre-insert predecessor read + PG `pg_advisory_xact_lock` in §3.1; red baseline `7 failed / 6 passed` (`sec015_red_baseline.log`), focused `13 passed` (`sec015_green_final.log`), related audit suites `73 passed` (`sec015_related_audit.log`), disposable PG16 `PG_VERIFY_RESULT=PASS` (`sec015_pg_verify.log`), full suite `5151 passed / 28 skipped / 0 failed, EXIT=0` (`sec015_full_suite.log`), low-fix rerun `13 passed` (`sec015_green_lowfix.log`); fresh-context reviewer session `ses_e0a984dadffemm3LClZf6oKOPo` **VERDICT: PASS** (engineering scope). Historical `5138 / 28 / 0` preserved in `/tmp/opencode/auditfix_full_suite_clean.log`. **Second independent review (`GULA-SEC015-REVIEW-2`, 2026-11-20):** `GULA_SEC015_ADVERSARIAL_REVIEW_2_REPORT.md` (MD5 `f2b44ae6b23ffbbb3f65344aa2126134`) — verdict **PASS WITH CONDITIONS**, fresh source-tied focused **13/13** and related **73/73**, SQLite cross-process serialization proof, disposable PG16 proof, no CRITICAL/HIGH; **F-01 MEDIUM: chain fork reproduced under `REPEATABLE READ` and `SERIALIZABLE`; no isolation enforcement in `backend/app`**. Review-1 award (`ses_e0a984dadffemm3LClZf6oKOPo`) is historical context only; Review-2 did not rely on it. Raw `/tmp/opencode/sec015_*` logs no longer exist after tmp cleanup — historical only. |
| **Available alternatives** | (1) Accept engineering evidence as-is with documented limitations (recommended). (2) Defer acceptance until a second independent reviewer re-runs the suite — costs time, no new technical evidence. (3) Revert the fix — rejected: restores a false-tamper defect and reintroduces the hash re-stitching workaround. (4) Accept and simultaneously authorize commit — rejected: commit is a separate decision (`OD-002`). |
| **Recommended option** | **Option 1**: record SEC-015 as `INDEPENDENTLY VERIFIED (engineering scope)` and technically accepted; keep commit `BLOCKED` and release posture `HOLD`. |
| **Risks** | F-01 (**MEDIUM, reproduced**): PG advisory-lock correctness holds only under `READ COMMITTED`; chain fork (`broken=[2]`) reproduced under `REPEATABLE READ` and `SERIALIZABLE` with the advisory lock as first data statement, and no application enforcement/rejection exists. Anchor checkpoint is pre-commit (pre-existing — rollback can leave an anchor line); SQLite multi-process/multi-file is unsupported; `shared/audit/service.py` schema mismatch remains separately `BLOCKED`; no runtime/production verification beyond disposable PG16. |
| **Required owner approval** | Exact text: *"I accept the SEC-015 engineering evidence package in `GULA_SEC015_AUDIT_CHAIN_REMEDIATION_REPORT.md` as the authoritative recorded engineering result. This acceptance does not authorize a commit, a deployment, `PRODUCTION READY`, or a change to HOLD."* **Additionally required after Review-2:** an explicit, scoped decision on F-01 — either *"I accept a READ-COMMITTED-only audit scope and require the fail-fast/enforcement guard described in `GULA_SEC015_F01_REMEDIATION_PACKAGE.md` before acceptance"* or a documented rejection/deferral with owner name and date. Approver: Program Director / engineering owner. **Recorded 2026-11-20:** “OD-001: ACCEPTED. The owner explicitly accepts the third independent SEC-015 F-01 review verdict (PASS) and authorizes recording OD-001 as ACCEPTED. This acceptance applies to the defined SEC-015/F-01 engineering scope only.” Reference: `GULA_SEC015_F01_INDEPENDENT_REVIEW_3_REPORT.md` (MD5 `329049ee6bed006901660e43b2d4b995`). |
| **Dependencies** | None for the acceptance record itself. Commit depends on `OD-002`; any production claim depends on `OD-007`/`OD-025`. |
| **Implementation scope** | Governance synchronization only: dated acceptance record in this register, completion ledger and execution status documents. Zero source changes, zero test changes, zero Git staging/write operations. |
| **Reversal strategy** | Acceptance is a documentary record; supersede with a new dated decision entry rather than editing history. The fix itself is separately reversible via a single targeted revert of `backend/app/services/audit_service.py` and its two test files. |
| **Owner decision status** | `ACCEPTED` (2026-11-20), for the defined SEC-015/F-01 engineering scope only. |
| **Engineering evidence status** | SEC-015 base remediation retains its historical `INDEPENDENTLY VERIFIED` engineering-scope award; F-01 remediation is `IMPLEMENTED` + `TESTED` with Review-3 verdict **PASS** for the defined engineering scope. No self-awarded `INDEPENDENTLY VERIFIED` for the remediation agent. |
| **Status** | `ACCEPTED` as an owner decision for the defined SEC-015/F-01 engineering scope only. Commit (`OD-002`), merge, release, deployment, `PRODUCTION READY` and HOLD→GO remain `BLOCKED`/unauthorized. |

### OD-002 — Decision B: change provenance and commit authorization

| Field | Record |
|---|---|
| **Decision ID** | `OD-002` (owner decision B) |
| **Description** | Authorize (or withhold) exact-path commits for the 13 attributed hunks in `backend/app/routes/ai.py` (6) and `backend/app/lims/routes.py` (7), across four workstreams `WS-1`…`WS-4`. |
| **Why it matters** | Both files contain line-disjoint changes from independent workstreams. A broad commit would appropriate other workstreams' work; a hunk-level extraction that discards another workstream's changes is explicitly prohibited. No commit authority exists in this directive. |
| **Evidence** | `GULA_CHANGE_PROVENANCE_RESOLUTION_REPORT.md` §2 (13-hunk manifest, L1–L7 and A1–A6), §3 (cross-worktree check — no hunk exists in any sibling worktree), §4 (disjoint but not authorized; positional-call AST guard validates the whole tree; extraction would not unblock a commit), §5 (`BLOCKED`). Ownership: `WS-1` `AUDIT-POSITIONAL-001`/`SEC-001` (previously `INDEPENDENTLY VERIFIED`), `WS-2` `AUDIT-BYPASS-001`/`SEC-014` (previously `INDEPENDENTLY VERIFIED`), `WS-3` Team C `AUD-CLIN-001`/`AUD-CLIN-003`/`R-CLIN-003-A` (previously `INDEPENDENTLY VERIFIED` with named awards), `WS-4` `S-09`/`S-12` (`IMPLEMENTED`/`TESTED` 8/8 and 5/5; no independent award located). Full authorization matrix in `GULA_OWNER_DECISION_PACKAGE.md` §3. |
| **Available alternatives** | (1) Keep all work uncommitted pending four separate workstream sign-offs (recommended). (2) Authorize only `WS-1`/`WS-2` hunks via patch-level staging — technically possible but does not clear the whole-tree AST guard and must not remove `WS-3`/`WS-4` lines. (3) Authorize a single all-workstream commit — rejected: conflates four provenance chains. (4) Archive both files — rejected: deletes verified fixes. |
| **Recommended option** | **Option 1**, with four independent approvals recorded before any exact-path action; a per-workstream commit only if each owner signs its own hunk set and the whole-tree guards pass. |
| **Risks** | `WS-4` individual contributor is not named in the evidence (workstream and tests are documented) — attribution is complete but sign-off must come from the named workstream owner. Any commit attempt without all four sign-offs risks provenance violation. |
| **Required owner approval** | Four separate, scoped approvals — *not one vague permission*: (a) `WS-1` owner for hunks L1–L2 in `lims/routes.py`; (b) `WS-2` owner for A1(`log_action` import), A5–A6 in `ai.py`; (c) Team C / `WS-3` owner for L5–L7; (d) `WS-4` owner for L3–L4 and A1(`require_ai_operator`), A2–A4. Each approval must state the exact file, hunk IDs and commit boundary. |
| **Dependencies** | `OD-001` (SEC-015 acceptance) is independent of this decision; SEC-001/SEC-014 commit claims depend on this decision. |
| **Implementation scope** | After approval: `git add` of only the exact approved paths/hunks, one commit per signed workstream, `git diff --check`, focused + related tests re-run, then provenance report update. No broad staging, no merge, no push. |
| **Reversal strategy** | One targeted `git revert <commit>` per workstream commit restores the pre-commit state; renames and protected files are never touched. |
| **Status** | `BLOCKED` (no-commit authority; four owner sign-offs absent) |

### OD-003 — Decision C1: ADR-A database ownership architecture (354-table matrix)

| Field | Record |
|---|---|
| **Decision ID** | `OD-003` (owner decision C, ADR-A) |
| **Description** | Choose the ownership architecture and migration strategy for the 354 source-based discrepancy tables reported at HEAD `2206654`, including the 51 tables on unregistered bases. |
| **Why it matters** | 19 declarative bases exist; only 17 are registered in `backend/migrations/env.py`. `DocIntelBase` (21) and `InsBase` (30) are invisible to Alembic autogenerate. Test-side `create_all()` masks the gap. A wrong architecture produces unreviewable bulk DDL or permanent schema drift on a national platform. |
| **Evidence** | `GULA_ORM_MIGRATION_COMPLETENESS_REPORT.md`: 834 distinct ORM names / 835 definitions; 493 migration-referenced names; 354 exact source-based discrepancy; classification of all 354 rows — `261 ACTIVE_REQUIRED`, `51 OWNERSHIP_UNCLEAR`, `22 DORMANT`, `20 UNUSED`; 188 discrepancy tables with FK declarations, 126 with enum columns, 28 with zero app refs; 51 tables on unregistered bases; duplicate `national_facilities` owner. Single Alembic head `20261119_0003` (111 revisions, 0 orphan roots). Historical 426 (per-context at `2827c1ff`) preserved and reconciled to 354 in §3.1. `GOVERNANCE/ADR_DECISION_REQUEST.md` §ADR-A options A1–A4, recommendation A1+A3. Full comparison in `GULA_DATABASE_OWNERSHIP_PROPOSAL.md`. |
| **Available alternatives** | (1) Register all 19 existing bases centrally in `env.py`. (2) Establish explicit domain-owned metadata registries joined into one Alembic metadata. (3) Consolidate only confirmed active (261) models into the migration chain. (4) Retain dormant/unused (42) modules outside the active chain via ship/no-ship declaration. Rejected: one bulk baseline revision; `create_all()` at deploy. |
| **Recommended option** | **Alternative 2 as the ownership architecture**, implemented with the safe registration of Alternative 1, sequenced by Alternative 3, and with Alternative 4 for the 42 dormant/unused tables — i.e. domain-owned registries imported into `env.py`, one additive reversible revision per context with strict round-trip proof, and a recorded non-shipping declaration. Equivalent to A1+A3 in the existing ADR request; never A2/A4. |
| **Risks** | 188 FK / 126 enum tables require ordered, context-scoped migrations; `READ COMMITTED` and tenant partitioning must be preserved; a single shared `target_metadata` can re-couple domains if registries are not enforced; misclassifying a dormant table as non-shipping removes a strategic module from releases (GULA constitution: dormant modules are assets, never deleted). |
| **Required owner approval** | Exact text: *"I approve ADR-A option A1+A3 as amended in `GULA_DATABASE_OWNERSHIP_PROPOSAL.md`: domain-owned metadata registries imported into `env.py`, context-by-context additive reversible migrations with strict round-trip proof, and a recorded ship/no-ship declaration — no bulk revision, no `create_all()`, no production DDL in this approval."* Approver: Program Director / Architect / Database owner. |
| **Dependencies** | `OD-004` (ADR-B) for the three reference tables; `OD-005` (W-017) for the acceptance gate; NR-011 prerequisite already resolved in code but requires the owner-approved work order. |
| **Implementation scope** | After approval only: register the two bases in `env.py`, author one context revision at a time, run upgrade→downgrade→re-upgrade on a disposable PG16, update the 354-row classification, never touch production. Each revision independently revertible. |
| **Reversal strategy** | Each context migration is an independent revision with a tested `downgrade()`; Alembic chain remains single-head. Registration change is one file and one revert. |
| **Status** | `BLOCKED` (no DDL, no registration, no bulk migration authorized) |

### OD-004 — Decision C2: ADR-B reference-table ownership

| Field | Record |
|---|---|
| **Decision ID** | `OD-004` (owner decision C, ADR-B) |
| **Description** | Assign authoritative ownership of `facilities`, `organizations`, and `national_facilities` (the latter mapped by two ORM packages). |
| **Why it matters** | These three tables survive `alembic downgrade base`, so their status is undecided; they may hold national reference data. Dropping or re-owning them without a decision risks irreversible loss of national facility identity. |
| **Evidence** | `GOVERNANCE/ADR_DECISION_REQUEST.md` §ADR-B (options B1 baseline infrastructure, B2 migration-owned with downgrade path, B3 split; recommendation B1 + one authoritative ORM owner); `GULA_ORM_MIGRATION_COMPLETENESS_REPORT.md` §7 (`BLOCKED`, no named owner for DocIntel/Ins) and §6 (`national_facilities` — 2 ORM owners: `models/clinical_scope.py:136`, `national/domain/facility.py:9`). |
| **Available alternatives** | B1 — declare pre-existing baseline infrastructure, excluded from `downgrade base` by design, plus one ORM owner for `national_facilities` (recommended). B2 — migration-owned, add to downgrade path (riskier: may drop national reference data). B3 — split ownership. |
| **Recommended option** | **B1** with an explicit architecture record and a single ORM owner for `national_facilities`; re-point the duplicate mapping later in a separate reversible change. |
| **Risks** | If these tables are later proven migration-owned, the baseline exclusion must be revisited; a downgrade may leave them behind by design — must be documented in runbooks. |
| **Required owner approval** | Exact text: *"I approve ADR-B option B1: `facilities`, `organizations`, `national_facilities` are pre-existing baseline infrastructure excluded from `downgrade base` by design, with `national_facilities` owned by one named ORM mapping to be recorded in the ADR."* Approver: Database owner / Program Director. |
| **Dependencies** | `OD-003` (work-order sequencing); release criterion 5 (`MIG-EXISTING`) and `NR-006`. |
| **Implementation scope** | After approval: one ADR record + one ownership note in the ORM report; no DDL, no drop, no data change. |
| **Reversal strategy** | Documentary only; a follow-up migration can adopt or drop the tables under a new decision. |
| **Status** | `BLOCKED` |

### OD-005 — Decision D: W-017 strict gate authorization and resources

| Field | Record |
|---|---|
| **Decision ID** | `OD-005` (owner decision D) |
| **Description** | Authorize a fresh W-017 strict-schema gate run and provide the exact trigger, harness and disposable PG16 environment; or keep the gate `FAILED`/`BLOCKED`. |
| **Why it matters** | W-017 is the only gate that tests the backend against a schema built exclusively by Alembic. Its historical result is `753 passed / 119 failed / 0 skipped (872)` — `FAILED`. The figures 119 and 753 are the failure and pass fractions of **one** historical run, not two independent current measurements. No threshold change is authorized. |
| **Evidence** | `GULA_W017_STRICT_GATE_REASSESSMENT.md`: §1 exact gate (threshold `872/872`, external harness `/tmp/opencode/strict-w1/`, strict `conftest.py`, 53 byte-copied modules, revision `20261114_0006` / 433 tables); §2 fresh re-run `BLOCKED`; §3 read-only recomputation `119` from preserved classification counts; §5 raw artifact absent everywhere; §6 119/753 reconciliation; §7 unblock plan. `QA_AUDIT.md:196` A09-004 P1 — approval required: A07 + owner decision. |
| **Available alternatives** | (1) Do not re-run; preserve `FAILED` and proceed only with documentary work (recommended absent authorization). (2) Authorize the full 7-step unblock plan with a newly recorded trigger and reconstructed harness. (3) Lower the threshold to accommodate 119 failures — **rejected outright** (no standard reduction). |
| **Recommended option** | **Option 1** until the exact authorization and resources in `GULA_EXACT_APPROVAL_RESOURCE_REQUIREMENTS.md` §1 are granted; then Option 2, with threshold unchanged. |
| **Risks** | Reconstructing the harness changes the evidence basis unless hashes are re-verified; a fixture write leak can self-poison 3 audit-chain tests; a strict-gate pass alone does not grant release (`D-020`/`D-021` still required). |
| **Required owner approval** | Exact text: *"I authorize one documented W-017 re-run under the unchanged 872/872 threshold, with trigger recorded in `GOVERNANCE/GECS/CHANGE_CONTROL.md`, QA Lead execution, A07 scope approval, and artifact capture under new evidence IDs. No threshold change, no production database, no `create_all()`, no `alembic stamp`."* Approvers: A07 (Backend/API/DB) + QA Lead + Program Director. |
| **Dependencies** | `OD-003`/`OD-004` implementation changes the schema under test and is the natural trigger; W-017 must be re-run after, not before, an authorized migration wave; A09-004 raw artifact gap accepted as unrecoverable. |
| **Implementation scope** | After approval: record trigger; provision disposable PG16 clone; reconstruct and hash-verify harness; export `STRICT_DATABASE_URL`; run exact command twice with artifact capture; classify results; never modify tests or migrations to obtain a pass. |
| **Reversal strategy** | No repository state change; the disposable environment is destroyed after capture. New evidence is additive; E-001…E-003 retained. |
| **Status** | `BLOCKED` (missing A07/owner authorization, raw A09-004 P1 artifact, approved harness, documented trigger, disposable PG16) |

---

## 3. Remaining unresolved owner decisions

Each row records all twelve required fields in compact form. All are `BLOCKED` — none is decided by this register.

| ID | Description | Why it matters | Evidence | Alternatives | Recommended | Risks | Required owner approval (exact scope) | Dependencies | Implementation scope | Reversal | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `OD-006` | SEC-004: classify 56 live OpenAPI operations without declared security | Critical paths may lack authorization/audit; blocks criterion 4 | `GULA_SECURITY_AND_RISK_REGISTER.md:19`; OpenAPI 2060 secured / 56 unguarded | (a) public-by-design allowlist with per-route rationale; (b) remediate each with guard+audit; (c) hybrid | (c) per-route classification, protect all clinical/PHI paths | Misclassifying a PHI path as public | Security lead + owner sign-off listing each of 56 routes and its disposition | `OD-001` evidence only | Route guards/tests after per-route decision; no bulk change | Per-route revert | `BLOCKED` |
| `OD-007` | D-020 security certification verdict | Security posture cannot self-certify; blocks RC | `FINAL_DECISION.md:46` NOT CERTIFIED; `GULA_SECURITY_AND_RISK_REGISTER.md` | certify / accept risk with register / defer | Defer until `OD-006` and full SAST/DAST matrix | Premature certification | Security lead + Program Director written verdict | `OD-006`, `OD-003`, `OD-005` | Documentary verdict only | Supersede with new verdict | `BLOCKED` |
| `OD-008` | D-021 clinical safety posture | No journey is E2E verified; patient-safety claim unsupported | `GULA_RELEASE_ACCEPTANCE_REPORT.md` criterion 6; 7 journeys contract-envelope only | accept with limitations / execute E2E then decide | Execute E2E in disposable env before acceptance | Unverified clinical path | Clinical Safety Owner written posture | `OD-003`, `OD-023` | E2E execution under owner gate | Supersede verdict | `BLOCKED` |
| `OD-009` | MP-001 official approval | Required for release criterion 16 | `DECISION_REGISTRY.md`; `status_registry.json` | approve / defer | Defer with prepared packet | Fabricated authority | Named ministry authority, exact document | `OD-007`, `OD-008` | Documentary | Supersede | `BLOCKED` |
| `OD-010` | ODR-001 official approval | Required for release criterion 16 | `DECISION_REGISTRY.md` | approve / defer | Defer | Fabricated authority | Named authority | `OD-007` | Documentary | Supersede | `BLOCKED` |
| `OD-011` | ODR-002 official approval | Required for release criterion 16 | `DECISION_REGISTRY.md` | approve / defer | Defer | Fabricated authority | Named authority | `OD-007` | Documentary | Supersede | `BLOCKED` |
| `OD-012` | ODR-003 official approval | Required for release criterion 16 | `DECISION_REGISTRY.md` | approve / defer | Defer | Fabricated authority | Named authority | `OD-007` | Documentary | Supersede | `BLOCKED` |
| `OD-013` | ODR-004 official approval | Required for release criterion 16 | `DECISION_REGISTRY.md` | approve / defer | Defer | Fabricated authority | Named authority | `OD-007` | Documentary | Supersede | `BLOCKED` |
| `OD-014` | ADR-C: care-continuum host vs decomposed services | Determines domain boundary for 45 models / 74 routes | `GOVERNANCE/ADR_DECISION_REQUEST.md` §ADR-C; inventory §4 | permanent cross-cutting host / decompose | Keep host with bounded modules until E2E evidence | Boundary churn | Architecture owner ADR | `OD-003` | ADR record only | Supersede ADR | `BLOCKED` |
| `OD-015` | ADR-D: audit coverage and `system:admin` blanket | Audit principal quality | `ADR_DECISION_REQUEST.md` §ADR-D | real principal required / documented exception | Require real principal; document break-glass | Availability vs accountability | Security + clinical owner ADR | `OD-006` | Code after ADR | Revert per change | `BLOCKED` |
| `OD-016` | ADR-E: public token/phone access model | External access safety | `ADR_DECISION_REQUEST.md` §ADR-E | signed short-TTL single-use / weaker link | Signed, bound, rate-limited, audited | Token misuse | Security + product owner ADR | `OD-006` | Code after ADR | Revert per change | `BLOCKED` |
| `OD-017` | ADR-F: lab duplication (`lab_service` vs inline routes) | Duplicated LIMS logic | `ADR_DECISION_REQUEST.md` §ADR-F; `ARC-001` in security register | wire routes to service with OpenAPI diff / keep both | Wire with byte-identical OpenAPI | Contract drift | Architecture owner ADR | `OD-002` | Refactor + OpenAPI diff | Revert | `BLOCKED` |
| `OD-018` | ADR-G: insurance 5 live ops vs 84 unserved endpoints | Service gap exposed as complete | `GULA_SECURITY_AND_RISK_REGISTER.md:26`; inventory #16 | provision / declare out of scope | Provision through `OD-003` wave + contract | Incomplete service | Program Director ADR | `OD-003`, `OD-004` | Migration + routes after ADR | Revert per revision | `BLOCKED` |
| `OD-019` | ADR-H: Shared Core boundary | Prevents duplicated central engines | `ADR_DECISION_REQUEST.md` §ADR-H | CI-enforced allowlist / review only | CI-enforced allowlist | False positives vs drift | Architecture owner ADR | none | CI config after ADR | Revert config | `BLOCKED` |
| `OD-020` | ADR-I: archive or retain unserved insurance API | Dead surface in release | `ADR_DECISION_REQUEST.md` §ADR-I | archive with provenance / retain | Archive with single-revert reversibility (ADR-028 pattern) | Removing dormant asset | Program Director ADR | `OD-018` | `git mv` only after approval | Single `git revert` | `BLOCKED` |
| `OD-021` | ADR-J: offline durability | Current engines are in-memory; no device-restart proof | `GULA_OFFLINE_SYNC_REASSESSMENT.md` §2–§4 | PostgreSQL outbox + idempotency / keep harness only | Durable tenant-scoped outbox contract, harness as conformance suite | Key management, ordering | Architecture + security + clinical owner ADR | `OD-003` | Code after ADR; no activation | Revert per change | `BLOCKED` |
| `OD-022` | ARC-001: circular-import remediation topology | Import-order fragility; no runtime failure observed | `GULA_DEPENDENCY_GRAPH.md` §4; `GULA_SECURITY_AND_RISK_REGISTER.md:29` | restructure kernel / retain with lazy mitigation | Retain until ADR-F; no restructure without evidence of failure | Churn in 5 hard cycles | Architecture owner decision | `OD-017` | Refactor only after ADR | Revert | `BLOCKED` |
| `OD-023` | Operational test resources (DR/PITR/RPO/RTO/failover/Redis/RabbitMQ/MinIO/clinical partition/device loss) | No live measurement; no DR claim permitted | `GULA_SECURITY_CI_READINESS_PLAN.md` §4; `FINAL_ACCEPTANCE_REPORT.md:23` | authorize disposable environment / keep `NOT IMPLEMENTED` | Authorize scoped drills with new evidence IDs | Invented RPO/RTO | Operations + clinical owner, exact environment | `OD-003`, `OD-008` | Drills in disposable env; never production | Environment destroyed | `BLOCKED` |
| `OD-024` | CI execution authorization | 33 workflows present, none executed; presence ≠ success | `GULA_SECURITY_CI_READINESS_PLAN.md` §3 | authorize runner / keep `BLOCKED` | Authorize items 1–3,5–7 first; 4,8,9 need PG16/owner/secrets | False PASS claim | DevOps owner, exact workflow list | CI runner | Run exact commands, capture artifacts | Rerun/revert config | `BLOCKED` |
| `OD-025` | Stable v1.0.0 / `PRODUCTION READY` / HOLD→GO | Final release authority | `GOVERNANCE/FINAL_DECISION.md` HOLD; `GULA_RELEASE_ACCEPTANCE_REPORT.md` | declare / keep HOLD | **Keep HOLD** until criteria 2,3,4,6,8,10,11,13,15,16,17 clear | Patient safety, data integrity | Program Director written release decision | `OD-001`…`OD-024` as applicable | Documentary release record only | Re-open HOLD by owner decision | `BLOCKED` |

---

## 4. Decision prioritization (directive §6)

1. `OD-001` SEC-015 technical acceptance.
2. `OD-002` provenance and authorization boundaries.
3. `OD-003` ADR-A then `OD-004` ADR-B database ownership.
4. `OD-005` A07 authorization and W-017 environment.
5. `OD-014`…`OD-022` remaining architectural decisions.
6. `OD-023` operational test resources; `OD-024` CI execution.
7. `OD-006`, `OD-007`, `OD-008`, `OD-009`…`OD-013`, `OD-025` release acceptance requirements.

No unrelated approvals are bundled. Each row in §2 and §3 carries its own scope and boundary.

---

## 5. Non-claims

No owner approval is recorded or invented. No `INDEPENDENTLY VERIFIED` or `PRODUCTION READY` is self-awarded: the only independent awards cited were made previously by fresh-context reviewers. No commit, push, merge, PR, deployment, production DB/Redis operation, real PHI, secret, destructive migration, `alembic stamp` or `create_all()` masking was performed. No threshold was changed. No simulated drill is presented as a real operational test. Standing decision **HOLD**; Stable v1.0.0 **NOT declared**; `production_ready_items = 0`.

---

## 6. Additive synchronization — GULA-MASTER-COMPLETION-2026-11-20

This section records the mandated SEC-015 REVIEW-2 verification only. It changes no criterion, no historical result, and no owner status.

| Item | Record |
|---|---|
| Directive | `GULA-MASTER-COMPLETION-2026-11-20` §5 / §22 — locate and verify the second adversarial review before OD-001 acceptance |
| Review artifact | `GULA_SEC015_ADVERSARIAL_REVIEW_2_REPORT.md`, MD5 `f2b44ae6b23ffbbb3f65344aa2126134`, 285 lines, 14 sections, dated 2026-11-20 |
| Verdict | **PASS WITH CONDITIONS** — no CRITICAL/HIGH; one unresolved **MEDIUM** (F-01) |
| Fresh evidence cited by Review-2 | focused 13/13, related 73/73, SQLite DB-level serialization (2 conn / 4 proc, WAL + rollback journal), disposable PG16 16.14 lock/isolation probes — all source-tied to MD5 `40c2598a02319b00c0351ddc689f7ed7` |
| Traceability limit | the pre-existing `/tmp/opencode/sec015_*` raw logs have been removed by tmp cleanup; Review-2 §10.1 records them as historical, and fresh source-tied runs substitute for re-binding |
| Consequence for OD-001 | **unchanged: `BLOCKED`**. Review-2 is not an acceptance and awards no verification status. Owner must decide F-01 explicitly before acceptance |
| Consequence for other decisions | none. `OD-002`…`OD-025` remain prepared and `BLOCKED`; release **HOLD**; Stable v1.0.0 **not declared**; `production_ready_items = 0` |
| Owner-gated work preparation | `GULA_SEC015_F01_REMEDIATION_PACKAGE.md` (prepared, **not implemented**) — R4 audit change requiring explicit review under mandate §23 |
| Repository invariant | branch `integration/gula-unification-v1`, HEAD `2206654dc713ea2de8c564a3207dfe05fde23549`; 20 staged `R100` renames; staged name-status MD5 `56c524d6ffe9872c3a3ac6eff8c8f203`; three protected MD5s exact; sibling HEAD `f478676b6fc375338648dde46fbf076c015a3f91`; `git diff --check` exit 0; no commit/push/merge/PR/deploy |

---

## 7. Authorized F-01 implementation — `GULA-SEC015-F01-REMEDIATION` (2026-11-20)

The owner explicitly authorized remediation of F-01 (implementation + testing only; no commit, push, merge, deploy, or automatic OD-001 acceptance). This section records that authorization and its outcome. It does **not** record an OD-001 acceptance.

| Item | Record |
|---|---|
| Owner decision | `GULA-SEC015-F01-REMEDIATION`, dated 2026-11-20 — approve scoped R4 implementation, actual-level enforcement, fail-fast guard, PG16 regression suite, disposable PG only |
| Implemented scope | `backend/app/services/audit_service.py` MD5 `566d64a2f8aa5c898a2511e1bbe304bd` (was `40c2598a02319b00c0351ddc689f7ed7`); new `backend/tests/unit/test_audit_chain_isolation_guard.py` MD5 `9ccfa3e92fac50c247f0e839ea180cc8` |
| Mechanism | guard reads the live transaction isolation level, the configured execution option, and the DBAPI autocommit flag on the writing connection; only READ COMMITTED is accepted; undeterminable state fails closed; no silent fallback |
| Additional bypass closed | `AUTOCOMMIT` is invisible to SQLAlchemy's `get_isolation_level()`; it is now rejected explicitly |
| Fresh evidence | focused **13/13** (`/tmp/opencode/f01_verify_focused_final.log`), related **73/73** (`/tmp/opencode/f01_verify_related.log`), PG16 suite **12/12** (`/tmp/opencode/f01_verify_pg16_final.log`); all exit 0; RC intact, RR/SER/raw-SET/autocommit rejected before write; concurrency, rollback, sequence and triggers verified |
| Status of the fix | `IMPLEMENTED` + `TESTED`. **Not** `INDEPENDENTLY VERIFIED` — no self-award; a fresh adversarial review of the final MD5s is required (`GULA_SEC015_F01_INDEPENDENT_REVIEW_PACKAGE.md`) |
| OD-001 status | **unchanged: `BLOCKED`.** The authorization covers implementation, not acceptance; Review-2 remains `PASS WITH CONDITIONS` against the earlier MD5; acceptance requires the new review to return PASS |
| Release posture | **HOLD** unchanged; Stable v1.0.0 **NOT declared**; `production_ready_items = 0`; no commit/push/PR/merge/deploy |
| Invariants | HEAD `2206654dc713ea2de8c564a3207dfe05fde23549`, 20 staged `R100` renames, staged MD5 `56c524d6ffe9872c3a3ac6eff8c8f203`, three protected MD5s exact, sibling HEAD `f478676b6fc375338648dde46fbf076c015a3f91`, `git diff --check` exit 0 |

---

## 8. Owner acceptance of OD-001 — GULA-AUDIT-COMPREHENSIVE-REVIEW (2026-11-20)

| Field | Record |
|---|---|
| Directive | `GULA-AUDIT-COMPREHENSIVE-REVIEW`, owner authorization dated 2026-11-20. |
| Exact owner text | “OD-001: ACCEPTED. The owner explicitly accepts the third independent SEC-015 F-01 review verdict (PASS) and authorizes recording OD-001 as ACCEPTED. This acceptance applies to the defined SEC-015/F-01 engineering scope only.” |
| Acceptance reference | `GULA_SEC015_F01_INDEPENDENT_REVIEW_3_REPORT.md`, MD5 `329049ee6bed006901660e43b2d4b995`, 171 lines, verdict **PASS** for the defined engineering scope. |
| Accepted scope | SEC-015 / F-01 engineering scope only: READ COMMITTED-only audit-chain enforcement, fail-closed rejection before any audit write, and the associated fresh-review evidence. |
| Explicit limitations | The review awarded no `PRODUCTION READY`, no `INDEPENDENTLY VERIFIED` status to the remediation agent, no release decision, and no change to HOLD. It preserved the five LOW/INFORMATIONAL observations (R3-01…R3-05) as recorded. |
| Not accepted by this decision | `OD-002`…`OD-025`; commit, merge, release, deployment, production DB/Redis access, PHI use, CI execution, or any change to release posture. |
| Register effect | OD-001 owner decision status changes from `BLOCKED` to `ACCEPTED`. Earlier `BLOCKED` statements in sections 1–7 remain historical records. |
| Release posture | **HOLD** unchanged; Stable v1.0.0 **NOT declared**; `PRODUCTION READY` **NOT authorized**; `production_ready_items = 0`. |
| Repository safety | Governance documentation only. No source, test, migration, config, staging area, branch, HEAD, protected MD5 or release decision was changed by this acceptance record. |

---

## 9. Owner directive 2026-11-21 — P-02 / P-03 / remaining R4 / release authority (additive, status-preserving)

| Field | Record |
|---|---|
| Directive | `GULA — OWNER AUTHORIZATION DIRECTIVE`, effective 2026-11-21, recorded in the authoritative owner decision register on 2026-11-24 UTC. |
| Exact decisions recorded | (1) `P-02 / AUD-F02: AUTHORIZED`; (2) `P-03 / AUD-F03: AUTHORIZED`; (3) all remaining packages classified `R4` in the authoritative roadmap: `GENERALLY AUTHORIZED`, within existing R4 scope and approved objectives only; (4) production deployment authority: `GRANTED`, subject to every mandatory release gate; (5) production acceptance authority: `GRANTED`, subject to every mandatory acceptance gate. |
| Supersession scope | Supersedes only the prior requirement for a *separate* owner authorization per remaining R4 package. It does **not** authorize scope expansion, unrelated architecture change, or removal of any governance control. |
| Mandatory precondition | Before P-02 or P-03 implementation: an isolated, disposable PostgreSQL environment, proven non-production and free of real patient data; DB version, schema, migrations, transaction behavior and test isolation verified; approved PostgreSQL RED tests executed; no SQLite substitution. If the gate cannot be established, implementation stops and the blocker is reported. |
| Execution order | 1) P-02 / F02; 2) P-03 / F03; 3) remaining R4 packages in authoritative roadmap dependency order. Per package: confirm finding and code paths, keep the approved REV3 packet as baseline, RED→GREEN, focused/related/regression/security/integration tests, Ruff, MyPy strict, applicable static/security checks, fresh independent review, residual/test evidence/file manifest; stop on any unresolved CRITICAL/HIGH; no silent scope expansion. |
| Release/acceptance gates | Authority is in principle only. No production action until all 11 pre-acceptance reports, security/privacy assessment, clinical and audit integrity, migration review/test, backup/recovery, performance/capacity, API compatibility, client validation where applicable, residual disclosure, tested rollback, monitoring/alerting/incident response/ownership and the formal release acceptance matrix are independently evidenced. |
| Explicit prohibitions preserved | Real PHI in tests; secrets in code/logs; unapproved external financial transactions; destructive migrations without tested recovery; disabling audit/security/identity/privacy controls; history rewrite or force-push; protected-record modification without history preservation; PR #307 modification/merge without separate review; treating test success as acceptance. |
| Git/preservation control | Mixed provenance resolved before any commit/push; exact ownership and preservation scope established; staged/unstaged/untracked verified independently; all work preserved; no `git add .` / `git add -A`; no unrelated or unreviewed files committed. |
| Register effect | Authorizations are recorded. No package is marked `ACCEPTED`; `ACCEPTED` requires complete acceptance evidence. No package is `PRODUCTION READY`; that requires all gates passed plus authorized, verified deployment. |
| Standing posture | **HOLD TRUE** · `production_ready_items = 0` · Stable v1.0.0 **NOT DECLARED** · PRODUCTION READY **NOT AUTHORIZED**. |
| Immediate next action | Record directive (this section), verify the PostgreSQL gate, then begin P-02 only after the gate passes. P-03 and later R4 packages remain queued behind their own prerequisites. |
