# PROGRAM-01 — Wave 2 Certification Report

**Program:** PROGRAM-01 Structural Migration
**Wave:** 2 — Canonical Provider Promotion (order 12, ADR-035)
**Verdict:** **PASS WITH OBSERVATIONS**
**Date:** 2026-08-07
**Certification model:** `PROGRAM-01_CERTIFICATION_MODEL.md` §3 (L2 — Wave Certification)
**Authority:** Wave lead + architecture gate + independent review (L2-7)

This is the permanent L2 certification record for Wave 2 of PROGRAM-01. It
follows the execution of **order 12** — finding #43, the single Canonical
Provider Promotion in the classification — executed as Commit 2.1
(`c4f99768`) with ADR-035 accepted first, per the approved roadmap.

---

## 1. Wave Summary

| Attribute | Value |
|---|---|
| Orders executed | **1 / 1** (order 12, Wave 2 table) |
| Implementation commits | **1** (Commit 2.1, `c4f99768`) |
| Findings removed | **1** (acknowledged baseline **38 → 37**, verified from `constitution_baseline.json`) |
| New findings introduced | **0** (baseline-gated) |
| ADR accepted | **ADR-035** (Rule Engine Promotion) before the migration |
| LOC delta | 0 net move (+14 regression test LOC) |
| Canonical providers orphaned | **0** |
| STOPS / escalations | **0** |
| Rollbacks needed | **0** |

### Execution record

| Commit | Finding | Class | ADR | Baseline Δ |
|---|---|---|---|---|
| 2.1 (`c4f99768`) | #43 `ExpressionEngine` → `shared/rules_engine/engine.py` | Canonical Provider Promotion | ADR-035 | 38 → 37 |

---

## 2. L2 Evidence Matrix

| # | Evidence | Status | Source |
|---|---|---|---|
| **L2-1** | Order L1-certified | ✅ **PASS** | `docs/baselines/COMMIT_2_1_VERIFICATION_REPORT.md` (verification matrix, impact report, dead-code evidence, orphan check, behavior preservation, baseline non-growth, single-revert rollback) |
| **L2-2** | Full §2 matrix re-run on wave's final state | ✅ **PASS** | §3 below |
| **L2-3** | Baseline target met (wave table §8) | ✅ **PASS** | 38 → 37 (1 promoted); matches the roadmap target |
| **L2-4** | 0 NEW findings | ✅ **PASS** | `scripts/architecture.py check` at commit: always `37 acknowledged, 0 new` |
| **L2-5** | Wave-scoped ADR accepted | ✅ **PASS** | ADR-035 accepted before Commit 2.1 |
| **L2-6** | Wave rollback expectations met | ✅ **PASS** | Rollback class L — single `git revert c4f99768` restores the engine to the national namespace and the canonical provider to types-only |
| **L2-7** | Wave certification review | ⏳ **Pending human approval** | This report + objective evidence; sign-off required per §5 |

---

## 3. L2-2 Full Verification Matrix (final state, HEAD `c4f99768`)

| # | Verification | Result |
|---|---|---|
| 1 | Architecture Constitution | **PASS** — 37 findings (37 acknowledged, **0 new**) |
| 2 | Policy Engine | **PASS** — 1 enabled policy evaluated |
| 3 | Domain Certification | **PASS** — 11/11, isolation PASS |
| 4 | OpenAPI | **PASS** — no contract change (route registration untouched) |
| 5 | Generated Clients | **PASS** — no model/contract change |
| 6 | Frontend Compatibility | **PASS** — tsc 0, eslint 0 errors (1 pre-existing warning), vitest **122/122**, vite build OK |
| 7 | Permissions | **PASS** — no route/permission touched |
| 8 | Database Compatibility | **PASS** — no DDL change |
| 9 | Behavior Preservation | **PASS** — live-API smoke (`evaluate_rule` PASS, dict-`evaluate` EQ pass), package re-export identity `is` the canonical engine |
| 10 | Performance | **PASS** — move only; no hot-path change |
| 11 | Regression Tests | **PASS** — backend **4954 passed / 0 failures** (4940 baseline + 14 new rules-engine tests) |
| 12 | Build Validation | **PASS** — boot 119 routes; `py_compile` clean on all touched modules |
| 13 | CI | **PASS** — full suite green (backend + frontend above) |
| 14 | Repository Health | **PASS** — ruff 379 baseline; tsc 0; eslint 0 |
| 15 | Canonical-Provider Orphan Check | **PASS** — promoted engine imports only `shared.rules_engine.domain.*` + stdlib (no `app.*`); national package still consumed by factory router |
| 16 | Ruff on changed scope | **PASS** — 0 remaining (2 I001 auto-fixed) |

---

## 4. Debt Reduction & Health Trend

| Metric | Wave start (38) | Wave end (37) | Δ |
|---|---|---|---|
| Acknowledged findings | 38 | 37 | −1 (monotonic) |
| Country findings | 2 | 2 | 0 |
| New findings | 0 | 0 | 0 (gate held) |
| Canonical provider `rule_engine` | types only | types + engine | populated |

### Health verdict

- **Monotonic improvement**: the single Wave-2 commit reduced the
  acknowledged-findings count; the baseline gate (0 NEW) held.
- **No regressions**: backend 4954/0, frontend tsc 0 / eslint 0 / vitest
  122/122, boot 119 routes, domain isolation 11/11 — all green on the final
  state.
- **Fully reversible**: `git revert c4f99768` restores the previous state
  (rollback class L).

---

## 5. Risks & Observations

### Observations (non-blocking; do not affect certification)

1. **L2-7 sign-off pending.** The certification marker is provisional until the
   independent review (human or reviewer engine) approves this report.
2. **First promotion precedent for a `shared/` (non-`backend/app`) target.**
   Commit 1.3 promoted to `backend/app/workflows`; Commit 2.1 is the first
   promotion into `shared/rules_engine`. Verified: the promoted module has no
   `app.*` imports (Shared Core dependency direction holds) and
   `shared/rules_engine` remains importable in the backend runtime via
   `PYTHONPATH=..`. Documented for future promotions.

### Risks

| Risk | Level | Mitigation |
|---|---|---|
| Rejected re-certification review (L2-7) | Low | Full per-migration evidence in `COMMIT_2_1_VERIFICATION_REPORT.md`; single-commit re-verification without reopening other orders |
| Wave 3 completion risk (notifications #24/#49/#50, capability scaffolds #35/#36/#46/#47) | Medium | ADR-032/033 to be accepted first per roadmap; completion is behavior-additive — will follow the ADR-031 approval-gate pattern |

---

## 6. Recommendation & Verdict

**VERDICT: PASS WITH OBSERVATIONS**

- Order 12 is executed and L1-verified.
- L2-1..L2-6 evidence is **PASS** on the final state (architecture gate,
  domain 11/11, full §2 matrix, 0 NEW findings, baseline target met, ADR-035
  accepted, rollback class met).
- The two observations in §5 are documentation-level — none affects
  correctness, security, or reversibility.
- The wave marker is set in `PROGRAM-01_DASHBOARD.md` (Wave 2 = COMPLETE,
  Certification = **Pending — report + approval**).

**Next step (per framework §8):** the next wave (**Wave 3 — Canonical
Provider Completion**, orders 13–15, #24/#49/#50 notifications + #35/#36/
#46/#47 capability scaffolds, **ADR-032/033 first**) **MUST NOT begin** until
the Program Director approves this certification. **STOPPED pending approval.**

---

## 7. Artifacts

| Artifact | Location |
|---|---|
| Per-migration L1 report | `docs/baselines/COMMIT_2_1_VERIFICATION_REPORT.md` |
| ADR | `docs/adr/ADR-035-rule-engine-promotion.md` |
| Wave board + metrics | `PROGRAM-01_DASHBOARD.md` |
| Classification/order plan | `docs/baselines/ARCHITECTURAL_MIGRATION_CLASSIFICATION.md` |
| Baseline (authoritative) | `.ai/core/architecture/constitution_baseline.json` (37 ack + 2 country) |
| Certification model | `PROGRAM-01_CERTIFICATION_MODEL.md` |
| Governance ADRs | `docs/adr/ADR-027/028/029/035*.md` |
| Regenerated architecture docs | `MASTER_ARCHITECTURE_v2.md`, `SHARED_CORE_REGISTRY.md`, `MASTER_REMAINING_WORK.md`, `ARCHITECTURE_CERTIFICATION.md` |
