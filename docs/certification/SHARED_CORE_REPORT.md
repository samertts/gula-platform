# Shared Core Report — PROGRAM-STABLE-002

> Generated: 2026-08-02 · Discovery: automated scan of `shared/` + backend usage

## Shared Core (`shared/`) — authoritative implementations

| Concern | Canonical location | Consumers | Duplicates |
|---|---|---|---|
| RBAC / roles / permissions | `shared/rbac/permissions.py` | `backend/app/security/rbac.py` (re-export), routes via `require_permission`, frontend `permissions/index.ts` | 0 (national enum RBAC = separate deliberate national layer) |
| Identity / auth contracts | `shared/auth`, `shared/identity` | NIAM + LIMS identity services | 0 |
| Audit | `shared/audit` | `services/audit_service.py`, `platform/audit.py` | 0 active duplicates |
| Notifications | `shared/notifications` | `notifications/service.py` (legacy), NIAM `identity/notifications`, national notification platform | 3 intentional layers (legacy/NIAM/national) — documented |
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

## Duplication findings

1. **National layer** (`backend/app/national/security/rbac.py`) defines its own enum-based
   `NationalRole`/`NationalPermission` (18 roles, ~40 permissions). Verdict: **deliberate, not
   duplication** — it is the national-government authorization model (different scope: national
   officers vs LIMS staff), isolated in the national bounded context. Tracked for future
   unification via contract mapping.
2. Notification delivery exists in 3 layers (legacy `/notify`, NIAM, national platform) —
   documented evolutionary layers; each has distinct scope and delivery channels.

## Verdict

**Shared Core is unique and authoritative for all cross-cutting concerns. No duplicated
infrastructure in active code.**
