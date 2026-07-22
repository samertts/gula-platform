# GULA Database Constitution

## Technology

1. **PostgreSQL 16** is the primary database. Version upgrades are evaluated within 6 months of each PostgreSQL release.

2. **Redis 7** is the cache and pub/sub layer. It is not used as a primary data store.

3. **SQLAlchemy 2.x** is the ORM. Raw SQL is used only where ORM performance is inadequate, and must be reviewed.

## Schema Design

4. **Every table has a single-column `id` primary key** (auto-incrementing integer or UUID).

5. **Every table has `created_at`** (NOT NULL, with default `now()`). Tables with mutable data have `updated_at`.

6. **Soft deletes** are used for patient, clinical, and audit records. Hard deletes are limited to transient data (sessions, cache).

7. **Foreign keys** are indexed. Cascade delete is used carefully — never cascade delete that would destroy patient data.

8. **Indexes** are created for:
   - Foreign key columns
   - Frequently queried columns
   - Sort and filter columns
   - Text search columns
   - Composite indexes for multi-column query patterns

9. **Indexes are not created for:**
   - Columns with low cardinality (boolean, status with 2-3 values)
   - Columns never used in WHERE, JOIN, or ORDER BY
   - Columns where the query planner would choose sequential scan anyway

## Migrations

10. **Every schema change is a new Alembic migration.** Existing migrations are immutable.

11. **Migrations are idempotent** — guarded by `_has_table()`, `_has_column()`, `_index_exists()`.

12. **Migrations must pass the round-trip test:** `upgrade` → `downgrade -1` → `upgrade head`.

13. **Data migrations** are separate from schema migrations. Data backfill is a script, not a migration.

14. **Migration naming:** `YYYYMMDD_{seq}_{description}.py`.

## Connection Management

15. **Connection pool** size: `WEB_CONCURRENCY × (DB_POOL_SIZE + DB_MAX_OVERFLOW) < max_connections`.

16. **Connection health** is verified by periodic pool recycling and connection checks.

17. **Read replicas** may be used for reporting and analytics, never for clinical write operations.

## Performance

18. **Queries are analyzed** for sequential scans on large tables. Missing indexes are added.

19. **N+1 query patterns** are prevented through eager loading and joined queries.

20. **Large result sets** use server-side cursors or streaming.

21. **Statement timeout** is set at the session level (30s default). Long-running queries are optimized or moved to background jobs.

## Data Integrity

22. **Check constraints** enforce domain validations at the database level (e.g., `status IN ('active', 'completed', 'cancelled')`).

23. **Unique constraints** prevent duplicate records where business rules require uniqueness.

24. **NOT NULL constraints** are used where data completeness is mandatory for clinical safety.

25. **Default values** are preferred over nullable columns where a sensible default exists.
