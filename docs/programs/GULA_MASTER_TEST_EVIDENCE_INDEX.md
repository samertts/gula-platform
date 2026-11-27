# GULA Master Test Evidence Index

Status: **INDEX ONLY — NOT A NEW FULL-SUITE CERTIFICATION**. Baseline: `a01352578c0df205b92e58444242e1fa6ae7d77b`. This index separates what was directly re-verified in the current audits from historical run claims preserved in earlier evidence. It does not weaken any gate or convert a historical result into current proof.

Path aliases:

- `REPO` = `/home/samertts/workspace/gula-preservation/20261124T125514Z/integration/gula-platform-integration`
- `PRES` = `/home/samertts/workspace/gula-preservation/20261124T173502Z/integration`

## 1. Exact CI commands — RE-VERIFIED

| Scope | Exact command / target | Evidence |
|---|---|---|
| Backend clinical safety regression gate | `python -m pytest -q --timeout=60` plus seven explicit test files | `REPO/.github/workflows/ci.yml:279-286` |
| Backend full suite | `python -m pytest tests/ -v --timeout=60 -x 2>&1` | `REPO/.github/workflows/ci.yml:301` |
| Working directory for both | `cd backend` | `REPO/.github/workflows/ci.yml:278`, `:300` |
| Migration before tests | `alembic upgrade head` | `REPO/.github/workflows/ci.yml:258-264` |
| Nightly integration tests | `python -m pytest tests/ -v --tb=long -ra --maxfail=5 --junitxml=pytest-integration.xml -m "integration"` | `REPO/.github/workflows/nightly.yml:112-114` |
| IAM identity tests | `python -m pytest backend/tests/identity backend/tests/test_clinical_gateway_contracts.py backend/tests/test_clinical_gateway_service.py -m "not integration" -q` | `REPO/.github/workflows/iam-hardening.yml:46` |
| IAM migration tests | `python -m pytest tests/identity/test_workspace_migration_phase5.py` and related files `-q` | `REPO/.github/workflows/iam-hardening.yml:109` |
| IAM frontend Vitest | `npm --prefix frontend-v3 run test -- --run` | `REPO/.github/workflows/iam-hardening.yml:143` |
| IAM security regression | `python -m pytest tests/test_security_regression.py tests/test_tenant_isolation_matrix.py ... -q` | `REPO/.github/workflows/iam-hardening.yml:194` |
| Frontend E2E | `npx playwright test` | `REPO/.github/workflows/frontend-e2e.yml:38` |
| Makefile backend target | `cd backend && python -m pytest tests/ -v` | `REPO/Makefile:207-208` |

Clinical gate files at `REPO/.github/workflows/ci.yml:280-286`:

1. `tests/test_clinical_command_guard_p0.py`
2. `tests/test_clinical_operational_readiness_p0.py`
3. `tests/test_pharmacy_radiology_workflow_p0.py`
4. `tests/test_pharmacy_pos.py`
5. `tests/test_radiology_tenant_isolation.py`
6. `tests/test_emergency_surgery_workflow_p0.py`
7. `tests/test_icu_lab_workflow_p0.py`

## 2. Test configuration — RE-VERIFIED

| Config | Effective setting | Evidence |
|---|---|---|
| CI-effective pytest config | `[pytest]`, `testpaths = tests`, `asyncio_mode = auto`, `asyncio_default_fixture_loop_scope = function` | `REPO/backend/pytest.ini:1-4` |
| CI-effective addopts | `-v`, `--tb=short`, `--strict-markers` | `REPO/backend/pytest.ini:7-10` |
| CI-effective warnings | `error::pydantic.warnings.PydanticDeprecatedSince20` | `REPO/backend/pytest.ini:5-6` |
| Repo-root pytest config | `testpaths = ["backend/tests", "services/device_bridge/tests", "tests"]` | `REPO/pyproject.toml:71-79` |
| Root discovery rules | `python_files = "test_*.py"`, classes `Test*`, functions `test_*` | `REPO/pyproject.toml:74-76` |
| Root markers | `unit`, `integration`, `routes`, `stress`, `security`, `smoke`, `kernel`, `slow`, `performance` | `REPO/pyproject.toml:85-95` |
| Pinned test deps | `pytest>=9.0.3`, `pytest-asyncio>=1.4.0,<2.0.0`, `pytest-timeout>=2.4.0,<3.0.0`, `factory_boy>=3.3.0` | `REPO/backend/requirements-dev.txt:8-12` |
| Frontend Vitest script | `vitest run --passWithNoTests --exclude 'e2e/**'` | `REPO/frontend-v3/package.json:13` |
| Frontend E2E script | `playwright test` | `REPO/frontend-v3/package.json:23` |
| Vitest environment | `environment: "jsdom"`, `setupFiles: "./src/test/setup.ts"` | `REPO/frontend-v3/vitest.config.ts:7-9` |
| Playwright test dir | `testDir: "./e2e"` | `REPO/frontend-v3/playwright.config.ts:4` |

CI runs from `backend/`, so `REPO/backend/pytest.ini` is operative for the CI full suite; `REPO/pyproject.toml:71-95` applies to repo-root invocations.

## 3. Test inventory counts — RE-VERIFIED by file inspection

Function counts are definitions, not collected/parameterized case counts.

| Area | Count |
|---|---:|
| `REPO/backend/tests` | 248 files, 3,154 test functions, 528 `Test*` classes |
| `REPO/services/device_bridge/tests` | 12 files, 29 test functions |
| Combined configured Python testpaths | 260 files, 3,183 test functions |
| `REPO/tests` | 0 `test_*.py` files; 14 shell/k6/yaml/load files |
| Whole repo first-party `test_*.py` | 329 files; 69 outside configured testpaths |
| Frontend first-party Vitest files | 17 |
| Frontend Playwright files | 12 |
| Total first-party frontend test/spec files | 29 |

## 4. Key test files — RE-VERIFIED paths

### Identity / NIDP / MPI

| File | Functions | First test line |
|---|---:|---:|
| `REPO/backend/tests/test_identity_matching.py` | 31 | `:32` |
| `REPO/backend/tests/test_mpi_matcher.py` | 35 | `:36` |
| `REPO/backend/tests/test_mpi_reliability.py` | 11 | `:30` |
| `REPO/backend/tests/test_wave05_1_mpi_safety.py` | 7 | `:37` |
| `REPO/backend/tests/test_wave05_3_identity_persistence_crypto.py` | 14 | `:52` |
| `REPO/backend/tests/test_wave05_3_nidp_original_card_policy.py` | 38 | `:302` |
| `REPO/backend/tests/test_wave05_3_ocr_nfc_patient_safety.py` | 21 | `:139` |
| `REPO/backend/tests/test_niam.py` | 44 | `:75` |
| `REPO/backend/tests/test_niam_v2.py` | 45 | `:44` |
| `REPO/backend/tests/test_persisted_identity_governance.py` | 35 | `:45` |

### Clinical / LIMS / FHIR

| File | Functions | First test line |
|---|---:|---:|
| `REPO/backend/tests/test_fhir_comprehensive.py` | 14 | `:12` |
| `REPO/backend/tests/test_fhir_interoperability.py` | 4 | `:18` |
| `REPO/backend/tests/test_fhir_r4_exchange.py` | 10 | `:14` |
| `REPO/backend/tests/test_lab_slice_pipeline.py` | 12 | `:149` |
| `REPO/backend/tests/test_lims_release_capability_gate.py` | 4 | `:35` |
| `REPO/backend/tests/test_lims_tenant_isolation.py` | 5 | `:85` |
| `REPO/backend/tests/test_routes_labs.py` | 21 | `:140` |
| `REPO/backend/tests/test_clinical_command_guard_p0.py` | 5 | `:38` |
| `REPO/backend/tests/test_wave05_clinical_integrity.py` | 11 | `:178` |
| `REPO/backend/tests/test_wave05_1_clinical_immutability.py` | 13 | `:108` |

### Offline, security, migration, API/contract, performance

| Area | Representative files |
|---|---|
| Offline/outbox | `REPO/backend/tests/test_offline_sync.py`, `test_wave05_1_offline_safety.py`, `test_device_outbox.py`, `test_outbox_service.py` |
| Security | `REPO/backend/tests/test_security.py`, `test_security_regression.py`, `test_platform_security_hardening.py`, `test_tenant_isolation_matrix.py`, `test_wave05_3_identity_access_audit.py` |
| Migration | `REPO/backend/tests/test_migrations.py`, `test_migration_resilience.py`, `tests/migrations/test_migration_graph_integrity.py` |
| API/contract | `REPO/contracts/compatibility/test_contract_api.py`, `test_contract_fhir.py`, `test_contracts.py`, `REPO/backend/tests/test_integration_contract_enforcement.py` |
| Performance | `REPO/backend/tests/test_performance_budgets.py`, `test_stress.py`, `test_wave05_3_performance_simulation.py` |

## 5. Historical run results — NOT RE-EXECUTED IN THIS EXECUTION

| Run | Result | Evidence |
|---|---|---|
| Wave 05.3 full backend suite | `3190 passed, 27 skipped, 38 deselected, 6 xfailed, 171 warnings in 350.23s` | `PRES/GULA-WAVE-05.3-.../raw/wave05_3_full_backend_suite.log:8,:393` |
| Wave 05.3 unfiltered suite | `3210 passed, 27 skipped, 6 xfailed, 171 warnings, 6 subtests passed in 405.49s` | `PRES/GULA-WAVE-05.3-.../raw/wave05_3_full_backend_suite_unfiltered.log:9,:3377` |
| Wave 05.3 NIDP final full suite | `3275 passed, 27 skipped, 38 deselected, 6 xfailed, 171 warnings in 422.34s` | `PRES/GULA-WAVE-05.3-.../raw/wave05_3_nidp_full_backend_suite.log:8,:395` |
| Current baseline exact CI command | `3364 passed, 27 skipped, 6 xfailed, 171 warnings, 6 subtests passed in 335.69s` | preserved prior execution evidence |
| NCI synthetic E2E | `12 passed` | preserved prior execution evidence |
| Frontend | 17 files / 58 tests passed; typecheck exit 0 | preserved prior execution evidence |

Historical failures were preserved and are not hidden: Wave 05.3 initial focused `5 failed, 95 passed`, second focused `1 failed, 102 passed`, Wave 05 national identity subset `4 failed, 75 passed`, Wave 05.1 point-31 reproduction `4 failed, 1 passed`, and Wave 05.1 targeted regression `2 failed, 361 passed`.

Repository reports contain mutually inconsistent historical claims (`1754 collected`, `2005 tests passing`, `1841 tests passing`, `1130 tests pass`, `1420 tests passing`). These are treated as historical conflicts, not current proof.

## 6. Ephemeral-table tests — inspected, NOT run in this execution

The following fixtures create ephemeral tables/schemas and were not run by the current master execution to avoid undeclared database side effects:

- `REPO/backend/tests/conftest.py:147-149`
- `REPO/backend/tests/blood_bank/test_postgres_concurrency.py:21-56`
- `REPO/backend/tests/test_idempotency.py:41-53`
- `REPO/backend/tests/integration/test_integration_inbox.py:20`
- `REPO/backend/tests/test_consent.py:51`
- `REPO/backend/tests/test_dashboard_data_minimization.py:46-52`
- `REPO/backend/tests/test_feature_flags.py:57-65`
- `REPO/backend/tests/test_fx_quote_engine.py:18-24`
- `REPO/backend/tests/test_governance.py:135`
- `REPO/backend/tests/test_institutional_subscriptions.py:18-24`
- `REPO/backend/tests/test_outbox_service.py:51-59`
- `REPO/backend/tests/test_payment_orchestration.py:19-25`
- `REPO/backend/tests/test_payments_foundation.py:19-25`
- `REPO/backend/tests/test_persisted_identity_governance.py:28-35`
- `REPO/backend/tests/test_routes_labs.py:75-77`
- `REPO/backend/tests/test_routes_register.py:79-81`
- `REPO/backend/tests/test_wave04_workforce_governance_delegation.py:129`
- `REPO/backend/tests/unit/test_metrics_service.py:33-40`

## 7. Current execution run results

See `GULA_MASTER_EXECUTION_20261126T053405Z/phase4/raw/` for exact commands, logs, and exit codes from the Category A remediation. These are focused synthetic/fake-session tests; they are not a full-suite or gate certification.
