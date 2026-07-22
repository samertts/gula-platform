# GULA Backward Compatibility Policy

## Core Principle

GULA guarantees backward compatibility for all published APIs, database schemas, and integration contracts within the same major version. Breaking changes are only introduced in new major versions with clear migration paths. See Article 22 (Release Policy) for versioning semantics.

## What We Guarantee

### API Compatibility
1. All public API endpoints within the same version (`/api/v1/...`) remain functional.
2. Request and response schemas are backward-compatible: new fields may be added, existing fields are never removed or changed in type.
3. Error codes and formats remain consistent.
4. Authentication and authorization mechanisms remain unchanged.

### Database Compatibility
5. All migrations are forward-only and backward-compatible for one version.
6. New columns are nullable or have default values.
7. Existing indexes and constraints are not removed without deprecation notice.
8. Data backfill scripts support online migration (no downtime).

### Integration Compatibility
9. FHIR endpoints maintain the same resource structure.
10. Event schemas are backward-compatible: new fields may be added, existing fields are never removed.
11. Webhook payloads remain compatible.

## Deprecation Process

12. **Deprecation notice** is published at least one full minor version before removal.

13. **Deprecation headers** (`Deprecation: true`, `Sunset: {date}`) are added to deprecated endpoints.

14. **Documentation** marks deprecated features and links to migration guides.

15. **Metrics** track deprecated API usage to inform removal timing.

## Exceptions

16. **Security patches** may break compatibility if the security risk outweighs the compatibility cost. Exception requires CISO approval and documented justification.

17. **Bug fixes** that correct obviously broken behavior (500 error, data corruption) may change behavior without deprecation if the previous behavior was clearly incorrect.

## Migration Guarantee

18. **Migration guides** are provided for every breaking change between major versions.

19. **Automatic migration tools** are provided where feasible (schema migration scripts, API request transformers).

20. **Coexistence window** — new and old versions run in parallel for at least 6 months to allow consumers to migrate at their own pace.
