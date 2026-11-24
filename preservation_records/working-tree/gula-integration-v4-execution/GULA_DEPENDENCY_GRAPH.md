# GULA DEPENDENCY GRAPH — WAVE 0

**Companion to:** `GULA_MASTER_BASELINE.md`, `GULA_COMPONENT_INVENTORY.md`
**Method:** fresh read-only inspection, 2026-11-19. This is an *observed* dependency map built from imports, registrations and build configuration — not a generated call graph. Absence of an edge here does not prove absence in code.
**Status legend (exclusive):** `IMPLEMENTED` · `TESTED` · `INTEGRATED` · `INDEPENDENTLY VERIFIED` · `PRODUCTION READY` · `BLOCKED` · `NOT IMPLEMENTED`

> **GULA-OWNER-GATE-2026-11-20 (additive cross-reference):** This observed dependency map is preserved. ARC-001 remains `BLOCKED` pending the ADR-F topology decision (`OD-017`/`OD-022` in `GULA_OWNER_DECISION_REGISTER.md`); no kernel restructure was performed. HOLD stands.

---

## 1. Runtime dependency layers

```
                        ┌──────────────────────────────┐
                        │  Clients (Web / Android /     │
                        │  iOS / Desktop / Expo)        │
                        └───────────────┬──────────────┘
                                        │ HTTPS / generated API client
                        ┌───────────────▼──────────────┐
                        │  Nginx / Gateway (config/,    │
                        │  K8s ingress, Helm chart)     │
                        └───────────────┬──────────────┘
                        ┌───────────────▼──────────────┐
                        │  FastAPI app (create_app,     │
                        │  backend/app/factory.py)      │
                        │  91 include_router(...)       │
                        └───┬───────────┬───────────┬───┘
                            │           │           │
              ┌─────────────▼──┐  ┌─────▼──────┐  ┌─▼──────────────┐
              │ routes/ (63)   │  │ middleware │  │ kernel/ event  │
              │                │  │ security/  │  │ bus, tasks     │
              └─────────────┬──┘  └─────┬──────┘  └─┬──────────────┘
                            │           │           │
                        ┌───▼───────────▼───────────▼───┐
                        │  services/ (46 top-level) +    │
                        │  bounded-context service layers│
                        └───┬───────────────┬───────────┘
                            │               │
                  ┌─────────▼──────┐  ┌──────▼──────────────┐
                  │ ORM models /   │  │ shared/ (42 pkgs:   │
                  │ 17 declarative │  │ audit, auth, events,│
                  │ bases          │  │ cache, search, …)   │
                  └─────────┬──────┘  └──────┬──────────────┘
                            │               │
                  ┌─────────▼───────────────▼──────────────┐
                  │ PostgreSQL · Redis · RabbitMQ · MinIO   │
                  └─────────────────────────────────────────┘
```

---

## 2. Observed edges (source → target)

| Source | Target | Mechanism | Status |
|---|---|---|---|
| `backend/app/main.py` | `backend/app/factory.py:1097 create_app()` | import + call | `IMPLEMENTED` |
| `factory.py` | 63 `routes/*` modules | 91 × `include_router` | `IMPLEMENTED` |
| `routes/*` | `services/*` and bounded-context services | direct imports | `IMPLEMENTED` |
| `services/*` | `shared/*` canonical providers | direct imports | `IMPLEMENTED` |
| All audit-writing modules | `backend/app/services/audit_service.py:184 log_action()` | direct import — finding `AUDIT-POSITIONAL-001` fixed: all 50 call sites across 8 files converted to keyword arguments; `INDEPENDENTLY VERIFIED` (engineering scope); commit `BLOCKED` by `lims/routes.py` provenance (`GULA_AUDIT_POSITIONAL_FIX_REPORT.md`). Finding `AUDIT-BYPASS-001`: `routes/ai.py::_emit_critical_alert` now imports and calls canonical `log_action` instead of constructing `AuditLog` directly (zero direct constructions remain in `backend/app/routes/`); `INDEPENDENTLY VERIFIED` (engineering scope); commit `BLOCKED` by `routes/ai.py` provenance (`GULA_AUDIT_BYPASS_FIX_REPORT.md`) | `INDEPENDENTLY VERIFIED` (engineering scope) |
| `services/*`, `routes/*` | `backend/app/models/*` + 16 bounded-context bases | SQLAlchemy ORM | `IMPLEMENTED` |
| `backend/migrations/env.py` | 17 declarative bases (`Base`, `NationalBase`, `EHRBase`, `CitizenPlatformBase`, `ClinicalBase`, `HealthDataBase`, `TrustBase`, `GovernanceBase`, `CareContinuumBase`, `HospitalBase`, `DataPlatformBase`, `NHDWBase`, `NursingBase`, `PharmacyBase`, `RadiologyBase`, `FinBase`, `IdentityBase`) | `target_metadata` merge | `IMPLEMENTED` |
| `backend/migrations/env.py` | `DocIntelBase` (21 classes), `InsBase` (30 classes) | **not registered** (F-085) | `BLOCKED` |
| `frontend-v3/src` | `contracts/export/openapi.json` | `verify:contracts`, `generate:route-gate` scripts | `IMPLEMENTED` |
| `frontend-v3` | `backend` | axios + generated client | `IMPLEMENTED`; runtime journey `BLOCKED` |
| `apps/gula-*` | tRPC 11 + Drizzle + Vite | package config | `IMPLEMENTED` |
| `mobile/android`, `mobile/ios`, `mobile/desktop` | backend REST | native API clients | `IMPLEMENTED`; runtime journey `BLOCKED` |
| CI `.github/workflows/ci.yml` | syntax gate → data-preservation gate → migration gate → lint → backend tests → security | workflow job order | `IMPLEMENTED` (file); CI execution `BLOCKED` |
| CI `.github/workflows/quality-gate.yml` | YAML + Dockerfile validation | workflow step | `IMPLEMENTED` (file) |
| CI `.github/workflows/constitution-compliance.yml` | constitution enforcement | workflow step | `IMPLEMENTED` (file) |
| `scripts/` (134) | governance, migration, discovery, restore tooling | direct invocation | `IMPLEMENTED` |

---

## 3. Migration graph

- 111 revision modules; 76 with plain `revision = "…"` declarations identified by naive regex, remainder using annotated or tuple forms — the naive regex is **not authoritative** (see baseline §2 note).
- Robust parse: **0 duplicate revisions, 4 merge revisions, exactly 1 head**.
- Head: `20261119_0003` (`backend/migrations/versions/20261119_0003_care_continuum_closure.py`), down `20261119_0002`.
- Tail chain: `20261119_0003 → 20261119_0002 → 20261119_0001 → 20261118_0001 → 20261114_0006 → …`
- Linear upgrade/downgrade/re-upgrade on disposable DB: `INDEPENDENTLY VERIFIED` (engineering scope) for the care-continuum closure; program-wide migration readiness `BLOCKED`.

---

## 4. Coupling and duplication risks

| Risk | Evidence | Status |
|---|---|---|
| Canonical audit service is a single point of misuse | 50 positional call sites mis-mapped arguments after signature change `aae20c89`; fix converts all 50 to keywords + adds a whole-tree AST guard (`test_audit_positional_regression.py`) — residual risk: future positional callers, commit gated by `lims/routes.py` provenance | `INDEPENDENTLY VERIFIED` (engineering scope) |
| Duplicate capability engines | Architecture baseline acknowledges repeated identity/notification/audit/barcode/QR/workflow/search engines | `BLOCKED` |
| Multiple client stacks | Web (`frontend-v3`), two `apps/`, `client/`, `server/`, `api/demo-api/`, 3 native + Expo + PySide6 | `IMPLEMENTED` (source); consolidation decision `BLOCKED` (owner-gated) |
| `create_all()` in tests can mask missing migrations | W-017 strict gate 753/872 vs 872/872 under SQLite `create_all()` | `BLOCKED` |
| Unserved insurance API | 84 endpoints in `insurance/api/` with no route | `BLOCKED` |
| Circular imports (ARC-001) | Measured this session (read-only AST + Tarjan SCC over 2,045 modules; 4,290 module-level + 426 lazy edges): **5 hard import-time cycles**, all confined to `app.kernel` (`kernel↔runtime.bootloader`, `event_bus.bus↔replay`, `tenant.registry↔resolver`, `config.registry↔reload`, `plugin.hot_reload↔manager`); plus a broader 11-module `app.kernel` cycle and 4 two-module cycles that are lazy-import-mitigated (`core.self_healing↔database`, `security.dependencies↔rbac`, `middleware↔services.metrics_service`, `national.background_platform interfaces↔entities`). All pre-existing; none introduced by this directive. **Runtime-impact analysis (2026-11-19):** all 10 import-order permutations (each pair A→B and B→A in fresh interpreters) PASS; `import app.factory` PASS; `create_app()` PASS (125 routes); kernel CLI import PASS; `python -m alembic heads` PASS (single head `20261119_0003`, 116 history lines). A direct `import migrations.env` fails only because Alembic sets `context.config` via its CLI — not a cycle. Conclusion: cycles are a **static architecture-score issue with no observed runtime failure**; per directive §3.4 the kernel is NOT restructured merely to improve the score. Remediation is a topology change → ADR-F owner-gated. | measurement + runtime-impact `TESTED`; remediation `BLOCKED` (ADR-F) |

---

## 5. External integrations (documented, not exercised)

FHIR R4 (`backend/app/fhir/`, `integration/`, `interoperability/`), HL7/ASTM device bridge (`services/device_bridge/`, `shared/barcode/`), LOINC/SNOMED/ICD reference data (`backend/app/reference/`), DICOM/radiology (`backend/app/radiology/`), analyzer integration (`backend/app/lims/`, `edge_agent/`).

Status: `IMPLEMENTED` (code/contracts). Government API connectivity and licensed terminology access: `BLOCKED` — no documented authority or credential; directive forbids assuming government APIs.

---

## 6. Next decision

`BLOCKED` — no dependency edge is removed or rewired in this wave. Topology changes require ADR decisions (ADR-F, ADR-G, ADR-H, ADR-I, ADR-J), all owner-gated. Circular imports were **measured** this session (§4: 5 hard `app.kernel` cycles + lazy-mitigated ones) but not remediated, since that is ADR-F topology work. The authorized dependency-level fixes in this wave — audit call-site correction (`AUDIT-POSITIONAL-001`) and critical-alert audit bypass (`AUDIT-BYPASS-001`, `routes/ai.py` now imports canonical `log_action`) — are complete and `INDEPENDENTLY VERIFIED` (engineering scope); they change call paths/arguments, not architecture, and their commits are `BLOCKED` pending mixed-provenance sign-off (`lims/routes.py`, `routes/ai.py`).
