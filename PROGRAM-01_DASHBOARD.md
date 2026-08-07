# PROGRAM-01 Dashboard

**Permanent program metrics for the Structural Migration.**
**Status:** Active
**Date:** 2026-08-07
**Baseline:** `.ai/core/architecture/constitution_baseline.json` — **48 acknowledged findings** (+ 2 country findings)
**Authority:** PROGRAM-01 Execution Framework §7 (metric definitions, owners, trend rules).

---

## 1. Metric Definitions (framework §7)

| # | Metric | Definition | Owner | Trend rule |
|---|---|---|---|---|
| M1 | **Architecture Health** | Gate verdict: constitution / domain / country / policy | Architecture gate | Always PASS |
| M2 | **Technical Debt** | Active-tree LOC, duplicate implementations, archived modules | Architect engine + migrations | Active shrinks; duplicates shrink |
| M3 | **Remaining Findings** | Acknowledged Shared Core findings in baseline | Architecture baseline | Monotonically non-increasing |
| M4 | **Shared Core Progress** | Findings migrated / total (48) | Migration program | Monotonically increasing |
| M5 | **Migration Progress** | Certified migrations / planned (by wave) | Migration program | Monotonically increasing |
| M6 | **Production Readiness** | Quality-gate summary (tests, ruff, tsc, eslint, CI) | Validation engine | Always green; improving |
| M7 | **Repository Size** | Active LOC vs archived LOC vs net | Architect engine | Active shrinks; archive grows; net stable |
| M8 | **Duplicate Implementations** | Active-tree duplicate Shared Core implementations | Architecture scan | Monotonically decreasing |
| M9 | **ADR Count** | Accepted ADRs governing the migration phase | Architecture decisions | Monotonically increasing |
| M10 | **Risk Trend** | Open risks, escalations, STOPs | Risk register | Non-increasing open risk |
| M11 | **Certification Level** | Waves certified / total (6) | Certification model | Monotonically increasing |

---

## 2. Current State (as of Commit 1.8)

| # | Metric | Current value | Trend |
|---|---|---|---|
| M1 | Architecture Health | **PASS** (46 ack, 0 new · domain 11/11 · country PASS · policy PASS) | Stable |
| M2 | Technical Debt | 379 ruff baseline (fixed); active-tree LOC **−599** cumulative | Improving |
| M3 | Remaining Findings | **46** (from 57 original) | ↓ 11 removed |
| M4 | Shared Core Progress | **11 / 57** original findings migrated (8 archives + 1 promotion + 2 false-positive fixes); **46 remain** | Increasing |
| M5 | Migration Progress | **6 implementation migrations certified** (1.1, 1.2, 1.3, 1.6, 1.7, 1.8) + **2 signal-precision fixes** (1.4, 1.5) | Increasing |
| M6 | Production Readiness | backend ≥ 4993 tests 0 fail; ruff 379 baseline; tsc 0; eslint 0; validate fast PASS | Stable |
| M7 | Repository Size | active LOC shrinking; archive = **8 modules** (+75 LOC national audit module) | Active ↓ |
| M8 | Duplicate Implementations | 46 remaining findings (duplicates being removed one per commit) | Decreasing |
| M9 | ADR Count | **34 ADRs** (incl. ADR-027/028/029 governing this phase; ADR-030/031/032/033/034/035/036 planned) | Increasing |
| M10 | Risk Trend | 0 open escalations; no STOPs in Commits 1.1–1.8 | Stable |
| M11 | Certification Level | **0 / 6 waves** certified (Wave 1 in progress: orders 5 done, 6–11 pending) | Pending |

\* False-positive fixes (1.4, 1.5) removed baseline entries via signal-precision
corrections rather than code migration; counted as finding removals, not
archives.

## 3. Shared Core Progress Detail

| Capability | Original findings | Remaining | Migrated |
|---|---|---|---|
| encryption | 3 | 2 (#1, #2 in Wave 5) | #3 archived (Commit 1.6) |
| audit | 7 | 5 | #6 AuditLogger (1.7), #7 national SecurityAuditService (1.8) archived |
| dependency_injection | 1 | 1 | — (Retain, Wave 6) |
| search_engine | 2 | 1 (#35+#36 Wave 3) | #38 false-positive removed (Commit 1.4) |
| authentication | 3 | 2 | #51 false-positive removed (Commit 1.5) |
| *remaining capabilities* | *—* | *by roadmap* | *Wave 1–6* |

Full per-capability table: `docs/baselines/ARCHITECTURAL_MIGRATION_CLASSIFICATION.md` §2.

---

## 4. Wave Status Board

| Wave | Orders | Status | Baseline target | Certification |
|---|---|---|---|---|
| **Wave 1** — Low-risk archive & false positives | 1–11 | **IN PROGRESS** (orders 1–5 done: #38, #51, #3, #6, #7) | 48 → 37 | Not certified |
| **Wave 2** — Canonical Provider Promotion | 12 | Not started | → 36 | — |
| **Wave 3** — Canonical Provider Completions | 13–15 | Not started | → 33 | — |
| **Wave 4** — High-risk infrastructure | 16–19 | Not started | → 29 | — |
| **Wave 5** — National Platform migrations | 20–22 | Not started | → 26 | — |
| **Wave 6** — Kernel exception + Retain register | 23–24 | Not started | → **0 actionable** | Program certification gate |

**Commit log (this program):**

| Commit | Finding | Action | Baseline |
|---|---|---|---|
| 4b115f32 (1.1) | platform facades ×4 | Archive | 57 → 53 |
| 576ade1d (1.2) | #20 identity/events | Archive | 53 → 52 |
| b393aac3 (1.3) | #48 workflow engine | Canonical promotion | 52 → 51 |
| 7ec3536c (1.4) | #38 search (false positive) | Signal fix | 51 → 50 |
| 2ceb373c (1.5) | #51 auth (false positive) | Signal fix | 50 → 49 |
| bf52a744 (1.6) | #3 EncryptedSyncStore | Archive | 49 → 48 |
| 6c35ead6 (1.7) | #6 AuditLogger | Archive | 48 → 47 |
| *(1.8, pending hash)* | #7 SecurityAuditService | Archive | 47 → 46 |

---

## 5. Escalation & Risk Trend

| Metric | Value |
|---|---|
| Open escalations | 0 |
| STOPs (blocking) | 0 |
| Behavior mismatches | 0 |
| API incompatibilities | 0 (OpenAPI byte-identical throughout) |
| Frontend incompatibilities | 0 |
| Security regressions | 0 |
| Baseline growth incidents | 0 |

Maintained in `MASTER_RISK_REGISTER.md`; any escalation per framework §6 is
recorded here immediately.

---

## 6. Dashboard Update Protocol

- Updated at **Stage 10** of every migration lifecycle (framework §1).
- Values must reconcile with: baseline JSON, gate output, latest
  `COMMIT_X_Y_VERIFICATION_REPORT.md`, `MASTER_REMAINING_WORK.md`,
  `ARCHITECTURE_CERTIFICATION.md`, `PROJECT_BRAIN.md`.
- **Any trend rule violation** (e.g., findings grew, a wave regressed) is a
  framework §6 escalation: STOP and record.
- Certification markers are appended here at each wave completion
  (framework §9).
