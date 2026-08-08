# PROGRAM-01 Certification Model

**The certification authority for the Structural Migration.**
**Status:** Adopted
**Date:** 2026-08-07
**Authority:** PROGRAM-01 Execution Framework §9 (program certification) + §3
(migration exit criteria) + ADR-028 Rule 7.
**Purpose:** define the three certification levels, their evidence, and the
final close-out gate. A migration, wave, or program is certified only on
objective, verifiable evidence — never on intent.

---

## 1. Certification Levels

| Level | Scope | Certified when |
|---|---|---|
| **L1 — Migration Certification** | One migration (one commit + one report) | Exit criteria E1–E11 (framework §3) all pass |
| **L2 — Wave Certification** | One execution wave (all its orders) | All orders L1-certified + wave-level matrix + approval |
| **L3 — Program Certification** | Entire PROGRAM-01 (all 6 waves) | All waves L2-certified + final close-out gate |

Certification is **linear and cumulative**: L3 requires L2 for all waves; L2
requires L1 for all orders. No level can be skipped.

---

## 2. L1 — Migration Certification

### Evidence required

| # | Evidence | Source |
|---|---|---|
| L1-1 | Full verification matrix PASS (framework §2, all HARD + mandatory rows) | `COMMIT_X_Y_VERIFICATION_REPORT.md` §6 |
| L1-2 | Migration Impact Report present (files moved/removed/replaced, duplicates, LOC, deps, API, frontend, rollback) | Report §0 (ADR-028 R4) |
| L1-3 | Dead-code/archive evidence (unused/superseded/duplicated/deprecated) | Report §3 (ADR-028 R2) |
| L1-4 | Canonical provider not orphaned | Report §4 |
| L1-5 | Behavior preservation (runtime/API/business/security/authorization/audit/DB) | Report §5 (ADR-028 R1) |
| L1-6 | Baseline did not grow; 0 NEW findings | Gate output + baseline JSON |
| L1-7 | Independently reversible by single `git revert` | Report rollback section (ADR-028 R6) |
| L1-8 | Exactly one implementation commit for the migration | git log (ADR-028 R7) |
| L1-9 | Independent review approved | Reviewer engine / human approval |

### Decision

All L1-1..L1-9 = **CERTIFIED**. Any missing = **NOT CERTIFIED** — the
migration is re-opened or reverted; certification is re-attempted only after
the fix re-passes the full matrix.

---

## 3. L2 — Wave Certification

### Evidence required

| # | Evidence | Source |
|---|---|---|
| L2-1 | Every order in the wave L1-certified | Dashboard wave board |
| L2-2 | Full §2 matrix re-run on the wave's **final state** | `architecture-check` + validate fast + backend suite |
| L2-3 | Baseline target for the wave met (wave table, framework §8) | Baseline JSON + dashboard |
| L2-4 | 0 NEW findings across the entire wave | Gate output history |
| L2-5 | Any wave-scoped ADRs accepted before the wave's first implementation | ADR log |
| L2-6 | Wave rollback expectations met (per-wave class) | Dashboard + reports |
| L2-7 | Wave certification review (human or reviewer engine) approved | Review record |

### Decision

All L2-1..L2-7 = **CERTIFIED**, certification marker appended to the
dashboard. The next wave may not begin before this marker is set
(framework §8: wave order fixed, no skipping).

---

## 4. L3 — Program Certification (Close-Out)

### Entry condition

- All 6 waves L2-certified (dashboard shows **6 / 6**).

### Final close-out evidence

| # | Evidence | Target |
|---|---|---|
| L3-1 | Baseline: **0 actionable findings** (48 → 0; retained/exception entries documented in the register) | `constitution_baseline.json` + `architecture-check` |
| L3-2 | All required ADRs accepted (ADR-028/029/030/031/032/033/034/035/036) | ADR log |
| L3-3 | Final full matrix PASS on the certified state | Full §2 re-run |
| L3-4 | `ARCHITECTURE_CERTIFICATION.md` regenerated reflecting 0 actionable findings | `scripts/architecture.py report` |
| L3-5 | Master docs + PROJECT_BRAIN consistent | `scripts/architecture/docs.py` + `scripts/project_brain.py --json` |
| L3-6 | PROGRAM-02 Readiness self-assessment attached (framework §10) | `PROGRAM-02` readiness evidence |
| L3-7 | Final certification review approved | Engineering lead / platform architect / CTO |

### Decision

All L3-1..L3-7 = **PROGRAM-01 CERTIFIED — COMPLETE**. The program remains
**open** (uncertified) until then. Program completion triggers PROGRAM-02
Shared Core Consolidation readiness (framework §10).

---

## 5. Certification Authority

- **L1:** migration executor + one independent reviewer (human or reviewer
  engine — `reviewer-verify` / `reviewer-gate`).
- **L2:** wave lead + architecture gate + independent review.
- **L3:** Engineering Lead, Platform Architect, CTO (sign-off required).

No single party certifies their own work at any level without an independent
review.

---

## 6. Certification Failure Handling

| Failure | Action |
|---|---|
| L1 fails | Re-open or revert the migration; re-run full matrix; re-certify |
| L2 fails | Halt the wave; fix the failing order; re-run wave matrix |
| L3 fails | Program remains open; document the gap; schedule remediation wave |
| Baseline growth / new finding | Framework §6 STOP — mandatory escalation; cannot certify |

Certification records are append-only: a certification marker is never
retracted without a documented re-certification event.

---

## 7. Artifacts Index

| Artifact | Content |
|---|---|
| `docs/baselines/COMMIT_X_Y_VERIFICATION_REPORT.md` | Per-migration L1 evidence |
| `PROGRAM-01_DASHBOARD.md` | Wave board + certification markers + metrics |
| `PROGRAM-01_EXECUTION_FRAMEWORK.md` | Lifecycle, matrix, exit criteria, rollback, decision rules, escalation, dashboard, waves |
| `PROGRAM-01_CERTIFICATION_MODEL.md` | This model |
| `docs/baselines/ARCHITECTURAL_MIGRATION_CLASSIFICATION.md` | Wave/order plan |
| `docs/adr/ADR-028…036` | Governance decisions |
| `.ai/core/architecture/constitution_baseline.json` | Acknowledged-findings baseline (shrinks) |
| `ARCHITECTURE_CERTIFICATION.md` | Regenerated certification statement |
