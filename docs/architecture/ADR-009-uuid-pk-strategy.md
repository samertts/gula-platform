# ADR-009: UUID Primary Key Strategy

**Status:** Accepted
**Date:** 2026-07-18
**Constitutional Basis:** ENGINEERING_CONSTITUTION.md §2.4, PLATFORM-CONSTITUTION.md §3

## Context

The Engineering Constitution mandates "PostgreSQL 16 with UUID primary keys" for all tables. However, the existing codebase has a mix of Integer/BigInteger PKs (the majority) and UUID PKs (some newer tables). A migration strategy is needed to move toward UUID PKs without breaking existing data or requiring downtime. Full replacement of all Integer PKs with UUIDs is a multi-phase effort.

## Decision

- All NEW tables MUST use UUID primary keys (generated via `gen_random_uuid()`)
- Existing tables with Integer PKs are grandfathered but flagged for future migration
- Foreign keys referencing Integer PK tables remain Integer until the parent table is migrated
- The migration will proceed in phases, one table group at a time, with dual-write columns during transition

### Implementation

```sql
-- New tables
id UUID PRIMARY KEY DEFAULT gen_random_uuid()

-- Migration pattern for existing tables (Phase 2+)
ALTER TABLE patients ADD COLUMN uuid_id UUID DEFAULT gen_random_uuid();
-- Backfill, update FKs, then swap
```

## Rationale

- UUIDs enable distributed/offline ID generation without coordination
- UUIDs prevent enumeration attacks on sequential IDs
- Full immediate migration would require extensive downtime and risk data integrity
- Phased approach aligns with the Stability First constitutional principle

## Consequences

- All Alembic revisions for new tables must use UUID PKs
- Existing Integer PK tables remain; no forced migration timeline
- A registry of Integer PK tables is maintained in `docs/technical-debt/REGISTRY.md`
- The complete migration is tracked as a P2 technical debt item
- API responses expose UUIDs where available; Integer IDs are deprecated but retained for backward compatibility

## Compliance

- Alembic review gates check new tables for UUID PK compliance
- Integer PK tables are flagged in the technical debt registry
- Architecture review is required before migrating any existing Integer PK table
