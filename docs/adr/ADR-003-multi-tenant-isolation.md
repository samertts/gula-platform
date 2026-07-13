# ADR-003: Multi-Tenant Isolation via lab_id

**Status:** Accepted
**Date:** 2026-01-01
**Deciders:** Engineering Lead

## Context

GULA serves multiple laboratories, each with sensitive patient data. Tenant isolation is required to prevent cross-lab data leakage.

## Decision

Use shared-database, shared-schema multi-tenancy with `lab_id` as the isolation mechanism. Every table that contains tenant-scoped data has a `lab_id` foreign key. Every query must filter by `lab_id = current_user.lab_id`.

Row-level security and optimistic locking (`version` column) provide additional protection.

## Alternatives Considered

- **Database-per-tenant** — Rejected due to operational overhead (schema migrations on N databases)
- **Schema-per-tenant** — Rejected due to connection pool complexity

## Consequences

Positive:
- Simple to implement and test
- Low operational overhead
- Efficient cross-tenant queries (for platform-level analytics)

Negative:
- Requires discipline in every query (missing `lab_id` filter = data leak)
- No physical data separation between tenants

## References

- `backend/app/security/rbac.py` — Permission enforcement
- `backend/app/security/dependencies.py` — Tenant context extraction
