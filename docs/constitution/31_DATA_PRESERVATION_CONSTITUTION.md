# GULA Data Preservation Constitution

**Version:** 1.0.0
**Status:** Ratified — Permanent
**Effective Date:** 2026-07-22
**Authority:** Architecture Board

---

## PREAMBLE

The GULA Platform serves Iraqi medical laboratories where patient data, laboratory records, and clinical history are matters of life and safety. This Constitution establishes permanent, non-negotiable rules for data preservation that bind all developers, operators, AI agents, CI/CD pipelines, and future platform evolutions.

**These rules may not be overridden by any subsequent task, refactor, migration, optimization, rewrite, rebuild, cleanup, modernization, or architecture change.**

---

## RULE 1 — ZERO DATA LOSS

Existing production data is SACRED.

The following categories may never be deleted:

- Patient data
- Laboratory data
- Organizations
- Facilities
- Users
- Roles
- Permissions
- Audit logs
- AI history
- Attachments
- Specimens (samples)
- Results
- Orders
- Appointments
- Notifications
- Events
- Configuration
- Feature flags
- Reference tables (test types, reference ranges, etc.)

Deletion of any data in these categories is prohibited.

---

## RULE 2 — EXPAND, NEVER DESTROY

Schema evolution must always ADD, never REPLACE.

**GOOD:**
- Add column
- Add table
- Add index
- Add constraint
- Add enum value

**BAD:**
- Drop column
- Drop table
- Rename column without compatibility shim
- Change data type destructively (e.g., `varchar` → `int` without migration)
- Remove enum value

---

## RULE 3 — BACKWARD COMPATIBILITY

Every schema migration must support existing data.

- Old records must remain readable after any migration.
- Old APIs must continue functioning until officially deprecated through the deprecation process.
- A compatibility layer must exist for at least two full release cycles before legacy paths are removed.

---

## RULE 4 — NO DROP MIGRATIONS

Alembic migrations may NEVER contain any of the following without explicit written approval from the Architecture Board:

- `DROP TABLE`
- `DROP COLUMN`
- `TRUNCATE`
- `DELETE FROM` (without a `WHERE` clause that limits scope to non-business data)

---

## RULE 5 — SAFE MIGRATION ONLY

All schema migrations must follow this mandatory sequence:

```
1. Create new structure (add column/table)
2. Copy existing data into new structure
3. Validate copied data (count, checksum, FK integrity)
4. Enable compatibility layer (views, triggers, or application code)
5. Switch reads to new structure
6. Switch writes to new structure
7. Wait at least one full release cycle
8. Only then may legacy structure be deprecated (not dropped — see Rule 4)
```

---

## RULE 6 — IMMUTABLE AUDIT

Audit tables are **append-only**.

- Never update audit history.
- Never delete audit history.
- Never rewrite audit history.
- Audit entries carry a hash-chain for tamper detection.

---

## RULE 7 — BACKUP BEFORE CHANGE

Before every migration (schema or data):

```
1. Automatic full backup
2. SHA-256 checksum computed and stored
3. Integrity verification (restore to temp database, validate)
4. Rollback point registered
5. Migration proceeds ONLY after backup succeeds
```

No migration script may proceed without a confirmed valid backup.

---

## RULE 8 — ROLLBACK

Every migration must include:

- `upgrade()` function
- `downgrade()` function
- Rollback validation step in CI
- Data must survive a full rollback cycle (upgrade → downgrade → upgrade)

---

## RULE 9 — DATA VALIDATION

After every migration, verify:

- Record count matches expected (pre-migration count + new rows, if any)
- All foreign key constraints are satisfied
- Checksums match for migrated data
- Constraints are valid and enforced
- Indexes are present and usable
- No NULL violations in previously non-nullable columns

---

## RULE 10 — SOFT DELETE ONLY

Business entities may not be physically deleted. Use soft delete pattern:

- `deleted_at` — timestamp of deletion
- `deleted_by` — user/service that performed the deletion
- `is_deleted` — boolean flag for query filtering

All queries against business tables MUST filter `WHERE is_deleted = FALSE` (or equivalent) by default.

Exceptions (may use hard delete):
- Transient sessions
- Expired cache entries
- Temporary processing data

---

## RULE 11 — VERSIONED MODELS

Support model evolution without data loss.

- Never overwrite previous meaning of a field.
- When semantics change, create a new version of the model alongside the old.
- Introduce Version 2 models beside Version 1 until migration completes.
- Document the mapping between versions.

---

## RULE 12 — API STABILITY

Never remove API endpoints without following the deprecation protocol:

1. Add `Deprecated` annotation/header to endpoint
2. Maintain endpoint for minimum 90 days after deprecation notice
3. Log usage of deprecated endpoints for impact analysis
4. Remove only after confirming zero production usage
5. An ADR must document any endpoint removal

---

## RULE 13 — TEST DATA SAFETY

CI must automatically verify:

- No migration loses rows (compare row counts before/after in test)
- No migration changes IDs
- No migration breaks foreign key constraints
- No migration corrupts UTF-8 text data
- No migration produces warnings or errors in PostgreSQL logs

---

## RULE 14 — DATA INTEGRITY GATE

A permanent automated Quality Gate named `DATA_PRESERVATION_GATE` enforces these rules:

- **Blocks merge** if:
  - `DROP TABLE`/`DROP COLUMN` detected in migration files
  - `DELETE` or `TRUNCATE` detected in migration files
  - Unsafe `ALTER` detected (type change without compatibility)
  - Missing `downgrade()` in any migration
  - Missing backup step before migration
  - Row count validation fails
  - FK validation fails

---

## RULE 15 — PROTECTED TABLES REGISTRY

A Protected Tables Registry (`docs/constitution/data_preservation/protected_tables_registry.md`) lists all tables requiring explicit Architecture Board approval before any structural change.

Protected tables include, at minimum:
- All patient-related tables
- All audit tables
- All order and result tables
- All user and role tables
- All subscription and billing tables

---

## RULE 16 — CONSTITUTION ENFORCEMENT

Every Pull Request must automatically verify compliance with this Constitution.

- Violation detected → build failure
- Bypass requires explicit Architecture Board approval documented in the PR
- Enforcement is applied by the `DATA_PRESERVATION_GATE` in CI

---

## RULE 17 — FUTURE PROOF

All future AI agents, Codex sessions, developers, contributors, automation pipelines, CI/CD workflows, and platform evolutions must comply with this Constitution automatically.

This rule is self-referential and permanent.

---

## ENFORCEMENT MECHANISM

| Layer | Tool | Trigger |
|-------|------|---------|
| Pre-commit | `data_preservation_gate.py --pre-commit` | Git hook |
| CI | `data_preservation_gate.py --ci` | GitHub Actions job |
| PR Review | Automated comment from gate | On PR open/sync |
| Architecture Board | Manual review | On gate bypass request |

---

## COMPLIANCE MATRIX

| Rule | Check Method | CI Gate | Pre-commit |
|------|-------------|---------|------------|
| Rule 1 — Zero Data Loss | Migration scanner | Yes | Yes |
| Rule 2 — Expand Never Destroy | Migration AST analysis | Yes | Yes |
| Rule 3 — Backward Compatibility | Migration review | Advisory | No |
| Rule 4 — No Drop Migrations | Pattern scanner | Yes | Yes |
| Rule 5 — Safe Migration Only | Sequence validator | Yes | No |
| Rule 6 — Immutable Audit | Append-only check | Yes | Yes |
| Rule 7 — Backup Before Change | Backup log check | Yes | No |
| Rule 8 — Rollback | Downgrade existence check | Yes | Yes |
| Rule 9 — Data Validation | Post-migration query | Yes | No |
| Rule 10 — Soft Delete Only | Model scanner | Yes | Yes |
| Rule 11 — Versioned Models | Convention check | Advisory | No |
| Rule 12 — API Stability | Route scanner | Advisory | No |
| Rule 13 — Test Data Safety | Test assertion scan | Yes | No |
| Rule 14 — Data Integrity Gate | Self-check | Yes | Yes |
| Rule 15 — Protected Tables | Registry cross-check | Yes | Yes |
| Rule 16 — Constitution Enforcement | Self-check | Yes | Yes |

---

## PENALTIES FOR VIOLATION

1. **Any violation** — Build failure, PR blocked, mandatory Architecture Board review.
2. **Second violation by same contributor** — Mandatory training on this Constitution.
3. **Data loss incident** — Immediate platform freeze, root cause analysis, and Architecture Board audit.

---

## GOVERNANCE

| Role | Responsibility |
|------|---------------|
| Architecture Board | Approves exceptions, reviews violations, amends Constitution |
| Engineering Lead | Ensures CI enforcement, reviews gate output |
| Platform Architect | Maintains Protected Tables Registry, reviews migration safety |
| DevOps Lead | Maintains backup/restore infrastructure, verifies disaster recovery |
| All Contributors | Comply with this Constitution in every change |

---

## AMENDMENT PROCESS

This Constitution may only be amended by:

1. Proposal submitted to Architecture Board
2. 30-day comment period
3. Two-thirds majority vote of Architecture Board
4. Approval documented in an ADR
5. Version bump in this document

---

## REFERENCES

- `docs/constitution/data_preservation/migration_safety_policy.md` — Detailed migration safety rules
- `docs/constitution/data_preservation/protected_tables_registry.md` — Registry of protected tables
- `docs/constitution/data_preservation/backup_strategy.md` — Backup procedures and policies
- `docs/constitution/data_preservation/restore_strategy.md` — Restore procedures and validation
- `docs/constitution/data_preservation/disaster_recovery_guide.md` — DR runbook
- `scripts/data_preservation_gate.py` — Automated enforcement script
- `.github/workflows/ci.yml` — CI pipeline with Data Preservation Gate
- `docs/adr/ADR-025-data-preservation-constitution.md` — Architecture Decision Record
