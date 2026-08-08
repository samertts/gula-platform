# TECHNICAL DEBT REGISTER — PROGRAM-01 (FINAL — LOCKED)

> **Owner:** Autonomous Chief Software Architect / Program Director
> **Scope:** Frozen register of all Shared Core findings (25 remaining) + program-level technical debt
> **Basis:** `.ai/core/architecture/constitution_baseline.json` (FINAL, 25 findings with states), `ARCHITECTURAL_MIGRATION_CLASSIFICATION.md`, `ARCHITECTURE_CONSTITUTION.md`
> **Gate state:** Shared Core **25/25** acknowledged (0 new); Domain 11/11; Country PASS; Policy PASS
> **Status:** PROGRAM-01 FINAL CLOSURE — every finding frozen to exactly one state (Domain-Owned / Strategic Exception / False Positive / Deferred); no unresolved classification.

---

## 1. Per-Finding Register (25 frozen + 2 resolved)

Legend — **Class (current):** R = Retain as Domain-Owned, SE = Strategic Exception,
A = Archive pending, FP = False positive (evidence-based). **Runtime:** LIVE = reachable
through a wired router/consumer path; DORMANT = no runtime consumer, interfaces/ABCs only;
FACADE = delegating wrapper, no duplication. **Recommended:** where the finding should land.

### 1.1 identity (2)

| # | Path | Signal | Class | Runtime | Risk | Rec. Action | ADR | Wave |
|---|---|---|---|---|---|---|---|---|
| 19 | `citizen_platform/identity.py` — `HealthIdentityService` (national-id verify) | IdentityService | R | LIVE (citizen_platform wired; sdk.py + integration.py import) | L | Retain register (ADR-034); NIAM CitizenRegistry is the strategic path | 034 | 6 |
| 21 | `services/authorization_service.py` — `IdentityService.get_identity_context` (legacy lab-UI) | IdentityService | R | LIVE (`routes/authorization.py` wired) | M | Retain, register + document strategic NIAM path | 034 | 5/6 |

### 1.2 notifications (2)

| # | Path | Signal | Class | Runtime | Risk | Rec. Action | ADR | Wave |
|---|---|---|---|---|---|---|---|---|
| 23 | `citizen_platform/notifications.py` — `CitizenNotificationService` (in-memory inbox) | NotificationService | R | LIVE (sdk.py, integration.py) | M | Retain register; canonical delivers, this persists in-memory — documented data-loss constraint | 034 | 6 |
| 26 | `platform/notifications.py` — `NotificationService` (facade over `app.notifications`) | NotificationService | FP | LIVE (canonical facade) | L | Retain register; de-facto canonical facade, zero duplication | 034 | 6 |

### 1.3 authorization (2)

| # | Path | Signal | Class | Runtime | Risk | Rec. Action | ADR | Wave |
|---|---|---|---|---|---|---|---|---|
| 29 | `control_plane/policy/enforcer.py` — `PolicyEnforcer` (component-governance policy) | PolicyEnforcer | R | LIVE (control_plane wired; policy/manager + routes) | L | Retain register — component governance, NOT user access control | 034 | 6 |
| 30 | `services/authorization_service.py` — `PermissionService/RoleService/PolicyService` (parallel ABAC) | PermissionService | R | LIVE (`routes/authorization.py` wired) | M | Retain + register ADR-034; document `Policy.evaluate_policies` vs `security/abac.py` duplication rationale | 034 | 5/6 |

### 1.4 audit (3)

| # | Path | Signal | Class | Runtime | Risk | Rec. Action | ADR | Wave |
|---|---|---|---|---|---|---|---|---|
| 4 | `document_intelligence/application/interfaces.py` — `AuditService(ABC)` | AuditService | R | DORMANT (interface only; importers=0) | L | Retain register | 034 | 6 |
| 8 | `national/task_engine/domain/repository.py` — `TaskAuditLogRepository(ABC)` | AuditLogRepository | R | LIVE (task_engine wired; infra now `CanonicalTaskAuditRepository` → canonical, re-pointed order 17; the archived #9 infra silent-drop is gone) | L | Retain register — ABC (domain contract) remains; behavior re-pointed to canonical | 034 | 6 |
| 10 | `services/authorization_service.py` — `AuthorizationAuditService` (decision-log, own schema) | AuditService | R | LIVE (`routes/authorization.py`) | L | Retain register — canonical lacks decision/policy/risk fields | 034 | 6 |

### 1.5 search_engine (2)

| # | Path | Signal | Class | Runtime | Risk | Rec. Action | ADR | Wave |
|---|---|---|---|---|---|---|---|---|
| 34 | `document_intelligence/application/interfaces.py` — `SearchService(ABC)` | SearchService | R | DORMANT (interface only) | L | Retain register | 034 | 6 |
| 37 | `national/fhir/search.py` — `FHIRSearchEngine` (in-memory) | SearchEngine | R | LIVE re-export (`app/fhir/__init__.py`, `national/fhir/__init__.py`) | L | Retain register — public re-exported API | 034 | 6 |

### 1.6 document_engine (6)

| # | Path | Signal | Class | Runtime | Risk | Rec. Action | ADR | Wave |
|---|---|---|---|---|---|---|---|---|
| 45 | `document_intelligence/application/interfaces.py` — `generate_pdf` (abstract) | generate_pdf | R | DORMANT (abstract) | L | Retain register | 034 | 6 |
| 12 | `document_intelligence/domain/repository.py` — `DocumentRepository(ABC)` | DocumentRepository | R | DORMANT (interface) | L | Retain register | 034 | 6 |
| 13 | `document_intelligence/infrastructure/repository.py` — `SqlDocumentRepository` (real SQLAlchemy) | DocumentRepository | R | DORMANT orchestrator; reachable via `wiring.py::get_orchestrator` | M | Retain register — canonical `capabilities/document_management` is a stub, cannot re-point | 034 | 6 |
| 14 | `national/document_platform/application/interfaces.py` — `PDFGenerator(ABC)` | DocumentRepository | R | DORMANT (interface) | L | Retain register | 034 | 6 |
| 15 | `national/document_platform/domain/repository.py` — `DocumentRepository(ABC)` | DocumentRepository | R | DORMANT (interface) | L | Retain register | 034 | 6 |
| 16 | `national/document_platform/infrastructure/repository.py` — `SQLAlchemyDocumentRepository` (real) | DocumentRepository | R | LIVE (document_platform wired) | M | Retain register — canonical is a stub, live repo is real | 034 | 6 |

### 1.7 scheduler (3)

| # | Path | Signal | Class | Runtime | Risk | Rec. Action | ADR | Wave |
|---|---|---|---|---|---|---|---|---|
| 31 | `document_intelligence/backup_dr.py` — `BackupScheduler` (async DR loop) | Scheduler | R | DORMANT (re-exported in `__init__` only) | L | Retain register | 034 | 6 |
| 32 | `kernel/background/cron.py` — `CronEngine` (registry only) | CronEngine | R | LIVE (kernel bootloader) | L | Retain, folded into kernel-domain ADR-030 | 030 | 6 |
| 33 | `kernel/background/scheduler.py` — `Scheduler` (269-L composition root) | Scheduler | R | LIVE (kernel bootloader) | L | Retain, folded into kernel-domain ADR-030 | 030 | 6 |

### 1.8 encryption (2) — **RESOLVED in PROGRAM-01 FINAL CLOSURE (Wave 5)**

| # | Path | Signal | Class | Runtime | Risk | Rec. Action | ADR | Wave | Status |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `document_intelligence/security.py` — `EncryptionService` / Fernet | Fernet | A | DORMANT orchestrator; reachable via `wiring.py` `DefaultEncryptionService` | L | **Module surgery** — delegate to canonical `shared/security/encryption.py` `encrypt_bytes`/`decrypt_bytes` | No | 5 | ✅ **RESOLVED** |
| 2 | `national/ecosystem/transformation/engine.py` — Fernet usage | Fernet | A | LIVE (ecosystem wired; `routes.py` instantiates `TransformationEngine`) | L | **Module surgery** — carve Fernet out to canonical `shared/security/encryption.py` `encrypt_value`/`decrypt_value` (SHA-256 derivation preserved) | No | 5 | ✅ **RESOLVED** |

### 1.9 events (2)

| # | Path | Signal | Class | Runtime | Risk | Rec. Action | ADR | Wave |
|---|---|---|---|---|---|---|---|---|
| 18 | `kernel/event_bus/bus.py` — `EventBus` (809-L: store/outbox/DLQ/replay) | EventBus | SE | LIVE (kernel backbone, 15 importers) | L (retain) / H (only if migrated) | **Strategic Exception** — ADR-030; no migration | 030 | 6 |
| 48 | `kernel/runtime_sdk.py` — `publish_event` (facade over kernel bus) | publish_event | FP | LIVE (facade) | L | Retain register — facade, not reimplementation | 034 | 6 |

### 1.10 dependency_injection (1)

| # | Path | Signal | Class | Runtime | Risk | Rec. Action | ADR | Wave |
|---|---|---|---|---|---|---|---|---|
| 11 | `kernel/runtime/di_container.py` — `DIContainer` (name-keyed locator) | DiContainer | R | LIVE (kernel bootloader) | M | Retain, folded into kernel-domain ADR-030 — API rewrite, no behavior gain | 030 | 6 |

### 1.11 barcode_engine (1)

| # | Path | Signal | Class | Runtime | Risk | Rec. Action | ADR | Wave |
|---|---|---|---|---|---|---|---|---|
| 40 | `models/sample.py` — `generate_barcode` (column default, live LIMS) | generate_barcode | R | LIVE (LIMS) | L | Retain register — different format/length; re-point changes barcode values (data impact) | 034 | 6 |

### 1.12 qr_engine (1)

| # | Path | Signal | Class | Runtime | Risk | Rec. Action | ADR | Wave |
|---|---|---|---|---|---|---|---|---|
| 41 | `national/document_platform/application/service.py` — `generate_qr` (doc-verify token) | generate_qr | R | LIVE (document_platform service delegator) | L | Retain register — document verification token, not image QR | 034 | 6 |

### 1.13 Summary of recommended disposition

| Disposition | Count | Findings | State |
|---|---|---|---|
| **RESOLVED — module surgery (Wave 5, FINAL CLOSURE)** | 2 | #1, #2 | ✅ done — canonical delegation, behavior preserved |
| **Strategic Exception** (ADR-030) | 1 | #18 | frozen |
| **Retain — kernel domain register** (ADR-030) | 3 | #11, #32, #33 | frozen |
| **Retain — domain-owned register** (ADR-034) | 19 | #4, #8, #10, #12, #13, #14, #15, #16, #19, #21, #23, #29, #30, #31, #34, #37, #40, #41, #45 | frozen |
| **False positive / canonical facade** (register) | 2 | #26, #48 | frozen |
| **Total frozen** | **25** | — | all 25 frozen, 0 unresolved |

**PROGRAM-01 result:** 51 findings → **2 resolved in FINAL CLOSURE** + **25 frozen**
(19 Domain-Owned + 1 Strategic Exception + 3 kernel-domain register + 2 False Positive)
→ **0 actionable**. The gate continues to fail any NEW finding (deterministic baseline).

---

## 2. Non-Finding Technical Debt (program-level) — FROZEN

Every debt has a unique ID, description, severity, owner, target program, priority, status,
and estimated effort.

| ID | Description | Severity | Owner | Target Program | Priority | Status | Effort |
|---|---|---|---|---|---|---|---|
| TD-01 | Docker Compose v2 unavailable on host; multi-container orchestration uses raw `docker` | Medium | DevOps | PROGRAM-02 | High | Open | 2 d |
| TD-02 | No automated release pipeline / versioning for backend+frontend artifacts; 43 K8s manifests not exercised by CI | Medium | DevOps | PROGRAM-02 | High | Open | 5 d |
| TD-03 | Frontend `/metrics` page WARN remains (PROGRAM-011 burn-down carry-over) | Low | FE | PROGRAM-02 | Medium | Open | 2 d |
| TD-04 | Cloud snapshot restore WARN remains (S3 restore untested live) | High | DevOps | PROGRAM-02 | High | Open | 3 d |
| TD-05 | ENCRYPTION_KEY rotation re-encryption WARN remains (tool + rotate-guard exist; live rotation unexercised) | High | Sec | PROGRAM-02 | High | Open | 3 d |
| TD-06 | 71 N999 module-name violations (mostly dormant `national_data/models/warehouse/` star-schema) — advisory | Low | Eng | PROGRAM-02 | Low | Open | 4 d |
| TD-07 | `mypy` full-backend timeout (capabilities/ modules) — per-module config recommended | Low | Eng | PROGRAM-02 | Medium | Open | 2 d |
| TD-08 | 62 `backref=` remain in inactive bounded contexts — advisory | Low | Eng | PROGRAM-02 | Low | Open | 3 d |
| TD-09 | 67 inactive bounded-context pages untranslated (i18n) — dormant contexts only | Low | FE | PROGRAM-02 | Low | Open | 5 d |
| TD-10 | `platform/notifications.py` facade + `kernel/runtime_sdk.py` re-exports keep dormant signal surface (documented de-facto canonical) | Low | Arch | PROGRAM-01 baseline | — | **Frozen** (False Positive) | 0 |
| TD-11 | Zero-drift engine regenerates 30+ tracked files (incl. docs) even on `--help` — churn risk; governed via reverted state | Low | Arch | PROGRAM-01 baseline | — | **Frozen** (accepted) | 0 |
| TD-12 | Integration suite requires live PG container at `172.18.0.3:5432` (localhost refused) — CI must pin network | Medium | DevOps | PROGRAM-02 | High | Open | 1 d |

**Count:** 12 identified, 0 unidentified. **Open:** 10 (all target PROGRAM-02). **Frozen in baseline:** 2 (TD-10, TD-11 — documented accepted).

---

## 3. Commit-3.6 Rollback Evidence (ADR-028 compliance)

Single `git revert` of `6aadb55c` restores all 15 archived `national/workflow_runtime/`
files + `platform/workflow.py` with provenance headers — verified. Independent revert of
`83c4601b` / `a03794e5` (docs-only) carries no production risk.

## 4. Provenance / Sources

- `.ai/core/architecture/constitution_baseline.json` — the 25 frozen findings + 2 resolved (authoritative)
- `docs/baselines/ARCHITECTURAL_MIGRATION_CLASSIFICATION.md` — class/risk/effort/ADR per finding
- `docs/baselines/COMMIT_3_6_VERIFICATION_REPORT.md` — Commit 3.6 evidence
- `backend/tests/test_encryption_canonical.py` — Wave-5 regression evidence (#1, #2 resolved)
- `MASTER_REMAINING_WORK.md` — capability-level view
