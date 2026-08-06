---
id: DB-000001
type: database
title: "Database Knowledge Bridge"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 100%
tags: [database, postgresql, redis, bridge]
---

# Database Knowledge — Bridge Reference

## Schema
- `docs/database/DATABASE_SCHEMA.md` — Full schema (62KB, 281 tables)
- `docs/database/entity_deduplication_plan.md` — Deduplication plan
- `docs/architecture/ENTITY_CATALOG.md` — All entities

## Stack
- PostgreSQL 16 — Primary data store
- Redis 7.x — Caching, sessions, task queue
- MinIO — S3-compatible object storage

## Migrations
- Alembic-managed
- 50 migrations to head `20260723_0002`
- Never destructive — backward compatible only

## Key Patterns
- UUID primary keys (ADR-009)
- Multi-tenant isolation via `tenant_id`
- Immutable audit log (append-only)
- Soft deletes (no hard deletes)
- JSONB for flexible fields

## Performance
- `docs/performance/query-optimization-guide.md` — Query optimization
- Redis caching with TTL
- Connection pooling

## Related
- `.ai/core/memory/PROJECT_MEMORY.md` — DB decisions
- `docs/decisions/SECURITY_DECISIONS.md` — DB security
