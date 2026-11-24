# GULA MASTER COMPLETION SCORECARD — BASELINE v1.0

**Generated:** 2026-11-20 (UTC) · **Repo:** `gula-integration` · **Branch:** `integration/gula-unification-v1`
**HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549` · **Protected sibling HEAD:** `f478676b6fc375338648dde46fbf076c015a3f91`
**Data class:** SYNTHETIC ONLY — no PHI, real patient data, production DB or secrets used.

> **Authority:** MASTER-MANDATE-1.0 + OWNER AUTHORIZATION (accelerated completion / GitHub preservation, 2026-11-20).
> **Release posture:** **HOLD** · Stable v1.0.0 **NOT declared** · `PRODUCTION READY` **NOT authorized** · `production_ready_items = 0`.

## 0. Scoring rules (non-negotiable)

Each status is counted **separately** and never merged:
1. `IMPLEMENTED` — code/config exists and is attributable to a named package.
2. `TESTED` — focused automated test executed green in an isolated non-production environment; command + count recorded.
3. `INDEPENDENTLY REVIEWED` — fresh-context reviewer returned a verdict with no unresolved CRITICAL/HIGH.
4. `ACCEPTED` — owner-recorded, package-scoped acceptance. Only OD-001 is accepted (SEC-015/F-01 engineering scope).
5. `PRODUCTION READY` — never awarded in this scorecard (no release gate passed).

Completion % = (tested ∧ independently reviewed) / requirements. `ACCEPTED` and `PRODUCTION READY` are reported but never used to inflate %.

## 1. Measured repository facts (Section A inventory)

| Metric | Measured value | Source |
|---|---|---|
| Backend Python source files | 2,045 | `find backend/app -name '*.py'` |
| Backend test files | 349 | `find backend/tests -name 'test_*.py'` |
| Backend test functions (static) | 4,526 | `grep -rh 'def test_' backend/tests` |
| Full-suite collection (registry baseline) | 4,675 collected, 0 errors | `status_registry.json` → `baseline.full_suite_collection` |
| Migrations | 113 | `find backend -path '*versions*' -name '*.py'` |
| Route modules / service modules | 63 / 63 | `find backend/app/{routes,services}` |
| Frontend TSX components | 131 | `find frontend-v3/src -name '*.tsx'` |
| Root markdown reports | 181 | `find . -maxdepth 1 -name '*.md'` |
| Workstreams (registry) | 7 (WS-01…WS-07) | `status_registry.json` |
| Program phases (registry) | 5 (A…E) | `status_registry.json` |
| Audit findings AUD-F01…F21 | 21 | `GULA_AUDIT_SECURITY_FINDINGS.md` |
| Open PRs relevant | #307 Draft (do not modify), #285–306 dependabot | `gh pr list` |

**Finding severity (21 total):** conditional-HIGH 1 (AUD-F15, only when `ENABLE_FINANCIAL_ENGINE=true`; MEDIUM by default): MEDIUM 7 (F01–F04, F16–F18) · LOW 11 (F05–F12, F19–F21) · INFO 2 (F13–F14).

**Test targets vs measured inventory (planning targets, NOT claims):**
Unit 800–1,200 · integration/DB 250–400 · identity/authz/audit 200–300 · API/FHIR 150–250 · offline/sync 100–150 · security/tenant 100–150 · E2E 80–120 · performance/resilience 30–50. Measured static test functions = 4,526 (aggregate; per-category classification not yet produced — tracked as a scorecard gap, not filled with fabricated numbers).

## 2. Scorecard by domain

**Recount correction (2026-11-20, owner-requested):** the draft's "4 / 37 = 10.8%" was
**not reproducible** from the table (Req summed to 36, and the reviewed-column
sum did not support the numerator). It is withdrawn. The corrected, fully
recomputable scope below is **29 requirement items = 21 AUD-F findings + 7
workstreams (WS-01…WS-07) + 1 accepted OD-001 package (SEC-015/F-01)**.
Governance/release-readiness is tracked separately and is **not** in this
denominator. Weights are informational and do not affect the percentages.

| # | Domain | Wt | Req | Impl | Tested | Indep. reviewed | Accepted | Prod ready | Remaining | % (reviewed/Req) | Evidence | Risks / blockers |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 1 | Identity & MPI = WS-01 + AUD-F16 (P-16) | 15 | 2 | 2 | 2 | 1 | 0 | 0 | 1 | 50 | P-16 focused 11/11; related 105/105; review PASS WITH CONDITIONS, 5 conditions cleared | workstream-level independent review absent; acceptance owner-gated |
| 2 | Security & audit = WS-02 + AUD-F15 (P-13) + AUD-F17 (P-15) + OD-001 | 15 | 4 | 4 | 4 | 3 | 1 (OD-001) | 0 | 1 | 75 | P-13 8/8+134; P-15 6/6+58; 3 independent reviews 0 CRIT/HIGH | residual R4/L2 owner gates; P-13/P-15 not accepted |
| 3 | FHIR R4 interoperability (WS-03) | 12 | 1 | 1 | 1 | 0 | 0 | 0 | 1 | 0 | registry WS-03 TESTED | no package-level independent review |
| 4 | Terminology (WS-04) | 8 | 1 | 1 | 1 | 0 | 0 | 0 | 1 | 0 | registry WS-04 TESTED | no package-level independent review |
| 5 | Reliability & offline-first (WS-05) | 12 | 1 | 1 | 1 | 0 | 0 | 0 | 1 | 0 | registry WS-05 TESTED | no package-level independent review |
| 6 | Client integration (WS-06) | 10 | 1 | 1 | 1 | 0 | 0 | 0 | 1 | 0 | registry WS-06 TESTED | no package-level independent review |
| 7 | National domains & journeys (WS-07) | 10 | 1 | 1 | 1 | 0 | 0 | 0 | 1 | 0 | registry WS-07 INTEGRATED | no package-level independent review |
| 8 | AUD-F01 dormant raw audit writer (P-01) | 3 | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 100 | focused 9/9; related 120/9 skipped; review PASS WITH CONDITIONS, 4 conditions cleared | `previous_hash` advisory-only; not accepted |
| 9 | AUD-F04 standalone verifier (P-04) | 2 | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 100 | focused 6/6; related 136/9 skipped; review **PASS**, 0 CRIT/HIGH/MED | L1/L2/INFO residuals; no daemon restart; not accepted |
| 10 | Remaining AUD-F (F02-F03, F05-F14, F18-F21) | 12 | 16 | 0 | 0 | 0 | 0 | 0 | 16 | 0 | `GULA_AUDIT_SECURITY_FINDINGS.md` | owner R0-R4 gates; OD-002..OD-025 blocked |

**Totals — recompute from the Req column:** 2+4+1+1+1+1+1+1+1+16 = **29**.
- IMPLEMENTED: 2+4+1+1+1+1+1+1+1+0 = **13 / 29 ≈ 44.8%**
- TESTED: 13 / 29 ≈ 44.8%
- INDEPENDENTLY REVIEWED: 1+3+1+1 = **6 / 29 ≈ 20.7%** ← engineering-verification figure, **NOT platform completion**
- ACCEPTED: 1 / 29 ≈ 3.4% (OD-001, SEC-015/F-01 engineering scope only)
- PRODUCTION READY: **0 / 29 = 0%**

### 2.1 Status separation checkpoint (2026-11-20, owner-requested)

Statuses are exclusive engineering states. An independent review verdict is **not** owner acceptance,
and owner acceptance of OD-001 is **not** production readiness. No package may be promoted without
its own record.

| Package / item | IMPLEMENTED | TESTED | INDEPENDENTLY REVIEWED | ACCEPTED | PRODUCTION READY | Open conditions |
|---|---|---|---|---|---|---|
| P-13 / AUD-F15 | YES | YES | YES (PASS WITH CONDITIONS, 0 CRIT/HIGH) | NO | NO | owner acceptance; feature-enable decision; retry/double-charge idempotency |
| P-15 / AUD-F17 | YES | YES | YES (PASS WITH CONDITIONS, 0 CRIT/HIGH) | NO | NO | owner acceptance; fail-closed availability trade-off |
| P-16 / AUD-F16 | YES | YES | YES (PASS WITH CONDITIONS, 5/5 conditions cleared) | NO | NO | owner acceptance; F6/F7/F9 residual disclosures |
| P-01 / AUD-F01 | YES | YES | YES (PASS WITH CONDITIONS, 4/4 cleared) | NO | NO | owner acceptance; `previous_hash` advisory-only disclosure |
| P-04 / AUD-F04 | YES | YES | YES (PASS, 0 CRIT/HIGH/MED) | NO | NO | owner acceptance; L1/L2/INFO residuals; no daemon restart; code frozen after review |
| OD-001 / SEC-015 F-01 | YES | YES | YES | **YES — engineering scope only** | NO | no commit/merge/release/deploy authority; no other OD accepted |
| F02 / F03 / remaining R4 | NO | NO | NO | NO | NO | package-specific owner decision required; no implementation started; P-02/P-03 packets independently reviewed **FAIL — NOT DECISION-READY** (2026-11-20), return to preparation |

**This percentage is NOT a platform completion claim.** It measures only whether a
requirement has a passing independent engineering review. It excludes the 11
release reports, clinical/institutional/legal approvals, operations readiness,
and every capability still dormant or unwired. A feature is scored only when
evidence exists; no points are awarded for interfaces, adapters, compilation,
status labels in the registry, or mock/dormant implementations.

## 3. Package status (P-13 / P-15 / P-16 / P-01 / P-04)

| Package | Finding | Status | Focused | Related | Independent verdict | Decision |
|---|---|---|---|---|---|---|
| P-13 Financial audit | AUD-F15 | TESTED + REVIEWED | 8/8 | 134/134 | PASS WITH CONDITIONS (0 CRIT/HIGH) | PASS WITH CONDITIONS |
| P-15 Password reset audit | AUD-F17 | TESTED + REVIEWED | 6/6 | 58/58 | PASS WITH CONDITIONS (0 CRIT/HIGH) | PASS WITH CONDITIONS |
| P-16 MPI identity | AUD-F16 | TESTED + REVIEWED | 11/11 | 105/105 | PASS WITH CONDITIONS (0 CRIT/HIGH), 5/5 conditions cleared | PASS WITH CONDITIONS |
| P-01 Dormant raw audit writer | AUD-F01 | TESTED + REVIEWED | 9/9 | 120 passed / 9 skipped | PASS WITH CONDITIONS (0 CRIT/HIGH), 4/4 conditions cleared | PASS WITH CONDITIONS |
| P-04 Standalone verifier | AUD-F04 | TESTED + REVIEWED | 6/6 | 136 passed / 9 skipped | **PASS** (0 CRIT/HIGH/MED), no blocking conditions | PASS (engineering scope) |

## 4. Open vulnerabilities by severity

- conditional-HIGH: 1 (AUD-F15 — **P-13 implemented+tested**, flag disabled in production posture).
- MEDIUM: 7 → P-15 (AUD-F17), P-16 (AUD-F16), P-01 (AUD-F01), P-04 (AUD-F04, graded LOW in
  `GULA_AUDIT_SECURITY_FINDINGS.md` but listed MEDIUM in this scorecard's inheritance) addressed;
  F02–F03 open.
- LOW: 11 open (F05–F12, F19–F21) · INFO: 2 open (F13–F14).

## 5. Human blockers (require owner decision)

1. R4 owner acceptance of fail-closed availability trade-off on auth path (P-15 L2).
2. **P-02 / P-03: do not sign yet.** Independent review verdict FAIL — NOT DECISION-READY; the
   packets must be rewritten against an explicit HEAD-vs-working-tree baseline, with PostgreSQL
   guard tests, caller-level failure signals, DB session/actor/secret-boundary definitions, explicit
   rejection criteria and a single unambiguous decision text, then re-reviewed. No implementation.
   (`AUDIT_EXECUTION_RECORDS/PACKET_REVIEW_2026-11-20.md`)
3. R4 owner acceptance for P-15 residual L1 (retry/double-charge idempotency key) and other
   dormant-path decisions. P-01/P-04 are engineering-closed only and still require owner
   acceptance; audit-completion is not claimed. The 20.7% figure is engineering verification, not
   platform completion.
4. DeepSeek key rotation and exposure assessment for the pre-existing public `.env` item: status
   **`ROTATION UNVERIFIED`** (`AUDIT_EXECUTION_RECORDS/ENV_INCIDENT_REVIEW.md`); no history rewrite
   authorized.
5. OD-002…OD-025 remain BLOCKED.
6. Release acceptance requires the 11 mandated reports; none awarded.

## 6. GitHub preservation state (Section B)

- Remote: `ssh://git@ssh.github.com:443/samertts/gula-platform.git`; `gh` authenticated (repo scope).
- Manifest: `AUDIT_EXECUTION_RECORDS/GITHUB_PRESERVATION_MANIFEST.md` (827 changed/untracked paths).
- SHA256 registry: `AUDIT_EXECUTION_RECORDS/CRITICAL_FILE_SHA256.txt`.
- Secret scan: 0 real credentials/PHI (only redacted `<DEV_DB_PASSWORD>`, `***`, synthetic CI DSNs).
- PR #307 (`execution/gula-national-completion-013`) exists as DRAFT — **not modified**.
- Backup/integration branches: to be created in the preservation step (not yet executed at baseline).

## 7. Next execution (numbers)

- Phase 1 unified report complete, with the P-01/P-04 addendum (§6).
- GitHub preservation: backup branch pushed and verified at `2206654…`; integration
  branch commit, push and Draft PR remain blocked by mixed provenance and scope sign-off.
- P-13/P-15/P-16/P-01/P-04 are engineering-closed (6/29 reviewed). No further package
  starts without a package-specific owner decision; F02/F03 packets are prepared only.
- Next allowed step: documentation/analysis, or execution of a decided package under a new
  review cycle. No post-review edits to P-04 code.
- Update this scorecard and the status register after each owner decision.

## 8. Preservation verification note

- Manifest and SHA256 registry are regenerated after the P-16 condition fixes;
  the earlier snapshot (untracked 648) was stale relative to the live tree (650).
- A committed `.env` in a **pre-existing 2026-03-08 commit** contains high-entropy
  API-key-shaped values. That commit is already on `origin/main`; my backup push
  introduced **no new exposure**. Recorded as a pre-existing history item in the
  Known Issues Register. No history rewrite, force-push or secret value was produced.
