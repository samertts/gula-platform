# Wave A execution report — 2026-11-24

## 1. Scope and result

Wave A is closed at the engineering-evidence level in the isolated execution
workspace. It was executed without touching the preserved original repository
or protected repository, without committing, pushing, merging, deploying, or
using production data or external provider/AI/financial services.

Wave A closure does **not** change `HOLD`, `production_ready_items = 0`, G1–G12,
or any owner-gated status.

## 2. Final regression evidence

### Wave A baseline regression (before CRUD hardening)

Exact command:

```bash
cd /home/samertts/workspace/projects/gula-integration-v4-execution/backend
/home/samertts/.cache/gula-int-py312/bin/python -m pytest -q \
  > /tmp/opencode/v4_full_backend_tests_after_contract_fix.log 2>&1
echo "EXIT=$?" >> /tmp/opencode/v4_full_backend_tests_after_contract_fix.log
```

* Interpreter: `/home/samertts/.cache/gula-int-py312/bin/python`
* Python/pytest: `3.12.13` / `9.2.0`
* Exit code: `0`
* Counts: `5212 passed, 47 skipped, 213 warnings in 700.96s (0:11:40)`
* Preserved log: `V4_WAVE_A_FULL_TEST_LOG_FINAL_2026_11_24.txt`
* Earlier failing full run preserved as:
  `V4_WAVE_A_FULL_TEST_LOG_PRE_FIX_2026_11_24.txt`

The earlier failure was
`tests/test_security_hardening_review.py::test_prometheus_metrics_fails_closed_without_production_bearer`.
Classification: **Wave A regression**, caused by a stale monkeypatch target
after `/metrics/prom` was delegated to the authoritative renderer. The test was
updated to patch `app.services.metrics_service.IS_PRODUCTION`; it was not
removed or marked xfail. The run above followed that correction and had zero
failures. No pre-existing failures, environment failures, or unresolved defects
remained in that run.

### Post-hardening regression

A second full regression was run after the CRUD ownership/authorization, audit,
P-03 anchor, and exact contract-drift guard changes. Interpreter and pytest were
the same approved Python 3.12 environment. Exit code was `0`; result:
`5216 passed, 80 skipped, 213 warnings in 661.90s (0:11:01)`; zero failures and
zero errors. The 80 skips include four PostgreSQL-only files that were executed
separately with disposable DSNs (`75 passed`). Final details are in
`V4_WAVE_A_FINAL_POST_HARDENING_RESULT_2026_11_24.md`; the preserved log is
`V4_WAVE_A_FULL_TEST_LOG_POST_HARDENING_2026_11_24.txt` with SHA-256
`dde5d503f878a759b378022018d525b45ddf609d00cfafcb378ca73910ea91ee`.

## 3. Targeted verification

| Command / suite | Result |
| --- | --- |
| Wave A original guard (5 files) | `38 passed, 1 warning in 92.46s` |
| Hardening targeted suite (6 files) | `45 passed, 1 warning in 89.18s` |
| Contract drift guard (3 files) | `22 passed, 1 warning in 94.57s` |
| PostgreSQL CRUD tests | `5 passed, 1 warning in 1.01s` |
| P-03 chain-integrity PG tests | `14 passed, 1 warning in 25.37s` |
| P-03 cross-track PG tests | `14 passed, 1 warning in 5.71s` |
| Combined guard with both PG DSNs | `75 passed, 1 warning in 119.55s` |

All targeted commands used the approved Python 3.12 interpreter. Failed
harness/implementation attempts were preserved in the evidence directory and
are listed in the SHA-256 manifest.

## 4. Exact changed-file inventory

### Runtime code and configuration

* `.github/workflows/ci.yml`
* `backend/app/_compat.py`
* `backend/app/contracts/generator.py`
* `backend/app/contracts/integration.py`
* `backend/app/contracts/routes.py`
* `backend/app/core/logging_config.py`
* `backend/app/factory.py`
* `backend/app/middleware.py`
* `backend/app/routes/metrics.py`
* `backend/app/services/audit_service.py`
* `backend/app/capabilities/_shared/__init__.py`
* `backend/app/capabilities/_shared/crud.py`
* `backend/app/capabilities/_shared/models.py`
* `backend/app/capabilities/_shared/routes.py`
* `backend/app/capabilities/{clinical_foundation,document_management,encounter_management,healthcare_consent,provider_management,reporting_service,storage_service,workflow_engine}/{__init__.py,capability.py,routes.py}`
* `backend/migrations/versions/20261124_0001_capability_crud_records.py`
* `backend/migrations/versions/20261124_0002_capability_record_ownership.py`
* `contracts/export/openapi.json`
* `helm/gula-platform/templates/_helpers.tpl`
* `helm/gula-platform/templates/backend/servicemonitor.yaml`
* `helm/gula-platform/values.yaml`

### Tests

* `backend/tests/test_capability_crud.py`
* `backend/tests/test_capability_crud_postgres.py`
* `backend/tests/test_contract_export_live.py`
* `backend/tests/test_integration_contract_enforcement.py`
* `backend/tests/test_p03_chain_integrity_postgres.py`
* `backend/tests/test_p03_cross_track_validation_postgres.py`
* `backend/tests/test_security_hardening_review.py`

### Durable evidence

* `AUDIT_EXECUTION_RECORDS/V4_EXECUTION_PROVENANCE_2026_11_24.md`
* `AUDIT_EXECUTION_RECORDS/V4_EXECUTION_SOURCE_SNAPSHOT_SHA256.txt`
* `AUDIT_EXECUTION_RECORDS/V4_EXECUTION_ADDENDUM_2026_11_24.md`
* `AUDIT_EXECUTION_RECORDS/V4_CONTRACT_VERIFICATION_2026_11_24.md`
* `AUDIT_EXECUTION_RECORDS/V4_CAPABILITY_STATUS_2026_11_24.md`
* `AUDIT_EXECUTION_RECORDS/V4_P03_EXECUTION_REPORT_2026_11_24.md`
* `AUDIT_EXECUTION_RECORDS/V4_PRG_STATUS_2026_11_24.md`
* all `V4_*` and `P03_*` logs/manifests in `AUDIT_EXECUTION_RECORDS/`

SHA-256 hashes for all 78 in-scope source, test, configuration, and evidence
files are in `AUDIT_EXECUTION_RECORDS/V4_WAVE_A_POST_CHANGE_SHA256.txt`; the
manifest verifies `78 OK, 0 failures`. This manifest was generated after the
final regression and includes the final log and this report.

## 5. Contract and OpenAPI verification

See `V4_CONTRACT_VERIFICATION_2026_11_24.md`. Summary: runtime and export both
report `2.5.0`; both expose `1850` paths and compare exactly; export contains
`643` component schemas; 40 capability CRUD operations are registered;
correlation propagation and metrics bearer behavior are covered by tests; CI now
enforces exact contract drift.

## 6. Capability CRUD status

See `V4_CAPABILITY_STATUS_2026_11_24.md`. All eight generated CRUD surfaces are
implemented with database-backed, lab-scoped, audited operations. Each
capability as a whole remains `PARTIAL`; no capability is production ready.

## 7. Residual gaps

* Architecture duplication remains: four event stacks, four offline engines,
  duplicate identity/authorization surfaces, and duplicate contracts.
* Frontend-v3 has 92 non-operational/demo-only surfaces still to operationalize.
* No DR/PITR restore drill, no approved load targets, and no G7 pass evidence.
* Public-health legal scope, P-03 D1–D5, and owner acceptance remain unresolved.
* No Stable v1.0.0 declaration or release-status upgrade was made.

## 8. Preservation

Original repository HEAD/branch/status and protected MD5s were reverified during
Wave A and remain unchanged. The V2 manifest and immutable pre-change snapshot
still verify. All V4 edits are uncommitted in
`execution/gula-national-v4`.
