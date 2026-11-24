# A07 — Backend, API & Database Audit: API CONTRACT AUDIT

**Agent:** A07 · **Program:** PROGRAM-GULA-PARALLEL-001 · **Wave:** A (READ-ONLY)
**Date:** 2026-11-19
**Status:** REVIEW-ONLY — no contract, route, or artifact file was modified.

---

## 1. Scope & Method

| Item | Detail |
|---|---|
| Read scope | `backend/app/routes/**` (63 modules), `backend/app/contracts/**` (7 modules), `backend/app/health_core/contracts/**` (8 modules), `backend/app/core/error_contract.py`, `backend/app/factory.py` (handlers + CORS), `backend/app/middleware.py` (`X-API-Version`), `contracts/export/openapi.json`, `CLAUDE.md:365-372`, `docs/constitution/14_API_CONSTITUTION.md`, `docs/constitution/23_BACKWARD_COMPATIBILITY.md`. |
| Focus | Response shapes, versioning strategy, breaking-change exposure for mobile/frontend clients, contract-generation endpoints, error-envelope consistency. |
| Constraint | Static analysis only. No app start, no OpenAPI regeneration, no DB access. The checked-in `openapi.json` was parsed as data only. |

### 1.1 Contract surfaces identified

| Surface | Location | Runtime status |
|---|---|---|
| Live FastAPI OpenAPI | `GET /openapi.json` (production guarded by `DocsAuthMiddleware`, `factory.py:446-449`) | Generated at runtime from route decorators. |
| Contract generator endpoints | `backend/app/contracts/routes.py` — `/contracts/openapi.json`, `/contracts/asyncapi.json`, `/contracts/schemas/{module:path}`, `/contracts/fhir/*`, `/contracts/graphql/schema`, `/contracts/catalog` | Registered at `factory.py:727-728`; read requires governance-reader role (`contracts/routes.py:23-24`). |
| Checked-in OpenAPI artifact | `contracts/export/openapi.json` | Tracked, clean in git; appears to be a stub (A07-008). |
| Canonical error envelope | `core/error_contract.py:55-82` + `factory.py:970-1094` | Used by all app-level exception handlers. |
| Health Core contract family | `backend/app/health_core/contracts/**`, version `1.0.0-alpha1` | Explicitly **LOCAL_SYNTHETIC_ONLY**, not served by routes (`version.py:6-8`). Not a wire contract today. |
| Version header | `middleware.py:200` (`X-API-Version: APP_VERSION`), exposed via CORS `factory.py:492` | Emitted on every response. |

---

## 2. Verified contract controls (positive)

1. **Bilingual error envelope is stable.** `build_error_payload()` (`core/error_contract.py:55-82`) always emits `code`, `message`, `details`, `request_id`, `timestamp`, `detail`, `detail_ar`; legacy fields retained deliberately (`:67-69`).
2. **Validation errors do not echo input** (`core/error_contract.py:31-52`).
3. **FHIR error path is isolated.** `_is_fhir_request()` (`factory.py:935-937`) routes only `/fhir` and `/fhir/*` to `OperationOutcome` responses (`factory.py:940-954,975-980,998-1004,1022-1027,1055-1060,1080-1085`). Non-FHIR clients are unaffected.
4. **Docs/auth boundary** in production: `/docs`, `/redoc`, `/openapi.json` guarded (`factory.py:446-449` per `CLAUDE.md:96`).
5. **Synthetic contract version discipline.** `health_core/contracts/version.py:13-42` documents additive-only evolution with `COMPATIBLE_MAJOR=1`; consumers validate with `is_compatible_version()`.

---

## 3. Findings

### A07-008 — P1 — Checked-in OpenAPI artifact is an empty stub with a stale version

- **Evidence**
  - `contracts/export/openapi.json` — parsed content: top-level keys `["openapi", "info"]` only; `info = {"title": "GULA Platform API", "version": "2.1.0"}`; `paths = 0`; `components.schemas = 0`; `servers = None`.
  - `backend/app/config.py:104` — `APP_VERSION = "2.5.0"`.
  - `backend/app/factory.py:1125-1136` — live app declares `version=APP_VERSION` (2.5.0).
  - File is tracked and clean (`git status --porcelain -- contracts/export/openapi.json` empty) → no user-work protection blocks a future regeneration, but the content is objectively unusable.
- **Affected components:** SDK/codegen consumers, contract-diff CI, external integrators, documentation, `contracts/export/**`.
- **Root cause:** Export artifact was committed as a placeholder and never refreshed; no gate compares it with the generated spec.
- **Impact:** Any client generating from this file sees **zero endpoints**; the version mismatch (2.1.0 vs 2.5.0) makes contract-drift detection meaningless. This is a P1 *contract-integrity* issue for external integration, not a runtime outage.
- **Safe-fix possible?** **Yes** — regenerate from `RUNTIME_MODE=openapi` in a controlled environment and commit the result; no runtime behaviour change.
- **Approval required?** **YES** for regenerating/committing a checked-in artifact (it is an API contract surface; `CLAUDE.md:369`). No DB/service execution permitted during regeneration — coordinate with orchestrator on a safe static export path.
- **Remediation plan:** 1) Confirm whether `contracts/export/openapi.json` is intentionally a stub by checking the generator (`contracts/generator.py`) and export workflow. 2) If not intentional, produce a full spec via the existing OpenAPI mode (no DB) and diff paths against `factory.py` route registration. 3) Add a CI check that fails when `info.version != APP_VERSION` or `paths` is empty. 4) Record before/after path counts in `INTEGRATION_LOG.md`.

### A07-009 — P2 — API versioning is claimed but not implemented consistently; no deprecation path for breaking changes

- **Evidence**
  - `backend/app/routes/compliance.py:83` — `"api_versioning": "URL-path versioning supported: /api/v1/ (current stable)"`
  - `backend/app/routes/compliance.py:113` — `"versioning": "URL-path versioning: /api/v1/ | Platform version: " + APP_VERSION`
  - Actual registered prefixes: `routes/patients.py:30` `prefix="/patients"`; `routes/results.py` (root router); `routes/stats.py:8` `prefix="/stats"`; `routes/labs.py`, `samples.py`, `login.py` etc. also root-level (`factory.py:565-579`).
  - Only two module-level versioned prefixes found: `routes/canonical_patient.py:26` `/api/v1/canonical-patients` and `routes/ai_platform.py:38` `/api/ai/v2`.
  - `X-API-Version` is emitted (`middleware.py:200`) but no request-side version negotiation, deprecation header, or sunset header was found.
  - Mobile compatibility field is a static string: `routes/mobile.py:253-254` — `"api_version": APP_VERSION, "min_app_version": "1.0.0"`.
- **Affected components:** all clients (mobile web, frontend-v3, device bridge), compliance reporting, API gateway routing.
- **Root cause:** Versioning exists as documentation and a couple of prefixes, not as an enforced routing/deprecation policy. `APP_VERSION` (2.5.0, product version) is conflated with an API major version.
- **Impact:** A breaking response-shape change (e.g., A07-002 or A07-011) cannot be isolated to `/v2`; clients cannot detect deprecation. The compliance endpoint overstates the platform's actual versioning posture.
- **Safe-fix possible?** **Partially** — correcting the compliance strings is documentation-only; introducing `/api/v1` aliases is a contract change with gateway implications.
- **Approval required?** **YES** — adding/aliasing URL prefixes changes the client contract and gateway config (`CLAUDE.md:369`); gateway files belong to A08's scope.
- **Remediation plan:** 1) Decide policy: product version (2.5.0) ≠ API version (v1/v2). 2) Either add versioned aliases with a documented deprecation window, or correct `compliance.py:83,113` to truthfully state "unversioned root paths + isolated versioned modules". 3) Add `Deprecation`/`Sunset` headers only with an approved policy. 4) Cross-check `frontend-v3/src/api/endpoints.ts` (A01/A03) and mobile clients before any alias.
- **SCOPE_REQUEST:** coordinate with A01 (gateway/architecture) and A08 (gateway config) before touching routing.

### A07-010 — P2 — Contract schema endpoints for core models are broken by an invalid import

- **Evidence**
  - `backend/app/contracts/routes.py:52` — `from .models import LabOrder, LabResult, Patient, Sample` inside the fallback branch of `GET /contracts/schemas/{module:path}`.
  - `backend/app/contracts/models.py:1-107` — defines only `ContractFormat`, `ContractStatus`, `ContractVersion`, `ContractMetadata`, `OpenAPISpec`, `AsyncAPISpec`, `JSONSchema`, `FHIRProfile`, `GraphQLSchema`, `ContractExport`; **none** of `LabOrder`, `LabResult`, `Patient`, `Sample`.
  - `backend/app/contracts/routes.py:53-61` — `model_map` routes `"patient"`, `"lab-order"`, `"lab-result"`, `"sample"` to those names.
- **Affected components:** `/contracts/schemas/patient`, `/contracts/schemas/lab-order`, `/contracts/schemas/lab-result`, `/contracts/schemas/sample`.
- **Root cause:** Copy/paste import from `app.models` into `app.contracts.models` (different module) without updating the path.
- **Impact:** `ImportError` → generic 500 via `_exception_handler` (`factory.py:1086-1094`) for four documented schema endpoints. Contract consumers receive no schema. Not exploitable (governance-reader only) → P2.
- **Safe-fix possible?** **Yes** — change to `from ..models import LabOrder, LabResult, Patient, Sample` (or `app.models`). Response shape unchanged.
- **Approval required?** **No** for the import correction alone; **Yes** if changing the schema output shape. Verify `contracts/routes.py` is clean in `git status` before Wave C.
- **Remediation plan:** 1) Confirm the intended models package. 2) One-line import fix. 3) Add four smoke tests asserting HTTP 200 and non-empty `properties`. 4) Verify `ContractGenerator.generate_json_schema()` resolves the models without DB access.

### A07-011 — P2 — A structured legacy error `detail` is flattened, dropping `message_ar` and the machine code clients expect

- **Evidence**
  - `backend/app/routes/results.py:356-364` — disabled public history raises `HTTPException(status_code=410, detail={"error": "public_patient_history_disabled", "message": "...", "message_ar": "..."})`.
  - `backend/app/factory.py:994-1015` — `_http_exception_handler` calls `public_http_detail(exc.detail, status_code=...)`.
  - `backend/app/core/error_contract.py:92-93` — `if isinstance(detail, Mapping): return "Request failed.", {}` (mapping details are discarded).
  - `backend/app/core/error_contract.py:74-82` — emitted body uses `code=code_for_status(410)` → `"HTTP_ERROR"` (not in `_STATUS_CODES`), `message="Request failed."`, `detail_ar` = same English string.
- **Affected components:** `GET /results/history/{phone}`, any client that reads `detail.message_ar` or `detail.error`, Arabic UX.
- **Root cause:** The global error normalizer intentionally collapses non-string `detail` objects for safety, but one route relies on structured `detail` surviving.
- **Impact:** Arabic message lost; the stable machine code becomes generic `HTTP_ERROR`; this is a **response-shape break** relative to what the route author intended. Because the endpoint is disabled by default (410), severity is P2 rather than P1.
- **Safe-fix possible?** **Yes** — either raise a `DomainError` (which carries `code`/`details`/Arabic text through `_domain_exception_handler`, `factory.py:970-991`) or allow an explicit allowlist of structured detail keys in `public_http_detail`.
- **Approval required?** **YES** — response-shape change (`CLAUDE.md:369`).
- **Remediation plan:** 1) Prefer migrating this route to `DomainError` with the existing canonical envelope. 2) Add a contract test asserting `code`, `message`, `detail_ar` for the 410 case. 3) Search all routes for `detail={...}` mappings (grep) and migrate consistently — do **not** globally relax `public_http_detail` without security review.

### A07-012 — P3 — Two modules both claim to define the "canonical" error envelope

- **Evidence**
  - `backend/app/core/error_contract.py:55-82` — live envelope: `code`, `message`, `details`, `request_id`, `timestamp`, `detail`, `detail_ar` (no `status_code`, no `retryable`).
  - `backend/app/health_core/contracts/errors.py:46-61,77-90` — `ERROR_RESPONSE_BODIES[0]` names `canonical_json` with the same shape, but `HealthCoreErrorResponse` adds `status_code: int` and `retryable: bool` and sets `extra="forbid"`.
  - `backend/app/health_core/contracts/version.py:6-8` — explicitly LOCAL_SYNTHETIC_ONLY, "not served by any application route".
- **Affected components:** future adapters, contract documentation, generated clients.
- **Root cause:** A synthetic-only contract family mirrors the live envelope but adds fields, and its docstring calls itself "canonical". No runtime divergence today.
- **Impact:** If a future Health Core adapter is promoted to a real route, clients would see two different "canonical" shapes. Low current risk — P3, documentation-level.
- **Safe-fix possible?** **Yes** — clarify docs: state that `HealthCoreErrorResponse` is a sandbox projection with two extra fields and is wire-incompatible with the live envelope; or align fields.
- **Approval required?** **No** for documentation-only clarification; **Yes** for changing the model fields.
- **Remediation plan:** 1) Add a docstring note in `health_core/contracts/errors.py` distinguishing sandbox vs live. 2) Add a unit test asserting the two shapes are deliberately different (guards against unnoticed convergence).

### A07-013 — P3 — `health_core` compatibility helper accepts prerelease majors but is not wired to any route

- **Evidence**
  - `backend/app/health_core/contracts/version.py:22-42` — `contract_major()` splits on `"-"`, `is_compatible_version()` compares to `COMPATIBLE_MAJOR=1`.
  - `backend/app/health_core/contracts/models.py:79` uses the constant as a default; `health_core/fhir/support.py:34,87` uses it in synthetic FHIR output.
  - No route or middleware calls `is_compatible_version()` (grep across `backend/app`).
- **Affected components:** synthetic contract consumers, future adapters.
- **Root cause:** Version gate implemented but never enforced at a boundary.
- **Impact:** A future client passing an incompatible version would not be rejected by the platform. Currently synthetic-only, so P3.
- **Safe-fix possible?** **Yes** when a synthetic HTTP adapter is introduced.
- **Approval required?** **YES** if it becomes a wire-level gate (new client-visible behaviour).
- **Remediation plan:** document that this is a library-level helper; add enforcement when the first non-synthetic adapter is approved. No action in Wave A.

---

## 4. Breaking-change risk register (for orchestrator consolidation)

| Change candidate | Client impact | Versioning mitigation available? | Finding |
|---|---|---|---|
| Add validators to `PatientUpdate` / normalize phone | Requests previously accepted may be rejected / stored values change | **No** — no v2 route | A07-002 |
| Fix `/contracts/schemas/*` import | Only fixes 500s; no shape change | n/a | A07-010 |
| Migrate 410 public-history to `DomainError` | `code`/`detail_ar` values change (intended) | **No** | A07-011 |
| Regenerate OpenAPI artifact | Additive documentation; version string 2.1.0 → 2.5.0 | n/a | A07-008 |
| Add `/api/v1` aliases | New paths; old paths retained if done additively | Policy undefined | A07-009 |

**Conclusion:** Because no enforced API versioning exists, **any** response-shape change is a breaking change for mobile/frontend clients until A07-009 is resolved with an approved policy.

---

## 5. Protected user work / constraints

- `frontend-v3/src/api/endpoints.ts` and related FE files are USER-MODIFIED (`PROGRAM_CONTROL.md:70-72`; `FILE_OWNERSHIP_MATRIX.md:43`). A07 did **not** read or modify them for this audit; client-impact statements above are inferred from backend routes only and are labelled as such.
- No contract file, route file, or OpenAPI artifact was changed by A07.

## 6. SCOPE_REQUESTs

1. **SCOPE_REQUEST-A07-05 → Orchestrator/A01/A08:** Decide API versioning policy and gateway ownership before any `/api/v1` alias work (A07-009).
2. **SCOPE_REQUEST-A07-06 → Orchestrator/A09:** Add contract smoke tests for `/contracts/schemas/{patient,lab-order,lab-result,sample}` and the 410 error envelope (A07-010, A07-011).
3. **SCOPE_REQUEST-A07-07 → Orchestrator:** Authorise a DB-free OpenAPI regeneration and define the workflow that keeps `contracts/export/openapi.json` current (A07-008). Out of A07's write set.
4. **SCOPE_REQUEST-A07-08 → Orchestrator/A03:** Verify frontend-v3/mobile consumers of `detail.message_ar` before approving the A07-011 shape change.

---

*End of API_CONTRACT_AUDIT.md. Companion reports: `BACKEND_AUDIT.md`, `DATABASE_MIGRATION_AUDIT.md`.*
