# GULA Platform Contracts — Quality Report

**Generated:** 2026-07-14  
**Platform Version:** 2.1.0  
**Scope:** `contracts/` tree

---

## 1. Syntax Check — Python Files

| File | Result |
|------|--------|
| `contracts/compatibility/conftest.py` | PASS |
| `contracts/compatibility/runner.py` | PASS |
| `contracts/compatibility/test_contract_api.py` | PASS |
| `contracts/compatibility/test_contract_dto.py` | PASS |
| `contracts/compatibility/test_contract_fhir.py` | PASS |
| `contracts/compatibility/test_contracts.py` | PASS |
| `contracts/sdk/python/gula/__init__.py` | PASS |
| `contracts/sdk/python/gula/client.py` | PASS |
| `contracts/sdk/python/gula/enums.py` | PASS |
| `contracts/sdk/python/gula/exceptions.py` | PASS |
| `contracts/sdk/python/gula/models.py` | PASS |
| `contracts/sdk/python/gula/sync.py` | PASS |
| `contracts/sdk/python/setup.py` | PASS |

**13/13 PASS** — All Python files compile without errors.

---

## 2. JSON Validation

| File | Result |
|------|--------|
| `contracts/api/v1/catalog.json` | PASS |
| `contracts/astm/protocol.json` | PASS |
| `contracts/compatibility/report.json` | PASS |
| `contracts/dto/catalog.json` | PASS |
| `contracts/events/catalog.json` | PASS |
| `contracts/fhir/capability-statement.json` | PASS |
| `contracts/fhir/profiles.json` | PASS |
| `contracts/hl7/protocol.json` | PASS |
| `contracts/security/report.json` | PASS |
| `contracts/sdk/typescript/package.json` | PASS |
| `contracts/sdk/typescript/tsconfig.json` | PASS |

**11/11 PASS** — All JSON files are valid.

---

## 3. Markdown Lint

| File | Lines | Result |
|------|-------|--------|
| `contracts/ADR.md` | 381 | PASS |
| `contracts/CHANGELOG.md` | 217 | PASS |
| `contracts/INTEGRATION_GUIDE.md` | 1341 | PASS |
| `contracts/SBOM.md` | 208 | PASS |
| `contracts/summary.md` | 156 | PASS |
| `contracts/diagrams/architecture.md` | 579 | PASS |
| `contracts/diagrams/sequence.md` | 471 | PASS |
| `contracts/sdk/python/README.md` | 380 | PASS |
| `contracts/sdk/typescript/README.md` | 290 | PASS |

**9/9 PASS** — All files pass basic structure checks.

---

## 4. File Completeness

| Path | Status |
|------|--------|
| `contracts/api/v1/catalog.json` | OK |
| `contracts/fhir/capability-statement.json` | OK |
| `contracts/fhir/profiles.json` | OK |
| `contracts/events/catalog.json` | OK |
| `contracts/dto/catalog.json` | OK |
| `contracts/hl7/protocol.json` | OK |
| `contracts/astm/protocol.json` | OK |
| `contracts/sdk/python/setup.py` | OK |
| `contracts/sdk/python/gula/__init__.py` | OK |
| `contracts/sdk/python/README.md` | OK |
| `contracts/sdk/typescript/package.json` | OK |
| `contracts/sdk/typescript/tsconfig.json` | OK |
| `contracts/sdk/typescript/src/index.ts` | OK |
| `contracts/sdk/typescript/README.md` | OK |
| `contracts/sdk/kotlin/build.gradle.kts` | **MISSING** (dir empty) |
| `contracts/sdk/kotlin/src/main/kotlin/*.kt` | **MISSING** |
| `contracts/sdk/kotlin/README.md` | **MISSING** |
| `contracts/sdk/dart/pubspec.yaml` | OK |
| `contracts/sdk/dart/lib/src/*.dart` | OK (10 files) |
| `contracts/sdk/dart/README.md` | **MISSING** |
| `contracts/sdk/cli/setup.py` | **MISSING** (dir empty) |
| `contracts/sdk/cli/gula_cli/*.py` | **MISSING** |
| `contracts/sdk/cli/README.md` | **MISSING** |
| `contracts/INTEGRATION_GUIDE.md` | OK (root level) |
| `contracts/CHANGELOG.md` | OK (root level) |
| `contracts/ADR.md` | OK (root level) |
| `contracts/SBOM.md` | OK (root level) |
| `contracts/summary.md` | OK (root level) |
| `contracts/diagrams/architecture.md` | OK |
| `contracts/diagrams/sequence.md` | OK |
| `contracts/compatibility/test_contracts.py` | OK |
| `contracts/compatibility/runner.py` | OK |
| `contracts/compatibility/report.json` | OK |
| `contracts/security/report.json` | OK |
| `contracts/quality/benchmarks.py` | **MISSING** |

**30/35 expected entries present (86%)**  
**5 missing:** `sdk/kotlin/` (all), `sdk/dart/README.md`, `sdk/cli/` (all), `quality/benchmarks.py`

---

## 5. Compatibility Tests (pytest)

| Suite | Pass | Fail | Error | Skip |
|-------|------|------|-------|------|
| `test_contract_api.py` | 3 | 5 | 0 | 0 |
| `test_contracts.py` | 5 | 4 | 2 | 0 |
| `test_contract_dto.py` | 12 | 1 | 0 | 6 |
| `test_contract_fhir.py` | 1 | 0 | 2 | 0 |
| **Total** | **21** | **10** | **4** | **6** |

### ⚠ Failed Tests Detail

**test_contract_api.py (5 failures):**
- `test_all_catalog_paths_registered` — ~200 catalog paths not found in backend (setup, patients, results, labs, samples, notifications, ehr, security, device-results, qc, critical-alerts, batch, admin, mobile, compliance, tiers, citizen-portal, claims, national-identity, insurance, ai, optimizer, stats, consent, integrations, edge, patient-card, ai-telemetry, kernel, lims, governance, governance-analytics, mpi)
- `test_methods_match_catalog` — 24 method mismatches (e.g., `DELETE /patients/{patient_id}` not registered)
- `test_health_endpoints_public` — RuntimeError: Kernel not initialized
- `test_login_endpoint_public` — RuntimeError: Kernel not initialized
- `test_auth_endpoints_require_bearer` — RuntimeError: Kernel not initialized
- (plus 2 sub-tests requiring auth)

**test_contracts.py (4 failures, 2 errors):**
- `test_all_catalog_endpoints_registered` — ~300 endpoints in catalog not found in backend routes
- `test_health_endpoints_reachable` — RuntimeError: Kernel not initialized
- `test_auth_required_endpoints_reject_unauthorized` — RuntimeError: Kernel not initialized
- `test_all_dto_schemas_have_backend_models` — 18 DTO schemas missing backend models (TestResultRead, MPI resolve/merge/citizen types, governance types, task types)
- Errors: `test_platform_version_matches` (TypeError: unsupported operand str/str), `test_version_match` (same)

**test_contract_dto.py (1 failure):**
- `test_known_enum_fields` — DeviceTokenRequest.platform regex mismatch

**test_contract_fhir.py (2 errors):**
- `test_patient_search_params` — TypeError: create_token() unexpected kwarg 'user_id'
- `test_observation_search_params` — Same TypeError

---

## 6. Compatibility Runner (standalone)

| Check | Result |
|-------|--------|
| platform_version_match | PASS |
| dto_catalog_structure | PASS |
| api_catalog_structure | PASS |
| events_catalog_structure | PASS |
| fhir_profiles_structure | PASS |
| fhir_required_fields | PASS |
| dto_backend_models_exist | PASS |

**7/7 PASS — 100%** without runtime dependencies.

---

## Summary

| Gate | Result |
|------|--------|
| Python syntax | ✅ 13/13 pass |
| JSON validity | ✅ 11/11 pass |
| Markdown lint | ✅ 9/9 pass |
| File completeness | ⚠️ 30/35 present (86%) |
| Compatibility runner | ✅ 7/7 pass |
| Pytest compatibility | ⚠️ 21 pass, 10 fail, 4 error, 6 skip |

**Key issues to resolve:**

1. **Missing SDK stubs** — `sdk/kotlin/`, `sdk/cli/`, `sdk/dart/README.md` are empty or absent
2. **Missing benchmark stub** — `quality/benchmarks.py` required but absent
3. **Kernel dependency** — 6 tests fail with `RuntimeError: Kernel not initialized` (require running backend with `init_kernel()`)
4. **API catalog drift** — ~200 catalog paths + ~300 catalog endpoints are not registered in the backend route table; 24 HTTP method mismatches
5. **DTO-model gap** — 18 DTO schema types have no backend ORM model
6. **create_token() API change** — FHIR tests fail due to signature mismatch
7. **version string parsing** — `str / str` TypeError in platform version checks
8. **Enum regex mismatch** — `DeviceTokenRequest.platform` validation pattern doesn't match enum values
