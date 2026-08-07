# MASTER_REMAINING_WORK — acknowledged debt and migration plan

> PROGRAM-ALPHA | regenerated 2026-08-07
> Everything below is tracked, deterministic debt. It is **blocked from
> growing** — the Architecture Constitution gate fails any PR that adds a new
> finding. Migration is performed only when correctness can be proven, and
> never changes observable behaviour.

## 1. Shared Core consolidation findings (37)

Detected by `architecture-scan` across `backend/app` + `shared/`. These are
legacy reimplementation candidates awaiting migration to their authoritative
provider (see SHARED_CORE_REGISTRY.md). Each requires a human-reviewed,
behaviour-preserving migration.

### By capability

| Capability | Issue | Findings |
|---|---|---|
| `audit` | A new audit-log implementation outside the platform audit core. | 5 |
| `authorization` | A new RBAC/ABAC permission implementation outside the platform. | 2 |
| `barcode_engine` | A new barcode generator/decoder outside shared/barcode. | 1 |
| `dependency_injection` | A new DI container outside shared/di_container. | 1 |
| `document_engine` | A new document/PDF engine outside the platform document core. | 8 |
| `encryption` | A new encryption/crypto implementation outside shared/security. | 2 |
| `events` | A new event bus outside shared/events. | 2 |
| `identity` | A new identity/authentication implementation outside the NIAM identity platform. | 2 |
| `notifications` | A new notification delivery system outside the platform notification core. | 5 |
| `qr_engine` | A new QR generator/decoder outside shared/qr. | 1 |
| `scheduler` | A new scheduler outside shared/scheduler. | 3 |
| `search_engine` | A new search implementation outside the platform search core. | 4 |
| `workflow_engine` | A new workflow engine outside the platform workflow core. | 1 |

### Full list

- [`audit`] `backend/app/document_intelligence/application/interfaces.py`
- [`audit`] `backend/app/document_intelligence/application/wiring.py`
- [`audit`] `backend/app/national/task_engine/domain/repository.py`
- [`audit`] `backend/app/national/task_engine/infrastructure/repository.py`
- [`audit`] `backend/app/services/authorization_service.py`
- [`authorization`] `backend/app/control_plane/policy/enforcer.py`
- [`authorization`] `backend/app/services/authorization_service.py`
- [`barcode_engine`] `backend/app/models/sample.py`
- [`dependency_injection`] `backend/app/kernel/runtime/di_container.py`
- [`document_engine`] `backend/app/document_intelligence/application/interfaces.py`
- [`document_engine`] `backend/app/document_intelligence/domain/repository.py`
- [`document_engine`] `backend/app/document_intelligence/infrastructure/repository.py`
- [`document_engine`] `backend/app/national/document_platform/api/routes.py`
- [`document_engine`] `backend/app/national/document_platform/application/interfaces.py`
- [`document_engine`] `backend/app/national/document_platform/application/service.py`
- [`document_engine`] `backend/app/national/document_platform/domain/repository.py`
- [`document_engine`] `backend/app/national/document_platform/infrastructure/repository.py`
- [`encryption`] `backend/app/document_intelligence/security.py`
- [`encryption`] `backend/app/national/ecosystem/transformation/engine.py`
- [`events`] `backend/app/kernel/event_bus/bus.py`
- [`events`] `backend/app/kernel/runtime_sdk.py`
- [`identity`] `backend/app/citizen_platform/identity.py`
- [`identity`] `backend/app/services/authorization_service.py`
- [`notifications`] `backend/app/citizen_platform/notifications.py`
- [`notifications`] `backend/app/identity/notifications/routes.py`
- [`notifications`] `backend/app/identity/notifications/services.py`
- [`notifications`] `backend/app/national/notification_platform/api/routes.py`
- [`notifications`] `backend/app/platform/notifications.py`
- [`qr_engine`] `backend/app/national/document_platform/application/service.py`
- [`scheduler`] `backend/app/document_intelligence/backup_dr.py`
- [`scheduler`] `backend/app/kernel/background/cron.py`
- [`scheduler`] `backend/app/kernel/background/scheduler.py`
- [`search_engine`] `backend/app/document_intelligence/application/interfaces.py`
- [`search_engine`] `backend/app/document_intelligence/application/service.py`
- [`search_engine`] `backend/app/document_intelligence/infrastructure/services.py`
- [`search_engine`] `backend/app/national/fhir/search.py`
- [`workflow_engine`] `backend/app/national/workflow_runtime/api/routes.py`

## 2. Country-specific hard-coding (2)

Allowed only inside the national layer (`backend/app/national`, `backend/app/nhdw`,
`backend/app/national_data`):

- `backend/app/research_platform/base.py` — marker `['\"](?:i)?raq['\"]`
- `backend/app/services/reference/master_reference_data.py` — marker `\bdinar\b`

## 3. High-priority migrations

1. **Notifications consolidation** — route `backend/app/platform/notifications.py`,
   `backend/app/identity/notifications/`, `backend/app/citizen_platform/notifications.py`
   and `backend/app/national/notification_platform/` onto the platform
   notification core (`backend/app/notifications`).
2. **Audit consolidation** — fold `backend/app/platform/audit.py`
   (archived, Commit 1.1) and `backend/app/national/security/audit.py`
   (archived, Commit 1.8) and document-intelligence audit
   (in progress, Wave 1/4) onto the NIAM immutable audit core.
3. **Authorization consolidation** — unify `backend/app/services/authorization_service.py`
   with the NIAM authorization service; audit platform/identity duplicate RBAC/ABAC.
4. **Engine consolidation** — kernel scheduler/event-bus/DI and identity
   workflow engine should consume `shared/` (scheduler, events, di_container,
   workflow) instead of reimplementing.
5. **Barcode/QR** — `backend/app/models/sample.py` `generate_barcode()` and the
   document-platform QR service must call `shared/barcode` + `shared/qr`.
6. **Encryption** — `backend/app/services/offline_sync_service.py` and the
   national transformation engine must consume `shared/security/encryption.py`.

## 4. Governance

- Every migration is a dedicated PR with regression tests + `architecture-check` PASS.
- New findings fail CI immediately (no baseline growth).
- Uncertain migrations STOP and request human review (per PROGRAM-ALPHA rules).

_Generated by scripts/architecture/docs.py._
