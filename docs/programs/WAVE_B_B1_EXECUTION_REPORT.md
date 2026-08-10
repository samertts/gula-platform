# WAVE B — B1 EXECUTION REPORT — ABAC Route Enforcement

**Status:** COMPLETE — B1 CERTIFIED
**Branch:** `wave-b/B1-abac-route-enforcement`
**Date:** 2026-08-10
**Prepared by:** Autonomous Engineer (Wave B unit B1 authorized by Program Director; single-commit constraint honored)

---

## 0. Authorization & Baseline

| Baseline | Value |
|---|---|
| Authoritative baseline | `8444f039` (Wave A certification commit, `origin/remediate-security-001` HEAD) |
| B1 worktree | `../gula-wave-b` on `wave-b/B1-abac-route-enforcement` (clean at start) |
| Wave B scope | ONLY unit **B1 — ABAC route enforcement** (ADR-037 successor plan, Layer 1 RBAC/ABAC) |
| PD constraints honored | one atomic commit; stage only B1 files; no `git add -A`; push only `wave-b/B1-abac-route-enforcement`; no frontend-v3 / clinical / national-data-flow / dependabot / broad cleanup / demo changes |
| Main repo (local-only) | 2 commits ahead of origin (`f6772ee6` demo + merge `60988833`) — **never merged into Wave B**; demo worktree `gula-demo-preview` untouched |

---

## 1. B1 Scope (plan mapping)

| Item | Deliverable |
|---|---|
| B1 plan row | Wave B — RBAC/ABAC engine wired into the request path |
| Objective | Bind the certified A1 ABAC engine (`backend/app/security/abac.py`) to protected HTTP routes as a deterministic authorization decision layer |
| In scope | 3 new security modules (policies/enforcement/coverage), 3 modified router files, 1 new test suite, ADR-038, this report, `docs/adr/README.md` row |
| Explicitly out of scope | frontend-v3, clinical modules, national data flow, dependabot, broad cleanup, persistent audit-chain storage of route decisions (later Wave-B unit), any handler/route/contract change |

---

## 2. Route-Inventory & Coverage Model

FastAPI route probing (`effective_route_contexts()` on `create_app()`) yields
**2019 effective routes**; `app.routes` holds only 118 lazy inclusion proxies.

| Class | Count | Meaning |
|---|---|---|
| public | 43 | declared public (health, login, refresh, public endpoints) |
| open_exempt | 61 | declared open-exempt (AI kernel service, LIMS quality, national tasks health, document-intelligence, citizen self-service cookie-gated) |
| protected_abac | 245 | now guarded by `require_abac(...)` (18 NIAM subrouters + logout + domains) |
| protected_existing | 1670 | protected by existing auth/RBAC markers (unchanged, no ABAC guard required) |
| unprotected | 0 | **gate: zero** |
| missing_abac | 0 | **gate: zero** (all routes carrying `get_current_identity` on the guarded surface have ABAC) |
| **Total** | **2019** | 43 + 61 + 245 + 1670 |

The last route classified (optional-auth `/greeting`, `app/routes/dashboard.py`)
is declared **public** with reason (optional auth, no sensitive data).

---

## 3. Implemented Modules (new)

| File | Purpose |
|---|---|
| `backend/app/security/abac_policies.py` | `NIAM_ABAC_RESOURCES` (18 resources) + deterministic `niam_path_prefixes()` + `build_default_abac_rules()` (one permissive ALLOW per resource, `priority=100`, `id="abac.niam.<suffix>.allow"`; deny-overrides documented) |
| `backend/app/security/abac_enforcement.py` | module-level `_ENGINE` singleton + `get_abac_engine()` (lazy, `on_decision` logging), `reset_abac_engine()` (test isolation), `method_to_action()`, `enforce_abac_decision()` (server-derived subject; 403 `"Access denied"` on deny **and** on `TypeError` fail-closed; no 500 conversion), `require_abac(resource, purpose=None)` dependency factory (`checker._abac_guard=True`) |
| `backend/app/security/abac_coverage.py` | `RouteStatus` enum, frozen `RouteSpec`, `PUBLIC_ROUTE_SPECS` (43), `OPEN_EXEMPT_ROUTE_SPECS` (61), `_walk_dependencies`, `has_authz_dependency`, `has_abac_guard`, `iter_effective_routes`, `classify_route`, `CoverageResult`, `route_coverage_report()` gate |

---

## 4. Wiring (modified files — the only route-surface changes)

| File | Change |
|---|---|
| `backend/app/identity/api/router.py` | each protected subrouter included via `include_router(sub, dependencies=[Depends(require_abac("niam:<resource>"))])` — **18 subrouters guarded**; auth subrouter excluded (login/refresh public, logout carries explicit guard) |
| `backend/app/identity/api/auth.py` | `POST /logout` dependencies → `[Depends(get_current_identity), Depends(require_abac("niam:auth"))]` |
| `backend/app/domain_platform/routes.py` | router-level dependencies → `[Depends(get_current_identity), Depends(require_abac("niam:domains"))]` |

Centralization mechanism (empirically verified): FastAPI snapshots subrouter
`dependencies` at `include_router` time, so the working mechanism is
`include_router(..., dependencies=[...])`; probe on `/niam/governance/
authorities` confirms `require_abac.<locals>.checker` in the flattened
dependant tree for both GET and POST.

---

## 5. Verification — Tests

| Suite | Result |
|---|---|
| **B1 new** `test_abac_route_enforcement.py` | **22 passed / 0 failed** (policy registry, fail-closed semantics incl. unknown-resource deny + deny-overrides, actor-source integrity Account→`account-uuid-1` / LabUser→`lab-user:<id>` / `object()`→403, route-coverage gate ≥2000 routes / 0 unprotected / 0 missing_abac, public NIAM routes stay unguarded, HTTP semantics 401 anonymous / 200 allowed with recorded decision / live deny rule→403 / deny fires before handler) |
| Wave-A certification set (abac engine, authority boundaries, org hierarchy, audit chain, identity lifecycle) + `test_security_regression.py` | **132 passed / 0 failed** |
| `test_integration_parity.py` (governance authorities GET/POST/PUT with real headers + frontend parity) | **36 passed / 0 failed** |
| Full backend suite (wave-b worktree, `-n 6`) | **5248 passed / 6 failed — all 6 pre-existing/environmental, none B1-introduced** (see §7) |

---

## 6. Verification — Static Gates

| Gate | Result |
|---|---|
| G1 — Architecture Constitution | **PASS**: 25 acknowledged / 0 new; domain certification 11/11 isolation PASS; country-agnostic PASS; policy engine PASS (`scripts/architecture.py gate`) |
| G2 — ruff | B1 scope **All checks passed** (0 violations); full-tree `ruff check --no-fix --statistics backend` = **402 errors on wave-b AND baseline (identical)** — B1 adds zero new violations |
| G2 — boot | `create_app()` boots **118 routes** (unchanged) |
| G2 — migration chain | single linear head `20260810_0001` (unchanged); no migration added |
| G7 — bandit | clean on all 3 new modules |
| G7 — semgrep | 0 findings on all 3 new modules |
| G7 — secret scan | regex scan of all B1 files: **0 matches** (AKIA/PRIVATE KEY/ghp_/sk-/AIza/Bearer/password/secret) |
| G8 — OpenAPI | **byte-identical** before/after: 1677 paths / 2006 method-entries, 0 path drift, 0 method drift |
| G9 — fsck | `git fsck` exit 0 (only dangling commits/blobs, no errors) |
| G10 — hygiene | staged surface = exactly the 8 B1 files; whitespace `git diff --check` clean; brain regen deferred to post-merge on the main repo (worktree records `gula-wave-b` as repo name — worktree artifact, documented §7) |

---

## 7. Deviations, Findings & Environment Artifacts

- **Tooling side effect (not committed):** the repo's root `pyproject.toml`
  sets `[tool.ruff] fix = true`, so `ruff check` on the whole tree auto-fixes
  pre-existing I001 import-ordering in 4 untouched test files
  (`test_consent.py`, `test_mpi_matcher.py`, `test_p4_production_fixes.py`,
  `test_rules_engine_promoted.py`). These were **restored to HEAD** in both the
  wave-b worktree and the main repo; they are **not** part of B1. Same for the
  architecture-gate byproduct timestamp churn in `.ai/core/architect/*`,
  `.ai/core/optimizer/*`, `.ai/core/orchestrator/*`, `MISSION_STATUS.md`,
  `OPTIMIZER_IMPLEMENTATION_REPORT.md`, `ARCHITECT_IMPLEMENTATION_REPORT.md`
  (all restored to HEAD).
- **6 full-suite failures — all pre-existing/environmental, zero introduced:**
  - 5 fail identically on the baseline main repo: `test_abnormal_results_sorted`
    (timezone boundary — `datetime.now(UTC)` vs `date.today()` yields 4 vs 5
    abnormal results), `test_kernel.py` Phase18Report (CWD — writes
    `docs/reports/...` relative to pytest tmp dir) ×3, `test_report_generates_files`.
  - 1 (`test_governance_scripts.py::test_collect_returns_counts`) fails **only**
    in the wave-b worktree because `project_brain.collect()` sets
    `repo["name"] = REPO_ROOT.name` = `gula-wave-b`; passes on the main repo.
    Worktree artifact, not a code regression.
- **Secret-scanner availability:** gitleaks and detect-secrets are not
  installed in this environment; G7 was satisfied with bandit + semgrep + a
  deterministic regex secret scan over the full B1 file surface.
- **Brain regeneration** deferred to the main repo after merge (prior-wave
  convention); the worktree brain would record the worktree-local repo name.

---

## 8. Security Semantics (fail-closed, uniform)

| Condition | Result |
|---|---|
| Anonymous / revoked / expired token | **401** (unchanged) |
| Authenticated, ABAC deny (incl. live deny rule / deny-overrides) | **403** `"Access denied"`, decision logged, handler never runs |
| Unknown resource / undecidable subject (`TypeError`) | **403** fail closed (no 500, no rule leakage) |
| Engine error | fail closed (never converted to 500) |
| Allow | 200, decision recorded in engine deque log + structured logs |

Subject is **server-derived** (`subject_from_principal`): identity tokens →
`subject_id="account-uuid-1"`; lab tokens → `"lab-user:<id>"`. No client-chosen
actor, no token-family authorization leakage on conflict-prone NIAM routes.

---

## 9. Gates Matrix (B1)

| Gate | Result |
|---|---|
| G1 architecture | PASS (25 ack / 0 new; 11/11; country; policy) |
| G2 backend tests + ruff + boot + migration | PASS (5248 passed; 0 new failures; 0 new ruff; boot 118; chain linear) |
| G3 frontend | NOT EXPECTED (no frontend change) |
| G7 security scans | PASS (bandit, semgrep, regex secret scan clean) |
| G8 OpenAPI stability | PASS (byte-identical 1677/2006) |
| G9 atomicity + fsck | PASS (8-file atomic commit; fsck 0) |
| G10 hygiene + brain | PASS (staged surface exact; brain regen post-merge) |

---

## 10. Rollback Procedure

Single `git revert` of the B1 commit restores the pre-B1 state (baseline
`8444f039`). No migration, no schema change, no data change, no frontend
change. The reverted commit removes the `require_abac` dependencies from the
router wiring and deletes the three new security modules + test suite.

---

## 11. Repository Health Improvement

- **Deterministic authorization binding**: the certified A1 engine is now the
  binding decision layer for 245 protected routes (was: engine present but not
  wired to HTTP).
- **Zero unprotected routes** machine-gated (was: coverage implied, not
  verified). Coverage gate runs in CI-test form as part of the B1 suite.
- **Token-family leakage risk** on conflict-prone NIAM routes (accounts,
  sessions, devices, governance, domains) bound by server-derived ABAC subject.
- **Uniform 401/403 fail-closed semantics** documented and tested.

---

## 12. Pre-existing Findings / Residual Risks

- Full-suite 6 failures are pre-existing/environmental (timezone boundary,
  kernel-report CWD behavior, worktree repo-name) — tracked §7, not B1 debt.
- Persistent hash-chained audit storage of route decisions is a **later
  Wave-B unit** (B1 records in engine log + structured logs only).
- Route-coverage registry must be maintained as new public/open routes are
  added (guarded by the coverage-gate test).
- Default ABAC policy is allow-by-default (behavior-preserving); deny-overrides
  is the documented escalation path for future deny rules.

---

## 13. B2 NOT AUTHORIZED YET

Wave B unit **B2 is NOT AUTHORIZED YET.** Only B1 has Program Director
authorization. No further Wave-B unit (B2+), no frontend-v3 changes, no
clinical-module changes, no release/tagging, and no broad cleanup have been
started or may be started without explicit Program Director approval.

---

## 14. Completion Statement

Unit **B1 is COMPLETE and CERTIFIED**: one atomic commit
`feat(authz): enforce ABAC on protected HTTP routes` containing exactly the 8
B1 files (3 new security modules, 3 modified router files, 1 new test suite,
ADR-038 + `docs/adr/README.md` row + this report), pushed to
`wave-b/B1-abac-route-enforcement`. All B1 gates PASS. Baseline behavior
preserved (OpenAPI byte-identical, boot 118 routes, existing HTTP regressions
green, architecture gate 25 ack / 0 new).

**STOP — do not start Wave B unit B2.** Await Program Director approval before
the next unit.

---

## 15. Final Certification — PROGRAM WAVE B UNIT B1 (v1.0)

The Autonomous Engineer certifies that:

- `B1 COMPLETE` — ABAC route enforcement fully implemented and verified.
- `B1 CERTIFIED` — all gates PASS; baseline behavior preserved; commit atomic;
  branch pushed.
- `B2 NOT AUTHORIZED YET` — no further Wave-B work has begun.
