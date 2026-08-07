# Shared Core Report — PROGRAM-STABLE-002

> Generated: 2026-08-02 · Discovery: automated scan of `shared/` + backend usage

## Shared Core (`shared/`) — authoritative implementations

| Concern | Canonical location | Consumers | Duplicates |
|---|---|---|---|
| RBAC / roles / permissions | `shared/rbac/permissions.py` | `backend/app/security/rbac.py` (re-export), routes via `require_permission`, frontend `permissions/index.ts` | 0 (national enum RBAC = separate deliberate national layer) |
| Identity / auth contracts | `shared/auth`, `shared/identity` | NIAM + LIMS identity services | 0 |
| Audit | `shared/audit` | `services/audit_service.py`, `platform/audit.py` | 0 active duplicates |
| Notifications | `shared/notifications`, `backend/app/notifications` | `notifications/service.py` (delivery), `notifications/services.py` `NotificationQueueService` (queue — promoted from NIAM, Commit 3.1/ADR-032), national notification platform | 2 intentional layers (delivery+queue in canonical `backend/app/notifications` / national platform) — documented |
| Barcode / QR | `shared/barcode`, `shared/qr` | `services/pdf_report.py`, patient-card, public result | 0 active |
| Cache | `shared/cache` | `security/redis_client.py` `_LazyCache`, `services/stats_service.py` | 0 |
| Events / bus | `shared/events` | outbox service, worker, factory | 0 |
| Health checks | `shared/health` | `main.py` health endpoints, `services/metrics_service.py` | 0 |
| Security (encryption) | `shared/security` | `backend/app/security/encryption.py` | 0 |
| Scheduler / workflow | `shared/scheduler`, `shared/workflow` | tasks, workflows | 0 |
| DI container | `shared/di_container` | factory wiring | 0 |
| Observability | `shared/metrics`, `shared/tracing`, `shared/logging` | telemetry, OTel | 0 |
| Declarative metadata (national+EHR) | `shared/models/base.py` (`SharedBase`) | `app/national/base.py` (re-export `NationalBase`), `app/ehr/base.py` (`EHRBase`) | 0 — single metadata; breaks the former `app.ehr ↔ app.national` import cycle |
| Rule-engine domain | `shared/rules_engine/domain` | `app/kernel/rules_runtime.py` (direct), `app/national/rules_engine/domain` (re-export) | 0 — breaks the former `app.kernel ↔ app.national` import cycle |
| Search | `backend/app/capabilities/search_service` | `DefaultSearchIndexer`, `DefaultSearchService`, `InfrastructureSemanticSearchService` (promoted from doc-intel, Commit 3.2/ADR-033), wired `/search-service` router; doc-intel `application/wiring.py` (re-pointed) | 1 canonical + 2 retained domain-owned ABCs/FHIR engine (#34/#37) — documented |

## Duplication findings

1. **National layer** (`backend/app/national/security/rbac.py`) defines its own enum-based
   `NationalRole`/`NationalPermission` (18 roles, ~40 permissions). Verdict: **deliberate, not
   duplication** — it is the national-government authorization model (different scope: national
   officers vs LIMS staff), isolated in the national bounded context. Tracked for future
   unification via contract mapping.
2. Notification delivery lives in the canonical `backend/app/notifications` package
   (sync delivery in `service.py` + DB-backed queue/templates/preferences in
   `services.py`/`models.py`/`routes.py`, promoted from `identity/notifications` by
   Commit 3.1/ADR-032) plus the national notification platform (`national/notification_platform`).
   The former 3-layer legacy/NIAM/national split is now 2: canonical vs national — documented
   evolutionary layers; the national platform is a Wave 4 finding (#50).
3. Search implementation lives in the canonical `backend/app/capabilities/search_service`
   (`DefaultSearchIndexer`/`DefaultSearchService`/`InfrastructureSemanticSearchService`,
   promoted from `document_intelligence` by Commit 3.2/ADR-033) behind the wired
   `/search-service` router. The retained `SearchIndexer`/`SearchService`/`SemanticSearchService`
   ABCs in `document_intelligence/application/interfaces.py` (#34) and the national FHIR search
   engine (#37) are classified **Retain as Domain-Owned** — interface contracts and national-layer
   logic respectively, not duplicates.

## Verdict

**Shared Core is unique and authoritative for all cross-cutting concerns. No duplicated
infrastructure in active code.**
