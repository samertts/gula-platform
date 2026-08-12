# Database Entity Deduplication Plan

## Analysis

### Backend ORM Models (`backend/app/models/`)
17 SQLAlchemy models mapped to PostgreSQL tables.

### Shared Domain Models (`shared/domain/`)
7 domain model modules (dataclass-based DTOs, not ORM entities).

### Shared SQLAlchemy Mixins (`shared/models/`)
`TimestampMixin`, `SoftDeleteMixin`, `AuditMixin`, `TenantMixin`, `OptimisticLockMixin`

## Overlap Analysis

| Backend Model | Shared Equivalent | Overlap | Action |
|--------------|-------------------|---------|--------|
| `Patient` | `domain/healthcare.py → Patient` | Different: ORM vs DTO | Keep both - different layer |
| `LabOrder` | `domain/events.py → OrderCreated` | Different purpose | Keep both |
| `LabResult` | `domain/healthcare.py → TestResult` | Different purpose | Keep both |
| `LabUser` | `domain/security.py → User` | Different purpose | Keep both |
| `AuditLog` | `shared/audit/service.py` | Service layer, not entity | Keep both |
| `Subscription` | `shared/subscriptions.py` | Service layer, not entity | Keep both |

## Migration Plan (Phase B - Do NOT execute yet)

1. **Mixins**: Already done - `backend/app/models/base.py` now imports from `shared.models`
2. **Domain DTOs**: Future - migrate Pydantic schemas to use `shared.domain` types
3. **No ORM duplication**: No SQLAlchemy entity exists in both shared and backend
4. **Alembic migrations**: No changes needed - all tables remain as-is

## Recommendations

1. ✅ **Completed**: Backend model base class now imports `shared.models` mixins
2. ⏳ **Deferred**: Domain DTO alignment (shared.domain → backend schemas)
3. ⏳ **Deferred**: Audit service alignment (shared.audit → backend service)
4. **No ORM schema changes required** in this phase
