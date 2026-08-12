# Migration Safety Policy

**Part of the GULA Data Preservation Constitution**
**Version:** 1.0.0
**Status:** Mandatory

---

## 1. PURPOSE

This policy defines the mandatory safety procedures for all database migrations in the GULA Platform. It enforces Rules 2, 4, 5, 7, 8, and 9 of the Data Preservation Constitution.

---

## 2. SCOPE

This policy applies to:

- All Alembic migration files in `backend/migrations/versions/`
- All data backfill scripts in `scripts/`
- All manual SQL executed against production databases
- All CI/CD migration steps

---

## 3. MIGRATION TYPES

### 3.1 Schema Migrations

Changes to table structure (columns, indexes, constraints).

### 3.2 Data Migrations

Changes to existing data (backfill, transformation, normalization).

### 3.3 Index-Only Migrations

Adding or removing indexes (no schema or data changes).

### 3.4 Seed Migrations

Inserting reference/configuration data.

---

## 4. PROHIBITED OPERATIONS

The following operations are **PROHIBITED** without explicit written Architecture Board approval:

| Operation | Risk | Safe Alternative |
|-----------|------|-----------------|
| `DROP TABLE` | Irreversible data loss | Set `is_deleted = TRUE`, archive |
| `DROP COLUMN` | Irreversible data loss | Set column nullable, ignore in app |
| `TRUNCATE` | Irreversible data loss | Soft delete, batch archive |
| `DELETE FROM` (unqualified) | Irreversible data loss | Soft delete with `deleted_at` |
| Destructive `ALTER COLUMN TYPE` | Data truncation/corruption | Add new column, migrate data, drop old |
| `RENAME COLUMN` | Breaks backward compatibility | Add new column, dual-write, phase out |
| `RENAME TABLE` | Breaks backward compatibility | Create view with old name, phase out |

---

## 5. MANDATORY MIGRATION SEQUENCE

Every migration MUST follow this sequence:

```
┌─────────────────────────────────────────────────────┐
│  Step 1: CREATE NEW STRUCTURE                       │
│  Add column/table with new name, nullable or        │
│  with server_default                                │
├─────────────────────────────────────────────────────┤
│  Step 2: COPY EXISTING DATA                         │
│  UPDATE new_structure SET col = transform(old_col)  │
│  Verify row count matches                           │
├─────────────────────────────────────────────────────┤
│  Step 3: VALIDATE COPIED DATA                       │
│  Checksum comparison                                │
│  FK constraint check                                │
│  NULL value check                                   │
├─────────────────────────────────────────────────────┤
│  Step 4: COMPATIBILITY LAYER                        │
│  Create views/triggers for backward compat          │
│  OR update application code to read from both       │
├─────────────────────────────────────────────────────┤
│  Step 5: SWITCH READS                               │
│  Update application to read from new structure      │
│  Monitor for errors                                 │
├─────────────────────────────────────────────────────┤
│  Step 6: SWITCH WRITES                              │
│  Update application to write to new structure       │
│  Verify dual-write consistency                      │
├─────────────────────────────────────────────────────┤
│  Step 7: DEPRECATION NOTICE                         │
│  Mark old structure as deprecated                   │
│  Document removal timeline (min 1 release cycle)    │
├─────────────────────────────────────────────────────┤
│  Step 8: LEGACY REMOVAL (FUTURE RELEASE)            │
│  Only after Architecture Board approval             │
│  Never DROP — archive or mark readonly              │
└─────────────────────────────────────────────────────┘
```

---

## 6. MIGRATION FILE REQUIREMENTS

Every migration file MUST include:

```python
"""Migration description.

Revision ID: <alembic revision id>
Revises: <parent revision id>
Create Date: <timestamp>
Data Preservation: <safe | requires_approval | prohibited>

Rules verified:
  - Rule 2 (Expand, Never Destroy): <pass/fail>
  - Rule 4 (No Drop): <pass/fail>
  - Rule 5 (Safe Migration): <pass/fail>
  - Rule 8 (Rollback): <pass/fail>
"""
```

---

## 7. IDEMPOTENCY GUARDS

All migrations must use idempotency guards:

```python
def _has_column(table, column):
    # Check if column exists before adding
    ...

def upgrade():
    if not _has_column("patients", "new_field"):
        op.add_column("patients", sa.Column("new_field", sa.String()))
```

---

## 8. ROLLBACK REQUIREMENTS

Every migration MUST provide `downgrade()` that:

1. Reverses all schema changes made in `upgrade()`
2. Preserves all data (no destructive rollback of data)
3. Passes the round-trip test: `upgrade → downgrade -1 → upgrade`

```python
def downgrade():
    if _has_column("patients", "new_field"):
        op.drop_column("patients", "new_field")
```

**IMPORTANT**: `downgrade()` must NEVER destroy data. If data was transformed in `upgrade()`, `downgrade()` must reverse the transformation.

---

## 9. PRE-MIGRATION BACKUP REQUIREMENTS

Before any migration on a non-development database:

```bash
# Step 1: Full backup
pg_dump -U postgres labdb > /backups/pre_migration_<revision_id>.sql

# Step 2: Checksum
sha256sum /backups/pre_migration_<revision_id>.sql > /backups/pre_migration_<revision_id>.sha256

# Step 3: Verify backup is valid
pg_restore --list /backups/pre_migration_<revision_id>.sql || \
psql -U postgres -c "SELECT COUNT(*) FROM information_schema.tables" labdb

# Step 4: Record rollback point
echo "Migration <revision_id> rollback point: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> /backups/migration_log.txt
```

---

## 10. POST-MIGRATION VALIDATION

After every migration, run:

```sql
-- Record count check
SELECT 'patients' AS table_name, COUNT(*) AS row_count FROM patients
UNION ALL
SELECT 'lab_orders', COUNT(*) FROM lab_orders
UNION ALL
SELECT 'lab_results', COUNT(*) FROM lab_results;

-- FK integrity check
SELECT conname, convalidated
FROM pg_constraint
WHERE contype = 'f' AND NOT convalidated;

-- Check for NULL in formerly non-nullable columns
-- (custom per migration)

-- Check indexes are present
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename IN ('patients', 'lab_orders', 'lab_results');
```

---

## 11. EMERGENCY EXCEPTIONS

In case of a production emergency requiring an unsafe migration:

1. Architecture Board Lead must approve verbally (recorded)
2. Written approval must follow within 1 hour
3. An ADR must be created documenting the exception
4. A full root cause analysis must be completed within 72 hours

---

## 12. REFERENCES

- Data Preservation Constitution: `docs/constitution/31_DATA_PRESERVATION_CONSTITUTION.md`
- Protected Tables Registry: `docs/constitution/data_preservation/protected_tables_registry.md`
- Backup Strategy: `docs/constitution/data_preservation/backup_strategy.md`
- Restore Strategy: `docs/constitution/data_preservation/restore_strategy.md`
- GULA Database Constitution: `docs/constitution/15_DATABASE_CONSTITUTION.md`
- Migration Policy (CLAUDE.md): See `Migration Policy (MANDATORY)` section in `CLAUDE.md`
