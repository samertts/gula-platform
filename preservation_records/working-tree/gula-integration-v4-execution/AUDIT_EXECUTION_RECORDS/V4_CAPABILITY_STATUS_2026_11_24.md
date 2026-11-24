# Eight generated capability CRUD routes — operational status

Generated 2026-11-24 UTC in the isolated execution workspace. Status labels are
`IMPLEMENTED`, `PARTIAL`, `STUB`, or `BLOCKED` as required by the V4 directive.
These labels describe the **generic CRUD surface** implemented in Wave A and the
**capability as a whole**; they are not production acceptance statements.

## Shared implementation

All eight prefixes use one authoritative implementation:

* Router builder: `backend/app/capabilities/_shared/routes.py`
* Persistence/authorization/audit helpers: `backend/app/capabilities/_shared/crud.py`
* SQLAlchemy model: `backend/app/capabilities/_shared/models.py`
* Migrations: `20261124_0001_capability_crud_records.py`,
  `20261124_0002_capability_record_ownership.py`
* Registration: `backend/app/factory.py`
* Tests: `backend/tests/test_capability_crud.py`,
  `backend/tests/test_capability_crud_postgres.py`

Every write requires `lab:manage`; every read requires `lab:read`; all rows are
scoped to the authenticated institutional user's `lab_id`; creator
`owner_user_id` is stored; create/update/delete append hash-chained audit
records with the authenticated actor. PostgreSQL uses `JSONB`; SQLite test
databases use portable JSON. OpenAPI exposes exactly `40` CRUD operations
(`8 × [list, get, create, update, delete]`).

## Per-capability status

| Capability | Prefix | CRUD surface | Capability as a whole | Evidence / remaining gap |
| --- | --- | --- | --- | --- |
| Document management | `/document-management` | IMPLEMENTED | PARTIAL | Generic records are durable; document binary storage, versioning, retention, and malware scanning are outside this surface. |
| Encounter management | `/encounter-management` | IMPLEMENTED | PARTIAL | Generic records are durable; encounter state machine and clinical linkage require domain-level evidence. |
| Storage service | `/storage-service` | IMPLEMENTED | PARTIAL | Generic records are durable; object-store integration and durability policy remain outside this surface. |
| Clinical foundation | `/clinical-foundation` | IMPLEMENTED | PARTIAL | Generic records are durable; canonical clinical resource contracts C04 require separate conformance evidence. |
| Workflow engine | `/workflow-engine` | IMPLEMENTED | PARTIAL | Generic records are durable; four historical workflow/event stacks remain unresolved. |
| Reporting service | `/reporting-service` | IMPLEMENTED | PARTIAL | Generic records are durable; derived-only analytics truth and report delivery remain unverified. |
| Provider management | `/provider-management` | IMPLEMENTED | PARTIAL | Generic records are durable; authoritative national provider registry ownership remains unresolved. |
| Healthcare consent | `/healthcare-consent` | IMPLEMENTED | PARTIAL | Generic records are durable; consent policy/break-glass semantics need owner decision and conformance proof. |

No capability in this table is STUB or BLOCKED at the generated CRUD layer.
None is production ready.

## Test evidence

* SQLite authenticated lifecycle/negative tests: `14 passed`.
* PostgreSQL 16 migration/schema/durability/rollback/audit tests: `5 passed`.
* Combined CI guard with both disposable PostgreSQL DSNs: `75 passed`.
* PostgreSQL logs and failure evidence are preserved in `AUDIT_EXECUTION_RECORDS/`.
