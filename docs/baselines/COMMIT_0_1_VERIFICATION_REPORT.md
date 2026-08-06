# Commit 0.1 Verification Report

**Commit:** `15bd2c81` — `feat(domain-platform): dormancy registry + 10th certification check (ADR-026)`
**Branch:** `remediate-security-001`
**Date:** 2026-08-06

This report is the permanent verification record for Commit 0.1 of the migration
program: the Dormancy Registry (abstraction layer), its canonical data source, and
the 10th Domain certification check `dormancy_policy` (ADR-026).

---

## 1. What Changed

| File | Change |
|---|---|
| `backend/app/domain_platform/dormancy.py` | New: `DormancySource` interface (`Protocol`), `DormancyRegistry` (in-memory), `JsonDormancySource` (config-file), `build_dormancy_source` factory, `load_default_dormancy_source` |
| `backend/app/domain_platform/config/dormancy.json` | New: canonical declarations (C1.4 archive set + platform/ + national_data/) |
| `backend/app/domain_platform/certification.py` | 10th check `dormancy_policy`; engine depends only on `DormancySource` via the factory |
| `backend/tests/unit/test_dormancy_registry.py` | New: **47 tests** (interface, canonical source, registry, JSON source, factory, check 10, backward compatibility) |
| `backend/tests/unit/test_domain_platform.py` | Certification-check count assertion 9 → 10 |
| `docs/adr/ADR-026-dormancy-registry.md` | New ADR (next free number; the plan's "ADR-014" slot was renumbered — 014 is taken by the observability ADR) |

The certification engine now depends **only on the `DormancySource` interface**;
the canonical data is a committed JSON configuration file, and the
`build_dormancy_source` seam already registers `database` / `governance` as
documented future providers (they fail loudly until implemented).

## 2. Final Test Summary

| Suite | Result |
|---|---|
| Complete backend suite (`pytest tests/`, clean env) | **4922 passed / 0 failed / 148 warnings** in 1052.93 s (17:32) |
| Commit 0.1 scope (dormancy + domain platform) | **118 passed / 0 failed** |
| Frontend suite (`vitest run`) | **122 passed (9 files)** |

## 3. Build Status

- Backend `compileall`: **PASS** (exit 0)
- `tsc --noEmit`: **0 errors**
- ESLint: **0 errors** (1 pre-existing warning in `frontend-v3/public/sw.js:65`, untouched by this commit — present since the baseline commit `d6574f8e`)
- `vite build`: **PASS** in 6.66 s

## 4. Architecture Gate

`scripts/architecture.py check` → **PASS**: Shared Core scan **57 findings (57 acknowledged, 0 new)**;
domain certification **11/11 (isolation PASS)**; country-agnostic scan **PASS**.

## 5. Domain Certification Gate

`scripts/domains.py check` → **PASS**: **11/11 certification, isolation PASS** (the 10th check keeps all canonical Domains at 100%).

## 6. API Compatibility & OpenAPI Comparison

Commit 0.1 touches **zero route files**. Verified with a byte-level Before-vs-After
comparison: the OpenAPI schema was generated from the parent commit (`732adc94`) in an
isolated worktree and from Commit 0.1, then compared.

| Metric | Before (parent `732adc94`) | After (Commit 0.1) | Δ |
|---|---|---|---|
| Top-level FastAPI routes (`app.routes`) | 119 | 119 | 0 |
| Served OpenAPI paths | 1,696 | 1,696 | 0 |
| Unique path+method pairs | 2,028 | 2,028 | 0 |
| `paths` dict | — | — | **byte-identical** |
| `components` (request/response models) | — | — | **byte-identical** |

**Verdict: zero API change.** No route added, removed, or altered; no model changed;
the OpenAPI duplicate-Operation-ID warning (`integration/connectors/routes.py`) is
documented as pre-existing in the baseline.

> Note: the baseline doc's "1,699 paths / 126 routes" figures were produced by the
> original baseline tooling under a different environment; the reproducible measurement
> of the immediate parent commit is 1,696 / 119 and is **identical** to Commit 0.1.

## 7. Frontend ↔ Backend Consistency

The Backend remains the single source of truth. Because Commit 0.1 changed no endpoint:

- **API contract compatibility** — unchanged (OpenAPI byte-identical).
- **Request/response models** — unchanged (`components` byte-identical).
- **Frontend consumers** — unaffected; zero frontend files changed; the only
  frontend mention of "dormant" is a pre-existing comment in `src/api/endpoints.ts:1542`.
- **Route guards / permissions** — unchanged (no route file touched).
- **Validation** — unchanged.
- **Generated client types** (`src/api/generated/`) — consistent; schema-derived and the
  schema did not change, so no regeneration is required.

**No mismatch.**

## 8. Before-vs-After Metrics

| Metric | Before (Commit 0.0) | After (Commit 0.1) | Δ |
|---|---|---|---|
| Backend suite | 4,865 passed / 0 failed | 4,922 passed / 0 failed | **+57** (47 dormancy + 10 certification-auth regression from the governance commit) |
| Certification checks per Domain | 9 | 10 | +1 (`dormancy_policy`) |
| New tests (dormancy) | 0 | 47 | +47 |
| Ruff (backend/app) | 379 | 379 | 0 new |
| Ruff (Commit 0.1 scope) | — | 0 | clean |
| Architecture gate | 57 ack / 0 new, 11/11 | 57 ack / 0 new, 11/11 | PASS |
| Domains gate | 11/11 | 11/11 | PASS |
| OpenAPI paths / routes | 1,696 / 119 (reproducible) | 1,696 / 119 | 0 |
| Migrations | 56 | 56 | unchanged |
| Frontend tests | 122 | 122 | unchanged |

## 9. Design Requirements (acceptance)

1. **Not a hard-coded single source of truth** — the registry is a `DormancySource`
   abstraction; canonical data lives in `config/dormancy.json`; `database`/`governance`
   kinds are registered as future providers. ✔
2. **Engine depends only on the interface** — `certification.py` imports `DormancySource`
   + the factory, never a concrete source. ✔
3. **Regression tests for every new rule** — 47 tests cover the protection invariant,
   archive set, dormant/archived/retired ownership failures, advisory undeclared
   modules, JSON-source validation, and the factory. ✔
4. **Backward compatibility** — engine default source unchanged; all callers
   (`services.py`, `gate.py`, `pipeline.py`) construct the engine without new
   arguments; all 11 canonical Domains still certify at 100% with no behavior change
   (the check fails only protected-asset coupling, which no existing Domain has). ✔

## 10. Rollback Readiness

- Revert: `git revert 15bd2c81` (pure additive — no schema/data/API change; the new
  check and registry are removed, certification returns to 9 checks).
- `config/dormancy.json` is data-only and lossless to remove.

## 11. Verdict

**GREEN.** Full suite green (4,922 passed / 0 failed); both gates PASS; build PASS;
API surface byte-identical; Frontend↔Backend consistent (no mismatch); ruff baseline
379 unchanged. Commit 0.1 is complete. Ready to proceed to **Commit 0.2** (advisory
`dormancy-check` in `ai-governance.yml`) — **pending explicit user approval**.
