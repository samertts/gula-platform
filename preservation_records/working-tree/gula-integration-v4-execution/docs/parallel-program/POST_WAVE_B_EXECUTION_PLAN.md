# POST-WAVE-B EXECUTION PLAN — PROGRAM-GULA-PARALLEL-001

**Phase:** Post-Wave-B execution planning (PLAN ONLY)
**Date:** 2026-11-19
**Orchestrator:** Principal Engineering Orchestrator (this session)
**Scope:** All 175 deduplicated findings in `MASTER_REMEDIATION_REGISTER.md`
**Status:** **NO SOURCE REMEDIATION AUTHORIZED · NO GIT STATE CHANGE · NO DB OPERATION · NO DEPLOY**

> This document converts the Wave B register into an executable, evidence-based plan.
> It does **not** authorize execution. Every downstream action is gated on the
> decisions in `APPROVAL_MATRIX.md`. Wave C remains **BLOCKED**.
> Clinical synchronization certification remains **HALTED** until **both A06-001 and
> A06-002 are resolved and verified** (explicit standing instruction).

---

## 1. Safety invariants (unchanged, reaffirmed)

1. Preserve all **378 protected paths** (126 modified, 20 staged renames, 232 untracked) and all Git state (branch, HEAD, 5 worktrees + 1 prunable, 2 stashes). No reset, clean, checkout, stash, merge, rebase, cherry-pick, force-push, worktree change, or history rewrite.
2. No source/config/migration file is modified until isolation, USER release, ownership, and independent approvals are granted.
3. No database execution, migration run, service start, or production deploy.
4. Every finding accepted on evidence (path:line, root cause, severity, verification method); unsupported findings are rejected.
5. No completion percentage above actual register state. Current: **Discovered 175 · Fixed 0 · Verified 0 (0% / 0%)**.

**Program footprint verification (2026-11-19, read-only):** exactly 28 new untracked files under `docs/parallel-program/`; **zero** source/config/migration files modified; **zero** state-changing git operations.

---

## 2. Severity reassessment of the eight P0 findings

Rule applied (per instruction): severity must reflect **actual patient safety, data integrity, security, or destructive operational impact**; visual defects are not P0.

| ID | Original | Reassessed | Basis for reassessment |
|---|---|---|---|
| A08-R001 | P0 | **P0 (keep)** | Destructive operational impact: `emergency-recover.sh:71,76,81` (`checkout -B`, `reset --hard`, `clean -fd`) targets a stale absent branch and would destroy all 378 protected paths. `deploy.sh:173` directs operators to run it on merge conflicts → live execution path. |
| A06-002 | P0 | **P0 (keep)** | Data integrity + patient safety: committed HEAD `offline_sync_service.py:19,176-182` silently resolves first-seen-key-wins (`CRDT_MERGE`), overwriting a clinical value. |
| A05-001 | P0 | **P0 (keep)** | Patient safety: LIMS is production-mounted (`factory.py:689-690`); `lims/workflows.py:227-318` detects critical results but `routes.py:2213-2229` only commits an outbox event — no clinician delivery/acknowledgement. |
| A05-002 | P0 | **P0 (keep)** | Patient safety: production auto-validation (`routes.py:2145-2183`) omits documented QC gate and caller context; `auto_validated` results are release-eligible. |
| A05-007 | P0 | **P0 (keep)** | Data integrity: `routes/ehr_fhir.py:1446-1507` (production `feature_routes`) commits partial FHIR `transaction` writes with no rollback. |
| A03-003 | P0 | **P0 (keep)** | Patient safety + approval integrity: `PharmacyPosPanel.tsx:52-70,158` collapses request and approval into one click against real endpoints `POST /pharmacy/substitutions/requests[/id/approve]` (`endpoints.ts:1759-1760`), exposed to admin/readonly roles (`routes/index.tsx:222-223`). |
| **A02-001** | P0 | **P1 (downgrade)** | **Visual defect.** Missing CSS utilities (`bg-surface`, `border-outline`, `text-on-surface`) cause unstyled overlays/loading/empty states in Modal/Skeleton/EmptyState. No patient-safety, data-integrity, security, or destructive impact. Real UX defect → P1, not P0. |
| **A06-001** | P0 | **P1 (downgrade)** | **Simulation/evidence defect.** `gula_offline_simulation_test.py:59-83,101-102` is a standalone tracked script (no server, no CI wiring — `grep .github/workflows` = 0 matches) that self-references a local hash and prints "100% data integrity". Risk is operator misinterpretation, not a production integrity failure → P1. |

**Recount after reassessment:** P0 **6** · P1 **49** · P2 **78** · P3 **42** = **175** (unchanged total).
The two downgrades **do not cancel their containment work** — see `P0_CONTAINMENT_PLAN.md §9–10`.
The clinical-sync certification halt on **A06-001 + A06-002** remains in force regardless of the A06-001 downgrade.

---

## 3. Coverage of all 175 deduplicated findings

| Domain plan | Agent(s) / findings | Count (raw) | Dedup effect |
|---|---|---|---|
| Clinical safety & workflows | A03 (16) + A05-001…005 (5) | 21 | — |
| Offline synchronization & event delivery | A06 (22) | 22 | — |
| Security & identity | A04 (14) | 14 | — |
| FHIR & database integrity | A05-006…008 (3) + A07 (20) | 23 | — |
| frontend-v3 design system & UX | A02 (21) | 21 | A02-017 merged with A09-010 (−1) |
| DevOps & reliability | A08 (42) | 42 | A08-009 merged with A09-011 (−1) |
| Testing & CI quality gates | A09 (15) | 15 | two merges referenced above |
| **Architecture & structural (8th domain, not in the requested 7)** | A01 (19) | 19 | — |
| **Total raw / unique** | | **177 / 175** | −2 |

All seven requested domain plans plus the A01 architecture plan are detailed in `MASTER_REMEDIATION_REGISTER.md §5` with per-issue owner, gate, and evidence; this plan supplies the batching, dependencies, tests, and acceptance criteria.

---

## 4. Execution model — gates and wave sequence

No wave below is authorized. This is the proposed order once decisions are granted.

| Stage | Name | Entry conditions | Content | Exit gate |
|---|---|---|---|---|
| G0 | Containment | ORCH decision | Quarantine A08-R001 (documentation + guard design only); label A06-001 as demo-only; freeze all P0-related writes | Written notice + no execution path remains |
| G1 | Isolation & release | USER release + `ISOLATION_OPTIONS.md` decision | Establish compliant isolated environment; identify released files | Environment attested; protected tree byte-identical |
| G2 | Approvals | SEC/CLIN/DB-API/ARCH/CI owners | Per-domain approvals in `APPROVAL_MATRIX.md` | Signed approval per finding |
| G3 | Baseline | `TEST_BASELINE_PLAN.md` | Reproducible gate baseline in isolation; record exit codes + artifacts | Machine-readable artifacts exist |
| G4 | Fix batches | G0–G3 + per-batch ownership | Domain plans in dependency order (§5) | Per-batch gates green; no new P0 |
| G5 | Verification | G4 | Full gate suite; register Fixed/Verified updated with evidence | 0 open P0; all gates green |
| G6 | Integration | G5 + explicit merge approval | Review/integrate; never automatic | User-authorized integration only |

---

## 5. Domain plan index and batching

### 5.1 Clinical safety & workflows (A03 + A05-001…005)
- **Owner:** clinical owner (decision authority) + A03 page-local implementer + A05 reviewer + A07 contract support + A09 tests.
- **Dependencies:** A02 shared primitives must stabilise first (A02-001/013); CLIN approval; real API contracts.
- **Batches:** (1) A03-003 pharmacy approval separation [P0]; (2) A05-001 critical-result delivery policy [P0]; (3) A05-002 QC gate + caller context [P0]; (4) A03-001/002/009/012 synthetic-as-live, fabricated IDs, load-failure state; (5) A03-005/006/007/008/013/014 workspace/PHI/FHIR/AI boundaries; (6) P2/P3 UX states.
- **Tests:** component tests for distinct approval step; workflow tests for delivery/ack failure paths; QC-gate unit + route integration; contract tests for changed payloads.
- **Acceptance:** no clinical action reachable from a single client mutation; every critical result has a recipient + ack or an explicit fail-closed state; auto-validation cannot release without QC evidence.

### 5.2 Offline synchronization & event delivery (A06)
- **Owner:** ORCH + user (A06-002 release) + clinical owner + A07/A09.
- **Dependencies:** USER release of the patch; certification halt on A06-001 + A06-002; real server/transport for A06-001.
- **Batches:** (1) A06-002 patch review/adoption [P0]; (2) A06-001 relabel + real test harness [P1, certification gate]; (3) A06-013/014/017/020 outbox + idempotency; (4) A06-003/004/005/012 architecture; (5) A06-006/016/018 clinical merge semantics; (6) P2/P3 cleanup.
- **Tests:** the 31 designed tests in `TEST_BASELINE_PLAN.md §3` plus new receive-replay-after-resolution, concurrency, and durability tests.
- **Acceptance:** no silent clinical overwrite; idempotency across reconnect *and* replay; honest CRDT claim; certification evidence machine-readable.

### 5.3 Security & identity (A04)
- **Owner:** SEC approver + A04 implementer + A07/A09 support; user release for A04-002 file.
- **Batches:** (1) A04-001/002/003 NIAM step-up, logout auth, token binding [P1]; (2) A04-004/005/006/008 OAuth2 + password policy [P2]; (3) A04-007/009 token-in-query + bcrypt perf; (4) P3 hardening.
- **Tests:** route-auth matrix; negative tests for anonymous logout, terminated-token access, arbitrary redirect; regression for protected user work.
- **Acceptance:** every NIAM route has an enforced dependency; no anonymous session termination; no committed live secret; `.gitignore` coverage verified.

### 5.4 FHIR & database integrity (A05-006…008 + A07)
- **Owner:** DB-API approver + clinical/interop owner + A07 implementer + A09 tests.
- **Dependencies:** DB-API approval; A05 clinical sign-off; **no DB execution** in this program; forward migrations only.
- **Batches:** (1) A05-007 transaction atomicity [P0]; (2) A07-014 cascade + A07-015/016 untracked migrations [P1/P2, USER]; (3) A07-001 tenant typing + A07-008 OpenAPI stub; (4) A05-003/006/008; (5) A07-002/009/010/011/017 contracts; (6) P3.
- **Tests:** failure-injection proving rollback of earlier entries; migration graph static integrity; contract schema tests; tenant-isolation tests.
- **Acceptance:** a failing transaction entry leaves zero partial writes; no destructive cascade; OpenAPI artifact non-empty and version-consistent.

### 5.5 frontend-v3 design system & UX (A02)
- **Owner:** A02 implementer; A03 consumer coordination; A08 CI for gate wiring; visual/a11y reviewer.
- **Batches:** (1) A02-001 token alias fix [P1, downgraded]; (2) A02-002/004/006/007 a11y improvements; (3) A02-003/005/009/010 HTML shell + RTL; (4) A02-008/011…015/018/021; (5) dedup with A09-010 (contrast rule re-enable **after** token contrast fixed); (6) P3.
- **Tests:** token→utility generation assertion, axe contrast after fix, visual snapshots for Modal/EmptyState/Skeleton.
- **Acceptance:** every shipped utility class resolves to generated CSS; contrast ≥ WCAG thresholds; no flash of wrong theme.

### 5.6 DevOps & reliability (A08)
- **Owner:** ORCH (A08-R001 containment) + CI/release owner + A04 for security-sensitive workflows.
- **Batches:** (1) A08-R001 containment [P0]; (2) A08-001/002 + R002…R006 pipeline/deploy [P1]; (3) DEDUP-01 gate wiring + A08-003/004/005/008/010/011/013; (4) R008/R009/R010 backup/DR; (5) P3.
- **Tests:** script static guard tests; workflow trigger simulation; YAML lint; no destructive script execution.
- **Acceptance:** `emergency-recover.sh` cannot be executed without dirty-tree guard + explicit flag; deploy triggers reference real workflows; pipeline cannot pass with zero tests.

### 5.7 Testing & CI quality gates (A09)
- **Owner:** A09 + user release for USER-owned files + A08 CI.
- **Batches:** (1) A09-001/002 no-op secret guard + `--passWithNoTests` [P1]; (2) A09-003 branch triggers; (3) A09-005/008/009/012 assertion + E2E fixes; (4) DEDUP-01/A09-011; (5) P3 + artifact capture.
- **Tests:** mutate-to-assert checks proving tests fail when behavior regresses; CI config assertions; artifact-emission verification.
- **Acceptance:** every gate emits a machine-readable artifact with exit code; zero unfalsifiable assertions; no CI pass with zero tests.

### 5.8 Architecture & structural (A01 — 8th domain)
- **Owner:** ORCH + ARCH approver + A01 reviewer; **no direct write** by A01.
- **Content:** A01-001…004 duplicate app trees; A01-005…009 services/cycles/composition; A01-011 stale gate catalog; A01-012…019 manifests, workflow engines, FHIR duplication, shared fan-in.
- **Approach:** ADR-led decisions first; no structural change until an ADR names the canonical surface and migration path.
- **Acceptance:** ADR per structural decision; no vendor coupling; architecture docs updated to verified state.

---

## 6. CONFLICT_QUARANTINE formal review — summary

Full formal report: **Appendix A of this document**. Verdict:

- The patch is a **genuine clinical-safety improvement** over HEAD and is **safe to propose for formal adoption in principle**.
- It is **NOT VERIFIED**: 0 tests were executed this session (see `TEST_BASELINE_PLAN.md`).
- Remaining risks: (R1) receive-layer replay can reset a resolved conflict; (R2) no thread-safety around the idempotency guard; (R3) metadata key namespace collision; (R4) in-memory state → no cross-restart idempotency/durability; (R5) enum string removal backward compatibility (no in-repo production consumer found); (R6) the untracked companion test file is itself protected user work.

---

## 7. Isolation position

In-place remediation is **rejected**. Clean clone from HEAD exists but lacks user work and `node_modules`. The only viable path to test the patch is a clone plus **explicitly approved replication of three named user files**; that replication is **not performed** here. See `ISOLATION_OPTIONS.md`.

---

## 8. Test-baseline position

Dependencies are present (python3 3.10.12, pytest 9.1.1, cryptography 49.0.0; `backend/pytest.ini`, `backend/tests/conftest.py` exist). A09 found **0 machine-readable artifacts**; all historical pass/fail counts (including "31 tests, 31/0") are **CLAIM — UNVERIFIED**. 31 tests are designed in `TEST_BASELINE_PLAN.md`; **0 executed**. No DB, migration, service, or production command will be run. See `TEST_BASELINE_PLAN.md`.

---

## 9. Exact decisions required from the user

1. **USER release** of `backend/app/services/offline_sync_service.py`, `backend/tests/test_offline_sync.py`, and untracked `backend/tests/test_offline_conflict_synthetic.py` for isolated replication (or provide a clean commit containing them).
2. **Isolation choice** among the options in `ISOLATION_OPTIONS.md` (recommended: Option D — clone + named-file replication, after release).
3. **Severity acceptance**: confirm downgrade of A02-001 and A06-001 to P1, with certification halt on A06-001 + A06-002 retained.
4. **Approvals**: name SEC, CLIN, DB-API, ARCH, and CI owners for the batches in §5 / `APPROVAL_MATRIX.md`.
5. **A08-R001 containment**: approve documentation notice + guard design (original file must **not** be edited or moved without separate approval).
6. **Baseline authorization**: approve executing the 31 designed tests in the isolated clone after release; confirm no DB/service operations.
7. **A01 architecture**: decide whether to open ADRs now or defer structural findings to a separate program.

**Until these decisions are made: no source modification, no Git state change, no DB operation, no production deployment, no new agents.**

---

## Appendix A — CONFLICT_QUARANTINE Formal Review Report

### A.1 Scope and method
Read-only review of the unstaged user patch in `backend/app/services/offline_sync_service.py` (95 +/− lines) and `backend/tests/test_offline_sync.py` (33 +/− lines), plus dependent untracked `backend/tests/test_offline_conflict_synthetic.py`. Methods: full `git diff`, full-file read, repo-wide reference search (`ConflictResolution`, `CRDT_MERGE`, `crdt`, `resolve_conflict`), production wiring checks, and static reasoning. **No file was modified, staged, committed, merged, or discarded; no test was executed.**

### A.2 Change set (complete, including dependencies)
| File | Git state | Role |
|---|---|---|
| `backend/app/services/offline_sync_service.py` | ` M` (unstaged) | Replacement of `CRDT_MERGE` with `CONFLICT_QUARANTINE`; idempotency guard; `resolved_at`; provenance; audit enrichment; defensive copies |
| `backend/tests/test_offline_sync.py` | ` M` (unstaged) | Renamed test `test_crdt_merge` → `test_conflict_quarantine_preserves_both_versions`; assertions for both-version retention, no auto-selection, idempotent replay |
| `backend/tests/test_offline_conflict_synthetic.py` | `??` (untracked USER) | 11 synthetic tests; explicitly disclaims CRDT convergence and crash durability (E-055) |

No production caller of `ConflictResolution` exists elsewhere in `backend/` (only the two test files import the service). Stale references remain only in evidence artifacts (`security-audit/bandit.json`, `backend/.pytest_cache/.../nodeids`) and governance docs — all non-executing.

### A.3 Correctness evaluation
- **Contested-key handling (correct):** for keys present in both ops with unequal values, both versions are retained under `_conflicts` with full provenance (`operation_id`, `device_id`, `user_id`, `timestamp`, `vector_clock`, deep-copied `value`); the key is excluded from the merged projection. No clinical value is auto-selected; timestamps are recorded but never used to order/overwrite. This directly removes the HEAD first-seen-wins overwrite.
- **Agreement merge (correct):** equal values and single-sided keys are merged with `deepcopy`.
- **Idempotency, sequential (correct):** `if conflict.resolved_at is not None` returns a deep copy of the stored result and emits no second audit row. `resolved_at=0.0` is handled correctly (`is not None`).
- **Deterministic time (correct):** optional keyword-only `resolved_at` sets both `ConflictRecord.resolved_at` and the audit timestamp.
- **Audit enrichment (correct):** `operation_a_id`, `operation_b_id`, `status`, `contested_keys`, `timestamp`.
- **Defensive copies (correct):** `copy.deepcopy` on stored/returned results prevents caller mutation of engine state.

### A.4 Clinical safety
Positive: the patch is fail-safe by construction — contested clinical values are preserved, not chosen. It does **not** solve A05-001 (critical-result delivery) or A03-003 (approval separation). It does not claim CRDT convergence (correct). It does **not** add durable storage (in-memory).

### A.5 Remaining risks (must be resolved before adoption/certification)
- **R1 (high) — receive-layer replay resets resolution.** `receive_operation` does not store a conflicting incoming op in `_operations`; replaying it finds the first op again, builds a **new** `ConflictRecord`, and overwrites `self._conflicts[conflict_id]`, clearing `resolved_at`. A subsequent resolve emits a second audit row. Not covered by the 31 tests (they replay `resolve_conflict`, not `receive_operation`). **Required test:** resolve → replay incoming op → assert one audit row and unchanged resolution.
- **R2 (medium) — concurrency.** No lock around the check-then-act idempotency guard; two concurrent `resolve_conflict` calls can both pass and double-log. **Required test:** threaded/async concurrent resolution with a single audit row.
- **R3 (low) — metadata namespace collision.** Data keys named `_conflicts`, `_resolution_status`, or `_message` are overwritten by metadata. **Required test/fix:** reserve or escape metadata keys.
- **R4 (high for certification) — no durability.** All state is in-memory (F-028). Cross-process restart loses resolution; "idempotent/replayable" is process-local only. Certification must remain halted until durability is proven or explicitly scoped out.
- **R5 (low) — backward compatibility.** Enum value `"crdt_merge"` removed; any external/persisted string would not deserialize. No in-repo production consumer or persisted value found; evidence artifacts are stale but non-executing.
- **R6 (process) — protected work.** The companion 11-test file is untracked user work; the patch cannot be committed or replicated without USER release.

### A.6 Adoption recommendation
**Safe to propose for formal adoption in principle** as a clinical-safety improvement over HEAD. **NOT verified** (0 tests executed). Adoption is conditioned on: (a) USER release; (b) R1 and R2 regression tests added and passing in isolation; (c) R3 decision; (d) R4 explicitly scoped; (e) clinical + SEC + ORCH approval. Clinical synchronization certification remains **HALTED** until A06-001 **and** A06-002 are resolved and verified.

### A.7 Reproduction procedure (safe, read-only — no execution of patch)
1. `git diff -- backend/app/services/offline_sync_service.py backend/tests/test_offline_sync.py` — observe enum rename and quarantine branch.
2. `git show HEAD:backend/app/services/offline_sync_service.py | sed -n '19p;176,182p'` — observe HEAD `CRDT_MERGE` first-seen-wins.
3. `grep -rn "CRDT_MERGE\|crdt_merge" backend --include=*.py` — confirm no production caller.
4. Static R1 reproduction by inspection: `receive_operation` (lines 121-140) vs `_detect_conflict` (293-309) vs `resolve_conflict` (154-271) — the conflicting op is never added to `_operations`, so replay re-creates the record.
5. Do **not** run the script-based simulation (`gula_offline_simulation_test.py`) as verification — it is A06-001's false-claim artifact.
