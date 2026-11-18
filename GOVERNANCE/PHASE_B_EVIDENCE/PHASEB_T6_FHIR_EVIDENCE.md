# Phase B / M4 — T6 FHIR R4 Interoperability Evidence

Agent: T6 FHIR R4 interoperability implementation agent.
Repository: `gula-integration`, branch `integration/gula-unification-v1`.
All resource identifiers, payloads, principals and claims are synthetic. No
production claim is made. Canonical status labels only are used below.

## 1. Status summary

| Item | Status |
|---|---|
| Self-contained FastAPI router with all required FHIR R4 interactions | IMPLEMENTED |
| `GET /fhir/metadata` deterministic CapabilityStatement | IMPLEMENTED |
| Patient and Observation `read`, `vread`, `search-type` | IMPLEMENTED |
| `POST /fhir/Observation` create with `Location` + `ETag` | IMPLEMENTED |
| Conditional `PUT /fhir/Observation/{id}` with `If-Match` | IMPLEMENTED |
| Fail-closed `fhir.read` / `fhir.write` authorization with tenant + facility claims | IMPLEMENTED |
| Structured FHIR R4 `OperationOutcome` for every failure | IMPLEMENTED |
| Deterministic strong ETag / version history / stale-write conflict | IMPLEMENTED |
| Identifier/token non-echo in diagnostics | IMPLEMENTED |
| WS-E Health Core dependency-purity guard preserved | TESTED |
| Focused endpoint suite (51 collected tests, no skips) | TESTED |
| Ruff on all owned Python files | TESTED |
| Health Core regression baseline (773 passed, 0 failed) | TESTED |
| Scoped MyPy on owned package (`--follow-imports=silent`) | TESTED |
| External interoperability validation against a real authority/endpoint | BLOCKED |
| Independent verification of this work | NOT IMPLEMENTED |
| Production readiness certification | NOT IMPLEMENTED |

This agent does not self-award `INDEPENDENTLY VERIFIED` or `PRODUCTION READY`.

## 2. Architectural placement and relocation

The FHIR HTTP adapter lives at:

- `backend/app/interoperability/fhir_http/` (package)
- `backend/tests/unit/test_fhir_http_endpoints.py` (focused tests)
- `GOVERNANCE/PHASE_B_EVIDENCE/PHASEB_T6_FHIR_EVIDENCE.md` (this report)

The package was relocated into the existing non-wired `app.interoperability`
scaffolding to preserve the WS-E structural guard in
`backend/tests/health_core/test_quality_review_static.py`, which requires the
synthetic `app/health_core/` slice to remain free of FastAPI/HTTP boundary code
and route decorators. The guard was not edited or weakened.

The router remains **NON-activated**: it is not imported or registered in
`app/factory.py` or `app/main.py`. Mounting is an explicit test action only:
`FastAPI()` followed by `app.include_router(router)`, driven with
`fastapi.testclient.TestClient`.

## 3. Files created/relocated (no existing files modified by this task)

| Path | Purpose |
|---|---|
| `backend/app/interoperability/fhir_http/__init__.py` | Public exports, non-activated scope caveat |
| `backend/app/interoperability/fhir_http/router.py` | All HTTP endpoints and request validation |
| `backend/app/interoperability/fhir_http/security.py` | Fail-closed header principal, scopes, tenant/facility checks |
| `backend/app/interoperability/fhir_http/errors.py` | Structured `OperationOutcome` construction and I-2-style diagnostics sanitisation |
| `backend/app/interoperability/fhir_http/versioning.py` | Deterministic ETag derivation, `If-Match` and version parsing |
| `backend/app/interoperability/fhir_http/capability.py` | Deterministic R4 `CapabilityStatement` |
| `backend/app/interoperability/fhir_http/repository.py` | In-memory versioned synthetic repository and seed data |
| `backend/tests/unit/test_fhir_http_endpoints.py` | 51 focused endpoint/auth/leak tests |
| `GOVERNANCE/PHASE_B_EVIDENCE/PHASEB_T6_FHIR_EVIDENCE.md` | This evidence report |

No `git add`, commit, push, stash, merge or checkout was performed. No edits
were made to `app/factory.py`, `app/main.py`,
`GOVERNANCE/NATIONAL_INTEGRATION/`, reports 13/14, the WS-E static guard,
`backend/app/health_core/fhir/**`, or any other agent's files.

## 4. Implementation summary

- **Endpoints**: `GET /fhir/metadata`; `GET`, `POST` and `PUT` under
  `/fhir/Patient` and `/fhir/Observation` as declared in the
  CapabilityStatement; exact-version reads under
  `/fhir/{Patient,Observation}/{id}/_history/{version_id}`.
- **CapabilityStatement**: `fhirVersion = 4.0.1`, `experimental = true`, JSON
  formats only, deterministic date, and an explicit local/synthetic
  documentation string. Only implemented interactions are declared.
- **Reuse**: Observation snapshots are produced by the existing Health Core
  `FhirR4Adapter`; incoming Observations are strictly deserialised through
  `deserialize_resource()` and re-serialised through the adapter, so unknown
  client fields never reach storage. Adapter-originated failures reuse the
  canonical `operation_outcome_from_error()` mapping.
- **Authorization**: the dependency requires `X-GULA-Principal`,
  `X-GULA-Scopes` (`fhir.read` or `fhir.write`), `X-GULA-Tenant` and
  `X-GULA-Facility`. Missing principal → 401 `login`; missing/malformed scope
  or claim, or a resource outside the claimed tenant/facility → 403 `denied`.
  The dependency returns a denial object because a router mounted with
  `include_router` cannot register application-level exception handlers.
- **Errors**: every failure is an `application/fhir+json` `OperationOutcome`.
  Diagnostics follow the I-2 pattern: closed allowlist of detail keys plus
  `html.escape(..., quote=True)`; identifier-bearing fields are discarded.
- **Versioning**: strong ETag = quoted SHA-256 of canonical JSON including
  `meta.versionId`. `If-Match` accepts strong, weak (`W/`) and `*` forms.
  Missing `If-Match` → 428; stale ETag → 409; write success → 200/201 with
  `ETag` and `Location`.
- **Repository**: immutable versioned snapshots in memory, resettable per
  test; synthetic `SYN-` identifiers and synthetic tenant/facility extensions.

## 5. Tests executed and exact results

Command prefix: `cd backend && ENV=test PYTHONPATH=.:..
PYTHONDONTWRITEBYTECODE=1
/home/samertts/workspace/projects/gula-platform/backend/.venv/bin/python -m
pytest ...`

| Check | Scope | Exact result |
|---|---|---|
| Focused tests | `tests/unit/test_fhir_http_endpoints.py -q --tb=short` | `51 passed, 1 warning in 3.02s` (warning = pre-existing `StarletteDeprecationWarning` from FastAPI's `TestClient`); 0 failed, 0 skipped |
| WS-E structural guard | `tests/health_core -q --tb=short` | `773 passed, 1 warning in 8.50s`; `test_quality_review_static.py ..................` — 0 static findings |
| Full Health Core regression | `tests/health_core -q --tb=short` | `773 passed, 1 warning in 8.50s` (clean baseline, 0 failed) |
| Ruff | `ruff check backend/app/interoperability/fhir_http/ backend/tests/unit/test_fhir_http_endpoints.py` | `All checks passed!` |
| MyPy (as specified) | `mypy app/interoperability/fhir_http --ignore-missing-imports` | `Found 2 errors in 1 file (checked 7 source files)`; both are the documented pre-existing `app/domain/order_state.py:63,81` untyped-def errors. Zero errors in `app/interoperability/fhir_http`. |
| MyPy (owned package isolated) | `mypy app/interoperability/fhir_http --ignore-missing-imports --follow-imports=silent` | `Success: no issues found in 7 source files` |

Covered cases include: capability declaration; read/vread/search for both
resource types; search count cap and invalid parameters; create with
`Location`/`ETag`; create with existing id; wrong `resourceType`; missing
required fields; NID and contained-identifier rejection without echo;
unsupported extension rejection; update success, 428, stale 409, weak ETag,
missing resource, id mismatch; 401 on every protected route; wrong scope on
read/write; missing and malformed claims; cross-tenant and cross-facility
denial; search tenant filtering; deterministic version-sensitive ETag; and an
explicit assertion that the router is not referenced by `factory.py` or
`main.py`.

## 6. Known limitations / blocked requirements

- **External interoperability validation is BLOCKED**: no external FHIR
  endpoint, authority, terminology server or notary was available. Evidence is
  limited to local adapter round-trips and in-process `TestClient` HTTP calls.
- The header-based principal is a synthetic test fixture, not an identity
  provider. No signed token, mTLS, session or real authorization middleware is
  involved; production identity integration is NOT IMPLEMENTED here.
- The repository is in-memory and process-local: no persistence, no database,
  no replication, no durable conflict log. A process restart loses all state.
- The CapabilityStatement is an honest local description, not a conformance
  grant. It is experimental and explicitly marked non-activated.
- FHIR search supports only `identifier` and `name` (Patient) and `identifier`
  (Observation); no chained search, `_include`, sorting or paging cursors.
- The router is intentionally not wired into application startup, so no
  production traffic can reach it.

## 7. Security implications

- Fail-closed authorization is applied before every resource lookup or write:
  no principal → 401; insufficient scope, incomplete/malformed claims, or a
  resource scoped to another tenant/facility → 403. No resource content is
  returned before the scope check succeeds.
- Every error is a structured R4 `OperationOutcome` with a stable issue code;
  diagnostics use a closed detail-key allowlist and HTML escaping, and never
  echo supplied tokens, national identifiers, patient references or raw
  payload fragments.
- The canonical adapter re-serialisation strips unknown client fields before
  storage; only the two allowlisted synthetic extensions are accepted on
  incoming Observations.
- Strong deterministic ETags and `If-Match` prevent silent overwrites of a
  stale version; missing preconditions fail with 428 rather than defaulting to
  unconditional write.
- Residual risk: if this router were ever wired into a real application
  without replacing the synthetic header principal, an attacker able to set
  HTTP headers could impersonate a synthetic principal. Activation therefore
  requires a real authentication/authorization boundary and is out of scope.

## 8. Dependencies

- Python 3.12 standard library: `json`, `hashlib`, `html`, `copy`,
  `dataclasses`, `typing`.
- FastAPI / Starlette `APIRouter`, `JSONResponse`, dependency injection and
  `fastapi.testclient.TestClient` (test-only mounting).
- Existing in-repo Health Core FHIR adapters
  (`app.health_core.fhir.adapter`, `deserializers`, `errors`, `support`) and
  synthetic domain types (`app.health_core.clinical.entities`,
  `app.health_core.common`).
- pytest, Ruff and MyPy from the provided `gula-platform` backend virtualenv.
- No external service, no network call, no database, no broker, no paid or
  proprietary component, no real credentials and no patient data.
