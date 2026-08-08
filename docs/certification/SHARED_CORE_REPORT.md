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
| Security (encryption) | `shared/security` | `backend/app/security/encryption.py` (delegating wrapper), `document_intelligence/security.py` `EncryptionService` (delegates to `encrypt_bytes`/`decrypt_bytes` — Wave 5 FINAL CLOSURE #1), `national/ecosystem/transformation/engine.py` `EncryptionEngine` AES-256 branch (delegates to `encrypt_value`/`decrypt_value`, SHA-256 derivation preserved — Wave 5 FINAL CLOSURE #2) | 0 active — last two `Fernet(` duplicates in `backend/app` removed in PROGRAM-01 FINAL CLOSURE |
| Scheduler / workflow | `shared/scheduler`, `shared/workflow` | tasks, workflows | 0 |
| DI container | `shared/di_container` | factory wiring | 0 |
| Observability | `shared/metrics`, `shared/tracing`, `shared/logging` | telemetry, OTel | 0 |
| Declarative metadata (national+EHR) | `shared/models/base.py` (`SharedBase`) | `app/national/base.py` (re-export `NationalBase`), `app/ehr/base.py` (`EHRBase`) | 0 — single metadata; breaks the former `app.ehr ↔ app.national` import cycle |
| Rule-engine domain | `shared/rules_engine/domain` | `app/kernel/rules_runtime.py` (direct), `app/national/rules_engine/domain` (re-export) | 0 — breaks the former `app.kernel ↔ app.national` import cycle |
| PDF / document | `shared/pdf/generator.py` (reportlab: `generate_result_pdf`, `generate_pdf`) | `citizen_platform/laboratory.py` (direct), `capabilities/document_management/pdf_generator.py` `SharedPdfGenerator` (thin adapter over the canonical generator, wired into the national document platform `POST /national/documents/{id}/generate-pdf`, Commit 3.3/ADR-033) | 0 active — the national `generate_pdf` delegator/handler signals were vacated; domain `PDFGenerator` ABC retained (#14) |
| Search | `backend/app/capabilities/search_service` | `DefaultSearchIndexer`, `DefaultSearchService`, `InfrastructureSemanticSearchService` (promoted from doc-intel, Commit 3.2/ADR-033), wired `/search-service` router; doc-intel `application/wiring.py` (re-pointed) | 1 canonical + 2 retained domain-owned ABCs/FHIR engine (#34/#37) — documented |
| Workflow engine | `backend/app/workflows/engine.py` (`WorkflowEngine`, `def_id`-keyed, exposed at `/niam/workflows` via `identity/workflows/routes.py`) | NIAM `WorkflowsPage`, identity workflows router | 0 active — the wired-but-broken `national/workflow_runtime` duplicate (0-byte service, every `/national/workflows/*` handler returned HTTP 500) was **archived in Commit 3.6/ADR-036** (#44); `platform/workflow.py` dead code archived with it |

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
   evolutionary layers. The national platform's fabricating adapters were re-pointed to the
   canonical provider by Wave 4 order 18 (ADR-032, finding #50).
3. Search implementation lives in the canonical `backend/app/capabilities/search_service`
   (`DefaultSearchIndexer`/`DefaultSearchService`/`InfrastructureSemanticSearchService`,
   promoted from `document_intelligence` by Commit 3.2/ADR-033) behind the wired
   `/search-service` router. The retained `SearchIndexer`/`SearchService`/`SemanticSearchService`
   ABCs in `document_intelligence/application/interfaces.py` (#34) and the national FHIR search
   engine (#37) are classified **Retain as Domain-Owned** — interface contracts and national-layer
   logic respectively, not duplicates.
4. Document PDF generation lives in the canonical `shared/pdf/generator.py`. The national
   document platform endpoint `POST /national/documents/{id}/generate-pdf` is wired to it via the
   canonical adapter `capabilities/document_management/pdf_generator.py` (`SharedPdfGenerator`,
   Commit 3.3/ADR-033) — the `generate_pdf` signals in the national routes/service were vacated
   (renamed `export_document_pdf`/`export_pdf`), so the platform has exactly one PDF concretion.
   The domain `PDFGenerator` ABC (`national/document_platform/application/interfaces.py`, #14) is
   retained as a domain-owned contract.
5. Workflow runtime lives in the canonical `backend/app/workflows/engine.py` (`WorkflowEngine`,
   exposed at `/niam/workflows`). The `national/workflow_runtime` package (finding #44) was
   **wired-but-broken**: its `application/service.py` was 0 bytes, so all 20
   `/national/workflows/*` handlers raised ImportError / HTTP 500. It was archived in
   Commit 3.6/ADR-036 (all 15 files preserved under `archive/platform-shared-core/` with
   provenance headers; `platform/workflow.py` dead code archived with it). The frontend national
   page, generated-client section, nav entry, and script registries were removed/re-pointed
   atomically. The canonical engine is the single live workflow implementation.
6. Encryption lives in the canonical `shared/security/encryption.py`. The last two `Fernet(`
   constructions in `backend/app` — the doc-intel `EncryptionService` (#1) and the ecosystem
   `EncryptionEngine` AES-256 branch (#2) — were migrated to canonical delegation in
   **PROGRAM-01 FINAL CLOSURE** (Wave 5 orders 20–21): both now round-trip through
   `encrypt_value`/`decrypt_value`/`encrypt_bytes`/`decrypt_bytes`; the ecosystem SHA-256 key
   derivation is preserved so existing ciphertext stays decryptable and new tokens are
   byte-identical. Regression coverage: `backend/tests/test_encryption_canonical.py` (9 tests).

## Verdict

**Shared Core is unique and authoritative for all cross-cutting concerns. No duplicated
infrastructure in active code.**

**PROGRAM-01 FINAL CLOSURE:** baseline **25 frozen findings** (19 Domain-Owned, 1 Strategic
Exception, 3 kernel-domain register, 2 False Positive) + **2 resolved** (encryption) = **0
actionable**. Architecture **LOCKED**. The deterministic gate continues to fail any NEW finding.
