# 08 — PostgreSQL and Migration Evidence — GULA-NATIONAL-COMPLETION-013

## Scope

Fresh PostgreSQL migration integrity, Python-version compatibility of migration modules, and application startup against the migrated schema.

## Methodology

A dedicated ephemeral PostgreSQL 16 container will be created with synthetic credentials only, no volume mount, and no use of existing databases. `alembic upgrade head` and module-import checks will be executed on the isolated branch.

## Environment

Docker 29.1.3; local Python 3.10.12 and 3.12 available. The container will be named `gula-nc013-pg` and removed after use.

## Commands and exit codes

Baseline source checks completed (exit 0):

```bash
rg -n 'sa\.String\(26\).*pharmacy_drug_catalog' backend/migrations/versions/20260815_0023_drug_substitution.py
rg -n 'from datetime import UTC' backend/migrations/versions
rg -n 'UTC = UTC' backend/app/_compat.py
```

Migration execution will be appended to `evidence/implementation_log.md`.

## Evidence paths

- `evidence/critical_defect_research.md` section 5
- `evidence/implementation_log.md`
- `docs/parallel-program/national-completion-013/evidence/pg_upgrade.log` (to be generated)

## Findings

- NC013-H01: `String(26)` FKs to `Integer` catalog ID — `PARTIALLY FIXED` at baseline.
- NC013-H02: `datetime.UTC` import and `UTC = UTC` shim — `NOT FIXED` at baseline.
- Historical PG-MIG-010-01 remains the authoritative defect ID.

## Verification state

`NOT VERIFIED` until a fresh-database upgrade is executed.

## Limitations

- SQLite unit tests are not proof of national PostgreSQL readiness.
- Modifying a historical migration requires documented deployment-state justification and database-owner approval.

## Residual risks

- A successful empty-database upgrade does not prove representative upgrade paths or deployed-database compatibility.

## Required actions

1. Patch FK types and UTC compatibility.
2. Run fresh PostgreSQL upgrade.
3. Record failures beyond the first blocker rather than stopping at one defect.
4. Preserve rollback/recovery plan and owner approval requirement.

## Execution update — 2026-11-20

A disposable PostgreSQL 16 container (`gula-nc013-pg`, port 55432, synthetic credentials only) was created from scratch; no existing PostgreSQL container or volume was reused.

- Initial `alembic upgrade head` exposed an inherited missing-hospital-core-table blocker at revision `20260820_0004`.
- Added self-contained revision `20261120_0001_nc013_hospital_core.py` and repointed `20260820_0004.down_revision`; no conflicting PR #261/#257 revision was imported.
- Final `alembic upgrade head` exited 0 and reached `20260908_0001`.
- Migration graph test exited 0 (3 passed); `alembic heads` reported exactly one head.
- Schema check found 5/5 expected hospital tables.
- Application import with the disposable database exited 0 (`app_import_ok GULA Platform 130`).
- Disposable container was removed after evidence capture.

Evidence: `evidence/test_logs/pg_upgrade_nc013.log`, `pg_schema_check_nc013.log`, `alembic_heads_nc013.log`, `alembic_current_nc013_final.log`, `migration_graph_nc013.log`, `app_startup_nc013_final.log`, `pg_container_cleanup.log`, and `evidence/implementation_log.md`.

Verification state: **FRESH-DATABASE UPGRADE PASSED; INDEPENDENT VERIFICATION IN PROGRESS**. This does not prove upgrade compatibility from an arbitrary deployed database or satisfy database-owner approval.
