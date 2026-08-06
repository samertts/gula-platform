# Commit 0.2 Verification Report

**Commit:** `7205c4d1` + `4789b4af` — `feat(domain-platform): architecture policy engine foundation (ADR-027)`
**Strengthening commit:** `1173d8b4`
**Hardening commit:** `516e3a65`
**Branch:** `remediate-security-001`
**Date:** 2026-08-06

This report is the permanent verification record for Commit 0.2 of the
migration program: the **Architecture Policy Engine** — a generic governance
framework in which the Dormancy Policy (ADR-026) is the first implemented
policy, and nine further policies are registered for future enablement.

---

## 1. What Changed

| File | Change |
|---|---|
| `backend/app/domain_platform/policies/core.py` | New: Policy Engine — `Policy` Protocol, `PolicySeverity`/`PolicyStatus`, `PolicyFinding`/`PolicyResult`, `PolicyContext`, `PolicyRegistry`, `PolicyWaiver`/`PolicyBaseline` (waivers), `PolicyReport` (JSON + Markdown), `PolicyEngine` (deterministic run loop, **no timestamps/durations** — byte-reproducible output) |
| `backend/app/domain_platform/policies/dormancy_policy.py` | New: `DormancyPolicy` — the first implemented policy (ports certification check-10 semantics) |
| `backend/app/domain_platform/policies/future.py` | New: 9 registered-but-disabled future policies (lifecycle, domain ownership, production readiness, shared core, dependency, cross-domain comms, API governance, security, data governance) |
| `backend/app/domain_platform/policies/__init__.py` | New: `POLICY_CATALOG` (10 names), `build_default_registry()` |
| `backend/app/domain_platform/certification.py` | Check 10 delegates to `DormancyPolicy` (backward compatible; 10 checks unchanged); WARN now maps to `passed=True` so undeclared-module Domains still certify |
| `backend/app/domain_platform/policies/dormancy_policy.py` | `DORMANCY-003` severity `info`→`minor`: an undeclared-modules Domain now **WARNs** instead of silently passing |
| `scripts/architecture/policy.py` | New: repository-mode engine runner + `policy` / `policy-json` / `policy-baseline` commands; baseline payload is purely the waiver list (deterministic) |
| `scripts/architecture/gate.py` | `run_all_gates()` now includes a `policies` section from the engine |
| `scripts/architecture/cli.py`, `scripts/architecture.py`, `scripts/kernel/cli.py` | New commands wired: `architecture-policy`, `architecture-policy-json`, `architecture-policy-baseline` |
| `.github/workflows/ai-governance.yml` | New CI step: `architecture-policy` (ADR-027) |
| `.ai/core/policies/policy_baseline.json` | Committed empty waiver baseline (`{"waivers": []}` — no note text, byte-stable) |
| `docs/adr/ADR-027-architecture-policy-engine.md` | New ADR (determinism clause added); `ADR-026` updated with the ADR-027 delegation + WARN note |
| `backend/tests/unit/test_policy_engine.py` | New: **68 tests** (was 54; + realistic regression scenarios, determinism, config-only enablement, single-implementation) |

## 2. Policy Engine Verification (dedicated)

`python scripts/architecture.py policy` → **PASS** (human report); `policy-json`
→ machine-readable report. Canonical repo verdict:

- registered policies: **10** (1 enabled, 1 executed) — `dormancy_policy` PASS
- disabled (future): lifecycle, domain ownership, production readiness, shared
  core, dependency, cross-domain comms, API governance, security, data
  governance — registered, deterministic `skipped` if run directly, never
  executed by the engine.
- waivers: `PolicyBaseline` loads `.ai/core/policies/policy_baseline.json`
  (empty); any un-acknowledged finding still fails the gate.
- **Deterministic output (byte-identical across runs):** `policy-json`
  produced twice → `diff` empty; `policy` (Markdown) twice → `diff` empty.
  Reports contain no `generated_at` / `duration_ms` fields; status is derived
  from findings; findings are emitted in stable order.

### WARN semantics (DORMANCY-003)

An undeclared-modules Domain now produces a `minor` finding → policy
`WARN` (was `info` advisory-pass). Certification check 10 maps
`PASS`/`WARN` → `passed=True`, so canonical 11/11 certification is
unchanged; the Architecture Gate verdict would surface a WARN for any
Domain that does not declare every module. All 11 canonical Domains declare
everything, so the repo verdict stays **PASS**.

## 3. Final Test Summary

| Suite | Result |
|---|---|
| Complete backend suite (`pytest tests/`, clean env) | **4993 passed / 0 failed / 148 warnings** in 609.73 s (10:09) |
| Policy Engine tests | **71 passed** |
| Dormancy + domain + policy + architecture scope | **206 passed** |
| Frontend suite (`vitest run`) | **122 passed (9 files)** |

## 4. Build Status

- Backend `compileall`: **PASS** (exit 0)
- `tsc --noEmit`: **0 errors**
- ESLint: **0 errors** (1 pre-existing warning in `public/sw.js:65`, untouched)
- `vite build`: **PASS** in 1.78 s
- Kernel self-check: **ALL KERNEL CHECKS PASSED**

## 5. Architecture Constitution Gate

`scripts/architecture.py check` → **PASS**: Shared Core **57 findings
(57 acknowledged, 0 new)**; domain certification **11/11 (isolation PASS)**;
country-agnostic **PASS**; **Policy Engine PASS** (new gate section).

## 6. Domain Certification Gate

`scripts/domains.py check` → **PASS**: isolation PASS, **11/11 certification**.
Check 10 (`dormancy_policy`) now delegates to the shared `DormancyPolicy`;
the 47 Commit 0.1 dormancy tests and all 71 domain tests still pass unchanged.

## 7. API Compatibility & OpenAPI Comparison

Commit 0.2 touches **zero route files**. Byte-level Before-vs-After comparison
(Commit 0.1 snapshot vs Commit 0.2 code):

| Metric | Before | After | Δ |
|---|---|---|---|
| Top-level FastAPI routes | 119 | 119 | 0 |
| Served OpenAPI paths | 1,696 | 1,696 | 0 |
| `paths` dict | — | — | **byte-identical** |
| `components` | — | — | **byte-identical** |

**Verdict: zero API change.** (The concurrent `Depends(get_current_user)`
router hardening committed as `f263f75e` also adds no schema surface —
confirmed identical to the Commit 0.1 snapshot.)

## 8. Frontend ↔ Backend Consistency

The Backend remains the single source of truth. Commit 0.2 changed no
endpoint, model, or guard:

- **API contract compatibility** — unchanged (OpenAPI byte-identical).
- **Request/response models** — unchanged (`components` byte-identical).
- **Frontend consumers** — unaffected; zero frontend files changed; no
  reference to the new policy engine exists or is needed client-side.
- **Generated client types** — consistent (schema unchanged).

**No mismatch.**

## 9. Before-vs-After Metrics

| Metric | Before (Commit 0.1) | After (Commit 0.2) | Δ |
|---|---|---|---|
| Backend suite | 4,922 passed / 0 failed | 4,993 passed / 0 failed | **+71** |
| Governance policies | 1 rule (inlined in check 10) | **10 policies** (1 enabled, 9 registered future) | +9 scaffolded |
| Policy Engine tests | 0 | 71 | +71 |
| Certification checks | 10 | 10 | unchanged |
| Ruff (backend/app) | 379 | 379 | 0 new |
| Architecture gate | PASS | PASS (+ Policy Engine section) | — |
| Domains gate | 11/11 | 11/11 | unchanged |
| OpenAPI paths / routes | 1,696 / 119 | 1,696 / 119 | 0 |
| Frontend tests | 122 | 122 | unchanged |
| CI gates | architecture-check | architecture-check + **policy engine step** | +1 |

## 10. Design Requirements (acceptance)

1. **Not single-purpose** — the Dormancy Check is now a *policy* inside a
   generic engine; the engine is the single governance entry point for CI,
   gates, and certification. ✔
2. **Common interface** — every policy implements the `Policy` Protocol
   (`name`/`description`/`enabled`/`evaluate`). ✔
3. **Independent policy modules** — 10 canonical policies; Dormancy
   implemented, nine registered-but-disabled (no rule bodies, no fake logic).
   ✔
4. **Deterministic results** — fixed registration order, sorted findings,
   stable summaries, **no timestamps/durations**; two runs produce
   byte-identical JSON and Markdown (verified by
   `test_report_is_byte_identical_across_runs`,
   `test_separate_engines_produce_identical_output`, and CLI `diff`). ✔
5. **Machine-readable + human-readable output** — JSON (`to_dict`) and
   Markdown (`render_markdown`) from one report. ✔
6. **Severity levels** — `info`/`minor`/`major`/`critical`; critical/major
   fail, minor warns, info passes. DORMANCY-003 is `minor` (WARN). ✔
7. **Waivers/baselines** — `PolicyBaseline` (committed JSON, `{"waivers":[]}`
   only); waived findings never block, un-acknowledged findings always fail. ✔
8. **Independently testable** — interface fakes + per-policy unit tests
   (68 tests). ✔
9. **Backward compatible** — certification engine callers unchanged, 10
   checks, 11/11 CERTIFIED, all Commit 0.1 tests green. ✔
10. **Not over-engineered** — static Protocol + registry, no plugin/DSL
    machinery; future policies are configuration. ✔
11. **Config-only enablement** — flipping a policy's `enabled` flag (stub or
    registered future) executes it without touching engine/registry
    (`test_flipping_enabled_flag_executes_without_engine_change`,
    `test_future_policy_enabled_by_configuration`). ✔
12. **Single implementation** — `run_policy_gate()` report equals a fresh
    engine run; certification check 10 uses the same `DormancyPolicy` rule as
    the gate; no duplicated governance logic (`TestSingleImplementation`). ✔
13. **Realistic regression scenarios** — PASS declared-active, WARN
    undeclared, FAIL dormant-owned (major), FAIL archived + retired-owned
    (critical), waiver→PASS (`waived==1`), multi-policy verdict aggregation,
    execution-order determinism, registry⇄catalog lockstep
    (`TestRealisticRegressionScenarios`). ✔

## 10A. Final Architecture Hardening Pass

Applied and re-verified end-to-end (all 8 hardening requirements):

1. **Engine stays infrastructure, not a framework** — audited every
   abstraction in `policies/core.py`. Removed the two unused, open-ended
   `PolicyContext` fields (`repo_root`, `extra`) — future-proofing with no
   current value. Everything else is exercised by an implemented policy or a
   report: Protocol, severity/status, finding/result, registry, waiver/
   baseline, report, engine. No plugin/DI/reflection/loading machinery.
2. **Open/Closed Principle** — adding a policy = implement the `Policy`
   interface + register it + set `enabled`; the engine never changes.
   Verified by `test_new_policy_joins_without_engine_modification` (a
   brand-new `naming_convention_policy` joins `build_default_registry()`
   and gates a FAIL without touching `PolicyEngine`).
3. **Complete determinism** — no timestamps, durations, randomness, or
   unordered collections in any output. `PolicyReport`/`PolicyResult` carry
   none; status is derived from findings; findings are emitted in stable
   order. Verified by `test_output_has_no_environment_dependent_fields`
   (JSON contains none of `generated_at`/`duration`/`elapsed`/`timestamp`/
   `random`/`perf_counter`) plus the byte-identical CLI `diff`.
4. **Deterministic execution order** — the registry now exposes canonical
   (name-sorted) order for `names()`, `enabled()`, and `to_manifest()`, so
   execution order and reports are independent of registration sequence or
   environment. `POLICY_CATALOG` is sorted to match. Verified by
   `test_execution_order_is_canonical_not_registration_order` and
   `test_output_identical_regardless_of_registration_sequence` (two
   registries, different registration order → identical `to_dict`).
5. **Single implementation** — Certification (check 10), the Architecture
   Gate (`run_policy_gate`), CLI (`architecture-policy`), and CI
   (`ai-governance.yml`) all consume the same `PolicyEngine`/
   `DormancyPolicy` modules; no duplicated business logic
   (`TestSingleImplementation`).
6. **Accidental-complexity review** — result of the audit above; the only
   removal was the two unused `PolicyContext` fields. No duplicated logic,
   no hidden coupling (certification→policies import is the documented
   ADR-027 delegation), no speculative abstractions retained.
7. **Frontend ↔ Backend sync** — Backend is the single source of truth.
   OpenAPI byte-identical (1,696 paths, paths + components unchanged);
   request/response models unchanged; no frontend references to the policy
   engine; zero frontend files changed; frontend routes and permissions
   untouched.
8. **Complete verification cycle re-run** — see sections 3–9 below with the
   updated numbers (4993 backend, 71 policy, 206 scope, gates PASS, ruff
   baseline 379, OpenAPI byte-identical).

## 11. Rollback Readiness

- Revert: `git revert <commit>` — additive, no schema/data/API change.
- Remove the gate wiring: `architecture.py`/`gate.py` revert restores the
  previous gate shape (policy section is additive).

## 12. Verdict

**GREEN.** Full suite 4,993 passed / 0 failed; both gates PASS (Policy Engine
now inside the architecture gate); build PASS; API surface byte-identical;
Frontend↔Backend consistent (no mismatch); ruff baseline 379 unchanged; policy
engine output is byte-identical across runs and across registration
sequences; OCP and single-implementation guaranteed by dedicated tests;
accidental-complexity audit clean (two unused `PolicyContext` fields removed).
Commit 0.2 is complete. Ready to proceed to **Commit 1.1** — **pending
explicit user approval**.
