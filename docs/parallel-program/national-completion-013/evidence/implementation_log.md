# NC013 Implementation and Validation Log

All commands were run from the authorized isolated clone unless a working directory is shown.
All data used was synthetic. Existing PostgreSQL/Redis containers were never reused.

## 1. Baseline and isolation

| Check | Command | Result |
|---|---|---|
| Isolated branch/HEAD | `git -C /tmp/opencode/gula-national-completion-013 status --short --branch` | `## execution/gula-national-completion-013`; docs commit `5079d67d` |
| Protected workspace branch/HEAD/status | `git -C /home/samertts/workspace/projects/gula-platform rev-parse --abbrev-ref HEAD`; `rev-parse HEAD`; `status --porcelain=v1 -uall \| sha256sum` | `remediate-security-001`; `f478676b6fc375338648dde46fbf076c015a3f91`; `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  -` |
| Protected worktrees/stashes | `git -C ... worktree list \| wc -l`; `git -C ... stash list \| wc -l` | 6 worktrees, 2 stashes |

## 2. Implemented fixes

- **NC013-C01** — `backend/app/services/critical_result_contract.py` introduces namespaced critical-result references (`lab_results`, `lims_results`). Producers in `routes/test_results.py` and `services/order_service.py` emit `result_store` plus `result_id`; consumer `lims/workflows.py` requires explicit `result_store`; bare/legacy `result_id` fails closed. `lims/routes.py` exposes the namespace as an explicit query parameter.
- **NC013-C02** — `identity/api/router.py` mounts `persons`, `sessions`, and `devices` only after `_AUTH_REQUIRED`; `identity/api/persons.py` applies handler-level authentication and returns HTTP 404 on lookup miss.
- **NC013-C03** — `integration/gateway/grpc_gateway.py` fails closed when gRPC is unavailable, never echoes the request payload, and does not report false delivery.
- **NC013-C04** — `routes/register.py` no longer imports MPI's NID hasher and never stores/uses a self-asserted NID as verified; `services/mpi/resolver.py` ignores unverified NIDs and requires `nid_verified` for the exact-match fast path.
- **NC013-H01** — `migrations/versions/20260815_0023_drug_substitution.py` FK columns changed from `String(26)` to integer-compatible types matching `pharmacy_drug_catalog.id`.
- **NC013-H02** — `backend/app/_compat.py` centralizes Python 3.10 shims for `UTC`, `StrEnum`, and `Self`; 17 modules and three `20260814_*` migrations were switched to the shim. Three known Python 3.12-only syntax sites (`clinical_gateway/contracts.py`, `identity/repositories/base.py`, `engineering/generators/capability.py`) are explicitly **not fixed** and out of the 3.10 compatibility claim.
- **Migration graph** — New self-contained revision `20261120_0001_nc013_hospital_core.py` creates hospital core tables required by `20260820_0004`; `20260820_0004.down_revision` was repointed to it. This avoids importing conflicting PR #261/#257 revisions wholesale.
- **Dependency hygiene** — `backend/requirements-lock.txt` upgraded `certifi 2026.6.17→2026.10.18`, `dnspython 2.8.0→2.9.2`, `pillow 12.3.0→13.0.0`, `pyasn1 0.6.4→0.6.5`, `joserfc 1.7.4→1.7.6`, `urllib3 2.7.0→2.8.0`.
- **Regression tests** — Five new `*_nc013.py` files cover the critical-result contract, gRPC fail-closed, NID fail-closed, Python 3.10 compatibility, and NIAM auth/404.

## 3. Syntax and import checks

```text
cd /tmp/opencode/gula-national-completion-013/backend
python3 -m compileall -q app/services/critical_result_contract.py app/identity/api/router.py app/identity/api/persons.py app/integration/gateway/grpc_gateway.py app/routes/register.py app/services/mpi/resolver.py app/_compat.py migrations/versions/20260814_0005_role_permission_engine.py migrations/versions/20260814_0006_security_audit_governance.py migrations/versions/20260814_0007_clinical_gateway_scope.py migrations/versions/20260815_0023_drug_substitution.py
# exit 0 — evidence/test_logs/compileall_nc013.log

python3 -m compileall -q app
# exit 1 — three PRE-EXISTING Python 3.12-only syntax sites remain; not claimed fixed.
# evidence/test_logs/compileall_app_nc013.log
```

## 4. Focused tests

```text
cd /tmp/opencode/gula-national-completion-013/backend

/tmp/opencode/gula013-venv312/bin/python -m pytest -q \
  tests/test_critical_result_contract_nc013.py \
  tests/test_grpc_gateway_fail_closed_nc013.py \
  tests/test_nid_fail_closed_nc013.py \
  tests/test_python310_compatibility_nc013.py \
  tests/identity/test_niam_persons_auth_hardening_nc013.py
# exit 0 — 19 passed, 1 warning (Python 3.12.13)
# evidence/test_logs/focused_nc013_py312_locked_final.log

python3 -m pytest -q \
  tests/test_critical_result_contract_nc013.py \
  tests/test_grpc_gateway_fail_closed_nc013.py \
  tests/test_nid_fail_closed_nc013.py \
  tests/test_python310_compatibility_nc013.py
# exit 0 — 14 passed, 1 warning (Python 3.10.12; NIAM module excluded because backend routes use 3.12-only syntax)
# evidence/test_logs/focused_nc013_py310_final.log
```

## 5. Surrounding regression suite

```text
/tmp/opencode/gula013-venv312/bin/python -m pytest -q tests/identity \
  tests/integration/test_identity_bundle.py tests/kernel/test_gateway.py \
  tests/migrations/test_migration_graph_integrity.py \
  tests/test_clinical_gateway_contracts.py tests/test_clinical_gateway_service.py \
  tests/test_gateway_modes.py tests/test_identity_authentication_security.py \
  tests/test_identity_matching.py tests/test_lims_release_capability_gate.py \
  tests/test_lims_tenant_isolation.py tests/test_migration_resilience.py \
  tests/test_migrations.py tests/test_mpi_matcher.py \
  tests/test_national_identity_production_guard.py tests/test_niam.py \
  tests/test_niam_v2.py tests/test_persisted_identity_governance.py \
  tests/test_routes_register.py tests/test_wave3_identity_mapping.py
# exit 0 — 471 passed, 4 skipped, 1 warning
# evidence/test_logs/regression_identity_lims_mpi_py312_locked_final.log
```

## 6. Fresh PostgreSQL migration drill

```text
docker rm -f gula-nc013-pg >/dev/null 2>&1 || true
docker run -d --name gula-nc013-pg --rm \
  -e POSTGRES_USER=gula_nc013 -e POSTGRES_PASSWORD=SyntheticOnly123 \
  -e POSTGRES_DB=gula_nc013 -p 127.0.0.1:55432:5432 postgres:16-alpine
# exit 0; ready_after=3 — evidence/test_logs/pg_container_create.log

cd /tmp/opencode/gula-national-completion-013/backend
DATABASE_URL='postgresql://gula_nc013:SyntheticOnly123@127.0.0.1:55432/gula_nc013' \
PYTHONPATH=/tmp/opencode/gula-national-completion-013 \
/tmp/opencode/gula013-venv312/bin/alembic -c alembic.ini upgrade head
# exit 0 — evidence/test_logs/pg_upgrade_nc013.log

docker exec gula-nc013-pg psql -U gula_nc013 -d gula_nc013 -Atc \
  "select version_num from alembic_version; select count(*) from information_schema.tables where table_schema='public' and table_name in ('hospitals','hospital_operation_theaters','hospital_surgical_safety_checklists','hospital_departments','bed_assignments');"
# 20260908_0001 / 5 — evidence/test_logs/pg_schema_check_nc013.log

/tmp/opencode/gula013-venv312/bin/alembic -c alembic.ini heads
# 20260908_0001 (head) — evidence/test_logs/alembic_heads_nc013.log

docker rm -f gula-nc013-pg
# exit 0; container removed — evidence/test_logs/pg_container_cleanup.log
```

Application startup check with the same disposable database:

```text
ENV=test DATABASE_URL='...' PYTHONPATH=/tmp/opencode/gula-national-completion-013 \
REFRESH_TOKEN_SECRET='SyntheticOnlyRefreshSecret' AUDIT_ANCHOR_KEY='SyntheticOnlyAuditKey' \
/tmp/opencode/gula013-venv312/bin/python -c 'from app.main import app; print("app_import_ok", app.title, len(app.routes))'
# exit 0 — app_import_ok GULA Platform 130
# evidence/test_logs/app_startup_nc013_final.log
```

## 7. Static and security scans

```text
ruff check <changed .py files>
# exit 0 — All checks passed! — evidence/test_logs/ruff_changed_nc013_final.log

bandit -q -ll <changed backend app/migration .py files>
# exit 0; no findings — evidence/test_logs/bandit_changed_nc013.log

semgrep scan --config p/python --metrics=off --quiet <changed backend app/migration .py files>
# exit 0; no findings — evidence/test_logs/semgrep_changed_nc013.log

semgrep scan --config p/python --metrics=off --json <changed backend app/migration .py files>
# exit 0; 0 results, 34 paths scanned, 1 WARN timeout:
# python.lang.security.audit.dangerous-system-call-tainted-env-args on backend/app/lims/routes.py
# evidence/test_logs/semgrep_changed_nc013.json, semgrep_changed_nc013_stderr.log

pip-audit --progress-spinner off -r backend/requirements-lock.txt
# initial exit 1: 55 known vulnerabilities in 6 packages — evidence/test_logs/pip_audit_nc013.log
# after lock upgrade exit 0: No known vulnerabilities found — evidence/test_logs/pip_audit_nc013_final.log

trivy fs --scanners vuln,secret,misconfig --exit-code 0 --no-progress .
# exit 1: vulnerability DB download timed out — evidence/test_logs/trivy_fs_nc013.log  [NOT COMPLETED]

trivy fs --scanners secret,misconfig --exit-code 0 --no-progress .
# exit 0; 0 secrets; 490 pre-existing misconfigurations:
# 34 CRITICAL, 85 HIGH, 91 MEDIUM, 280 LOW — evidence/test_logs/trivy_secret_misconfig_nc013.log
```

The Trivy misconfigurations are in pre-existing Terraform/Kubernetes/Docker manifests, not in the NC013 code changes. They remain open risks and are not represented as remediated.

## 8. Independent-verifier drift closure (second pass)

The first independent pass classified the critical-result contract as **PARTIALLY VERIFIED** and identified four concrete gaps. All four were closed:

1. `backend/app/contracts/events.py` — `ResultPublished`, `ResultAmended`, `CriticalAlertTriggered` now require `result_store`, forbid bare `result_id` (`not.required`), and conditionally require the matching `lab_result_id`/`lims_result_id` via `oneOf`. Version bumped to `1.1.0`.
2. `backend/app/services/critical_alerts.py` — alert API payload now carries `result_store` + `lab_result_id`, not bare `result_id`.
3. `backend/app/services/order_service.py` — order-time `RESULT_CRITICAL` emission restored with a namespaced reference and with the original `patient_name`/`patient_phone` notification fields preserved; `_check_critical_alerts()` now uses committed `LabResult.id` values.
4. `backend/app/contracts/generator.py` — `UTC` imported from `app._compat` so `app.contracts.events` is importable on Python 3.10.

Three new regression tests were added (`test_event_registry_rejects_bare_result_ids`, `test_critical_alert_api_payload_is_namespaced`, `test_order_creation_critical_event_is_namespaced`).

```text
cd /tmp/opencode/gula-national-completion-013/backend
/tmp/opencode/gula013-venv312/bin/python -m pytest -q <5 focused NC013 files>
# exit 0 — 22 passed, 1 warning (Python 3.12.13)
# evidence/test_logs/focused_nc013_py312_driftclosed.log

python3 -m pytest -q <4 focused NC013 files>
# exit 0 — 17 passed, 1 warning (Python 3.10.12)
# evidence/test_logs/focused_nc013_py310_driftclosed.log

/tmp/opencode/gula013-venv312/bin/python -m pytest -q <surrounding regression subset>
# exit 0 — 471 passed, 4 skipped, 1 warning
# evidence/test_logs/regression_identity_lims_mpi_py312_driftclosed.log

ruff check --no-cache <all changed .py files>       # exit 0, All checks passed!
bandit -q -ll <changed backend app files>            # exit 0, no findings
semgrep scan --config p/python --metrics=off --disable-version-check --quiet <changed backend app files>  # exit 0, no findings
```

The two `RUF001` findings in `critical_alerts.py` are pre-existing medical unit strings (`×10³/µL`); they were annotated with targeted `# noqa: RUF001` rather than changing clinical notation.

The second independent pass found that `oneOf` did not reject a payload carrying both result namespaces. The three schemas were changed to `not.anyOf` clauses rejecting bare `result_id` and dual IDs. `jsonschema` `Draft202012Validator` validation (system Python 3.10, exit 0) reports `schema_ok=True single_accepted=True bare_rejected=True dual_rejected=True` for all three events. Final focused suites: `22 passed` (3.12), `17 passed` (3.10). Final static scans: Ruff/Bandit/Semgrep exit 0. Evidence: `focused_nc013_py312_schema_final.log`, `focused_nc013_py310_schema_final.log`, `event_schema_jsonschema_final.log`, `ruff_changed_nc013_schema_final.log`, `bandit_changed_nc013_schema_final.log`, `semgrep_changed_nc013_schema_final.log`.

**Compatibility limitations retained:** three Python 3.12-only syntax sites remain (`clinical_gateway/contracts.py`, `identity/repositories/base.py`, `engineering/generators/capability.py`), and 13 further app modules still import `UTC` directly from `datetime`. They are not claimed as fixed; see `compileall_app_nc013.log`.

**Deliberately not activated:** no live `RESULT_CRITICAL` subscriber was added. `process_critical_result_from_event()` remains a tested, fail-closed consumer path but is not wired to the in-process event bus, because critical-result notification policy (`AUD-CLIN-001`) is `BLOCKED`. This is a safety non-activation, not an unfixed defect; it remains an explicit open item.

## 9. Full backend suite (2,782 tests)

```text
cd /tmp/opencode/gula-national-completion-013/backend
PYTHONDONTWRITEBYTECODE=1 /tmp/opencode/gula013-venv312/bin/python -m pytest -q -p no:cacheprovider
# exit 1 — 1 failed, 2,754 passed, 27 skipped, 165 warnings in 716.17s
# evidence/test_logs/full_suite_nc013_driftclosed.log
```

The single failure is `tests/test_icu_lab_workflow_p0.py::test_transfusion_requires_independent_crossmatch_and_bedside_verification`: `verify_transfusion_safely()` sets status `verified`, but `blood_bank/domain/state_machine.py` only permits `verification -> started / in_progress`. It was reproduced identically on an untouched detached worktree of the baseline commit `2ee9e8bcb9d81e9cac6801f5dea9b86d59beaffa` (`baseline_icu_transfusion_check.log`, exit 1), proving it is **pre-existing and not a NC013 regression**. It is recorded as NC013-C05 and deliberately not changed without a clinical workflow owner decision. The temporary worktree was removed.

## 10. Delivery state at time of logging

- Docs commit `5079d67d` exists locally only; no program-013 commit has been pushed.
- No program-013 branch/PR/merge/deployment has been created outside the isolated clone.
- First independent pass: 5 claims VERIFIED, 4 claims PARTIALLY VERIFIED, 0 FALSIFIED. Four critical-result gaps from that pass are now closed locally; the second independent pass is in progress.
- Release posture remains `NOT ACCEPTED FOR PRODUCTION — HOLD`; `production_ready=0`; OD-001…OD-025 remain `BLOCKED`.
