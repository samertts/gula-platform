# PROGRAM-01 Dashboard

**Permanent program metrics for the Structural Migration.**
**Status:** Active
**Date:** 2026-08-07
**Baseline:** `.ai/core/architecture/constitution_baseline.json` — **31 acknowledged findings** (+ 2 country findings)
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

## 2. Current State (as of Wave 3 — certified)

| # | Metric | Current value | Trend |
|---|---|---|---|
| M1 | Architecture Health | **PASS** (31 ack, 0 new · domain 11/11 · country PASS · policy PASS) | Stable |
| M2 | Technical Debt | 378 ruff baseline (fixed); active-tree LOC **−2151** cumulative (service archives only); engine promoted (+0 net) | Improving |
| M3 | Remaining Findings | **31** (from 57 original) | ↓ 26 removed |
| M4 | Shared Core Progress | **26 / 57** original findings migrated (15 archives + 3 promotions + 2 false-positive fixes + 1 in-place class archive + 3 completion orders [#24+#49 Commit 3.1, #35+#36 Commit 3.2, #46+#47 Commit 3.3]); **31 remain** | Increasing |
| M5 | Migration Progress | **16 implementation migrations certified** (1.1–1.3, 1.6–1.14, 2.1, 3.1, 3.2, 3.3) + **2 signal-precision fixes** (1.4, 1.5) | Increasing |
| M6 | Production Readiness | backend 0 fail (5030 passed; boot 119 routes); ruff 378 baseline; tsc 0; eslint 0 | Stable |
| M7 | Repository Size | active LOC shrinking; archive = **30 non-test modules** (+7 workflows +2 test files; −364 active LOC) | Active ↓ |
| M8 | Duplicate Implementations | 31 remaining findings (removed/promoted one per commit) | Decreasing |
| M9 | ADR Count | **37 ADRs** (incl. ADR-027/028/029/032/033/035 governing this phase; ADR-030/031/034/036 planned) | Increasing |
| M10 | Risk Trend | 0 open escalations; no STOPs in Commits 1.1–3.3 | Stable |
| M11 | Certification Level | **3 / 6 waves certified** (Wave 1 + Wave 2 **PASS WITH OBSERVATIONS**, approved; **Wave 3 CERTIFIED** `WAVE_3_CERTIFICATION.md`) | Increasing |

\* False-positive fixes (1.4, 1.5) removed baseline entries via signal-precision
corrections rather than code migration; counted as finding removals, not
archives.

## 3. Shared Core Progress Detail

| Capability | Remaining | Migrated (this program) |
|---|---|---|
| encryption | 2 (#1, #2 in Wave 5) | #3 archived (Commit 1.6) |
| audit | 5 | #6 AuditLogger (1.7), #7 national SecurityAuditService (1.8) archived |
| events | 2 (#18 Strategic Exception + #48 Retain, Wave 6) | #17 ESB message_bus archived (Commit 1.9) |
| authorization | 2 (#21+#30 legacy path, Wave 5) | #42 APIAuth archived (Commit 1.9) |
| identity | 2 (#19 Retain, #21 Retain) | #20 national IdentityService archived (Commit 1.10), #22 risk_based_auth_service archived (Commit 1.11) |
| qr_engine | 1 (#41 Retain) | #27 EmergencyQRService + #28 PersistedEmergencyQRService archived (Commit 1.12) |
| notifications | 3 (#23 Retain, #50 Wave 4, #26 Retain) | #25 workflow_runtime WorkflowNotifier archived (Commit 1.13); #24+#49 queue promoted to `backend/app/notifications` (Commit 3.1, ADR-032) |
| workflow_engine | 1 (#44 Wave 4) | #39 national/workflows WorkflowEngine + 5 dormant subclasses archived (Commit 1.14) |
| rule_engine | 0 | #43 ExpressionEngine promoted to `shared/rules_engine/engine.py` (Commit 2.1, ADR-035) |
| dependency_injection | 1 | — (Retain, Wave 6) |
| search_engine | 2 (#34, #37 Retain as Domain-Owned) | #38 false-positive removed (Commit 1.4); #35+#36 doc-intel search promoted to `capabilities/search_service` (Commit 3.2, ADR-033) |
| authentication | 2 | #51 false-positive removed (Commit 1.5) |
| document_engine | 6 (#12, #13, #15, #16 repositories + #14, #45 interfaces — all Retain as Domain-Owned) | #46 routes + #47 service PDF wired to canonical `shared/pdf` via `capabilities/document_management/pdf_generator.py` (Commit 3.3, ADR-033) |
| *remaining capabilities* | *—* | *by roadmap* |

Full per-capability table: `docs/baselines/ARCHITECTURAL_MIGRATION_CLASSIFICATION.md` §2.

---

## 4. Wave Status Board

| Wave | Orders | Status | Baseline target | Certification |
|---|---|---|---|---|
| **Wave 1** — Low-risk archive & false positives | 1–11 | **COMPLETE** (all 11 orders done: #38, #51, #3, #6, #7, #17+#42, #20, #22, #27+#28, #25, #39) | 57 → 38 (19 removed) | **PASS WITH OBSERVATIONS** (`PROGRAM-01_WAVE1_CERTIFICATION.md`) — approved |
| **Wave 2** — Canonical Provider Promotion | 12 | **COMPLETE** (order 12: #43 ExpressionEngine promoted, ADR-035) | 38 → 37 (1 promoted) | **PASS WITH OBSERVATIONS** (`PROGRAM-01_WAVE2_CERTIFICATION.md`) — approved |
| **Wave 3** — Canonical Provider Completions | 13–15 | **COMPLETE & CERTIFIED** (order 13: #24+#49 notifications queue promoted, ADR-032, Commit 3.1; order 14: #35+#36 doc-intel search promoted, ADR-033, Commit 3.2; order 15: #46+#47 document PDF wired, ADR-033, Commit 3.3) | 37 → 35 (order 13); 35 → 33 (order 14); 33 → **31** (order 15) | **CERTIFIED** (`WAVE_3_CERTIFICATION.md`) — pending approval |
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
| 94cb3279 (1.8) | #7 SecurityAuditService | Archive | 47 → 46 |
| 33e1a22f (1.9) | #17 ESBMessageBus + #42 APIAuth | Archive | 46 → 44 |
| c6f906d8 (1.10) | #20 national IdentityService | Archive | 44 → 43 |
| 63d2f2bf (1.11) | #22 risk_based_auth_service | Archive | 43 → 42 |
| 9f52dc2a (1.12) | #27 EmergencyQRService + #28 Persisted* | Archive | 42 → 40 |
| c5ada270 (1.13) | #25 workflow_runtime WorkflowNotifier | Archive | 40 → 39 |
| ff04022c (1.14) | #39 national/workflows WorkflowEngine + 5 subclasses | Archive | 39 → 38 |
| c4f99768 (2.1) | #43 ExpressionEngine → `shared/rules_engine/engine.py` | Promotion | 38 → 37 |
| 231e343b (2.2) | Wave 2 certification doc | Docs | 37 |
| _ (3.1) | #24+#49 identity notification queue → `backend/app/notifications` (ADR-032) | Completion | 37 → 35 |
| _ (3.2) | #35+#36 doc-intel search → `capabilities/search_service` (ADR-033) | Completion | 35 → 33 |
| 537ee5d8 (3.3) | #46+#47 document PDF → canonical `shared/pdf` via `capabilities/document_management/pdf_generator.py` (ADR-033) | Completion | 33 → 31 |
| _ (3.4) | Wave 3 certification docs | Docs | 31 |

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
