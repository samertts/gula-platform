# AUTONOMOUS ENGINES REMEDIATION PLAN — Phase 3 (approval-bound, no code repair executed)

**Repository / HEAD:** `gula-integration` · `integration/gula-unification-v1` @ `2827c1ff…` (unchanged)
**Date:** 2026-11-17 · **Category:** A (documentation-only) · **Change record:** CC-005
**Companions:** inventory · verification · findings · dependency map (all `GOVERNANCE/AUTONOMOUS_ENGINES_*.md`)
**Release verdict:** `FINAL_DECISION.md` **HOLD** — this plan cannot lift it.

---

## 1. Governing rule

This phase is authorized for **bounded discovery, isolated synthetic verification, classification and
documentation only**. Every proposed repair below is *recorded, not performed*. The mandate requires
architectural changes, migrations and clinical-behavior changes to have separate approval; test/fixture
changes are category B; production code is category C. Nothing in this plan grants those categories.

**Repairs executed in code: 0.** No engine source, route, worker, test, fixture, conftest, migration,
`env.py`, schema, operational DB, `gula-platform` or Platform-Core file was changed. No engine was
enabled, mounted, restarted or refactored. No new engine was created to fill a gap.

## 2. What was actually delivered (documentation-only repairs)

| Deliverable | Repair effect | Reversibility |
|---|---|---|
| `AUTONOMOUS_ENGINES_INVENTORY.md` | Removes ambiguity between "code exists" and "verified" for 39 engines; explicit 10-status taxonomy | delete file; no code dependency |
| `AUTONOMOUS_ENGINES_VERIFICATION.md` | Adds 7 new evidence records (E-046…E-052, 740 tests) with exact commands/logs | delete file; logs in `/tmp` are independent |
| `AUTONOMOUS_ENGINES_FINDINGS.md` | Adds F-066…F-072 with duplicate-prevention proof; no existing finding rewritten | delete file; registry rows reverted from `ACTIVATION_BASELINE.md` md5s |
| `AUTONOMOUS_ENGINES_REMEDIATION_PLAN.md` | This approval-bound plan | delete file |
| `AUTONOMOUS_ENGINES_DEPENDENCY_MAP.md` | Entry points/dependencies/consumers for safe future change analysis | delete file |

No runtime behavior changed, so a full revert is the deletion of these five files plus the Phase 7
registry row appends (never a code rollback).

## 3. Candidate remediations (proposed — each needs its own approval)

| # | Finding | Proposed minimal repair | Category | Named authority | Risk if done now | Reversibility | Sequence / trigger |
|---:|---|---|---|---|---|---|---|
| 1 | F-066 | Add dedicated synthetic tests for `rules_runtime`, `policy_runtime`, expression engine; **no logic change** | B | QA Lead (explicit authorization) | Low; but test additions without mandate are unauthorized | revert test files only | After Phase 7; independent of ADR-A waves; cannot bypass P0 |
| 2 | F-067 | Add synthetic MDM matcher/merge tests | B | QA Lead | Low; synthetic data only | revert test files only | After F-066; patient-data matching claims stay unverified until then |
| 3 | F-070 | Add synthetic lab-device-gateway tests (parser, mapping, malformed input) | B | QA Lead | Low; no device connection | revert test files only | Independent, after approval |
| 4 | F-072 | Add certification-dimension tests + scope disclaimer next to generated certification output | B | QA Lead + Documentation owner | Low | revert test/doc files | Before any certification artifact is cited |
| 5 | F-068 | Clinical-safety review of 9 permissive exception paths; decide fail-closed semantics; add tests; decide route mount | **C + D-021** | Clinical Safety Owner + Program Director | **High** — changes clinical decision output; wrong default could suppress or fabricate alerts | code revert after approval; no DB change | **Do not act without D-021 sign-off.** Unmounted route stays unmounted |
| 6 | F-069 | Real CRDT with convergence tests **or** accurate rename/gating of `CRDT_MERGE` | **C + D-012** | Architecture + Clinical Safety Owner (offline clinical behavior) | Medium–high — offline clinical merge semantics | code revert after approval | After ADR-J (D-012) decision; linked to F-028 (in-memory queue) |
| 7 | F-071 | None — keep `capabilities/workflow_engine` dormant | — | Architecture | Activation would add a second, untested workflow engine | archival/removal would be a separate ADR | **Never activate**; canonical engine is `app/workflows/engine.py` |

**Sequencing principle:** items 1–4 are test-only and cannot bypass unresolved P0 blockers (B-005…B-010,
B-015). Items 5–6 change clinical/offline behavior and are gated by D-021 / D-012. Item 7 is a no-op.

## 4. Explicitly not authorized (recorded, not executed)

- Any change to `backend/app/**` (category C) — including "small" fixes to swallowed exceptions,
  conflict resolution, route mounting, rate limiter or certification logic.
- Any test/fixture/conftest/CI edit (category B) — including the seven proposed test additions above;
  they are **proposals** until QA authorization exists. W-031 (fixture leak) remains pending approval.
- Any migration, DDL, `alembic stamp`, schema change or operational-DB action (category D). The
  NR-011 `env.py` change (E-041) is complete and must not be re-edited without new evidence.
- Architecture changes, service-boundary changes, ownership model changes, Shared Core changes,
  adoption of ADR-C…ADR-J (category E). D-001…D-004 approvals are limited to their recorded scopes.
- Enabling dormant surfaces (ENG-A12 scaffold, ENG-B09 national CDS route), adding dependencies,
  building dashboards, starting a QA campaign, rerunning the 872-test strict suite without a trigger.
- Closing D-020 or D-021, lifting HOLD, publishing RPO/RTO numbers, claiming clinical certification,
  claiming runtime or production verification, or attributing this work to security/clinical reviewers.
- Commit, push, merge, PR, deploy, destructive Git, `git add .` / `git add -A`, touching `gula-platform`.

## 5. Approval request text (to be presented, not self-granted)

1. **QA (category B):** "Authorize bounded synthetic tests for F-066, F-067, F-070 and F-072 only;
   no existing test, fixture or conftest to be edited; each new test file reversible; evidence to
   receive a new E-ID."
2. **Clinical Safety Owner + Program Director (D-021, category C):** "Decide fail-safe semantics for
   the nine permissive exception paths in `app/national/services/cds_engine.py` and whether the CDS
   route is shipping. No behavior change is authorized until this decision is recorded."
3. **Architecture + Clinical Safety (D-012/category C):** "Decide whether `CRDT_MERGE` is a real
   convergence feature (implement + test) or a mislabeled first-wins strategy (rename/gate)."
4. **No approval requested** for: F-071 (keep dormant), the 740-test evidence set (already executed
   from existing suites), or the five documentation artifacts (category A).

## 6. Verification and rollback for this plan

- **Verification of the documentation work:** registry row counts, unique IDs, cross-references,
  HOLD md5 unchanged, HEAD/branch unchanged, no new code delta — performed in Phase 7.
- **Rollback:** delete the five `GOVERNANCE/AUTONOMOUS_ENGINES_*.md` files and remove only the
  appended Phase 3 registry rows (baseline md5s in `ACTIVATION_BASELINE.md` define the exact prior
  state). Because no code changed, no build, migration or runtime rollback is needed.
- **Re-execution rule:** the seven test batches (E-046…E-052) have a documented purpose and are not
  rerun without a new trigger (changed engine source, failed acceptance, new dependency).

## 7. Hand-off statement

The safe independent work of Phase 3 is complete: engines are discovered, classified and evidenced;
gaps are recorded as findings with named authorities. Everything that would change behavior,
tests, schema or release status is parked behind the approvals above. **No approval is inferred from
this plan, and `FINAL_DECISION.md` remains HOLD.**
