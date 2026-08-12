# ADR-005: PostgreSQL 16 with Redis 7

**Status:** Accepted
**Date:** 2026-07-08
**Deciders:** Engineering Lead, Platform Architect, Database Administrator

## Context

The GULA Platform requires a primary database for patient data, lab orders, results, and audit logs, plus a fast cache layer for session management, rate limiting, and real-time features. The chosen technologies must support Arabic text (UTF-8), provide ACID compliance for patient data, and scale to hundreds of concurrent laboratory users.

## Decision

Use PostgreSQL 16 as the primary database and Redis 7 as the cache and session store.

### PostgreSQL 16
- ACID-compliant relational database for all transactional data
- Full-text search for Arabic patient names (via ICU tokenisation)
- JSONB support for flexible lab result schemas
- Alembic for schema migrations with immutable revision policy
- Connection pool sized to fit within PostgreSQL's default `max_connections=100`

### Redis 7
- In-memory cache for JWT token blacklist
- Rate limiting counters (sliding window)
- Session storage for refresh tokens
- Pub/sub for real-time notifications
- Configurable via `REDIS_URL` environment variable

## Alternatives Considered

### 1. MySQL 8

**Pros:** Widely deployed, good tooling.
**Cons:** Weaker full-text search for Arabic, less mature JSONB support, migration tooling less integrated with Python.
**Rejected because:** PostgreSQL provides superior Arabic text handling and JSONB flexibility for lab results.

### 2. MongoDB

**Pros:** Schema-less, flexible for lab result variability.
**Cons:** No ACID guarantees across documents, weaker audit trail integrity, team lacks MongoDB operations experience.
**Rejected because:** ACID compliance is non-negotiable for patient data.

### 3. SQLite

**Pros:** Zero configuration, embedded.
**Cons:** No concurrent write support, no network access, unsuitable for multi-tenant SaaS.
**Rejected because:** Cannot support concurrent laboratory users.

### 4. Memcached (instead of Redis)

**Pros:** Simpler, lower memory overhead.
**Cons:** No pub/sub, no data persistence, no native rate limiting structures.
**Rejected because:** Redis features are needed for rate limiting, pub/sub, and token blacklisting.

## Consequences

### Positive
- PostgreSQL 16 provides robust Arabic text support via ICU
- Alembic integration ensures safe, version-controlled schema evolution
- Redis 7 supports all required cache patterns (rate limiting, session, pub/sub)
- Both are well-supported by SQLAlchemy 2.0 and Python ecosystem
- Connection pool budget formula (`WEB_CONCURRENCY × (DB_POOL_SIZE + DB_MAX_OVERFLOW) < max_connections`) ensures safe scaling

### Negative
- Two data stores increase operational complexity
- Redis persistence must be configured for production (RDB/AOF)
- PostgreSQL connection pool must be re-budgeted when scaling horizontally
- Migration from older PostgreSQL versions requires careful planning

### Neutral
- Both technologies are mature and widely deployed in healthcare SaaS
- Team has operational experience with both
- Cloud-managed alternatives (RDS, ElastiCache) remain options

## References
- `backend/app/database.py` — Connection pool and contextvar configuration
- `backend/app/config.py` — Database and Redis environment variables
- `backend/migrations/` — Alembic migration versions
- ADR-002: Monolith First Architecture
- ADR-003: Multi-Tenant Isolation via lab_id
