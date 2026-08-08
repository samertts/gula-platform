# MASTER_REMAINING_WORK — acknowledged debt and migration plan

> PROGRAM-ALPHA | regenerated 2026-08-08
> **PROGRAM-01 FINAL CLOSURE — ARCHITECTURE LOCKED.** Baseline frozen at
> **25 acknowledged findings** + 2 resolved (encryption)
> = **0 actionable**. The remaining findings are intentionally frozen
> (Domain-Owned, Strategic Exception, kernel-domain register, or False
> Positive) and are **blocked from growing** — the Architecture Constitution
> gate fails any PR that adds a new finding. Migration is performed only when
> correctness can be proven, and never changes observable behaviour.

## 1. Shared Core consolidation findings (25) — FROZEN

Detected by `architecture-scan` across `backend/app` + `shared/`. These are
legacy reimplementation candidates awaiting migration to their authoritative
provider (see SHARED_CORE_REGISTRY.md). Each requires a human-reviewed,
behaviour-preserving migration.

### By capability

| Capability | Issue | Findings |
|---|---|---|
| `audit` | A new audit-log implementation outside the platform audit core. | 3 |
| `authorization` | A new RBAC/ABAC permission implementation outside the platform. | 2 |
| `barcode_engine` | A new barcode generator/decoder outside shared/barcode. | 1 |
| `dependency_injection` | A new DI container outside shared/di_container. | 1 |
| `document_engine` | A new document/PDF engine outside the platform document core. | 6 |
| `events` | A new event bus outside shared/events. | 2 |
| `identity` | A new identity/authentication implementation outside the NIAM identity platform. | 2 |
| `notifications` | A new notification delivery system outside the platform notification core. | 2 |
| `qr_engine` | A new QR generator/decoder outside shared/qr. | 1 |
| `scheduler` | A new scheduler outside shared/scheduler. | 3 |
| `search_engine` | A new search implementation outside the platform search core. | 2 |

### Full list

- [`audit`] `backend/app/document_intelligence/application/interfaces.py`
- [`audit`] `backend/app/national/task_engine/domain/repository.py`
- [`audit`] `backend/app/services/authorization_service.py`
- [`authorization`] `backend/app/control_plane/policy/enforcer.py`
- [`authorization`] `backend/app/services/authorization_service.py`
- [`barcode_engine`] `backend/app/models/sample.py`
- [`dependency_injection`] `backend/app/kernel/runtime/di_container.py`
- [`document_engine`] `backend/app/document_intelligence/application/interfaces.py`
- [`document_engine`] `backend/app/document_intelligence/domain/repository.py`
- [`document_engine`] `backend/app/document_intelligence/infrastructure/repository.py`
- [`document_engine`] `backend/app/national/document_platform/application/interfaces.py`
- [`document_engine`] `backend/app/national/document_platform/domain/repository.py`
- [`document_engine`] `backend/app/national/document_platform/infrastructure/repository.py`
- [`events`] `backend/app/kernel/event_bus/bus.py`
- [`events`] `backend/app/kernel/runtime_sdk.py`
- [`identity`] `backend/app/citizen_platform/identity.py`
- [`identity`] `backend/app/services/authorization_service.py`
- [`notifications`] `backend/app/citizen_platform/notifications.py`
- [`notifications`] `backend/app/platform/notifications.py`
- [`qr_engine`] `backend/app/national/document_platform/application/service.py`
- [`scheduler`] `backend/app/document_intelligence/backup_dr.py`
- [`scheduler`] `backend/app/kernel/background/cron.py`
- [`scheduler`] `backend/app/kernel/background/scheduler.py`
- [`search_engine`] `backend/app/document_intelligence/application/interfaces.py`
- [`search_engine`] `backend/app/national/fhir/search.py`

## 2. Country-specific hard-coding (2)

Allowed only inside the national layer (`backend/app/national`, `backend/app/nhdw`,
`backend/app/national_data`):

- `backend/app/research_platform/base.py` — marker `['\"](?:i)?raq['\"]`
- `backend/app/services/reference/master_reference_data.py` — marker `\bdinar\b`

## 3. High-priority migrations

1. **Notifications consolidation** — route `backend/app/platform/notifications.py`,
   `backend/app/identity/notifications/`, `backend/app/citizen_platform/notifications.py`
   and `backend/app/national/notification_platform/` onto the platform
   notification core (`backend/app/notifications`). (Partially complete: the
   NIAM queue was promoted and the national adapters were re-pointed in
   PROGRAM-01 Wave 4; remaining #23 is frozen Domain-Owned.)
2. **Audit consolidation** — fold `backend/app/platform/audit.py`
   (archived, Commit 1.1) and `backend/app/national/security/audit.py`
   (archived, Commit 1.8) and document-intelligence audit
   (re-pointed, Wave 4 order 16) onto the NIAM immutable audit core.
   (Remaining #4/#8/#10 are frozen Domain-Owned.)
3. **Authorization consolidation** — unify `backend/app/services/authorization_service.py`
   with the NIAM authorization service; audit platform/identity duplicate RBAC/ABAC.
   (Remaining #21/#30 are frozen Domain-Owned, ADR-034.)
4. **Engine consolidation** — kernel scheduler/event-bus/DI and identity
   workflow engine should consume `shared/` (scheduler, events, di_container,
   workflow) instead of reimplementing. (Remaining #11/#32/#33 are frozen
   kernel-domain register; #18 is a frozen Strategic Exception.)
5. **Barcode/QR** — `backend/app/models/sample.py` `generate_barcode()` and the
   document-platform QR service must call `shared/barcode` + `shared/qr`.
   (Remaining #40/#41 are frozen Domain-Owned.)
6. **Encryption** — ✅ **RESOLVED in PROGRAM-01 FINAL CLOSURE**: the
   `national/ecosystem/transformation` EncryptionEngine (#2) and the
   document-intelligence EncryptionService (#1) now delegate to
   `shared/security/encryption.py`; `offline_sync_service` encryption
   routes through the canonical wrapper. No actionable encryption findings
   remain.

## 4. Governance

- **PROGRAM-01 is COMPLETE and ARCHITECTURE LOCKED.** All remaining findings are frozen with an explicit state (`Domain-Owned`, `Strategic Exception`, `kernel-domain`, `False Positive`); `0 actionable`.
- Every future migration is a dedicated PR with regression tests + `architecture-check` PASS.
- New findings fail CI immediately (no baseline growth).
- Uncertain migrations STOP and request human review (per PROGRAM-ALPHA rules).

_Generated by scripts/architecture/docs.py._
