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
