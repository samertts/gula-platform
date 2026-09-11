# Reusable capability catalog

**PROGRAM-EXT-001, Phase 5.** Measured, not designed.

Before building anything, look here. The Platform Constitution's *Reuse Before
Build* article is the rule; this page is the evidence needed to follow it.

## 1. Method

Every `*Service` class in `app/` was enumerated by name, then grouped by the
concept it implements. Disposition is one of KEEP (canonical, use it),
CONSOLIDATE (several exist, one must win — decision required), REUSE (canonical
exists, stop writing new ones), REPLACE, DEFER.

Nothing was consolidated by this batch. Choosing which of four notification
services is canonical is an ownership decision, and guessing would create a
fifth.

## 2. The catalog

| Concept | Implementations found | Disposition |
| --- | --- | --- |
| **Audit** | `identity/services/audit_service.py` (v1), `identity/services/canonical_audit.py` (v2), `platform/audit.py`, `document_intelligence/.../interfaces.py` (2 ABCs) | **KEEP** `CanonicalAuditService` as canonical. v1 and v2 share one table separated by `event_version` and that is deliberate. `platform/audit.py` is a third writer — **CONSOLIDATE** |
| **Notification** | `identity/notifications/services.py`, `platform/notifications.py`, `national/notification_platform/application/service.py`, `notifications/service.py` | **CONSOLIDATE** — four implementations of one concept. Decision required: which is canonical |
| **Document** | `platform/documents.py`, `national/document_platform/application/service.py`, `document_intelligence/` (4 ABCs), `capabilities/document_management/` (dead) | **CONSOLIDATE** — and note that the capability package is the one that cannot import |
| **Workflow** | `platform/workflow.py`, `national/workflow_runtime/application/service.py`, `identity/workflows/engine.py`, `capabilities/workflow_engine/` (dead) | **CONSOLIDATE** |
| **Consent** | `identity/services/consent_service_v2.py` (`NiamConsentService`), `trust/services.py` (`ConsentService`), `national/security/consent_enforcement.py`, `capabilities/healthcare_consent/` (dead) | **CONSOLIDATE** — and the registry lists both `consent_management` (2.1.0) and `healthcare_consent` (1.0.0), which is the same duplication at the descriptor level |
| **Terminology** | `services/clinical_service.py::TerminologyService`, `integration/standards/terminology.py::TerminologyService` | **CONSOLIDATE** — two classes, same name, different modules |
| **Search** | `platform/search.py`, `capabilities/search_service/` (dead), 5 domain-local searchers | **REUSE** `platform/search.py` |
| **Verification** | `identity/services/verification_service.py` (protocol), `verification_workflow.py` (writer), `verification_record_service.py` (reader) | **KEEP** — this one is already canonical and layered correctly (AUTH-004/005) |
| **Identity** | `app/identity/` | **KEEP** — single trusted provider; no domain may implement its own |
| **Approval** | `identity/governance/services.py::PolicyApprovalService`, 1 other | **DEFER** — too little in place to consolidate |
| **Task / queue** | `national/task_engine/`, `kernel/background/` | **DEFER** |
| **Attachment** | 2 modules, no service class | **DEFER** |
| **Appointment** | 2 modules, 1 service | **DEFER** |
| **Referral** | 5 modules, 1 service | **DEFER** |
| **Storage** | `capabilities/storage_service/` (dead) | **REPLACE** — nothing usable exists; the only implementation cannot import |
| **Import/export** | `platform/export.py` | **KEEP** |

## 3. What the duplication costs

Four notification services means four places a national alert can silently fail
to send, and no single place to look. Two `TerminologyService` classes with the
same name in different modules means an import fixes which one you get by
accident of path.

None of this is hypothetical drift; it is what the repository contains today.

## 4. The rule going forward

Guard `test_a_new_capability_does_not_duplicate_a_canonical_one` blocks a **new**
capability descriptor whose name collides with a canonical concept in the table
above. It does not attempt to consolidate what is already there — that requires
the decisions in §2, and those are the user's.

## 5. Decisions required

1. Canonical **notification** service — four candidates.
2. Canonical **document** service — three live candidates plus one dead.
3. Canonical **workflow** engine — three live plus one dead.
4. Canonical **consent** service — three live plus one dead, and two registry
   descriptors for the same concept.
5. Canonical **terminology** service — two.
6. Whether `platform/audit.py` may write audit at all, given
   `CanonicalAuditService` is the hash-chained writer.
7. `app/capabilities/` (NR-050): complete these ten packages, or retire them.
