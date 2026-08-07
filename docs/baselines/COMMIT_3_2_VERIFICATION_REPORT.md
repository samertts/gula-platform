# PROGRAM-01 — Commit 3.2 Verification Report

**Finding:** #35 + #36 — `search_engine`
**Class:** Canonical Provider Completion (ADR-033)
**Commit:** 3.2
**Date:** 2026-08-07
**Baseline:** 35 → 33 acknowledged findings

---

## 1. Executive Summary

The search capability was completed inside its canonical provider
`backend/app/capabilities/search_service`. `DefaultSearchService` (#35,
`document_intelligence/application/service.py`) and
`InfrastructureSemanticSearchService` (#36,
`document_intelligence/infrastructure/services.py`) — together with the
`DefaultSearchIndexer` they depend on — were promoted verbatim into the
canonical package, which previously held only the live-but-stub
`/search-service` router. The stub handlers were wired to the promoted
in-memory indexer so the live router now performs real indexing and search
over its own state. `application/wiring.py` (the sole consumer) was
re-pointed atomically to the canonical imports. The old namespace is fully
vacated with no facade.

**Result:** architecture constitution findings **35 → 33**, OpenAPI contract
byte-identical (2028 methods / 1696 paths), full backend suite
**5017 passed / 0 failed** (+40 regression tests), all gates PASS.
**VERDICT: APPROVED for commit.**

## 2. Files Changed

**Created (canonical provider — promoted implementations, behavior-preserving):**

| File | Purpose | LOC |
|---|---|---|
| `backend/app/capabilities/search_service/indexer.py` | `DefaultSearchIndexer` (verbatim from `application/wiring.py`) + `get(document_id)` helper for the router | 71 |
| `backend/app/capabilities/search_service/search.py` | `DefaultSearchService` (verbatim from `application/service.py`); error imports from local `exceptions` | 60 |
| `backend/app/capabilities/search_service/semantic.py` | `InfrastructureSemanticSearchService` (verbatim from `infrastructure/services.py`) | 42 |
| `backend/app/capabilities/search_service/exceptions.py` | standalone `SearchError` / `IndexingError` (not `DocumentIntelligenceError` subclasses — canonical provider imports no domain package) | 9 |
| `backend/app/capabilities/search_service/interfaces.py` | `SemanticQuery` / `SemanticSearchResult` / `SearchableDocument` dataclasses (structurally mirror the domain types; no domain import) | 50 |
| `backend/app/capabilities/search_service/composition.py` | composition root — lazily-initialised singletons `get_search_indexer()` / `get_search_service()` | 21 |
| `backend/tests/unit/test_search_promoted.py` | **40 regression tests** | 400 |

**Edited (behavior-preserving):**

- `backend/app/capabilities/search_service/routes.py` — the 5 stub
  endpoints (`/search-service/`, `/search-service/{id}` GET/POST/PUT/DELETE)
  re-wired to `get_search_indexer()`: real in-memory index/list/update/delete.
  Signatures, prefix, tags and `get_current_user` dependency unchanged.
- `backend/app/capabilities/search_service/__init__.py` — exports extended
  (all promoted classes + `SearchableDocument` + exceptions); docstring-first
  layout (no E402).
- `backend/app/document_intelligence/application/service.py` — removed
  `DefaultSearchService` class (53 LOC) and the now-unused `SearchError`
  import; `IndexingError` import retained (used by `DefaultKnowledgePipelineService`).
- `backend/app/document_intelligence/application/wiring.py` — removed
  `DefaultSearchIndexer` class (63 LOC) and `SearchIndexer` /
  `DefaultSearchService` module imports; added canonical imports inside
  `build_orchestrator`; instantiations unchanged (names now resolve to canonical).
- `backend/app/document_intelligence/infrastructure/services.py` — removed
  `InfrastructureSemanticSearchService` class (34 LOC) + now-unused
  `SemanticQuery`/`SemanticSearchResult` imports.
- `backend/tests/test_document_intelligence.py` — removed unused
  `DefaultSearchService` import; re-pointed `InfrastructureSemanticSearchService`
  import to `app.capabilities.search_service.semantic`.

**Governance artifacts (regenerated):**

- `.ai/core/architecture/constitution_baseline.json` (35 → 33),
  classification, dashboard, Shared Core report, verification report.

## 3. Canonical Provider Verification

| Provider | Check | Result |
|---|---|---|
| `backend/app/capabilities/search_service` | promoted classes + wired router + composition root; no competing duplicate remains | **PASS** |
| `document_intelligence` old namespace | `service.py`/`wiring.py`/`infrastructure/services.py` vacated (repo-wide grep: only canonical + wiring re-points remain) | **PASS** |
| Consumer inventory | exactly 3 files referenced the classes pre-move (service.py, wiring.py, infrastructure/services.py) + 1 test file — all re-pointed | **PASS** |
| Router contract | 5 operations unchanged (`/search-service/` GET/POST, `/search-service/{id}` GET/PUT/DELETE); prefix `/search-service`, tags `Search Service`, `get_current_user` retained | **PASS** |
| Exceptions | `SearchError`/`IndexingError` no longer `DocumentIntelligenceError` subclasses — deliberate (canonical provider independence); `service.py` except-tuple still catches `IndexingError` from the canonical `DefaultSearchService` (raise chain preserved) | **PASS** |
| Retained domain assets | `SearchIndexer`/`SearchService`/`SemanticSearchService` ABCs (#34) and `FHIRSearchEngine` (#37) stay Domain-Owned, as classified | **PASS** |

## 4. Before vs After Metrics

| Metric | Before (Commit 3.1) | After (Commit 3.2) |
|---|---|---|
| Architecture findings | 35 | **33** (−2: #35, #36) |
| OpenAPI paths | 1696 | 1696 (byte-identical) |
| OpenAPI methods | 2028 | 2028 (byte-identical) |
| Route entries (boot) | 119 | 119 |
| Backend tests | 4977 passed / 0 failed | **5017 passed / 0 failed** (+40) |
| `search_service` surface | stub router only | indexer + search + semantic + composition + wired router |
| Search persistence layers | 1 (in-memory, doc-intel) | 1 (in-memory, canonical) — behavior unchanged |
| Ruff (`backend/app`) | 379 | **378** (below baseline) |
| Full-suite runtime | 645.71s | **691.59s** (11:31) |

## 5. Architecture Metrics

| Metric | Value |
|---|---|
| Constitution findings | 33 acknowledged, **0 new** |
| Baseline delta | 35 → 33 (−2) |
| Country-agnostic scan | PASS (2 known national-layer findings) |
| Policy Engine | PASS (1 enabled policy evaluated) |
| Shared Core catalog | 50 services (unchanged) |

## 6. Shared Core Findings (33 acknowledged, 0 new)

`scripts/architecture.py gate` → **PASS**:

```
Architecture Constitution gate: PASS
  Shared Core scan: 33 findings (33 acknowledged, 0 new)
  Domain certification: 11/11 (isolation PASS)
  Country-agnostic: PASS
  Policy Engine: PASS (1 enabled policy/policies evaluated)
```

Baseline regenerated to 33 records; `service.py` and
`infrastructure/services.py` absent from `constitution_baseline.json`. The
remaining 2 `search_engine` records are #34 (`interfaces.py` ABC) and #37
(`national/fhir/search.py`) — Retain as Domain-Owned.

## 7. Domain Certification

| Check | Result |
|---|---|
| Domain certification | **11/11** PASS |
| Domain isolation | PASS (0 findings in all 6 categories) |
| Cross-domain administration | none introduced (move within platform infra layer) |

## 8. Backend Test Results

Full suite with PostgreSQL:

```
DATABASE_URL=postgresql://postgres:gula_dev_2026@172.18.0.3:5432/gula
backend/tests — 5017 passed, 150 warnings in 691.59s (11:31)
```

- **5017 passed / 0 failed** (4977 baseline + 40 search promotion tests).
- `tests/unit` alone: **2429 passed** in 325.70s.
- `tests/test_document_intelligence.py`: 66 passed.
- No new warnings attributable to the migration.

## 9. Frontend Verification

- **No frontend files changed** by Commit 3.2.
- OpenAPI contract byte-identical → generated client unchanged.
- `tsc --noEmit`: **0 errors** (exit 0).
- ESLint baseline unchanged (no frontend diff).

## 10. OpenAPI Compatibility

- **PASS** — before/after spec diff **byte-identical** (2028 methods / 1696 paths),
  method-level params (name/in/required/schema.type) verified equal.
- Live-boot re-check: `/search-service/` (GET, POST) and `/search-service/{id}`
  (GET, PUT, DELETE) — 5 operations, unchanged from the stub router.
- Duplicate Operation ID warnings (connectors routes) are pre-existing and unrelated.

## 11. Build Status

| Check | Result |
|---|---|
| Backend boot with PG | **PASS** — 119 route entries, "All platform routes registered" |
| PostgreSQL | **PASS** — PG 16.14 @ `172.18.0.3:5432`, `gula` DB, 351 tables, single alembic head |
| Ruff (changed scope) | **PASS** — 0 violations; `backend/app` total 378 < 379 baseline |
| py_compile / imports | **PASS** — all touched modules import cleanly |
| Frontend tsc | **PASS** — 0 errors |

## 12. Rollback Procedure

- **Rollback class:** M (single `git revert <hash>`).
- Reverts: 6 new canonical files, 5 edited source files, the re-pointed test
  imports, the 40 regression tests, and the regenerated baseline (35 findings)
  **atomically**.
- No data involved — DB tables and DDL untouched; the in-memory index is
  ephemeral and rebuildable, so no data migration or coordination is required.

## 13. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Canonical `SearchError`/`IndexingError` are not `DocumentIntelligenceError` subclasses | Low | Deliberate (canonical provider independence); `service.py` catch sites verified; `raise ... from exc` chain preserved |
| `SearchableDocument` is a structural mirror, not the domain `ScannedDocument` | Low | Field names/behaviour identical for the indexer's consumption; routes construct it directly |
| In-memory search is not durable/persistent | Low | Pre-existing behaviour — the index was already in-memory in doc-intel; no regression |
| PG reachable only at container IP `172.18.0.3:5432` | Low (env) | `DATABASE_URL` documented; localhost refused is a host-network artifact, not a code issue |
| Engine state-file regeneration noise on gate runs | Low | Governance JSONs restored to committed state; gate verdict is the signal |

## 14. Unexpected Observations

1. **`app.routes` deferred-routing quirk:** `ENV=test` boot lists 119 entries as
   deferred `_IncludedRouter` objects (only 4 eager top-level paths); the
   search-service router is deferred and invisible in `app.routes`. Contract
   verified via the authoritative OpenAPI spec instead (1696 paths), not `app.routes`.
2. **Ruff safe-fixes on unrelated test files:** ruff's default `check` applied
   I001 import-sorting fixes to `test_consent.py`, `test_mpi_matcher.py`,
   `test_p4_production_fixes.py`, `test_rules_engine_promoted.py`. These were
   reverted to keep the commit atomic (no behavioural impact either way).
3. **Re-running the gate regenerates synthetic engine state** (optimizer/architect/
   orchestrator governance JSONs + root status reports). Restored to committed state.
4. **The scaffold `queries/`, `commands/`, `events/`, `contract.py`,
   `capability.py`, `permissions.py`, `policies.py`** remain stub files with
   baseline-blessed E402/N801/N999 violations (generated scaffolding style,
   capabilities pattern) — unchanged by this commit.

## 15. Final Certification Verdict

**APPROVED.**

- Constitution gate PASS (33 ack, 0 new) · Domain 11/11 · Country-agnostic PASS.
- OpenAPI byte-identical · Boot 119 routes · Full suite **5017 passed / 0 failed**.
- Ruff clean (378 < 379 baseline) · Frontend tsc 0 · Baseline 35 → **33**.
- Rollback = single `git revert` (class M, no data).

Commit 3.2 (order 14) is complete. Commit 3.3 (order 15, PDF) shall not begin
without explicit approval.
