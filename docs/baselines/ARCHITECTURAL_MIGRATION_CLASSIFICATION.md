# Architectural Migration Classification

**PROGRAM-01 Structural Migration — authoritative execution plan**
**Date:** 2026-08-07
**Baseline:** `.ai/core/architecture/constitution_baseline.json` — 51 findings (+ 2 country findings)
**Decision model:** 5-class classification, established by Commit 1.3 (ADR-029 Canonical Provider Promotion)

---

## 1. Classification Model

Every remaining Architecture Constitution finding is assigned **exactly one** of
five migration strategies:

| # | Class | Meaning | Canonical provider state |
|---|---|---|---|
| 1 | **Archive and Re-point** | Canonical provider is already complete; finding is dead code or a real duplicate. Archive (or delete with evidence) + re-point consumers. | Complete & live |
| 2 | **Canonical Provider Promotion** | The live implementation is the ONLY behaviorally complete implementation. Promote it into the canonical path (ADR-029). | Incomplete/empty; live impl elsewhere |
| 3 | **Canonical Provider Completion** | Canonical provider exists but is incomplete. Complete the canonical provider first, then migrate the finding. | Exists but incomplete/stub |
| 4 | **Retain as Domain-Owned** | Implementation belongs inside its domain; it is NOT a Shared Core violation. Document, do not migrate. | n/a — legitimate domain code |
| 5 | **Strategic Exception** | The Constitution should not automatically apply. Requires an ADR to document the exception. | n/a — deliberate deviation |

**Cross-cutting sub-class (found within classes 1/4):** *False Positive* — the
baseline entry no longer matches any source signal; removal is evidence-based
(ADR-028 Rule 2), not a migration.

---

## 2. Complete Classification (51 findings)

Legend: **Effort** S=Small, M=Medium, L=Large · **Risk** L=Low, M=Medium, H=High
· **Rollback** L=Low (single revert), M=Medium, H=High (requires data/coordination).

### 2.1 Encryption (3)

| # | Current implementation | Canonical provider | Behavioral equivalence | Class | Risk | Effort | Rollback | ADR | Order |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `document_intelligence/security.py` — `EncryptionService` (Fernet) | `shared/security/encryption.py` — complete | Equivalent (symmetric) | **Archive and Re-point** | L | S | L | No | 21 |
| 2 | `national/ecosystem/transformation/engine.py` — `EncryptionEngine` (Fernet+RSA-OAEP) | `shared/security/encryption.py` | Equivalent for active scope (RSA branch dormant) | **Archive and Re-point** | L | M | L | No | 20 |
| 3 | `services/offline_sync_service.py` — `EncryptedSyncStore` (Fernet) | `shared/security/encryption.py` | Equivalent | **Archive and Re-point** | L | S | L | No | 3 |

Evidence: all three are real but **production-dead** (consumers = tests + package
re-exports only). Canonical is complete and live.

### 2.2 Audit (7)

| # | Current implementation | Canonical provider | Behavioral equivalence | Class | Risk | Effort | Rollback | ADR | Order |
|---|---|---|---|---|---|---|---|---|---|
| 4 | `document_intelligence/application/interfaces.py` — `AuditService(ABC)` | `identity/services/audit_service.py::AuditService` (complete, live, hash-chained) | Interface only — not an impl | **Retain as Domain-Owned** | L | S | L | No | — |
| 5 | `document_intelligence/application/wiring.py` — `DefaultAuditService` (no-op logger) | same | Canonical complete; finding is a **no-op stub** | **Archive and Re-point** (behavior-additive) | M | M | M | Yes | 16 |
| 6 | `document_intelligence/security.py` — `AuditLogger` (in-memory) | same | Canonical stronger (DB+chain) | **Archive and Re-point** | L | S | L | No | 4 |
| 7 | `national/security/audit.py` — `SecurityAuditService` (in-memory, broken verify_chain) | same | Canonical complete; finding is dead+buggy | **Archive and Re-point** | L | S | L | No | 5 |
| 8 | `national/task_engine/domain/repository.py` — `TaskAuditLogRepository(ABC)` | same | Interface only — domain contract | **Retain as Domain-Owned** | L | S | L | No | — |
| 9 | `national/task_engine/infrastructure/repository.py` — `SQLAlchemyTaskAuditLogRepository` (no-op, drops audit) | same | Canonical complete; finding is a **silent no-op** | **Archive and Re-point** (behavior-additive) | M | M | M | Yes | 17 |
| 10 | `services/authorization_service.py` — `AuthorizationAuditService` (decision-log, own schema) | same | **Not equivalent** — canonical lacks decision/policy/risk fields | **Retain as Domain-Owned** | L | S | L | No | — |

### 2.3 Dependency Injection (1)

| # | Current implementation | Canonical provider | Behavioral equivalence | Class | Risk | Effort | Rollback | ADR | Order |
|---|---|---|---|---|---|---|---|---|---|
| 11 | `kernel/runtime/di_container.py` — `DIContainer` (name-keyed locator) | `shared/di_container` (type-keyed, auto-wiring) | Incompatible APIs; kernel container is its own runtime infra | **Retain as Domain-Owned** | M | M | H | Yes | — |

Evidence: kernel runtime is LIVE (startup_guard Step 5, factory routers);
`shared/di_container` has zero consumers/tests. Consolidation = API rewrite of
kernel boot with no behavior gain. ADR to document kernel-domain retention.

### 2.4 Document Engine / PDF (10)

| # | Current implementation | Canonical provider | Behavioral equivalence | Class | Risk | Effort | Rollback | ADR | Order |
|---|---|---|---|---|---|---|---|---|---|
| 12 | `document_intelligence/domain/repository.py` — `DocumentRepository(ABC)` | `capabilities/document_management` (stub routes) | Interface only | **Retain as Domain-Owned** | L | S | L | No | — |
| 13 | `document_intelligence/infrastructure/repository.py` — `SqlDocumentRepository` (real SQLAlchemy) | same (stub) | Canonical is a **stub** (NotImplementedError); live repo cannot be re-pointed | **Retain as Domain-Owned** | M | M | M | Yes | — |
| 14 | `national/document_platform/application/interfaces.py` — `PDFGenerator(ABC)` | `shared/pdf/generator.py` (real reportlab) | Interface only, zero concrete impls | **Retain as Domain-Owned** | L | S | L | No | — |
| 15 | `national/document_platform/domain/repository.py` — `DocumentRepository(ABC)` | `capabilities/document_management` (stub) | Interface only | **Retain as Domain-Owned** | L | S | L | No | — |
| 16 | `national/document_platform/infrastructure/repository.py` — `SQLAlchemyDocumentRepository` (real) | same (stub) | Canonical is a stub; live repo is real | **Retain as Domain-Owned** | M | M | M | Yes | — |
| 45 | `document_intelligence/application/interfaces.py` — `generate_pdf` (abstract) | `shared/pdf/generator.py` (real) | Abstract only, zero concrete impls | **Retain as Domain-Owned** | L | S | L | No | — |
| 46 | `national/document_platform/api/routes.py` — `generate_pdf` (live endpoint → 422) | `shared/pdf/generator.py` (real) | Canonical complete; endpoint needs wiring | **Canonical Provider Completion** | M | S | L | Yes | 15 |
| 47 | `national/document_platform/application/service.py` — `generate_pdf` (delegator to None) | `shared/pdf/generator.py` (real) | Same as #46 | **Canonical Provider Completion** | M | S | L | Yes | 15 |

Note on #13/#16: canonical `capabilities/document_management` and
`capabilities/search_service` **routers ARE registered** in factory.py
(`/document-management`, `/search-service`) and return hardcoded stub responses —
live HTTP surfaces that would break if the real repos were re-pointed. They
belong in Wave 4 (completion of capability scaffolds).

### 2.5 Event Bus (4)

| # | Current implementation | Canonical provider | Behavioral equivalence | Class | Risk | Effort | Rollback | ADR | Order |
|---|---|---|---|---|---|---|---|---|---|
| 17 | `integration/esb/message_bus.py` — `ESBMessageBus` (async, DLQ) | `shared/events` (sync pub/sub) | Canonical is a strict subset; finding is **dead** (never instantiated) | **Archive and Re-point** (delete with evidence) | L | S | L | No | 6 |
| 18 | `kernel/event_bus/bus.py` — `EventBus` (809-L: store/outbox/DLQ/replay) | `shared/events` (41-L sync) | Canonical is a strict subset; kernel bus is LIVE backbone (6+ services) | **Strategic Exception** | H* | L | L* | **Yes** | — |
| 48 | `kernel/runtime_sdk.py` — `publish_event` (facade over kernel bus) | `shared/events` | Facade, not reimplementation — false positive | **Retain as Domain-Owned** (false positive) | L | L | L | No | — |

*#18 risk H applies only if migrated (it is a rewrite, not refactor); Retain =
L/L/L. ADR-required to register the kernel event bus as a Strategic Exception.

### 2.6 Identity / Authentication (4)

| # | Current implementation | Canonical provider | Behavioral equivalence | Class | Risk | Effort | Rollback | ADR | Order |
|---|---|---|---|---|---|---|---|---|---|
| 19 | `citizen_platform/identity.py` — `HealthIdentityService` (national-id verify) | `backend/app/identity` (NIAM) | Different stack; citizen-portal national-id verification | **Retain as Domain-Owned** | L | S | L | No | — |
| 20 | `national/services/identity_service.py` — `IdentityService` (dead route layer) | NIAM CitizenRegistry | Overlaps canonical; **dead** (unwired route) | **Archive and Re-point** | L | S | L | No | 7 |
| 21 | `services/authorization_service.py` — `IdentityService.get_identity_context` | NIAM identity context | Analogous but legacy lab-UI scoped | **Retain as Domain-Owned** | M | M | L | No | 22 |
| 22 | `services/risk_based_auth_service.py` — `RiskBasedAuthService` (dead) | `identity/adaptive_auth` (live) | Canonical equivalent is live; finding is dead | **Archive and Re-point** | L | S | L | No | 8 |
 | 51 | `services/mobile_service.py` — `verify_password` | `shared/auth` (via `security/auth.py`) | **Already canonical** — imports and calls the shared bcrypt fn; signal matched the call site, not a definition (fixed via `def\s+`-only signals, Commits 1.5) | **False Positive** (remove with evidence) | L | S | L | No | 2 |

### 2.7 Notifications (6)

| # | Current implementation | Canonical provider | Behavioral equivalence | Class | Risk | Effort | Rollback | ADR | Order |
|---|---|---|---|---|---|---|---|---|---|
| 23 | `citizen_platform/notifications.py` — `CitizenNotificationService` (in-memory inbox) | `backend/app/notifications` (real delivery, no persistence) | Canonical delivers but has no persistence; this has neither | **Retain as Domain-Owned** (data-loss risk) | M | M | M | Yes | — |
| 24 | `identity/notifications/services.py` — `NotificationService` (queue-only) | `backend/app/notifications` (delivery) | Complementary halves — canonical delivers, this queues | **Canonical Provider Completion** | M | M | M | Yes | 13 |
| 25 | `national/workflow_runtime/application/interfaces.py` — `WorkflowNotifier(ABC)` | `backend/app/workflows` (live engine) | Orphan interfaces; service.py is **0 bytes** | **Archive and Re-point** | L | S | L | No | 10 |
| 26 | `platform/notifications.py` — `NotificationService` (facade) | `backend/app/notifications` | **Is** the canonical facade — delegates, no duplication | **Retain as Domain-Owned** (false positive) | L | S | L | No | — |
| 49 | `identity/notifications/routes.py` — `send_notification` (queue-only) | `backend/app/notifications` | Same as #24 | **Canonical Provider Completion** | M | M | M | Yes | 13 |
| 50 | `national/notification_platform/api/routes.py` — `send_notification` (16 endpoints) | `backend/app/notifications` | **Adapters fabricate `success=True` without sending** (Email/SMS/Push/WS/InApp/WA/Gov/Fax) | **Canonical Provider Completion** (clinical-safety risk) | **H** | L | M | Yes | 18 |

### 2.8 QR (3)

| # | Current implementation | Canonical provider | Behavioral equivalence | Class | Risk | Effort | Rollback | ADR | Order |
|---|---|---|---|---|---|---|---|---|---|
| 27 | `citizen_platform/identity.py` — `EmergencyQRService` (in-memory token) | `shared/qr` (real image gen) | Different scheme (token-verify, not image); **dead** | **Archive and Re-point** | L | S | L | No | 9 |
| 28 | `governance/services/citizen_platform_persistence.py` — `PersistedEmergencyQRService` (DB, orphaned) | `shared/qr` | Dead twin of dead class | **Archive and Re-point** | L | S | L | No | 9 |
| 41 | `national/document_platform/application/service.py` — `generate_qr` (doc-verify token) | `shared/qr` | Document verification token, not image QR | **Retain as Domain-Owned** | L | S | L | No | — |

### 2.9 Authorization / RBAC / ABAC (3)

| # | Current implementation | Canonical provider | Behavioral equivalence | Class | Risk | Effort | Rollback | ADR | Order |
|---|---|---|---|---|---|---|---|---|---|
| 29 | `control_plane/policy/enforcer.py` — `PolicyEnforcer` | `security/abac.py`, `shared/rbac` | Component-governance policy, NOT user access control | **Retain as Domain-Owned** | L | S | L | No | — |
| 30 | `services/authorization_service.py` — `PermissionService/RoleService/PolicyService` (DB-backed) | `identity/services/authorization_service.py` (canonical) | Parallel ABAC (Policy.evaluate_policies) duplicates `security/abac.py` | **Retain as Domain-Owned** | M | M | L | Yes | 22 |
| 42 | `integration/api_management/auth.py` — `APIAuth.check_permission` (in-memory API-key+HMAC) | `identity/services/authorization_service.py`, `shared/rbac` | Different mechanism (machine API-key vs person RBAC); **dead** — `APIGateway`/`APIPortal` never instantiated, zero callers/tests | **Archive and Re-point** (delete with evidence) | L | S | L | No | 6 |

### 2.10 Scheduler (3)

| # | Current implementation | Canonical provider | Behavioral equivalence | Class | Risk | Effort | Rollback | ADR | Order |
|---|---|---|---|---|---|---|---|---|---|
| 31 | `document_intelligence/backup_dr.py` — `BackupScheduler` (async DR loop) | `shared/scheduler.py` (79-L, complete, 0 consumers) | Real DR utility, test-covered; dormant | **Retain as Domain-Owned** | L | S | L | No | — |
| 32 | `kernel/background/cron.py` — `CronEngine` (registry only, no exec) | `shared/scheduler.py` | Kernel scheduler is a **superset** (queue/worker/locks) | **Retain as Domain-Owned** | L | L | L | Yes | — |
| 33 | `kernel/background/scheduler.py` — `Scheduler` (269-L composition root) | `shared/scheduler.py` | Kernel is strictly richer; live registered component | **Retain as Domain-Owned** | L | L | L | Yes | — |

### 2.11 Search (5)

| # | Current implementation | Canonical provider | Behavioral equivalence | Class | Risk | Effort | Rollback | ADR | Order |
|---|---|---|---|---|---|---|---|---|---|
| 34 | `document_intelligence/application/interfaces.py` — `SearchService(ABC)` | `capabilities/search_service` (stub routes) | Interface only | **Retain as Domain-Owned** | L | S | L | No | — |
| 35 | `document_intelligence/application/service.py` — `DefaultSearchService` (in-memory) | same (stub) | Real impl behind un-initialized orchestrator | **Canonical Provider Completion** | M | M | M | Yes | 14 |
| 36 | `document_intelligence/infrastructure/services.py` — `InfrastructureSemanticSearchService` | same (stub) | Real impl, dormant orchestrator | **Canonical Provider Completion** | M | M | M | Yes | 14 |
| 37 | `national/fhir/search.py` — `FHIRSearchEngine` (in-memory) | `backend/app/fhir` | Re-exported public API (`app/fhir/__init__.py`) | **Retain as Domain-Owned** | L | S | L | No | — |
 | 38 | `services/clinical_service.py` — `ResearchService` (research-registry CRUD) | `capabilities/search_service` | **Scanner signal-precision bug** — IGNORECASE matches embedded lowercase "search"; fixed via case-sensitive `search_engine` rule (Commits 1.4) | **False Positive** (remove with evidence) | L | S | L | No | 1 |

### 2.12 Workflow (3)

| # | Current implementation | Canonical provider | Behavioral equivalence | Class | Risk | Effort | Rollback | ADR | Order |
|---|---|---|---|---|---|---|---|---|---|
| 39 | `national/workflows/base.py` — `WorkflowEngine[T]` (ABC + 5 dormant subclasses) | `backend/app/workflows` (live promoted engine) | Dead (test-only consumers); canonical complete | **Archive and Re-point** | L | S | L | No | 11 |
| 44 | `national/workflow_runtime/api/routes.py` — `execute_workflow` (20 endpoints) | `backend/app/workflows` | **Wired but broken** — service.py is 0 bytes → every call raises ImportError | **Archive and Re-point** | M | M | L | Yes | 19 |

### 2.13 Rule Engine (1)

| # | Current implementation | Canonical provider | Behavioral equivalence | Class | Risk | Effort | Rollback | ADR | Order |
|---|---|---|---|---|---|---|---|---|---|
| 43 | `national/rules_engine/domain/expression_engine.py` — `ExpressionEngine.evaluate_rule` (complete) | `shared/rules_engine` (**domain types only — no engine**) | Finding is the ONLY real `evaluate_rule` in the platform | **Canonical Provider Promotion** | M | M | L | Yes | 12 |

### 2.14 Barcode (1)

| # | Current implementation | Canonical provider | Behavioral equivalence | Class | Risk | Effort | Rollback | ADR | Order |
|---|---|---|---|---|---|---|---|---|---|
| 40 | `models/sample.py` — `generate_barcode` (column default, live LIMS) | `shared/barcode` (dormant, different format) | **Different format/length** — re-point changes barcode values (data impact) | **Retain as Domain-Owned** | L | S | L | Yes | — |

---

## 3. Classification Summary

| Class | Count | Findings |
|---|---|---|
| **Archive and Re-point** | **16** | 1, 2, 3, 5, 6, 7, 9, 17, 20, 22, 25, 27, 28, 39, 42, 44 |
| **Canonical Provider Promotion** | **1** | 43 |
| **Canonical Provider Completion** | **7** | 24, 35, 36, 46, 47, 49, 50 |
| **Retain as Domain-Owned** | **24** | 4, 8, 10, 11, 12, 13, 14, 15, 16, 19, 21, 23, 26, 29, 30, 31, 32, 33, 34, 37, 40, 41, 45, 48 |
| **Strategic Exception** | **1** | 18 |
| **False Positive** (evidence-based removal) | **2** | 38, 51 |
| **Total** | **51** | |

**Notes:**

- **Retain as Domain-Owned (24)** includes two that are *de-facto* canonical
  facades with no duplication: #26 (`platform/notifications.py` — delegates to
  `app.notifications`) and #48 (`kernel/runtime_sdk.publish_event` — delegates
  to the kernel bus). Both are signal false-positives resolved by documentation,
  not code change.
- **Strategic Exception (1)** is #18 (kernel EventBus); the kernel cluster
  #11/#32/#33 are classified Retain-as-Domain-Owned but recommend being folded
  into the same kernel-domain ADR-030 (they carry the ADR tag via §4).
- **#42** (`integration/api_management/auth.py::APIAuth.check_permission`) is
  classified **Archive and Re-point** as an evidence-based **deletion** (dead —
  `APIGateway`/`APIPortal` never instantiated, zero callers/tests).

**Post-roadmap baseline:** 51 → **0 actionable** (2 false positives removed,
16 archived, 1 promoted, 7 completed, 1 strategic exception, 24 retained-and-
documented). The constitution gate continues to fail any NEW finding.

---

## 4. Strategic Exception — ADR-required (1)

### #18 Kernel Event Bus (`kernel/event_bus/bus.py::EventBus`)

- **Why exception:** the kernel event bus is a 809-LIVE-LOC subsystem with
  event store, outbox, inbox, DLQ, retry, replay, snapshots and a recovery
  engine — the production event backbone for 6+ national services. The
  canonical `shared/events` (41-L sync pub/sub) is a **strict subset**. The
  signal fires only because the canonical provider is minimal. Migrating would
  be a rewrite (H/H/H), not a refactor; retaining preserves the backbone.
- **Recommendation:** ADR-030 registers the kernel event bus (and by extension
  kernel `Scheduler`/`CronEngine`/`DIContainer`, findings 11/32/33 — see below)
  as a **kernel-domain Strategic Exception** — the kernel is its own bounded
  context whose infrastructure intentionally exceeds the minimal Shared Core
  providers.

### Kernel-domain cluster (findings 11, 18, 32, 33)

The kernel runtime (`backend/app/kernel/`) is LIVE platform infrastructure
(auto-booted in `startup_guard.py` Step 5, routers in `factory.py`). Its
`DIContainer`, `EventBus`, `Scheduler`, and `CronEngine` are all **supersets**
of the minimal Shared Core providers (`shared/di_container`,
`shared/events`, `shared/scheduler`) — which themselves have **zero consumers
and zero tests** repo-wide. Recommend a **single ADR** covering the kernel
cluster: Retain as kernel-domain, do not consolidate. Findings 11/32/33 then
carry the ADR tag too.

---

## 5. ADR Register (required ADRs during migration)

| ADR | Topic | Findings |
|---|---|---|
| ADR-030 | Kernel Domain Strategic Exception (event bus, DI, scheduler, cron) | 11, 18, 32, 33 |
| ADR-031 | Behavior-additive audit activation (canonical AuditService re-points) | 5, 9 |
| ADR-032 | Canonical Provider Completion — notifications (queue + delivery unification) | 24, 49, 50 |
| ADR-033 | Canonical Provider Completion — capability scaffolds (document/search/pdf wiring) | 35, 36, 46, 47 |
| ADR-034 | Retain-as-Domain-Owned register (authorization, barcode format, citizen inbox, document repos) | 13, 16, 23, 30, 40 |
| ADR-035 | Rule Engine Promotion (ExpressionEngine → shared/rules_engine) | 43 |
| ADR-036 | Workflow Runtime retirement (broken national workflow_runtime → canonical) | 44 |

ADRs 030, 035 are required **before** their migrations begin. ADR-031 is
required because audit re-points are behavior-additive (approval gate). ADR-032
touches delivery semantics (clinical-safety). ADR-034 documents retained
domain-owned code so the gate can acknowledge it. ADR-036 retires a wired-but-
broken national route surface.

---

## 6. Migration Roadmap — Execution Waves

### Wave 1 — Low-risk Archive & False-Positive removals (Commits 1.4–1.8)
*Pure dead code + stale baselines; no runtime path touched. Baseline 51 → 46.*

| Order | Finding | Class | Risk | ADR |
|---|---|---|---|---|
| 1 | #38 clinical_service (false positive) | Remove | L | No |
| 2 | #51 mobile_service verify_password (false positive) | Remove | L | No |
| 3 | #3 offline_sync EncryptedSyncStore | Archive | L | No |
| 4 | #6 doc-intel AuditLogger | Archive | L | No |
| 5 | #7 national security audit (broken) | Archive | L | No |
| 6 | #17 ESB message_bus + #42 APIAuth.check_permission (dead) | Delete | L | No |
| 7 | #20 national identity_service (dead route) | Archive | L | No |
| 8 | #22 risk_based_auth_service (dead) | Archive | L | No |
| 9 | #27 EmergencyQRService + #28 Persisted* twins (dead) | Archive | L | No |
| 10 | #25 workflow_runtime orphan interfaces | Archive | L | No |
| 11 | #39 national/workflows/base.py (dead ABC) | Archive | L | No |

### Wave 2 — Canonical Provider Promotion (Commit 1.9)
*ADR-035 first. Promote the only complete implementation into canonical path.*

| Order | Finding | Class | Risk | ADR |
|---|---|---|---|---|
| 12 | #43 ExpressionEngine → `shared/rules_engine` | **Promotion** | M | ADR-035 |

### Wave 3 — Canonical Provider Completions (Commits 1.10–1.12)
*Complete the canonical provider, then migrate. ADR-032/033 first.*

| Order | Finding | Class | Risk | ADR |
|---|---|---|---|---|
| 13 | #24+#49 identity notification queue → canonical | Completion | M | ADR-032 |
| 14 | #35+#36 doc-intel search → capabilities/search_service | Completion | M | ADR-033 |
| 15 | #46+#47 national document PDF → shared/pdf | Completion | M | ADR-033 |

### Wave 4 — High-risk infrastructure (Commits 1.13–1.15)
*Live paths, behavior-additive or broken-but-wired. Every commit needs explicit approval.*

| Order | Finding | Class | Risk | ADR |
|---|---|---|---|---|
| 16 | #5 doc-intel DefaultAuditService (no-op → canonical) | Archive (behavior-additive) | M | ADR-031 |
| 17 | #9 task_engine silent audit drop → canonical | Archive (behavior-additive) | M | ADR-031 |
| 18 | #50 national notification adapters fabricating success → canonical | Completion | **H** | ADR-032 |
| 19 | #44 workflow_runtime wired-but-500 → canonical engine | Archive | M | ADR-036 |

### Wave 5 — National Platform migrations (Commits 1.16–1.18)
*National-layer code; heavier coordination. Strategic Exceptions registered first.*

| Order | Finding | Class | Risk | ADR |
|---|---|---|---|---|
| 20 | #2 ecosystem EncryptionEngine (module surgery) | Archive | L | No |
| 21 | #1 doc-intel EncryptionService | Archive | L | No |
| 22 | #21+#30 legacy authorization (strategic path: NIAM) | Retain | M | ADR-034 |

### Wave 6 — Kernel Strategic Exception + Domain-Owned register (Commit 1.19)
*No code movement — documentation + gate recognition.*

| Order | Finding | Class | Risk | ADR |
|---|---|---|---|---|
| 23 | #18 kernel EventBus (**Strategic Exception**); #11/#32/#33 kernel DI/Scheduler/Cron (**Retain**, folded into same kernel-domain ADR) | Exception + Retain | — | ADR-030 |
| 24 | #4,8,10,12,13,14,15,16,19,21,23,26,29,30,31,34,37,40,41,45,48 | Retain (register) | — | ADR-034 |

**Result after all waves:** baseline 51 → **0 actionable findings** (2 false
positives removed; 16 archived; 1 promoted; 7 completed; 1 strategic exception;
24 retained-as-domain-owned documented in the baseline register). The gate
continues to fail any NEW finding.

---

## 7. Execution Ordering Rationale

1. **False positives / signal-precision first** (#38, #51): zero-risk,
   evidence-based; 51 → 49. (#38 required fixing the `search_engine` rule to
   case-sensitive so embedded lowercase "search" in `ResearchService` no longer
   false-positives — Commits 1.4. #51 required the `authentication` rule's
   `verify_password`/`create_access_token` signals to match definitions only,
   so canonical call sites are not flagged — Commits 1.5.)
2. **Dead-code archives before live migrations** (Wave 1): each is a single
   `git revert`; builds confidence; every commit verified end-to-end.
3. **Promotion before completion** (Wave 2 before Wave 3): promotion is
   self-contained (ADR-029 pattern); completion requires canonical rewiring.
4. **Behavior-additive & broken-live after the safe waves** (Wave 4): these
   change observable behavior (audit rows begin appearing; notification
   adapters begin sending) and need the approval gate + ADRs first.
5. **National layer last** (Wave 5): heavier blast radius, national-platform
   constraints.
6. **Kernel exception + Retain register last** (Wave 6): documentation-only,
   closes the baseline deterministically without code churn.

---

## 8. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Behavior-additive audit re-points (#5, #9) create new audit rows | Medium | ADR-031 approval gate; feature-flag; verify chain integrity post-change |
| Notification adapters (#50) begin actually sending | High (clinical-safety) | ADR-032; staged delivery enablement per channel; sandbox first |
| Workflow_runtime retirement (#44) removes a wired 500-surface | Medium | ADR-036; confirm no client depends on the 500 responses |
| Barcode format change (#40) alters sample barcodes | Medium (data) | Retained as domain-owned — no change; documented |
| Capability scaffold routers (document/search) currently return stubs | Medium | Wave 3 completion replaces stub responses with real behavior; OpenAPI re-check |
| Kernel retention may look like "not migrating" | Low | ADR-030 makes it a deliberate, documented exception |

---

## 9. Method & Evidence

- Classification derived from four parallel codebase analyses + independent
  verification of critical claims:
  - False positive #51 (import chain → `shared/auth` canonical) verified by
    direct scanner execution: the `authentication` rule matched the `verify_password`
    **call site** in `mobile_service.py` (imported from `security/auth.py`, the
    canonical wrapper of `shared/auth`); the two non-`def\s+` function signals
    were fixed to definition-only (Commits 1.5, baseline 51 → 49).
  - #44 (0-byte `service.py`) and #50 (8 adapters returning fabricated
    `success=True`) verified by direct file inspection.
- Canonical completeness verified per provider: `shared/security/encryption.py`
  (51 LOC, live), `identity/services/audit_service.py` (live hash-chain),
  `shared/events` (41 LOC), `shared/scheduler` (79 LOC, 0 consumers),
  `shared/di_container` (0 consumers), `shared/rules_engine` (types only),
  `shared/barcode` (dormant), `shared/qr` (live), `capabilities/*` (stub
  routers registered in factory), `backend/app/notifications` (real delivery),
  `backend/app/workflows` (live promoted engine).
- **No source code was modified, no files moved.** The single finding removed
  in Commit 1.4 (search_engine → clinical_service) was removed by fixing the
  scanner signal precision (`case_sensitive: True` on the `search_engine` rule)
  plus baseline + master-doc regeneration. This document remains analysis;
  Commit 1.4 is the first execution commit.
- **Commit 1.6 (Wave 1, order 3):** `EncryptedSyncStore` in
  `services/offline_sync_service.py` was proven dead (zero production importers
  repo-wide; sole consumer was its own test class `TestEncryptedSyncStore` in
  `backend/tests/test_offline_sync.py`) and archived byte-for-byte to
  `archive/platform-shared-core/encrypted_sync_store.py` (Commit 1.1/1.2
  precedent). The live `OfflineSyncEngine` in `integration/offline.py` is a
  different module and was untouched. Baseline 49 → 48.
- **Commit 1.7 (Wave 1, order 4):** `AuditLogger` in
  `document_intelligence/security.py` was proven dead (zero production
  importers repo-wide; sole consumer was its own test class
  `TestAuditLogger` in `backend/tests/test_docintel_enterprise.py`) and
  archived byte-for-byte (class + module singleton + accessor) to
  `archive/platform-shared-core/document_intelligence_audit_logger.py`
  (Commit 1.1/1.2/1.6 precedent). Canonical provider:
  `identity/services/audit_service.py` (hash-chained, 3+ active consumers —
  orphan check PASS).   `EncryptionService` (#1) and `IntegrityChecker` (not a
  finding) in the same module were untouched. Baseline 48 → 47.
- **Commit 1.8 (Wave 1, order 5):** `backend/app/national/security/audit.py`
  (whole dead module — `SecurityAuditEvent` + `SecurityAuditService`) was
  proven dead (zero production importers; sole consumer was the
  `national/security/__init__.py` re-export, removed with the move) and
  archived byte-for-byte via `git mv` (rename detected, 0 insertions/0
  deletions — Commit 1.1/1.2 precedent) to
  `archive/platform-shared-core/national_security_audit.py`. Canonical
  provider: `identity/services/audit_service.py` (orphan check PASS — 3+
  active consumers). The rest of `national/security/` (abac, rbac,
  break_glass, etc.) was untouched. Baseline 47 → 46.

## 10. Next Action

Commits 1.4–1.8 executed: two false positives removed (#38, #51) and three
dead-code archives landed (#3 `EncryptedSyncStore`, #6 doc-intel `AuditLogger`,
#7 national `SecurityAuditService`; baseline 51 → 46). Next: begin **Wave 1,
order 6** — #17 ESB `message_bus` + #42 `APIAuth.check_permission` delete
(dead, evidence-based), run the full verification cycle, commit, and STOP.
